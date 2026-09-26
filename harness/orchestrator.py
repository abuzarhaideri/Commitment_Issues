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
    return any(x.lower() in {'tests', 'test', 'evaluation', 'eval', 'evals', '.github', '.agents', '.codex'} for x in p.parts) or p.name.startswith('test_') or p.name.endswith(('_test.py', '.test.js', '.spec.ts'))

def diff_snapshots(before, after):
    changed = sorted(k for k in before.keys() | after.keys() if before.get(k) != after.get(k))
    text = ''.join(''.join(difflib.unified_diff(before.get(k, b'').decode('utf-8', errors='replace').splitlines(True), after.get(k, b'').decode('utf-8', errors='replace').splitlines(True), fromfile='a/' + k, tofile='b/' + k)) for k in changed)
    return changed, text

class Orchestrator:
    def __init__(self, repo, issue, adapter, artifacts=Path('artifacts'), max_steps=50,
                 context_budget=12000, token_budget=100000, wall_seconds=600,
                 command_timeout=30, test_commands=None):
        self.repo = Path(repo).resolve()
        if not self.repo.is_dir():
            raise ValueError('Repository path must be an existing directory')
        self.adapter = adapter
        self.state = TaskState(issue, str(self.repo))
        self.tools = ToolRegistry(self.repo, timeout=command_timeout)
        self.context = ContextManager(context_budget)
        self.max_steps, self.token_budget, self.wall_seconds = max_steps, token_budget, wall_seconds
        self.test_commands = test_commands
        self.artifacts = Path(artifacts).resolve() / (time.strftime('%Y%m%d-%H%M%S') + '-' + uuid.uuid4().hex[:8])
        self.artifacts.mkdir(parents=True)
        self.before = snapshot(self.repo, self.artifacts)
        self.start = time.monotonic()
        if hasattr(self.adapter, 'pacer'):
            self.adapter.deadline = self.start + self.wall_seconds
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
        self.event('recovery', **record)
        self.context.add({'action': 'recovery'}, {'ok': False, **record, 'instruction': 'Replan and use an alternate approach.' if repeated >= 3 else 'Inspect failure and repair.'})
        if repeated > 3:
            self.state.status, self.state.reason = 'FAILED', 'Repeated failure exhausted recovery budget'

    def verify(self, semantic_review):
        after = snapshot(self.repo, self.artifacts)
        changed, diff = diff_snapshots(self.before, after)
        (self.artifacts / 'final.diff').write_text(diff)
        self.state.tool_calls += 1
        self.event('verification', stage='diff', files=changed)
        # Model sees the final diff before a subsequent finish can be accepted.
        digest = hashlib.sha256(diff.encode()).hexdigest()
        if getattr(self, 'review_digest', None) != digest:
            self.review_digest = digest
            self.review_chunks = [diff[i:i + 1800] for i in range(0, len(diff), 1800)] or ['(empty diff)']
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
        if snapshot(self.repo, self.artifacts) != after:
            self.failure('VERIFICATION_FAILURE', 'Verification commands changed repository files; inspect final diff again')
            return False
        if not isinstance(semantic_review, str) or not semantic_review.strip():
            self.failure('VERIFICATION_FAILURE', 'finish requires a semantic_review of behavior, edge cases, and test integrity')
            return False
        self.state.verification, self.state.status = 'PASS', 'RESOLVED'
        self.state.reason = semantic_review
        return True

    def run(self):
        self.profile = profile_repository(self.repo)
        self.event('session_start', repo=str(self.repo), issue=self.state.issue)
        self.event('repo_profile', profile=self.profile)
        schemas = self.tools.schemas() + [
            {'type': 'function', 'function': {'name': 'update_plan', 'description': 'Set or revise task plan', 'parameters': {'type': 'object', 'properties': {'steps': {'type': 'array', 'items': {'type': 'string'}}}, 'required': ['steps']}}},
            {'type': 'function', 'function': {'name': 'finish', 'description': 'Request independent completion verification', 'parameters': {'type': 'object', 'properties': {'summary': {'type': 'string'}, 'semantic_review': {'type': 'string'}}, 'required': ['summary', 'semantic_review']}}}]
        try:
            for step in range(self.max_steps):
                if self.state.status != 'RUNNING':
                    break
                self.state.steps = step + 1
                if time.monotonic() - self.start >= self.wall_seconds or self.state.input_tokens + self.state.output_tokens >= self.token_budget:
                    self.state.status, self.state.reason = 'BUDGET_EXHAUSTED', 'Time or total-token budget exhausted'
                    break
                messages = self.context.pack(self.state, self.profile, schemas, self.adapter)
                self.state.llm_calls += 1
                if hasattr(self.adapter, 'timeout'):
                    self.adapter.timeout = min(self.adapter.timeout, max(0.1, self.wall_seconds - (time.monotonic() - self.start)))
                try:
                    response = self.adapter.generate(messages, tools=schemas)
                except (ProtocolError, ModelError) as e:
                    self.state.input_tokens += getattr(e, 'input_tokens', self.adapter.count_or_estimate_tokens(messages) + self.adapter.count_or_estimate_tokens(schemas))
                    self.state.output_tokens += getattr(e, 'output_tokens', getattr(self.adapter, 'max_output_tokens', 2048))
                    self.state.usage_estimated |= getattr(e, 'usage_estimated', True)
                    self.event('llm_call_failed', usage='provider usage' if not getattr(e, 'usage_estimated', True) else 'conservative estimate', error=type(e).__name__)
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
                for action in response.actions:
                    if time.monotonic() - self.start >= self.wall_seconds:
                        self.state.status, self.state.reason = 'BUDGET_EXHAUSTED', 'Wall-clock budget exhausted'
                        break
                    if action.name == 'finish':
                        self.verify(action.arguments.get('semantic_review'))
                        break
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
                    if action.name == 'run_tests':
                        self.state.tests.append({'command': action.arguments.get('command'), **result})
                        self.event('test_run', command=action.arguments.get('command'), result=result)
                    self.context.add(asdict(action), result)
                    if not result.get('ok'):
                        self.failure('TOOL_FAILURE', json.dumps(result))
                    elif self.pending_recovery:
                        self.pending_recovery = False
                        self.state.successful_recoveries += 1
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
