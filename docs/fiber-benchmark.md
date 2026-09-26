# Fiber harness benchmark

Prepared September 26, 2026. This is a harness test, not a developer-authored repair. **The first live attempt exhausted its token budget without editing Fiber production code.** A Gemini key is not available to the tool process; the user can enter it privately through the existing Free Tier launcher.

## Environment and baseline

- Public repo: https://github.com/gofiber/fiber
- Pinned commit: e10bca7375d87511d8c764642689db7809a4e1c8
- Unchanged clone: artifacts/external/fiber/source
- Go 1.26.8 darwin/arm64 downloaded from go.dev with published SHA256 validation, installed under artifacts/external/fiber/runtime. No global Go install changed.
- Module/build caches are local to this benchmark. Dependencies downloaded without modifying go.mod/go.sum; verifier uses readonly modules and GOPROXY=off.
- Original `go test -json -count=1 ./...` passed: **56 packages, 2,957 top-level tests**, **6,386 passing test/subtest events**, one skip event. Parent/subtest counts overlap, so these are not 6,386 independent top-level tests.
- Original JSON output: artifacts/external/fiber/baseline-original.jsonl; metadata: benchmark.json in that directory.

## Prepared repair test

The documented Range contract states that empty comma-list elements count toward MaxRanges even though they are not ranges. Current parsing misses the final trailing empty element. Seven fixed checks reproduce three failures and four passing controls. The bug exists in upstream source; no defective production code was injected. This is a locally reproduced documented-contract issue, not a claim of a filed upstream issue.

The previously discussed #4604 URL-escaping task was not selected: existing tests explicitly expect behavior that a broad escaping change would alter. Its scope needs maintainer clarification rather than weakening those tests.

Each live invocation copies the untouched clone into a new runs/<id>/target and adds the same fixed Go regression file. Original clone and earlier targets are preserved. The model gets a general inspection/repair task, not the prepared diagnosis or a patch. Tests are visible for diagnosis and read-only. This is **a prepared regression-backed repair task**, not a blinded claim of unrestricted autonomous bug discovery across all Fiber code.

The harness owns navigation, diagnosis, production edits, testing, recovery and diff review. The developer owns setup, fixed checks and independent review. `_test.go` files are now protected by edit tools and final integrity checking; the verifier also checks hashes of tests, dependency files, Makefile, instructions and CI files.

## Run privately

```bash
make benchmark-free ARGS=--fiber
```

Confirm FREE and enter the Gemini key at the hidden local prompt. Do not put it in chat. Uses Gemini 3.1 Flash-Lite native JSON actions, low reasoning, 20 model turns, 60,000 aggregate tokens, 600 seconds, 12-second request pacing and no automatic fallback. Only a user-confirmed Free Tier project with billing disabled should be used.

The launcher verifies a fresh 4-pass/3-fail baseline before requesting the model. Final checks are the full Go suite plus go vet, followed by focused Range race tests. Full raw Go JSON is stored outside the target; concise failures/counts are supplied to the model. Commands have a 240-second limit within the overall task budget.

For preparation without model calls:

```bash
.venv/bin/python benchmarks/run_fiber.py --baseline-only
```

The setup is currently specific to this machine's prepared arm64 Go runtime. It is a benchmark prerequisite, not a portable installer or the official submission profile.

## Acceptance and limits

- Before repair: seven regression checks, four pass/three fail.
- After repair: all seven pass, existing suite/vet and focused race checks pass, tests/config remain unchanged, final source diff reviewed.
- Read Fiber AGENTS.md. Its audit/generate/betteralign/format/lint/test checklist remains necessary before proposing an upstream merge. The benchmark verifier does not substitute for that entire checklist; no upstream merge readiness is claimed.
- Missing credentials, provider errors, budget exhaustion or failed checks are failures/pending states, not successful fixes.
- No GitHub issue/comment/PR has been created. Contributor discussions precede upstream contribution; local benchmarking does not authorize external messaging.

Current status: **first live attempt BUDGET_EXHAUSTED / NOT_RUN; no repair produced**. See the [first-run analysis](fiber-first-run-report.md). The retry now supplies a focused regression diagnostic command while retaining full final checks. Live confirmation of the changes is pending.

Second live attempt also exhausted budget without editing: 52,314 tokens / 87.147 seconds. See [second-run review and follow-up](fiber-second-run-report.md). Latest local suite: 109 passing tests; signature fallback, large-file definition maps and remaining-budget context packing await live validation.

Third attempt reached the implementation but failed action parsing before editing. See [third-run report](fiber-third-run-report.md). No verified repair across three attempts; next controlled experiment should provide an explicit issue description and retain this discovery task separately. Accounting fix locally validated with 111 tests.

## Explicit issue-driven control

```bash
make benchmark-free ARGS=--fiber-focused
```

The prompt describes trailing empty Range entries, exact failing inputs, MaxRanges limits and expected error/status/header behavior. It supplies neither a patch nor an implementation file location. Original discovery mode stays available as --fiber.

Focused mode preserves model settings, token/time limits, fresh-target isolation, fixed protected tests and independent final verification. task-manifest.json labels task_mode=focused (discovery otherwise); issue.txt saves its base issue text and state/events retain the complete runtime task with the diagnostic command. Previous discovery runs used earlier harness revisions and stochastic model responses; their historical metrics are not a controlled measurement of prompt effects alone.

For offline preparation: .venv/bin/python benchmarks/run_fiber.py --focused --baseline-only. This reproduces the same four-pass/three-fail baseline without API calls. Live focused results are pending.

Focused mode first live attempt also failed without a net patch; see [report](fiber-focused-first-run-report.md). Four total attempts have produced no verified Fiber repair. Latest local suite: 123 tests; model output and exact-edit reliability remain the priority.
