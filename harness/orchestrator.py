from dataclasses import asdict
from pathlib import Path
import ast
import difflib
import hashlib
import json
import os
import re
import time
import uuid
from collections import Counter
from .state import TaskState
from .context import ContextManager
from .models import ProtocolError, ModelError, ModelHTTPError, ServiceUnavailableError
from .rate_limits import RateLimitError
from .tools import ToolRegistry, profile_repository

SKIP = {'.git', '.venv', 'venv', 'node_modules', '__pycache__', 'artifacts', '.pytest_cache', 'target', 'dist'}

def snapshot(repo, exclude=None):
    result = {}
    for base, dirs, files in os.walk(repo, followlinks=False):
        dirs[:] = [d for d in dirs if d not in SKIP and not (Path(base) / d).is_symlink() and (exclude is None or (Path(base) / d).resolve() != exclude)]
        for name in files:
            path = Path(base) / name
            if path.is_symlink() or not path.is_file():
                continue
            rel = str(path.relative_to(repo))
            if path.stat().st_size <= 1_000_000:
                result[rel] = path.read_bytes()
            else:
                digest = hashlib.sha256()
                with path.open('rb') as source:
                    for chunk in iter(lambda: source.read(65536), b''):
                        digest.update(chunk)
                result[rel] = ('[large file SHA256: ' + digest.hexdigest() + ']\n').encode()
    return result

def protected(path):
    p = Path(path)
    return any(x.lower() in {'tests', 'test', 'evaluation', 'eval', 'evals', '.github', '.agents', '.codex'} for x in p.parts) or p.name.startswith('test_') or p.name.endswith(('_test.py', '_test.go', '.test.js', '.spec.ts'))

def diff_snapshots(before, after):
    changed = sorted(k for k in before.keys() | after.keys() if before.get(k) != after.get(k))
    sections = []
    for name in changed:
        lines = difflib.unified_diff(before.get(name, b'').decode('utf-8', errors='replace').splitlines(True),
                                    after.get(name, b'').decode('utf-8', errors='replace').splitlines(True),
                                    fromfile='a/' + name, tofile='b/' + name)
        for line in lines:
            sections.append(line if line.endswith('\n') else line + '\n\\ No newline at end of file\n')
    text = ''.join(sections)
    return changed, text

class Orchestrator:
    def __init__(self, repo, issue, adapter, artifacts=Path('artifacts'), max_steps=50,
                 context_budget=12000, token_budget=100000, wall_seconds=600,
                 command_timeout=30, test_commands=None, token_reserve=None):
        self.repo = Path(repo).resolve()
        if not self.repo.is_dir():
            raise ValueError('Repository path must be an existing directory')
        self.adapter = adapter
        self.state = TaskState(issue, str(self.repo))
        self.tools = ToolRegistry(self.repo, timeout=command_timeout)
        self.context = ContextManager(context_budget)
        self.max_steps, self.token_budget, self.wall_seconds = max_steps, token_budget, wall_seconds
        # Split reserve between correction/protocol recovery and final review.
        # This is part of (never additional to) the total token allowance.
        if token_reserve is None:
            token_reserve = min(12000, int(token_budget * 0.15))
        if isinstance(token_reserve, bool) or not isinstance(token_reserve, int) or not 0 <= token_reserve <= token_budget:
            raise ValueError('token_reserve must be an integer between zero and token_budget')
        self.token_reserve = token_reserve
        self.budget_phase = 'normal'
        self.test_commands = test_commands
        self.artifacts = Path(artifacts).resolve() / (time.strftime('%Y%m%d-%H%M%S') + '-' + uuid.uuid4().hex[:8])
        self.artifacts.mkdir(parents=True)
        self.before = snapshot(self.repo, self.artifacts)
        self.start = time.monotonic()
        if hasattr(self.adapter, 'pacer') or hasattr(self.adapter, 'deadline'):
            self.adapter.deadline = self.start + self.wall_seconds
        if hasattr(self.adapter, 'pacer') or hasattr(self.adapter, 'event_callback'):
            self.adapter.event_callback = self.event
        self.failures = Counter()
        self.pending_recovery = False

    def event(self, kind, **payload):
        with (self.artifacts / 'events.jsonl').open('a') as f:
            f.write(json.dumps({'event': kind, 'elapsed_seconds': round(time.monotonic() - self.start, 3), **payload}) + '\n')
        self.state.save(self.artifacts / 'state.json')

    def failure(self, category, message):
        fingerprint = category + ':' + message[:300]
        self.failures[fingerprint] += 1
        repeated = self.failures[fingerprint]
        record = {'category': category, 'message': message[:2000], 'repeated': repeated}
        self.state.failures.append(record)
        self.state.recoveries += 1
        self.pending_recovery = True
        self.budget_phase = 'corrective'
        self.event('recovery', **record)
        instruction = 'Replan and use an alternate approach.' if repeated >= 3 else 'Inspect failure and repair.'
        if category in ('ProtocolError', 'MODEL_PROTOCOL_ERROR'):
            self.context.recover_protocol()
            instruction = ('Your last response was rejected; no invalid action was executed. '
                           'Return exactly one JSON object with action and arguments, no markdown or commentary. '
                           'Use only available tool names. '
                           'Escape quotes/newlines inside source strings as JSON. Example: '
                           '{"action":"read_file","arguments":{"path":"README.md"},"goal":"inspect"}. '
                           'Choose the next useful action from the existing evidence; do not restart diagnosis.')
        self.context.add({'action': 'recovery'}, {'ok': False, **record, 'instruction': instruction})
        if repeated > 3:
            self.state.status, self.state.reason = 'FAILED', 'Repeated failure exhausted recovery budget'

    def verify(self, semantic_review):
        self.budget_phase = 'verification_review'
        after = snapshot(self.repo, self.artifacts)
        changed, diff = diff_snapshots(self.before, after)
        (self.artifacts / 'final.diff').write_text(diff)
        self.state.tool_calls += 1
        self.event('verification', stage='diff', files=changed)
        # Model sees the final diff before a subsequent finish can be accepted.
        digest = hashlib.sha256(diff.encode()).hexdigest()
        if getattr(self, 'review_digest', None) != digest:
            self.review_digest = digest
            self.review_chunks = []
            cursor = 0
            while cursor < len(diff):
                size = min(4000, len(diff) - cursor)
                while len(json.dumps(diff[cursor:cursor + size])) > 4500:
                    size //= 2
                self.review_chunks.append(diff[cursor:cursor + size])
                cursor += size
            self.review_chunks = self.review_chunks or ['(empty diff)']
            self.review_cursor = 0
        if self.review_cursor < len(self.review_chunks):
            chunk = self.review_chunks[self.review_cursor]
            self.review_cursor += 1
            self.context.add({'action': 'final_diff_review'}, {
                'ok': True, 'output': chunk, 'chunk': self.review_cursor,
                'chunks': len(self.review_chunks),
                'instruction': 'Review this diff chunk. Call finish again to obtain remaining chunks or request verification after the last chunk.'})
            return False
        if not changed:
            self.state.verification = 'UNVERIFIED'
            self.state.status, self.state.reason = 'UNVERIFIED', 'No code change produced'
            return False
        if any(protected(k) for k in changed):
            self.state.verification = 'FAIL'
            self.failure('VERIFICATION_FAILURE', 'Protected test/evaluation infrastructure changed; restore it before finishing')
            return False
        for name in changed:
            if name.endswith('.py') and name in after:
                try:
                    ast.parse(after[name], filename=name)
                except (SyntaxError, ValueError) as e:
                    self.state.verification = 'FAIL'
                    self.failure('VERIFICATION_FAILURE', str(e))
                    return False
        commands = self.test_commands if self.test_commands is not None else self.profile.get('test_commands', [])
        if not commands:
            self.state.status, self.state.reason = 'UNVERIFIED', 'No runnable verification command discovered; provide --test-command'
            self.state.verification = 'UNVERIFIED'
            return False
        if getattr(self, 'verified_snapshot', None) != after:
            for command in commands:
                if time.monotonic() - self.start >= self.wall_seconds:
                    self.state.status, self.state.reason = 'BUDGET_EXHAUSTED', 'Wall-clock budget exhausted during verification'
                    return False
                self.tools.timeout = min(self.tools.timeout, max(0.1, self.wall_seconds - (time.monotonic() - self.start)))
                result = self.tools.execute('run_tests', {'command': command})
                self.state.tool_calls += 1
                self.state.tests.append({'command': command, **result})
                self.event('test_run', command=command, result=result)
                self.context.add({'action': 'run_tests', 'arguments': {'command': command}}, result)
                output = result.get('output', '').lower()
                if not result.get('ok') or 'ran 0 tests' in output or 'no tests ran' in output:
                    self.state.verification = 'FAIL'
                    self.failure('VERIFICATION_FAILURE', json.dumps(result))
                    return False
        verified_after = snapshot(self.repo, self.artifacts)
        command_changes, _ = diff_snapshots(after, verified_after)
        if any(protected(name) for name in command_changes):
            self.state.verification = 'FAIL'
            self.failure('VERIFICATION_FAILURE', 'Verification commands changed protected test/evaluation files')
            return False
        self.verified_snapshot = verified_after
        if verified_after != after:
            self.state.verification = 'PASS_PENDING_REVIEW'
            self.event('verification', stage='post_test_diff', files=command_changes)
            self.context.add({'action': 'post_test_diff'}, {
                'ok': True, 'output': 'Verification commands passed but changed repository files.',
                'instruction': 'Call finish to review the updated diff. Unchanged verified content does not need another test run.'})
            return False
        if not isinstance(semantic_review, str) or not semantic_review.strip():
            self.failure('VERIFICATION_FAILURE', 'finish requires a semantic_review of behavior, edge cases, and test integrity')
            return False
        self.state.verification, self.state.status = 'PASS', 'RESOLVED'
        self.state.reason = semantic_review
        # Task-level verified recovery, not success of an unrelated read/search.
        if self.pending_recovery:
            self.state.successful_recoveries = 1
            self.pending_recovery = False
            self.event('verified_recovery', metric='task passed final verification after failure feedback')
        return True

    def run(self):
        self.profile = profile_repository(self.repo)
        if self.test_commands is not None:
            self.profile['discovered_test_commands'] = self.profile.get('test_commands', [])
            self.profile['test_commands'] = self.test_commands
            self.profile['test_command_source'] = 'provided verification commands'
        self.event('session_start', repo=str(self.repo), issue=self.state.issue)
        self.event('repo_profile', profile=self.profile)
        schemas = self.tools.schemas() + [
            {'type': 'function', 'function': {'name': 'update_plan', 'description': 'Set or revise task plan', 'parameters': {'type': 'object', 'properties': {'steps': {'type': 'array', 'items': {'type': 'string'}}}, 'required': ['steps']}}},
            {'type': 'function', 'function': {'name': 'record_findings', 'description': 'Retain model hypothesis, evidence locations, next action; each field at most 500 characters', 'parameters': {'type': 'object', 'properties': {'hypothesis': {'type': 'string'}, 'evidence': {'type': 'string'}, 'next_action': {'type': 'string'}}, 'required': ['hypothesis', 'evidence', 'next_action'], 'additionalProperties': False}}},
            {'type': 'function', 'function': {'name': 'finish', 'description': 'Request independent completion verification', 'parameters': {'type': 'object', 'properties': {'summary': {'type': 'string'}, 'semantic_review': {'type': 'string'}}, 'required': ['summary', 'semantic_review']}}}]
        try:
            for step in range(self.max_steps):
                if self.state.status != 'RUNNING':
                    break
                self.state.steps = step + 1
                if time.monotonic() - self.start >= self.wall_seconds or self.state.input_tokens + self.state.output_tokens >= self.token_budget:
                    self.state.status, self.state.reason = 'BUDGET_EXHAUSTED', 'Time or total-token budget exhausted'
                    break
                remaining = self.token_budget - self.state.input_tokens - self.state.output_tokens
                phase = 'protocol_recovery' if self.context.protocol_recovery else self.budget_phase
                held_reserve = (self.token_reserve if phase == 'normal' else
                                self.token_reserve // 2 if phase in ('corrective', 'protocol_recovery') else 0)
                # Enter a bounded correction phase when ordinary diagnosis no
                # longer fits. Reads remain available; do not mandate an edit.
                if phase == 'normal' and remaining - held_reserve < 768:
                    self.budget_phase = phase = 'corrective'
                    held_reserve = self.token_reserve // 2
                request_allowance = remaining - held_reserve
                budget_profile = {**self.profile, 'token_budget_guidance':
                    'Token allowance is finite. Use retained diagnosis for small corrective actions; narrow reads remain allowed. '
                    'Request targeted verification and finish/diff review promptly once the change is ready.'}
                normal_context_budget = self.context.budget
                available_context = max(1, int((request_allowance - 768) / 1.25))
                self.context.budget = min(normal_context_budget, available_context)
                try:
                    try:
                        messages = self.context.pack(self.state, budget_profile, schemas, self.adapter)
                    except ValueError:
                        if phase != 'normal' or available_context >= normal_context_budget:
                            raise
                        self.budget_phase = phase = 'corrective'
                        held_reserve = self.token_reserve // 2
                        request_allowance = remaining - held_reserve
                        available_context = max(1, int((request_allowance - 768) / 1.25))
                        self.context.budget = min(normal_context_budget, available_context)
                        messages = self.context.pack(self.state, budget_profile, schemas, self.adapter)
                except ValueError:
                    if available_context < normal_context_budget:
                        self.state.status = 'BUDGET_EXHAUSTED'
                        self.state.reason = 'Remaining estimated token allowance cannot fit essential task context with phase reserve held; no request sent'
                        self.event('request_budget_guard', remaining=remaining, phase=phase, held_reserve=held_reserve)
                        break
                    raise
                finally:
                    self.context.budget = normal_context_budget
                estimate_request = getattr(self.adapter, 'estimate_request_tokens', None)
                request_input_tokens = (estimate_request(messages, schemas) if estimate_request else
                                        self.adapter.count_or_estimate_tokens(messages) +
                                        self.adapter.count_or_estimate_tokens(schemas))
                estimated_input = int(1.25 * request_input_tokens) + 256
                if phase == 'normal' and request_allowance < estimated_input + 512:
                    self.budget_phase = phase = 'corrective'
                    held_reserve = self.token_reserve // 2
                    request_allowance = remaining - held_reserve
                if request_allowance < estimated_input + 512:
                    self.state.status = 'BUDGET_EXHAUSTED'
                    self.state.reason = 'Insufficient estimated tokens for another request and minimum response with phase reserve held; no request sent'
                    self.event('request_budget_guard', remaining=remaining, estimated_input=estimated_input,
                               phase=phase, held_reserve=held_reserve)
                    break
                original_output_limit = getattr(self.adapter, 'max_output_tokens', None)
                if original_output_limit is not None:
                    self.adapter.max_output_tokens = min(original_output_limit, request_allowance - estimated_input)
                request_output_limit = getattr(self.adapter, 'max_output_tokens', 2048)
                self.event('token_reserve_decision', phase=phase, remaining=remaining,
                           configured_reserve=self.token_reserve, held_reserve=held_reserve,
                           estimated_input=estimated_input, request_allowance=request_allowance,
                           output_limit=request_output_limit,
                           output_limit_enforced=original_output_limit is not None)
                self.state.llm_calls += 1
                if hasattr(self.adapter, 'timeout'):
                    self.adapter.timeout = min(self.adapter.timeout, max(0.1, self.wall_seconds - (time.monotonic() - self.start)))
                try:
                    try:
                        response = self.adapter.generate(messages, tools=schemas)
                    finally:
                        if original_output_limit is not None:
                            self.adapter.max_output_tokens = original_output_limit
                except (ProtocolError, ModelError) as e:
                    input_tokens = getattr(e, 'input_tokens', request_input_tokens)
                    output_tokens = getattr(e, 'output_tokens', request_output_limit)
                    usage_estimated = getattr(e, 'usage_estimated', True)
                    self.state.input_tokens += input_tokens
                    self.state.output_tokens += output_tokens
                    self.state.usage_estimated |= usage_estimated
                    # No response bodies or arbitrary exception messages in call
                    # telemetry. Provider classifications are safe allowlisted data.
                    details = {}
                    status = getattr(e, 'status_code', None)
                    if isinstance(status, int):
                        details['status_code'] = status
                    reason = getattr(e, 'finish_reason', None)
                    if reason in ('MAX_TOKENS', 'STOP', 'SAFETY', 'RECITATION', 'OTHER',
                                  'length', 'content_filter', 'function_call', 'UNKNOWN'):
                        details['finish_reason'] = reason
                    self.event('llm_call_failed', input_tokens=input_tokens, output_tokens=output_tokens,
                               usage_estimated=usage_estimated, details=details,
                               usage='conservative estimate' if usage_estimated else 'provider usage', error=type(e).__name__)
                    if isinstance(e, ServiceUnavailableError):
                        self.state.status = 'BUDGET_EXHAUSTED' if time.monotonic() >= self.start + self.wall_seconds else 'SERVICE_UNAVAILABLE'
                        self.state.reason = str(e)
                        break
                    if isinstance(e, RateLimitError) and e.terminal_quota:
                        self.state.status = 'BUDGET_EXHAUSTED' if time.monotonic() >= self.start + self.wall_seconds else 'QUOTA_EXHAUSTED'
                        self.state.reason = str(e)
                        break
                    if isinstance(e, ModelHTTPError) and e.status_code in (400, 401, 403, 404):
                        self.state.status, self.state.reason = 'FAILED', str(e) + '; check model, endpoint, key, and access'
                        break
                    self.failure(type(e).__name__, str(e))
                    continue
                self.state.input_tokens += response.input_tokens
                self.state.output_tokens += response.output_tokens
                self.state.usage_estimated |= response.usage_estimated
                self.event('llm_call', input_tokens=response.input_tokens, output_tokens=response.output_tokens)
                if not response.actions:
                    self.failure('MODEL_PROTOCOL_ERROR', 'No tool action supplied')
                    continue
                if self.state.input_tokens + self.state.output_tokens > self.token_budget or time.monotonic() - self.start >= self.wall_seconds:
                    self.state.status, self.state.reason = 'BUDGET_EXHAUSTED', 'Time or total-token budget exhausted after model call'
                    break
                if len(response.actions) > 16:
                    self.failure('MODEL_PROTOCOL_ERROR', 'At most 16 actions are allowed per response')
                    continue
                self.context.clear_protocol_recovery()
                for action in response.actions:
                    if time.monotonic() - self.start >= self.wall_seconds:
                        self.state.status, self.state.reason = 'BUDGET_EXHAUSTED', 'Wall-clock budget exhausted'
                        break
                    if action.name == 'finish':
                        self.verify(action.arguments.get('semantic_review'))
                        break
                    if action.name == 'record_findings':
                        fields = ('hypothesis', 'evidence', 'next_action')
                        if set(action.arguments) != set(fields) or not all(
                                isinstance(action.arguments.get(field), str) and
                                0 < len(action.arguments[field].strip()) <= 500 for field in fields):
                            self.failure('MODEL_PROTOCOL_ERROR', 'record_findings requires three nonempty strings of at most 500 characters')
                        else:
                            self.state.findings.append({field: action.arguments[field] for field in fields})
                            self.state.findings = self.state.findings[-4:]
                            self.event('findings_recorded', findings=self.state.findings[-1])
                        continue
                    if action.name == 'update_plan':
                        steps = action.arguments.get('steps')
                        if not isinstance(steps, list) or not all(isinstance(s, str) for s in steps):
                            self.failure('MODEL_PROTOCOL_ERROR', 'Plan steps must be a list of strings')
                        else:
                            self.state.plan = steps
                            self.event('plan_updated', plan=steps)
                        continue
                    self.state.tool_calls += 1
                    self.tools.timeout = min(self.tools.timeout, max(0.1, self.wall_seconds - (time.monotonic() - self.start)))
                    result = self.tools.execute(action.name, action.arguments)
                    self.event('tool_result', action=asdict(action), result=result)
                    # A real source change makes the next request eligible to
                    # ask for tests/finish. Waiting for finish itself could
                    # strand the review allowance before that action is sent.
                    if action.name == 'edit_file' and result.get('ok'):
                        changed, _ = diff_snapshots(self.before, snapshot(self.repo, self.artifacts))
                        if any(not protected(name) for name in changed):
                            self.budget_phase = 'verification_review'
                    if action.name == 'run_tests':
                        if snapshot(self.repo, self.artifacts) != self.before:
                            self.budget_phase = 'verification_review'
                        self.state.tests.append({'command': action.arguments.get('command'), **result})
                        self.event('test_run', command=action.arguments.get('command'), result=result)
                    self.context.add(asdict(action), result)
                    if not result.get('ok'):
                        output = result.get('output', '')
                        test_evidence = re.search(r'FAILED \(failures=|--- FAIL:|AssertionError|[1-9]\d* failed', output)
                        unchanged = (not self.tools.files_modified and
                                     snapshot(self.repo, self.artifacts) == self.before)
                        if action.name in ('run_tests', 'run_command') and test_evidence and unchanged and not result.get('timed_out'):
                            record = {'command': action.arguments.get('command'),
                                      'category': 'PRE_EDIT_TEST_FAILURE',
                                      'message': 'Tests fail on unchanged source; baseline evidence, not patch recovery.'}
                            if record not in self.state.baseline_failures:
                                self.state.baseline_failures.append(record)
                            self.event('baseline_test_failure', **record)
                            self.context.add({'action': 'baseline_feedback'}, {'ok': False, **record,
                                             'instruction': 'Use the failing tests to diagnose the issue. No patch has been attempted.'})
                        else:
                            self.failure('TOOL_FAILURE', json.dumps(result))
                    if self.state.status != 'RUNNING':
                        break
            if self.state.status == 'RUNNING':
                self.state.status, self.state.reason = 'BUDGET_EXHAUSTED', 'Maximum steps reached'
        except KeyboardInterrupt:
            self.state.status, self.state.reason = 'INTERRUPTED', 'Run interrupted; modified working tree preserved'
        except (ValueError, OSError) as e:
            self.state.status, self.state.reason = 'FAILED', str(e)
        return self.report()

    def report(self):
        changed, diff = diff_snapshots(self.before, snapshot(self.repo, self.artifacts))
        (self.artifacts / 'final.diff').write_text(diff)
        report = asdict(self.state)
        report['token_reserve'] = self.token_reserve
        report['recovery_metric_definition'] = 'successful_recoveries is 0/1: final task verified after failure feedback; baseline-only failures excluded'
        passed = sum(bool(t.get('ok')) for t in self.state.tests)
        report['verification_commands_passed'] = passed
        report['verification_commands_failed'] = len(self.state.tests) - passed
        report['test_counts'] = []
        for test in self.state.tests:
            match = re.search(r'Ran (\d+) tests?', test.get('output', ''))
            if match:
                report['test_counts'].append({'command': test['command'], 'collected': int(match.group(1)), 'passed': bool(test.get('ok'))})
        report.update(wall_seconds=round(time.monotonic() - self.start, 3),
                      files_inspected=sorted(self.tools.files_seen), files_modified=changed,
                      cache_hits=self.tools.cache_hits, cache_misses=self.tools.cache_misses,
                      http_requests=getattr(self.adapter, 'http_requests', self.state.llm_calls),
                      transport_retries=getattr(self.adapter, 'transport_retries', 0),
                      rate_limit_retries=getattr(self.adapter, 'rate_limit_retries', 0),
                      service_retries=getattr(self.adapter, 'service_retries', 0),
                      service_wait_seconds=round(getattr(self.adapter, 'service_wait_seconds', 0), 3),
                      rate_limit_wait_seconds=round(getattr(self.adapter, 'rate_limit_wait_seconds', 0), 3),
                      model=getattr(self.adapter, 'model', type(self.adapter).__name__),
                      diff_additions=sum(l.startswith('+') and not l.startswith('+++') for l in diff.splitlines()),
                      diff_deletions=sum(l.startswith('-') and not l.startswith('---') for l in diff.splitlines()),
                      context_reduction_percent=round(100 * (1 - self.state.sent_context_tokens / self.state.candidate_context_tokens), 2) if self.state.candidate_context_tokens else 0,
                      artifacts=str(self.artifacts))
        (self.artifacts / 'performance.json').write_text(json.dumps(report, indent=2))
        self.event('session_end', status=self.state.status, verification=self.state.verification)
        return report
