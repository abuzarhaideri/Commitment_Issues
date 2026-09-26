# Fiber — first live harness run

Reviewed September 26, 2026. Pinned commit: e10bca7375d87511d8c764642689db7809a4e1c8. Run: artifacts/external/fiber/runs/20260926-111031-c78d5d65; evidence: evidence/20260926-164037-a6faf254.

**BUDGET_EXHAUSTED / NOT_RUN:** no production changes or completed repair. Prepared baseline remains four passing and three failing regression checks. This is a failed repair attempt, not a Fiber success.

| Measure | Result |
| --- | --- |
| Model | Gemini 3.1 Flash-Lite |
| Runtime | 141.252 seconds of 600 allowed |
| Model / counted tool calls | 8 / 12 |
| Provider tokens | 59,384 input + 1,343 output = 60,727 |
| Token budget | 60,000; exceeded by 727 (1.2%) |
| Request pacing | 57.630 seconds |
| Context reduction metric | 5.75% |
| Quota / service retries | 0 / 0 |
| Diff | No changes |

## Why it stopped

The token budget, rather than the wall-clock limit, ended the run. The last response crossed the aggregate limit and its actions were not executed. Provider token counts arrive after a request; the current aggregate guard cannot guarantee a hard billed-token ceiling.

The harness first repeated the full failing suite, taking about 65 seconds despite the prepared regression baseline. It searched guessed receiver signatures, including the same empty literal query three times. A later broad search produced test-heavy results. It eventually reached the implementation, but history and duplicated failure context had accumulated. Input was 97.8% of total usage. There was no provider outage, invalid patch or completed verification.

## Changes prepared for the retry

- Supply a focused regression diagnostic command before full final verification; no source-file diagnosis or patch is provided.
- Explain literal search behavior and flag repeated empty searches with an alternate-search suggestion.
- Bound recent failure messages in the model context anchor; preserve original event/state evidence.
- Keep the same model, 60,000-token budget and full suite/vet/race acceptance checks.

These are locally tested changes, not measured live efficiency gains. No Fiber production fix was authored by the developer. Next: rerun the harness on a fresh target, compare calls/tokens/navigation, then independently inspect any patch and test integrity. If navigation still stalls, prioritize source-aware search and durable findings memory. Multi-seed repairs, held-out compatibility cases and strict token reservation remain outstanding.

Run: make benchmark-free ARGS=--fiber. Enter the key only at the hidden local prompt.
