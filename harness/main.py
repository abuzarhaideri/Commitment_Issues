"""CLI entry point; configuration is explicit and secrets stay in the environment."""
import argparse
import json
import os
from pathlib import Path
import sys
from urllib.parse import urlparse
from .models import OpenAICompatibleAdapter
from .orchestrator import Orchestrator

def parser():
    p = argparse.ArgumentParser(description='Commitment Issues autonomous coding harness')
    p.add_argument('--repo', default=os.getenv('HARNESS_REPO'))
    p.add_argument('--issue', default=os.getenv('HARNESS_ISSUE'))
    p.add_argument('--issue-file', type=Path, help='UTF-8 text issue, including multiline descriptions')
    p.add_argument('--evaluation', action='store_true', help='Load the committed evaluation profile and use only AI_API_KEY')
    p.add_argument('--launch-check', action='store_true', help='Validate startup only; no API call or repair')
    p.add_argument('--config', type=Path, help='JSON configuration file, without credentials')
    p.add_argument('--provider', choices=['openai-compatible', 'local-compatible', 'openai-responses', 'gemini-compatible'])
    p.add_argument('--model')
    p.add_argument('--base-url')
    p.add_argument('--reasoning-effort', choices=['none', 'low', 'medium', 'high', 'xhigh', 'max'])
    p.add_argument('--min-request-interval', type=float)
    p.add_argument('--max-rate-retries', type=int)
    p.add_argument('--gemini-api-route', choices=['compatibility', 'native'])
    p.add_argument('--free-tier-confirmed', action='store_true', help='Confirm the Gemini key belongs to a Free Tier project')
    p.add_argument('--max-output-tokens', type=int)
    p.add_argument('--native-tools', action='store_true', default=None)
    p.add_argument('--max-steps', type=int)
    p.add_argument('--context-budget', type=int)
    p.add_argument('--budget', type=int, help='Total input/output token budget (checked between calls)')
    p.add_argument('--wall-seconds', type=float)
    p.add_argument('--command-timeout', type=float)
    p.add_argument('--test-command', action='append', help='Repeat for targeted and broader verification')
    p.add_argument('--artifacts', type=Path, default=Path('artifacts'))
    p.add_argument('--demo', action='store_true', help='Offline scripted repair in a temporary fixture; no live LLM')
    return p

def main(argv=None):
    p = parser()
    args = p.parse_args(argv)
    if args.demo:
        from .demo import run_demo
        report = run_demo(args.artifacts)
    else:
        try:
            config_path = args.config
            if args.evaluation and config_path is None:
                config_path = Path(__file__).resolve().parent.parent / 'config/evaluation.json'
            config = json.loads(config_path.read_text()) if config_path else {}
            if not isinstance(config, dict):
                raise ValueError('Config must be a JSON object')
            if any('key' in k.lower() or ('token' in k.lower() and k.lower() not in ('token_budget', 'max_output_tokens')) for k in config):
                raise ValueError('Credentials must come from environment variables, never config')
            def choose(name, env, default=None):
                cli = getattr(args, name)
                return cli if cli is not None else os.getenv(env, config.get(name, default))
            provider = os.getenv('HARNESS_OFFICIAL_PROVIDER') or choose('provider', 'HARNESS_PROVIDER')
            model = os.getenv('HARNESS_OFFICIAL_MODEL') or choose('model', 'HARNESS_MODEL')
            endpoint = os.getenv('HARNESS_OFFICIAL_BASE_URL') or choose('base_url', 'HARNESS_BASE_URL')
            if provider not in ('openai-compatible', 'local-compatible', 'openai-responses', 'gemini-compatible') or not model or not endpoint:
                raise ValueError('Set provider, model, and base URL using CLI, HARNESS_* environment variables, or --config. No model is guessed.')
            key = os.getenv('AI_API_KEY', '') if args.evaluation else (os.getenv('AI_API_KEY') or (os.getenv('GEMINI_API_KEY', '') if provider == 'gemini-compatible' else os.getenv('OPENAI_API_KEY', '')))
            free_only = config.get('require_free_tier', False)
            if type(free_only) is not bool:
                raise ValueError('require_free_tier must be true or false')
            if args.evaluation and free_only:
                raise ValueError('The Free Tier development profile is separate from the AI_API_KEY evaluation entry point')
            if free_only:
                key = os.getenv('GEMINI_API_KEY', '')
                from .gemini import GEMINI_ENDPOINT, FREE_DEVELOPMENT_MODEL
                if provider != 'gemini-compatible' or model != FREE_DEVELOPMENT_MODEL or endpoint.rstrip('/') != GEMINI_ENDPOINT:
                    raise ValueError('Free development configuration cannot switch to a different provider, endpoint, or model')
                if not args.free_tier_confirmed:
                    raise ValueError('Confirm this key belongs to a Free Tier project in AI Studio, then supply --free-tier-confirmed. The harness cannot inspect billing tier.')
            if free_only and not key:
                raise ValueError('GEMINI_API_KEY is required for free development; unrelated AI_API_KEY is not reused')
            if provider != 'local-compatible' and not key:
                raise ValueError('AI_API_KEY is required for a cloud endpoint')
            if provider == 'local-compatible' and urlparse(endpoint).hostname not in ('localhost', '127.0.0.1', '::1') and not key:
                raise ValueError('Remote endpoints require AI_API_KEY')
            commands = args.test_command or config.get('test_commands')
            if commands is not None and (not isinstance(commands, list) or not all(isinstance(c, str) and c.strip() for c in commands)):
                raise ValueError('test_commands must be an array of nonempty strings')
            limits = {
                'max_steps': int(choose('max_steps', 'HARNESS_MAX_STEPS', 50)),
                'context_budget': int(choose('context_budget', 'HARNESS_CONTEXT_BUDGET', 12000)),
                'token_budget': int(choose('budget', 'HARNESS_TOKEN_BUDGET', 100000)),
                'wall_seconds': float(choose('wall_seconds', 'HARNESS_WALL_SECONDS', 600)),
                'command_timeout': float(choose('command_timeout', 'HARNESS_COMMAND_TIMEOUT', 30))}
            if any(value <= 0 for value in limits.values()):
                raise ValueError('All resource limits must be positive')
            native = choose('native_tools', 'HARNESS_NATIVE_TOOLS', False)
            if isinstance(native, str):
                if native.lower() not in ('true', 'false', '1', '0'):
                    raise ValueError('HARNESS_NATIVE_TOOLS must be true or false')
                native = native.lower() in ('true', '1')
            if type(native) is not bool:
                raise ValueError('native_tools must be true or false')
            max_output = int(choose('max_output_tokens', 'HARNESS_MAX_OUTPUT_TOKENS', 8192 if provider in ('openai-responses', 'gemini-compatible') else 2048))
            if provider == 'openai-responses':
                if native:
                    raise ValueError('openai-responses currently uses JSON actions; omit --native-tools')
                from .openai_responses import OpenAIResponsesAdapter
                adapter = OpenAIResponsesAdapter(model, endpoint, key,
                    reasoning_effort=choose('reasoning_effort', 'HARNESS_REASONING_EFFORT', 'low'),
                    timeout=min(60, limits['wall_seconds']), max_output_tokens=max_output)
            elif provider == 'gemini-compatible':
                if native:
                    raise ValueError('gemini-compatible currently uses JSON actions; omit --native-tools')
                from .gemini import GeminiAdapter
                adapter = GeminiAdapter(model, endpoint, key,
                    reasoning_effort=choose('reasoning_effort', 'HARNESS_REASONING_EFFORT', 'low'),
                    min_interval_seconds=float(choose('min_request_interval', 'HARNESS_MIN_REQUEST_INTERVAL', 12)),
                    max_rate_retries=int(choose('max_rate_retries', 'HARNESS_MAX_RATE_RETRIES', 3)),
                    api_route=choose('gemini_api_route', 'HARNESS_GEMINI_API_ROUTE', 'compatibility'),
                    timeout=min(60, limits['wall_seconds']), max_output_tokens=max_output)
            else:
                adapter = OpenAICompatibleAdapter(model, endpoint, key, native_tools=native,
                    timeout=min(60, limits['wall_seconds']), max_output_tokens=max_output)
            if args.evaluation or args.launch_check:
                print(f'HARNESS READY | provider={provider} | model={model} | API access not yet checked', flush=True)
                if args.evaluation and config.get('profile_status') == 'provisional-development-model':
                    print('Base profile is provisional; organiser model compatibility has not been validated.', flush=True)
            if args.launch_check:
                print('Launch check passed. No API request, tool or repair was run.')
                return 0
            if args.issue_file:
                if args.issue:
                    raise ValueError('Use either --issue or --issue-file')
                args.issue = args.issue_file.read_text(encoding='utf-8')
            if not args.repo or not args.issue:
                if sys.stdin.isatty():
                    args.repo = args.repo or input('Repository path: ').strip()
                    args.issue = args.issue or input('Issue: ').strip()
                elif args.evaluation:
                    print('Awaiting one JSON line: {"repo":"local path","issue":"text","test_commands":["command"]}', flush=True)
                    line = sys.stdin.readline(1024 * 1024 + 1)
                    if len(line) > 1024 * 1024:
                        raise ValueError('Task input exceeds 1 MiB')
                    task = json.loads(line) if line.strip() else None
                    if not isinstance(task, dict) or set(task) - {'repo', 'issue', 'test_commands'}:
                        raise ValueError('Task input must be a JSON object with repo, issue and optional test_commands')
                    args.repo = args.repo or task.get('repo')
                    args.issue = args.issue or task.get('issue')
                    if commands is None:
                        commands = task.get('test_commands')
                else:
                    raise ValueError('Supply --repo and --issue or HARNESS_REPO/HARNESS_ISSUE in noninteractive mode')
            if not isinstance(args.repo, str) or not args.repo.strip():
                raise ValueError('Repository path must be a nonempty string')
            if not isinstance(args.issue, str) or not args.issue.strip():
                raise ValueError('Issue must be a nonempty string')
            if commands is not None and (not isinstance(commands, list) or not all(isinstance(c, str) and c.strip() for c in commands)):
                raise ValueError('test_commands must be an array of nonempty strings')
            report = Orchestrator(args.repo, args.issue, adapter, args.artifacts,
                                  test_commands=commands, **limits).run()
        except (ValueError, OSError, EOFError) as exc:
            p.error(str(exc))
    print('HARNESS REPORT')
    print(f"Status: {report['status']} | Verification: {report['verification']}")
    print(f"Model: {report['model']} | Steps: {report['steps']} | LLM calls: {report['llm_calls']} | Tool calls: {report['tool_calls']}")
    print(f"Tokens: {report['input_tokens']} input / {report['output_tokens']} output ({'includes estimates' if report['usage_estimated'] else 'reported by provider'})")
    print(f"Files modified: {', '.join(report['files_modified']) or '(none)'} | Diff: +{report['diff_additions']} / -{report['diff_deletions']}")
    print(f"Reason: {report['reason']}")
    print(f"Evidence: {report['artifacts']}")
    return 0 if report['status'] == 'RESOLVED' else 1

if __name__ == '__main__':
    raise SystemExit(main())
