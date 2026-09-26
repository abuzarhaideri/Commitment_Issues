"""Gemini-only free-tier development benchmark with hidden local key entry."""
import argparse
import getpass
import os
from pathlib import Path
import sys
import subprocess

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from harness.gemini import GEMINI_ENDPOINT, FREE_DEVELOPMENT_MODEL, list_generation_models, GeminiAdapter
from harness.models import ModelError
from benchmarks.run_live import run as run_benchmark, FIXTURES
from benchmarks.run_synthetic import ISSUES as SYNTHETIC_ISSUES


def main(argv=None):
    parser = argparse.ArgumentParser(description='Free-tier Gemini repair benchmark; never selects a paid fallback')
    parser.add_argument('--free-tier-confirmed', action='store_true', help='You checked that the key project shows Free Tier in AI Studio')
    parser.add_argument('--list-models', action='store_true', help='List advertised model names only; do not run a repair or generate content')
    parser.add_argument('--probe', action='store_true', help='One small native API generation request; no repository tools or repairs')
    parser.add_argument('--fixture', choices=sorted(FIXTURES), default='label_normalization')
    parser.add_argument('--sequelize', action='store_true', help='Run the prepared real Sequelize repository benchmark')
    parser.add_argument('--synthetic-issue', choices=list(SYNTHETIC_ISSUES), help='Run one issue in a fresh synthetic repository')
    parser.add_argument('--min-request-interval', type=float, default=12,
                        help='Seconds between request starts; adjust using your AI Studio quota')
    args = parser.parse_args(argv)
    if args.probe and args.list_models:
        parser.error('Choose --probe or --list-models')
    if args.sequelize and (args.probe or args.list_models or args.fixture != 'label_normalization'):
        parser.error('--sequelize cannot be combined with another benchmark or diagnostic')
    if args.synthetic_issue and (args.sequelize or args.probe or args.list_models or args.fixture != 'label_normalization'):
        parser.error('--synthetic-issue cannot be combined with another benchmark or diagnostic')
    if not args.list_models:
        print(f'Selected Free Tier development model: {FREE_DEVELOPMENT_MODEL}. No automatic provider fallback.', flush=True)
    if not args.free_tier_confirmed:
        if not sys.stdin.isatty():
            parser.error('Check that the Gemini project shows Free Tier in AI Studio, then pass --free-tier-confirmed')
        print('Use a Gemini key from a project showing Free Tier in AI Studio. Do not enable billing.')
        print('Free-tier data may be used to improve Google products; use this public test fixture.')
        if input('Does the key project show Free Tier? Type FREE to continue: ').strip() != 'FREE':
            print('Stopped before any API request.')
            return 1
    key = os.getenv('GEMINI_API_KEY', '')
    if not key:
        if not sys.stdin.isatty():
            parser.error('Set GEMINI_API_KEY locally or run this command in an interactive terminal')
        key = getpass.getpass('Gemini API key (hidden; not saved): ').strip()
    if not key:
        parser.error('Gemini API key must not be empty')
    if args.list_models:
        try:
            names = list_generation_models(key)
        except (ModelError, ValueError) as exc:
            print(f'Model listing failed: {exc}', file=sys.stderr)
            return 1
        print('Models advertised for generateContent (listing does not confirm Free Tier quota or compatibility-route access):')
        for name in names:
            print(name)
        print('No content generation or repair was run. Key was not saved.')
        return 0
    if args.probe:
        try:
            adapter = GeminiAdapter(FREE_DEVELOPMENT_MODEL, GEMINI_ENDPOINT, key,
                api_route='native', timeout=30, max_output_tokens=2048, max_rate_retries=0)
            result = adapter.generate([{'role': 'user', 'content':
                'Connectivity test only. Return {"actions":[{"action":"probe_ok","arguments":{},"goal":"Connectivity check"}]}.'}])
            if len(result.actions) != 1 or result.actions[0].name != 'probe_ok':
                raise ModelError('Probe received an unexpected action')
        except (ModelError, ValueError) as exc:
            print(f'Native API probe failed: {exc}', file=sys.stderr)
            return 1
        print(f'Native API probe passed: {FREE_DEVELOPMENT_MODEL}; {result.input_tokens} input / {result.output_tokens} output tokens.')
        print('No tools or repair were run. Key was not saved.')
        return 0
    # Use this selected Gemini key; do not reuse an unrelated AI_API_KEY.
    previous_key = os.environ.get('AI_API_KEY')
    previous_gemini_key = os.environ.get('GEMINI_API_KEY')
    try:
        os.environ['AI_API_KEY'] = key
        os.environ['GEMINI_API_KEY'] = key
        model_options = [
            '--config', str(ROOT / 'config/gemini-free.json'), '--free-tier-confirmed',
            '--provider', 'gemini-compatible', '--model', FREE_DEVELOPMENT_MODEL,
            '--base-url', GEMINI_ENDPOINT, '--reasoning-effort', 'low',
            '--gemini-api-route', 'native',
            '--max-steps', '20', '--wall-seconds', '600', '--budget', '60000',
            '--min-request-interval', str(args.min_request_interval)]
        if args.sequelize:
            from benchmarks.run_sequelize import run
            try:
                return run(model_options)
            except (ValueError, OSError, subprocess.TimeoutExpired, subprocess.CalledProcessError) as exc:
                print(f'Sequelize benchmark setup failed: {exc}', file=sys.stderr)
                return 1
        if args.synthetic_issue:
            from benchmarks.run_synthetic import run
            try:
                return run(['--issue', args.synthetic_issue, *model_options])
            except (ValueError, OSError, subprocess.TimeoutExpired) as exc:
                print(f'Synthetic benchmark setup failed: {exc}', file=sys.stderr)
                return 1
        return run_benchmark(['--fixture', args.fixture, *model_options])
    finally:
        if previous_gemini_key is None:
            os.environ.pop('GEMINI_API_KEY', None)
        else:
            os.environ['GEMINI_API_KEY'] = previous_gemini_key
        if previous_key is None:
            os.environ.pop('AI_API_KEY', None)
        else:
            os.environ['AI_API_KEY'] = previous_key


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (EOFError, KeyboardInterrupt):
        print('\nStopped; key was not saved.')
        raise SystemExit(1)
