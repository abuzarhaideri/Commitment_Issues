# Commitment Issues — readiness and hackathon checklist

Last reviewed: September 26, 2026. Basis: supplied AI Harness Submission PDF, PRD v2.0, current source, local tests, and saved live benchmark evidence. See the [official guidelines audit](official-guidelines-audit.md): startup rules are confirmed, while model/runtime/input specifics and scoring remain unspecified. This is a working checklist, not a claim of universal codebase support or guaranteed placement.

`[x]` means implemented or completed to the stated extent. `[ ]` means missing or awaiting the stated validation. Implementation and live validation are listed separately. P0 = submission blocker, P1 = next reliability work, P2 = differentiation after correctness.

## 1. Submission contract — P0

- [x] Root `make setup`, `make run`, and `make test` exist.
- [x] Standard-library Python implementation; Python 3.11+ required, no mandatory Docker or third-party packages.
- [x] CLI and interactive repository/issue inputs; one repo, issue, model, and agent loop per task.
- [x] Text-only model path; official `AI_API_KEY` accepted outside the explicit free-development configuration.
- [x] Provider/model/endpoint overrides and explicit configuration errors.
- [x] Review supplied official Makefile/key/text-only/submission guidelines; fresh local copy passed setup and 80 tests, but plain run failed.
- [ ] Obtain remaining organiser details: prescribed model, endpoint, issue transport, repo location, output schema, permitted tools/network, runtimes, budgets, and scoring weights. These are not specified in the supplied PDF.
- [x] Fix missing default startup configuration: plain make run loads the provisional evaluation profile and accepts terminal/JSON tasks with AI_API_KEY only.
- [ ] Finalize prescribed organiser model/runtime/input settings and validate live; current profile is explicitly provisional. See [progress](submission-progress.md).
- [x] Evaluation entry point reads AI_API_KEY only, rejects the Free Tier development profile and requires no FREE prompt.
- [ ] Test the final submission from a clean clone on the evaluator OS/runtime: setup, normal run, test, missing configuration, interrupted run, and nonzero failure exit.
- [x] Initialize local Git and prepare allowlisted ZIP/hash manifest; clean local clone/setup/test/simulated repair passed 93 tests.
- [ ] Complete final tracked-file/history/security review, submission commit/publication and prescribed-environment rehearsal.
- [ ] Add CI for supported Python versions/platforms and a submission smoke test.
- [ ] Prepare a concise reviewer quickstart, license/attributions, and reproducible demo command.

Acceptance: a reviewer follows the official startup instructions without editing source or contacting the team; the run leaves modified code and the required report.

## 2. Model access and protocols

- [x] Adapter boundary keeps provider HTTP calls outside the orchestrator.
- [x] Generic Chat Completions, OpenAI Responses, Gemini native generation, and Gemini compatibility transports.
- [x] Strict JSON actions and opt-in generic native tool calls, locally tested.
- [x] Missing/invalid configuration and malformed key rejection; hidden local key entry without saving credentials.
- [x] Gemini model-list diagnostic, single-request native probe, request pacing, bounded quota/service retries, daily-quota stop, and no automatic paid fallback.
- [x] Live Gemini 3.1 Flash-Lite connectivity and two repairs through the native JSON-action path.
- [ ] Validate the organiser-selected adapter/model live, including native tools only if needed and supported. Other adapter tests currently use mocked responses.
- [ ] Preserve exact provider usage for every malformed, truncated, refused, or incomplete response; generic/Gemini action parse errors can currently fall back to estimates.
- [ ] Improve transient network/server-error handling for adapters beyond Gemini.
- [ ] If useful and permitted, implement native tool continuation and reasoning replay with provider-specific tests. These are optional, not prerequisites for the current JSON path.

## 3. Repository intelligence — P1

- [x] Repository map, directory listing, file metadata, selective/range reads, heuristic outlines, literal search.
- [x] Optional ripgrep with bounded Python fallback; content-hash read cache and edit invalidation.
- [x] Build/test marker heuristics for Python, JS/TS, Go, Rust, Maven, Gradle, and Make; README/CI filenames exposed as hints.
- [ ] Prove navigation on a real repository with distractor files and a bug that crosses modules.
- [ ] Read actual CI/package configuration for test/build commands rather than relying mainly on marker guesses.
- [ ] Handle monorepos, nested projects, custom layouts, and multiple test roots without scanning everything into context.
- [ ] Separate missing dependencies/toolchains and baseline failures from patch-caused failures.
- [ ] Document or automate allowed dependency preparation with bounded commands. Current harness does not automatically install project dependencies.
- [ ] Validate live on at least one non-Python project before claiming broad language capability.
- [ ] Consider symbol-aware navigation only after real-repo evidence shows a need.

## 4. Planning, tools, and autonomy

- [x] Model-authored revisable plans; validated tool arguments; targeted unique text replacement.
- [x] Read/search/edit/command/test/diff tools; bounded outputs, command timeouts, and process termination.
- [x] Autonomous loop with step, time, token, and repeated-failure limits.
- [x] Single-file and two-file live repair without human intervention during the loop.
- [ ] Validate a feature implementation or refactor in addition to bug fixes.
- [ ] Validate dirty working trees, new/deleted files, binary/large files, and unfamiliar build workflows on representative tasks.
- [ ] Improve edit guidance after ambiguous matches and large-file read limits; avoid blind whole-file rewrites.
- [ ] Validate accurate plans/decisions across longer tasks; plans are advisory and not enforced as a separate required phase.

## 5. Failure recovery — P1

- [x] Tool/protocol/test/verification failure feedback, repeated-failure detection, replan instructions, and clean budget termination.
- [x] Local tests cover malformed actions, failed commands, edit protection, test failures, and quota/service stops.
- [ ] Record a live run in which a first fix fails, the agent uses the evidence, changes approach, and passes final verification.
- [ ] Distinguish failure categories more precisely: dependency/toolchain, flaky test, baseline regression, syntax, edit conflict, API, and timeout.
- [ ] Replace the current recovery-success metric: a later successful tool call is not evidence that the original failure was resolved.
- [ ] Evaluate recovery when a command fails differently each time; fingerprint-based counts alone may not identify semantic repetition.
- [ ] Add validated resume with issue/config/repository fingerprints if time and scoring justify it. State is currently inspection-only.

## 6. Verification and accuracy — P1

- [x] Full final diff delivered in bounded chunks before acceptance.
- [x] Fresh final tests independent of the model's earlier test runs; Python syntax checks.
- [x] Test/evaluation infrastructure change detection; zero-test Python runs cannot pass.
- [x] Model completion cannot bypass the verification gate; no test command/no change returns `UNVERIFIED`.
- [x] Issue-based semantic review is required, but supplied by the same model and not an independent correctness oracle.
- [ ] Add language-appropriate build/lint/type checks based on actual project configuration.
- [ ] Validate targeted plus broad regression coverage on real repositories. Repeating one small suite is not broad project coverage.
- [ ] Test issue-derived cases held outside the agent-visible fixture to detect overfitting and hard-coding.
- [ ] Differentiate “visible checks passed” from “requested behavior fully correct” in reports; hidden tests remain unknown.
- [ ] Refine protection rules: conventional test/CI filenames can miss hidden evaluation files or block legitimate source paths. Preserve organiser rules.
- [ ] Cover snapshot exclusions, symlinks, large-file hashes, and shell side effects explicitly; current snapshots do not observe every host change.

## 7. Context, memory, and efficiency — P1/P2

- [x] Issue/profile/plan/recent failures anchored in bounded context, with recent observations retained.
- [x] Output truncation, selective retrieval, read cache, candidate/sent context estimates.
- [ ] Implement durable decisions, hypotheses, important file references, and failed approaches. Old observations are dropped, not semantically summarized.
- [ ] Recover gracefully when anchored state or the latest observation cannot fit; current behavior fails cleanly rather than automatically compacting/retrieving narrower evidence.
- [ ] Fix failure extraction to operate on raw multiline logs before JSON encoding; current filtering often sees an escaped, single-line string.
- [ ] Measure and reduce duplicated tool instructions/schemas in the actual provider request; the context estimate does not account for every wire-payload detail.
- [ ] Account for model-specific tokenization and reasoning budgets; label estimates clearly.
- [ ] Stress-test a long conversation with noisy logs and a relevant early decision.
- [ ] Run paired baseline-versus-optimized tasks with the same model/settings/issues, identical fresh targets, and correctness checks. Report all attempts, including failures.
- [ ] Establish measured savings before adopting compressors/vector stores/external navigation dependencies.

Both live fixtures reported 0% context reduction under the current retained-history metric. Cache hits demonstrate reuse, not measured provider-token savings. No efficiency win is proven yet.

## 8. Execution boundaries and secrets — P1

- [x] Repository path/symlink checks for file tools, basic shell deny patterns, filtered subprocess environment, bounded execution/output.
- [x] Local key prompt; credentials are not intentionally written to source/config/reports; sanitized model transport errors.
- [ ] Provide optional process/container isolation for untrusted repository commands. The shell guard is not an OS sandbox and scripts can access the host.
- [ ] Test prompt-injection handling in repository text/tool output and accidental secret exposure from repository files/logs. A filtered environment alone does not solve these.
- [ ] Test network/file restrictions against the actual organiser execution policy.
- [ ] Final credential scan and artifact retention review before sharing/publishing the repository.

## 9. Reporting, reproducibility, and documentation

- [x] Console report, isolated JSONL events, atomic state snapshot, final diff, and performance JSON.
- [x] Token estimates labeled; provider-reported usage where available; call counts, wall time, cache and retry metrics.
- [x] Fresh fixture copies and baseline validation before model invocation.
- [x] README reflects current model, native route, diagnostics, both verified runs, and limitations.
- [ ] Add a benchmark manifest with fixture/repository version, initial tree hash, model/provider/settings, harness revision, commands, result, and evidence location.
- [ ] Add task-level structured test summaries for runners beyond unittest, separating targeted/broad/final runs and failure causes.
- [ ] Separate pacing/backoff/model latency/tool time so runtime comparisons are interpretable.
- [ ] Add an aggregate benchmark report with attempt counts, verified repair rate, token/runtime distributions, failure causes, and links to evidence.
- [ ] Ensure all fatal startup/baseline/runtime paths have useful diagnostics; baseline timeout and unexpected transport/protocol shapes need robustness review.
- [ ] Keep README/checklist/build-plan synchronized at each material change, with confirmed results distinguished from planned work.

## 10. Evidence today

| Evidence | Result | Limit |
| --- | --- | --- |
| Local harness suite | 93 passing tests | Mostly deterministic/mocked integration, not model performance |
| Label normalization | 6/6 final tests; 3 model calls; 29.647 s; 4,448 input + 999 output tokens | One small Python repair, one live attempt |
| Cart checkout | 10/10 final tests; 4 model calls; 39.192 s; 9,522 input + 1,807 output tokens | Two small Python modules, one live attempt |
| Sequelize utility | 158 original + 5 regression checks pass; 8 model calls; 95.230 s; 44,286 input + 5,313 output tokens | Real TypeScript monorepo, narrow task; independent review found extra trailing-decimal acceptance |
| API failures | 3.8 Flash service unavailable; 2.5 Flash 404 on both routes | Service availability varies; catalog/pricing do not prove usable generation |

The two successful runs preserve tests, use Gemini 3.1 Flash-Lite via the native API, and have saved diffs/final verification. “2/2 selected fixtures passed” must not be presented as a general success rate. Raw evidence is under the two benchmark run directories linked in the README.

The subsequent Sequelize run preserves tests and repairs the reported exponent-only cases, but its passing checks missed a compatibility change. See [first-run review](sequelize-first-run-report.md). Prioritize behavior-preservation coverage, compact successful logs, source/build-output diff handling, and genuine live failed-fix recovery. The recorded infrastructure re-review is not proof of coding recovery.

## 11. Recommended execution order

| Priority | Deliverable | Suggested ownership from PRD | Done when |
| --- | --- | --- | --- |
| P0 | Confirm official contract and final startup | Abuzar + shared | Clean evaluator-style run works with prescribed inputs |
| P1 | Real-repository issue benchmark | Shared | Frozen repository/task, baseline, independent final checks, reviewed diff |
| P1 | Demonstrate failure recovery | Shrijan + Abuzar | Live failed attempt → changed approach → verified repair |
| P1 | Long-context memory/filter fixes | Ayush + Abuzar | Noisy long task retains critical decisions and finishes correctly |
| P1 | Non-Python project verification | Shrijan + Ayush | Correct build/test discovery and reviewed live repair |
| P2 | Measured context/runtime comparison | Ayush + shared | Same-task paired runs show benefit without lower correctness |
| P0 | Submission rehearsal + README + demo | Shared | Fresh startup, concise evidence, no secrets, failure paths demonstrated |

These are suggested team responsibilities, not messages or assignments sent to teammates. The organiser contract can change the order and required deliverables.

## 12. What could make us stand out

- [ ] Lead with reproducible real-repository correctness, including cases the agent has not seen.
- [ ] Demonstrate one difficult recovery with a clear trace: failure, diagnosis, revised patch, fresh verification.
- [ ] Show selective navigation and useful memory in a large/noisy repository, with measured context and runtime benefit against a fair baseline.
- [ ] Produce a compact evidence package: issue → reviewed diff → verification → resource use → honest limitations.
- [ ] Make startup effortless and show graceful failure under quota, malformed output, timeouts, and missing tooling.
- [ ] Preserve a deterministic offline demo and saved live evidence if service availability disrupts the presentation; label them accurately.

Avoid spending scarce time on a GUI, multi-agent runtime, model routing, fine-tuning, or speculative integrations. They are outside PRD V1 and do not yet address our biggest risks. Competition scoring is unconfirmed: these priorities improve the submission's substance, but cannot guarantee a win.

**Immediate focus:** confirm the evaluation contract in parallel with selecting one modest real-repository issue, then use its failures to drive recovery and context improvements. Keep Free Tier development, one configured model per task, and README updates throughout.
