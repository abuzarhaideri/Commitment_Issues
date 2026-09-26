# Fiber — second live harness attempt

Evidence: artifacts/external/fiber/runs/20260926-195521-57c54f48/evidence/20260927-012526-b92f9382. Same upstream commit and prepared seven-check baseline as attempt one.

**BUDGET_EXHAUSTED / NOT_RUN; no edit or verified repair.** Gemini 3.1 Flash-Lite used 50,797 input + 1,517 output = 52,314 provider-reported tokens, eight model calls and eight tool calls in 87.147 seconds. Steps=9 includes the final iteration where no request was sent. Request pacing took 55.272 seconds; context reduction was 13.89%.

| Measure | Attempt one | Attempt two |
| --- | --- | --- |
| Total tokens | 60,727 | 52,314 |
| Runtime | 141.252 s | 87.147 s |
| Model calls | 8 | 8 |
| Tool calls | 12 | 8 |
| Production edit | None | None |
| Verification | NOT_RUN | NOT_RUN |

Recorded usage fell 13.9% and runtime 38.3%; both are single attempts with different trajectories, not a controlled reliability estimate. Neither fixed the defect.

## Diagnosis

The focused baseline ran successfully as a diagnostic (expected three failing checks). The model read the regression test, searched guessed Ctx and DefaultCtx method signatures without matches, then used grep without line numbers. It found req.go but read its first 200 lines and lines 300–499, missing the implementation at 1550. Navigation guidance was not followed consistently.

The budget guard correctly withheld another request: remaining allowance 7,686; estimated input including safety margin 8,762, before reserving response capacity. This did not indicate provider quota exhaustion. It prevented another predicted unaffordable request but did not solve navigation.

## Follow-up implementation

- If an automatic literal search for a function signature finds no source matches, derive the method symbol and search it independent of receiver. Label this fallback explicitly and preserve file/line locations. Exact-source and explicit-all search scopes remain available.
- Default reads of large source files return recognized definitions with line numbers; explicit start/end continues to return exact source. This prevents sequential scrolling through unrelated file sections.
- Tighten context packing using remaining estimated request allowance before applying the guard. Essential/latest context must still fit; estimates remain approximate.
- 109 infrastructure tests pass. On the untouched Fiber clone the exact failed signature query now returns req.go:1550, and its default file map includes that definition. No Fiber production patch was authored.

Live repair success and new token savings remain pending. Rerun make benchmark-free ARGS=--fiber with the hidden local key prompt; independently verify any returned patch against unchanged acceptance checks.
