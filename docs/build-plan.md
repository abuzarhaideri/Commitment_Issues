# Build plan

## Completed first milestone

- Root `make setup`, `make run`, `make test`, and optional demo/clean targets.
- CLI + interactive repo/issue input and explicit model/endpoint configuration.
- Replaceable model adapter, native tools and JSON fallback.
- Repository profile, search fallback, selective reads, unique edits, command timeouts, diffs.
- Agent loop, model-authored revisable plan, failure feedback, repeated-failure/step/time/token limits.
- Bounded context, output filtering, content-hash cache.
- Complete final diff delivery, protected file integrity, syntax checks, fresh verification.
- Persisted inspection state, JSONL telemetry, performance JSON, console report.
- Offline repair demo and 143 tests covering protocol, containment, recovery, tampering, cache, verification, and benchmark selection.

## Live repair validation

1. Configure the organiser-prescribed provider/model when known, or an explicitly chosen development endpoint.
2. Run one real small repair through JSON mode, then native tools if supported.
3. Confirm endpoint-specific request parameters, credential handling, reported usage, and rate-limit behavior.
4. Run a repeatable fixture set with regressions and issue-derived edge cases. Save diffs, commands, and failures.

The user selected zero-cost development. Gemini 3.1 Flash-Lite via the native API passed the connectivity probe and both built-in repair fixtures on September 26, 2026. Label normalization passed six tests in 29.647 seconds. The two-module checkout repair passed ten tests in 39.192 seconds after five baseline failures. Both retained tests unchanged and needed no quota/service retries. Hidden-key entry, request pacing, bounded quota/service retries, and clean exhaustion reporting are implemented. Next validation should exercise a larger repository, failure recovery, and bounded context behavior. OpenAI configurations remain optional and require new payment authorization.

## Then: quality and evaluation hardening

The first real-repository run now completed in Sequelize: 158 original utility tests and five added regression checks passed after TypeScript rebuild, with 8 model calls and 49,599 tokens in 95.230 seconds. Independent review found additional acceptance of previously rejected trailing-decimal forms; behavior preservation needs stronger checks before accepting the patch more broadly. See [run report](sequelize-first-run-report.md). Prioritize this coverage gap, successful-log compression, source/build-output diff handling, and a genuine failed-fix recovery benchmark.

- Richer CI command extraction, baseline failure classification, non-Python build/static checks.
- Broaden retry handling beyond Gemini and preserve exact usage on all malformed response paths.
- Durable decisions/files memory and validated resume tied to issue/config/repository fingerprints.
- Stronger evaluation-file identification and optional isolated command runner.
- Benchmark context packing on the same model and issues against an unoptimized baseline.
- Add organiser-specific input/output and provider adapter only once specified.
- Check original official rules/PDFs and exercise startup on the actual evaluator OS/runtime.

Acceptance for submission requires live end-to-end repair evidence and evaluator-compatible configuration. The offline demo alone is insufficient.
