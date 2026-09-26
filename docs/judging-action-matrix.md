# Requirements → actions → evidence matrix

September 27, 2026. Source distinction matters: **O** = confirmed official PDF requirement; **P** = team PRD acceptance/priority; **E** = observed engineering failure. The PDF is AI Harness Submission (1).pdf, sections below. PRD sections 4 and 26 set correctness → verification → recovery → efficiency; section 27 explicitly leaves numerical scoring weights unknown. This is an evidence mapping, not the organisers' unpublished scoring sheet.

| Requirement / source | Observed gap | Action and causal relationship | Bounded acceptance check | Remaining limit |
| --- | --- | --- | --- | --- |
| O §5: supplied issue/test case must run through harness; P §26 autonomy/correctness | E Fiber found correct cause but produced no edit | **Priority 1: constrain action output and match arguments to allowed tool schema.** Valid actionable output enables model decisions to reach tools; invalid or incomplete actions still never mutate files. | Offline valid action dispatch plus malformed/truncated rejection; native request schema includes tool-specific fields. | Schema validity does not establish algorithmic correctness; no new live success claim. |
| P §26 failures enter recovery; O §11 evaluators will not modify implementation to make it executable | E two invalid/truncated responses prevented repair | **Priority 2: narrow corrective context**, preserving issue/contract, diagnosis and relevant source; restore normal mode after valid output. This targets automated recovery without orchestrator coaching. | Offline protocol failure → correct small edit → independent PASS; stale/irrelevant history omitted, essential source/constraints retained. | Official §11 is a startup requirement, not an explicit recovery scoring weight. Offline scripted recovery is infrastructure evidence. |
| P §4/§26 token/context and runtime efficiency; O §10 reproducible settings | E failed responses consumed 29,612 of 59,712 tokens (49.6%) | Bound corrective instructions, avoid diagnosis repetition and instrument failed-call usage. Compare measured recovery context while keeping final verification unchanged. | Record per-call usage/estimate flag and bounded recovery context in deterministic fixtures; no higher total allowance. | Numeric efficiency threshold/scoring weight unknown. Smaller context alone does not prove live total-token savings. |
| P §26 verification and reporting; O §5 testing infrastructure | E completion claims can exceed actual acceptance | Keep exact unique edits, protected tests, independent final checks and full diff review while changing action/recovery paths. | Recovery integration test must pass unchanged tests; truncated action applies no writes; report unsuccessful attempts accurately. | Visible tests and model review cannot guarantee hidden-test correctness. |
| O §3/§4 text-only prescribed model; team informed DeepSeek/Qwen | Exact model IDs/protocol unavailable | Put vendor-specific schema handling in adapter; retain generic JSON route instead of assuming Google schema support everywhere. | Adapter request/normalization regressions; no provider fallback; text-only inputs maintained. | Actual prescribed DeepSeek/Qwen connectivity/action/repair validation still pending. |
| O §1/§2/§8/§9/§12–14 root setup/run/test, AI_API_KEY, no credentials, clean environment | Final runtime/profile not supplied | Preserve startup/key flow; rehearse refreshed source through clean clone and simulated HTTP model. | Full infrastructure suite once; one local clean-clone setup/test/launch/repair rehearsal; limited package format scan. | Simulation is not the official runtime/model, limited scanning is not full secret audit. |

## Two-agent implementation boundary

Sol agents use gpt-6-sol with low reasoning (the available configuration for the requested Sol Light). Agent 1 owns models/Gemini protocol and adapter tests; agent 2 owns orchestration/context/recovery tests. The orchestrator reviews integration, this matrix and README/checklist. Neither agent changes the frozen Fiber comparison targets or reclassifies its failed run.

## Stop criteria

One targeted regression pass per changed component, one integrated infrastructure suite, one clean-clone simulated rehearsal. Repair failures in these checks before release; stop once passing. No live Gemini retries, new benchmark tasks, paid API calls or unsupported final-model claim are included.

## Measuring progress honestly

- Action reliability: complete valid actions dispatch, malformed/truncated actions rejected; do not label syntax success as repair success.
- Recovery: deterministic failing-response → verified-task completion without external patch assistance; distinguish scripted control from live behavior.
- Efficiency: compare context and per-call usage at equal correctness; preserve estimates and failures. No general percent improvement from one control.
- Submission: startup rehearsal passes; final model/runtime gates remain explicit.

This aligns our two immediate actions with the PRD's first unmet practical boundaries, while preserving the PDF's submission requirements. It does not assign invented official points.

## Implementation outcome

Both priorities implemented by two isolated Sol/low agents and reviewed together. Current infrastructure suite: 151 tests. Native Gemini requests now include a tool-specific responseJsonSchema once and request one canonical action; generic routes request the same single-object shape without unsupported schema options. Legacy response arrays remain accepted by the decoder. Google's API reference documents these schema fields: https://ai.google.dev/api/generate-content#v1beta.GenerationConfig. No live endpoint compatibility is claimed.

Focused recovery retains full issue/safety/verification contract, model findings, supplied test commands and up to two relevant source observations plus latest useful edit/test/diff. Unrelated history/maps are omitted from that request, with full evidence retained. If source cannot fit, the model is explicitly told to reread a narrower exact range. Normal context resumes after valid output. Corrective instructions request one small edit or necessary read, not a whole-function rewrite.

Failed-call events now include input/output counts, estimated flag and safe finish/status classifications. Native request estimates include schema overhead. Total budgets and output allowances were not increased or reduced. A dedicated future-token reserve was not implemented: narrowed recovery avoids resend waste, but cannot guarantee adequate budget after a very expensive generation.

Offline checks cover malformed/truncated rejection with usage preservation, schema binding, no partial action return, focused diagnosis/source retention, schema-heavy budget guards and truncation → corrective edit → independent PASS. These are infrastructure checks, not a rerun of Fiber or evidence of live token savings. Final evaluator configuration/validation remains pending.

Integrated clean-clone setup/test/launch/simulated HTTP repair passed with 151 tests: artifacts/submission/rehearsals/20260926-220452-6dc37497/rehearsal.json. Local package: 129 allowlisted files. Subsequent documentation records this result only; no additional live trials.

## Next two priorities: reserve and evaluator transport

| Source/target | Action | Acceptance evidence required | What it does not prove |
| --- | --- | --- | --- |
| P §4/§26 correctness, recovery, efficiency | Hold an adaptive correction/review reserve inside the existing total budget; allow phase-dependent access and expose decisions | Normal diagnosis holds reserve; corrective action can access part; actual patch verification/review can access remainder; no no-op release or total increase | A provider/token estimate can still overshoot; reserve alone cannot guarantee a correct repair |
| O §4 prescribed-model configuration, O §9/§10 reproducible execution; P model abstraction | Strengthen configurable compatible/Responses adapters with representative provider contracts, request overhead estimates, bounded retries and task deadlines | Offline JSON/native contracts, reasoning/content separation, incomplete-action rejection, preserved usage/auth/model, retry/deadline/fatal-error controls | Actual DeepSeek/Qwen model/version/hosting/API support remains unconfirmed; do not guess final profile |

No official numeric score is derived. A 7+/10 target must be earned through verified representative repairs and actual evaluator readiness; passing additional infrastructure tests is not sufficient to guarantee it.

These two priorities are now implemented and offline-validated: adaptive phase reserve and compatible/Responses transport contracts. Integrated suite: 172 tests. Details, controls and remaining live-validation limits: [reserve/adapter report](reserve-adapter-progress.md).
