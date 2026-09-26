# Commitment Issues

A Python 3.11+ CLI harness that gives one configured text model repository tools, runs an autonomous repair loop, and records verification evidence. Implements the first working milestone of PRD v2.0.

## Submission readiness

Plain `make run` now automatically loads a committed evaluation profile, reads only `AI_API_KEY`, and accepts text tasks through terminal prompts or a JSON line. The profile is **provisional Gemini configuration**, pending the organisers' prescribed model/runtime/input protocol. A local clean-clone rehearsal passed setup, **93 infrastructure tests**, startup and a full repair through simulated HTTP with unchanged fixture tests. This is not live official-model validation. See the [progress checklist](docs/submission-progress.md), [evaluator quickstart](docs/submission-quickstart.md) and original [guidelines audit](docs/official-guidelines-audit.md). The PDF specifies no token ceilings or efficiency scoring weights.

`make package` creates an allowlisted candidate ZIP/hash manifest; `make rehearse` performs a localhost simulated-model clean-clone check. Local Git is initialized; final commit/publication remain pending. Passing-test summaries reduce observation text in offline replay, but total live API savings remain unmeasured. Stronger Sequelize compatibility checks still fail four cases.

## Start

```bash
make setup
make test
make run ARGS=--demo
```

No third-party Python dependencies, Docker, or ripgrep installation is required. `make setup` creates `.venv`; run from the project root. The demo uses a scripted adapter in a temporary repository. It reproduces an addition bug, edits the implementation, runs three tests, and requests independent verification. It tests harness infrastructure; it is **not evidence of an LLM's coding ability**.

## Free development: Gemini

Our current development choice is **Gemini 3.1 Flash-Lite**, using Google's native `generateContent` API with low reasoning and JSON actions. Use a key from a project showing Free Tier in [Google AI Studio](https://aistudio.google.com/apikey); keep billing disabled. The launcher asks for local tier confirmation and hidden key entry, and does not save the key:

```bash
make benchmark-free
```

Type `FREE` when prompted, then paste the key into the hidden prompt. No characters appear during key entry. To check connectivity first, run `make benchmark-free ARGS=--probe`; this makes one small generation request without running repository tools. `make benchmark-free ARGS=--list-models` reads model metadata without generating content.

See [free setup](docs/free-development.md) for account steps, quota tuning, and evidence paths. Requests are paced and temporary quota/service errors receive bounded retries. Daily quota exhaustion stops as `QUOTA_EXHAUSTED`; persistent service errors stop as `SERVICE_UNAVAILABLE`. There is no automatic paid fallback. Free-tier quotas and availability can vary; the harness cannot inspect a key's billing tier.

## Verified live benchmarks

On September 26, 2026, Gemini 3.1 Flash-Lite repaired the label normalization fixture through the native API:

| Measure | Result |
| --- | --- |
| Baseline | 6 tests, 4 expected failures |
| Final verification | All 6 tests passed; `RESOLVED` / `PASS` |
| Changes | Only `catalog.py`, +9 / -3 lines; tests unchanged |
| Runtime | 29.647 seconds |
| Calls | 3 model requests, 6 repository tool calls |
| Provider-reported tokens | 4,448 input / 999 output, including thinking |
| Quota/service retries | 0 |

The repair preserves first occurrence order using a seen set and result list, while retaining trimming, Unicode case folding, blank/duplicate removal, iterable support, and input immutability. Evidence is in `artifacts/benchmarks/20260926-132009-ffb4c367/evidence/20260926-132009-c9282193/`. This validates one small coding task; broader performance is still being evaluated. The local harness suite currently has **93 passing tests**.

The second benchmark is a checkout repair across `pricing.py` and `checkout.py`, covering quantities, discount clamping, shipping thresholds, zero quantities, empty carts, generators, and input immutability:

```bash
make benchmark-free ARGS='--fixture cart_checkout'
```

Its live run on September 26, 2026 also returned `RESOLVED` / `PASS`: all 10 tests passed after a baseline of 5 failures. Only `checkout.py` and `pricing.py` changed (+11/-2), with tests unchanged. It took 39.192 seconds, 4 model requests and 10 tool calls, using 9,522 input / 1,807 output tokens reported by the provider, with no quota/service retries. Evidence is in `artifacts/benchmarks/20260926-132804-ac3d5bdd/evidence/20260926-132804-bee9c759/`.

Both built-in fixtures have now passed one live run each. They are small Python tasks, so this is early validation rather than a general coding success rate. Each invocation creates a fresh target and evidence directory. The default fixture remains `label_normalization`. See [benchmark details](benchmarks/README.md).

The first real-repository TypeScript run repaired exponent-only numeric syntax in Sequelize at commit `abf5936c77ad9c09ba1a3116b54e7558bb4528e5`. It returned `RESOLVED` / `PASS`: all **158 original utility tests + 5 added regression checks** passed after source rebuild, with tests unchanged. Runtime was **95.230 seconds**, with **8 model calls**, **13 counted tool calls**, and **44,286 input / 5,313 output tokens**. One source line changed; generated JavaScript and its source map account for the other two reported files. No quota/service retries occurred, and the current context-reduction metric remained 0%.

**Review limitation:** the patch additionally accepts `1.`, `-1.`, and `1.e3`, which the original rejected. The supplied tests missed this compatibility change; the repair therefore needs stronger behavior-preservation checks before acceptance beyond the targeted benchmark. Its recorded recovery was a build-output diff re-review, not recovery from an incorrect fix. See the [short run report](docs/sequelize-first-run-report.md) for conclusions and prioritized improvements, and [Sequelize benchmark](docs/sequelize-benchmark.md) for scope/setup. Evidence: `artifacts/external/sequelize/evidence/20260926-145231-50413f2e/`. The launcher stops on the now-modified baseline; prepare a fresh separate target before another independent attempt.

## Run with a model

For a progressive synthetic test plan, use the [four-issue synthetic repository](benchmarks/synthetic_lab/README.md). Each attempt starts from a fresh copy with one active defect and runs all 31 regression tests. Start with:

```bash
make benchmark-free ARGS='--synthetic-issue label-order'
```

Issue 1 (`label-order`) passed its first live run: **31/31 tests**, only `catalog.py` changed (+9/-3), **41.174 seconds**, **4 model calls / 7 counted tool calls**, and **6,681 input / 1,151 output tokens**. Baseline test hashes confirm tests and unrelated modules stayed unchanged. Review found the order-preserving implementation consistent with the task, with no unintended change identified. There were no recoveries or API retries; context reduction remains 0%, and 24.465 seconds were spent pacing requests. See the [short analysis](docs/synthetic-label-order-report.md) and [synthetic results](benchmarks/synthetic_lab/results.md).

Issue 2 (`boolean-config`) also passed **31/31 checks**, with only `settings.py` changed (+12/-1). It took **65.435 seconds**, **6 model calls / 9 counted tool calls**, and **19,820 input / 2,194 output tokens** (22,014 total). Tests and unrelated modules stayed unchanged; review found the explicit parsing/default/error behavior consistent with the issue. The recovery record was an expected pre-fix baseline failure, not an incorrect patch. Context reduction remains 0%; request pacing took 34.442 seconds. See the [boolean report](docs/synthetic-boolean-config-report.md).

Across five completed live runs, total usage varies from 5,447 to 49,599 tokens; about 88% of their recorded usage is input, and all currently report 0% context reduction. These are different tasks, not a controlled optimization comparison. See the [efficiency and PRD checkpoint review](docs/efficiency-review.md) for full measurements, limits, and priorities: compact test logs, baseline-aware feedback, durable memory, and less duplicated diff/context content. Official numerical scoring/limits remain unconfirmed.

Next run `pagination`, then `checkout` separately through the same option; these two lab live runs remain pending. Offline baselines for all four match expected failures; the healthy template passes all 31 tests. This combined lab's results are distinct from our earlier standalone fixture runs.

Set credentials in your shell. `.env.example` documents names; `.env` files are not automatically loaded. Never put credentials in configuration or source files.

```bash
export AI_API_KEY="<provided-key>"
export HARNESS_PROVIDER="openai-compatible"
export HARNESS_MODEL="<explicit-model-name>"
export HARNESS_BASE_URL="https://<provider-host>/v1"
make run
```

`make run` prompts for the repository path and a single-line issue in an interactive terminal. For automation:

```bash
make run ARGS='--repo /path/to/target --issue "Fix the login bug"'
```

Or invoke the CLI directly:

```bash
.venv/bin/python -m harness.main \
  --repo /path/to/target \
  --issue "Fix the login bug" \
  --provider openai-compatible \
  --model "<explicit-model>" \
  --base-url "https://<provider-host>/v1" \
  --native-tools \
  --test-command "python3 -m pytest tests/test_login.py" \
  --test-command "python3 -m pytest"
```

Native tool calling is opt-in for the generic adapter. Otherwise, tools are described in text and the model returns validated JSON actions. Adapters support **Chat Completions compatible APIs**, **OpenAI Responses**, and **Gemini native generation**. Gemini also supports its compatibility route; `--gemini-api-route native` selects the native route for the `gemini-compatible` provider. Gemini uses JSON actions on both routes, without native tool continuation or thought-signature replay. Anthropic's native protocol is not implemented; “model-agnostic” describes the replaceable adapter architecture, not universal API support today.

For a local runtime, use `--provider local-compatible --base-url http://localhost:11434/v1 --model <installed-model>`. Loopback local endpoints can run without an API key. HTTPS is required for remote endpoints. Compatibility and model tool ability still need validation against the chosen runtime.

## Optional OpenAI configurations (paid)

GPT-6 Luna and GPT-6 Sol configurations remain available for explicitly authorized paid testing. They are not the selected development workflow. Explicit configurations are in `config/openai-luna.json` and `config/openai-sol.json`. These use `https://api.openai.com/v1` through the dedicated `openai-responses` adapter.

```bash
# Set AI_API_KEY in this terminal first.
.venv/bin/python benchmarks/run_live.py --config config/openai-luna.json
```

The Responses adapter currently uses the JSON action fallback with stateless requests (`store: false`), low reasoning, and an 8,192-token output allowance including reasoning. It normalizes results into the same model contract as the compatible adapter. Native Responses function-call continuation and encrypted reasoning replay are not implemented. Use `--reasoning-effort` and `--max-output-tokens` to tune the run. This is separately configured and does not change the model/provider contract for official evaluation.

Model sources: [Luna](https://developers.openai.com/api/docs/models/gpt-6-luna), [Sol](https://developers.openai.com/api/docs/models/gpt-6-sol), [Responses guidance](https://developers.openai.com/api/docs/guides/migrate-to-responses).

## Configuration

Use `--config config/example.json` after replacing its placeholders. Precedence is organiser override, CLI, environment, config file, defaults. `HARNESS_OFFICIAL_PROVIDER`, `HARNESS_OFFICIAL_MODEL` and `HARNESS_OFFICIAL_BASE_URL` override ordinary provider/model/endpoint choices. Credentials normally use `AI_API_KEY` first, then `GEMINI_API_KEY` for Gemini or `OPENAI_API_KEY` for other cloud adapters. The explicit Free Tier configuration requires `GEMINI_API_KEY`, tier confirmation, and the selected model/provider/endpoint; it rejects overrides away from that selection. Direct module invocation requires explicit provider/model/endpoint configuration. Plain `make run` supplies these through `config/evaluation.json` and reads only `AI_API_KEY`; its profile is currently provisional.

CLI controls include `--max-steps`, `--context-budget`, `--budget` (total input/output tokens), `--wall-seconds`, `--command-timeout`, and repeated `--test-command`. Environment equivalents are `HARNESS_MAX_STEPS`, `HARNESS_CONTEXT_BUDGET`, `HARNESS_TOKEN_BUDGET`, `HARNESS_WALL_SECONDS`, `HARNESS_COMMAND_TIMEOUT`, and `HARNESS_NATIVE_TOOLS`. Noninteractive inputs support `HARNESS_REPO` and `HARNESS_ISSUE`.

Model-call budgets are checked between calls; a call can exceed a token ceiling before usage is returned. Failed responses are conservatively charged estimated prompt usage plus the configured output allowance. Commands and network calls have timeouts limited to remaining wall time. Repository profiling/snapshot overhead is not a strict process-level deadline.

## Evidence and completion

Each run writes an isolated `artifacts/<run-id>/` directory:

- `events.jsonl`: structured model/tool/recovery/verification events.
- `state.json`: latest state for inspection after interruption.
- `final.diff`: changes relative to the starting working tree, including new files.
- `performance.json`: status, timings, usage, context estimates, files, cache, commands, and diff counts.

A `finish` action triggers a final diff review in complete bounded chunks, Python syntax checks on changed Python files, protected infrastructure checks, and fresh verification commands. Another finish is required after all diff chunks have been delivered. Passing commands plus the model's issue-based semantic review produce `RESOLVED`; hidden-test correctness remains unknown. Missing test commands and no-op changes return `UNVERIFIED`. Failing tests, zero-test Python suites, or changed protected infrastructure cannot pass. A verification command that modifies tracked snapshot content forces another review.

The profiler proposes commands from Python, npm, Go, Rust, Maven, Gradle, and Make markers. README/CI filenames are exposed as navigation hints. Unusual projects need explicit verification commands; the agent can inspect CI and run exploratory commands. It does not install project dependencies automatically.

Exit codes: `0` resolved, `1` failed/unverified/budget-exhausted/quota-exhausted/service-unavailable/interrupted, `2` CLI configuration error. Modified code stays in the target working tree even on failure; the harness does not commit, reset, or publish it.

Usage is provider-reported when available, otherwise estimated. Candidate/sent context is a character-based estimate including tool schemas; context reduction compares the accumulated retained history against bounded packing, not a full-repository baseline or measured cost saving. Test counts are parsed for unittest logs; other runners retain command-level outcomes and raw bounded evidence. Recovery success means a subsequent tool action succeeded, not proof the issue was repaired.

## Execution boundary

Read/edit tools validate repository paths and symlinks, protect conventional test/evaluation paths, cap file reads, and use exact unique replacement. Shell commands run in the target directory with a small environment and a basic configurable deny pattern. This **is not an OS sandbox**: development commands and repository scripts can access the host filesystem. Use a disposable checkout in an isolated machine/container for untrusted repositories. Target source and bounded command output are sent to the configured model and retained in local artifacts.

Known limits: conventional protected filenames cannot identify every hidden evaluation file; large files are tracked by hashes rather than full textual diffs; symlink files and generated directories are excluded from snapshots; outline reads are heuristic; persisted state does not yet support automatic resume. Reports preserve evidence rather than claiming coverage they do not have.

See [architecture](docs/architecture.md), [build plan](docs/build-plan.md), and the [readiness and hackathon checklist](docs/hackathon-checklist.md) for module boundaries, verified work, remaining gaps, and submission priorities.
