# One final real-repository comparison

Planned, not executed. Repository: https://github.com/gofiber/fiber at e10bca7375d87511d8c764642689db7809a4e1c8. Use the existing focused RangeMaxRanges trailing-empty-entry task from benchmarks/run_fiber.py, not unrestricted bug discovery. This is a known previous failure, so it is a regression/improvement check, not a fresh blind holdout.

Why this task: real upstream defect at the pinned snapshot, original 56-package baseline already prepared, seven fixed regressions (4 pass / 3 fail), independent suite/vet/race verifier, and four earlier unsuccessful harness attempts. No injected production defect or developer-provided patch. Historical runs used earlier revisions and cannot serve as a controlled comparison by themselves.

## Run conditions

- Freeze source, exact issue text, regression checks, runtime and harness revision before either repair.
- Separate fresh copies from the pristine source; never copy one side's patch/results to the other.
- Harness: existing free Gemini 3.1 Flash-Lite native route unless user explicitly changes the model. Hidden local key required; no paid API fallback.
- Codex comparison: fresh agent with no inherited conversation, gpt-6-sol with low reasoning (the available configuration corresponding to the requested Sol Light baseline). Do not claim a distinct model ID called Sol Light.
- Give both sides identical issue and public checks, no file-location hint, solution or previous failure diagnosis. Fresh Codex agent receives only task, runtime/verifier instructions and comparison constraints.
- One attempt per side, no orchestrator coaching or patch changes mid-run. Start repair time after environment preparation. Target 600-second wall limit and 60,000 aggregate-token allowance per side; record any inability to enforce/observe these on the Codex side. Do not pretend API tokens and agent usage are directly comparable without available totals.
- Model turn limits/tool implementations may differ; disclose actual limits. Full acceptance verification is performed independently after each repair, with equal verification limits. A candidate patch is not counted as resolved merely because a focused check passes.
- Keep tests/config/instructions protected. Require seven regression checks, original full suite, vet, focused race checks and independent patch review.

## Comparison report

Record model/version/reasoning, starting commit, issue hash, budget enforcement, final status, checks, protected-file hashes, patch size/quality, runtime, calls, usage source/estimates and any human intervention. Correctness first; compare efficiency only when acceptance outcomes match. Provider pacing is part of end-to-end time and should be stated.

Gemini harness versus Sol Codex is a comparison of complete systems, combining model and orchestration effects. It cannot isolate the harness's benefit. A same-model ablation would require API access/configuration that is not currently free/available to us and is not part of this plan.

Stop after these two attempts and one independent review each. Failure is a result; do not launch repeated retries. If the harness fails, the fresh Sol attempt still runs. If either is unavailable due to credentials/provider/usage limits, record that limitation rather than change models silently. No upstream publishing, messaging or PR is included.

Both runs await execution; no live calls or repair were made while writing this plan. User remains committed to no paid API usage. Codex execution is subject to the user's existing account limits; no purchase is authorized.

## Execution started

Frozen manifest: artifacts/comparisons/final-fiber/manifest.json. Both baseline targets reproduced 4 pass / 3 fail. Sol is isolated with no inherited conversation and restricted to its own target. Harness/config source hashes are frozen; the hidden-key launcher rejects changes and a second attempt.

Harness command: `.venv/bin/python artifacts/comparisons/final-fiber/run_harness.py`. User enters the key privately. Do not use an older run or repeat launcher to fill this comparison slot. Results are pending; no winner is asserted.
