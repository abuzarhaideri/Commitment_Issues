# Fiber final comparison — completed

One attempt per side on pinned Fiber e10bca7375d87511d8c764642689db7809a4e1c8 with the same focused trailing-empty Range task and protected checks.

**Sol/low performed better on verified completion of this task. The harness failed without a patch.** This compares different models and execution surfaces, not an isolated measure of orchestration quality.

| Measure | Harness | Isolated Codex baseline |
| --- | --- | --- |
| Model | Gemini 3.1 Flash-Lite | gpt-6-sol, low reasoning |
| Result | BUDGET_EXHAUSTED / NOT_RUN | Independently verified PASS |
| Production changes | None; starting hashes unchanged | req.go, two-line fix |
| Acceptance | No final verification | 7 regressions; full suite/vet; Range race passed |
| Repair-session time | 109.726 seconds | 272 seconds, agent-reported |
| Tokens | 59,712, provider-reported | Unavailable; target allowance unenforced |
| Model/tool calls | 7 / 5 | Not directly comparable; agent manual counts only |

The shorter failed session is not an efficiency win. Parent independent verification is outside Sol's reported repair time. The complete contributor checklist was not run; no upstream merge-ready claim. Full-suite socket restrictions required a permission retry, recorded as an environment failure. No token-efficiency winner can be established without Sol usage.

## What the harness actually did

1. Reproduced the baseline and searched for a guessed parseRange symbol (no match).
2. Read the regression test, then used the labelled method-signature fallback to locate req.go.
3. Read req.go lines 1550–1650 by about 40 seconds.
4. Encountered invalid action JSON.
5. Correctly recorded that `moreRanges != ""` drops the last empty comma element.
6. Received no complete action text with finish reason MAX_TOKENS.
7. Stopped at 288 remaining tokens. No edit action executed, no net patch and no final verification.

Two failed model responses consumed 29,612 tokens (49.6% of 59,712). This is computed from provider-reported total minus the five successful llm_call event totals. Their output usage alone was 14,757 tokens. Gemini output accounting includes reported thought tokens when present; it is not all visible JSON text. Failed response bodies were not retained, so the exact first malformed payload cannot be diagnosed from this trace.

Navigation and hypothesis recording worked in this attempt. The principal observed bottleneck is converting a correct diagnosis into a complete, valid, compact edit action and recovering within budget. Provider availability was not the cause; no service/rate retries occurred. Request pacing contributed 31.183 seconds, reported separately.

## Next focused improvements, without another live retry

1. Validate schema-constrained/native action generation on offline malformed/truncated-response fixtures; keep strict rejection and no partial writes.
2. Add compact patch guidance/action limits: one small unique replacement per edit, bounded goals/findings, no full-function rewrites unless necessary. Output caps must account for reasoning and must not simply truncate necessary JSON.
3. Make protocol recovery narrower and reserve budget for one corrective action plus verification; larger total limits alone do not address wasted generation.
4. Record per-call provider input/output usage for failed calls, sanitized finish reason, action phase and response-size metrics. Current failed totals require subtraction; avoid logging credentials/source indiscriminately.
5. Validate the exact DeepSeek/Qwen transports when organisers provide them. A better model may help, but this two-model comparison cannot separate model from harness effects.

The two-attempt experiment is finished. Do not retry this unchanged benchmark or copy Sol's solution into the harness target and label it a harness repair. A future run requires a specific implemented improvement and a new explicitly scoped experiment.

Raw comparison: artifacts/comparisons/final-fiber/comparison.json. Harness evidence: artifacts/external/fiber/runs/20260926-213832-eaeaba5b/evidence/20260927-031003-88f961b7. Sol result and independent logs are linked in the comparison JSON. Historical Fiber runs retain their original failure statuses.
