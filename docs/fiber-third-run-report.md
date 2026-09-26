# Fiber — third live harness attempt

Evidence: artifacts/external/fiber/runs/20260926-200125-c392bf50/evidence/20260927-013130-a4032bae. Same pinned commit and prepared regression baseline.

**BUDGET_EXHAUSTED / NOT_RUN; no edit.** Eight model calls, nine tool calls, 107.778 seconds. Reported total: 46,259 input / 10,325 output = 56,584 tokens, **including estimates**. Context reduction metric: 28.31%. Do not compare this mixed total directly as provider-measured efficiency against previous attempts.

## What improved and what failed

The harness reproduced the three failures, read the fixed regression tests and searched for the error. After an unsuccessful file-scoped guessed signature, automatic repository-wide symbol fallback found req.go:1550. The model read lines 1540–1600 and 1601–1650, including the actual empty-element counting loop. Unlike earlier attempts, it reached relevant implementation evidence.

It then reread the regression test instead of editing. The eighth model response failed action parsing with ProtocolError: Invalid action JSON. No partial or guessed patch was executed. Conservative accounting left only 3,416 estimated tokens; essential context could not fit another request.

The seven successful responses report 40,044 input / 2,133 output tokens. The failed response was charged an additional estimated 6,215 input / 8,192 output. The actual failed-response usage cannot be recovered from the saved trace; no exact corrected total is claimed.

## Accounting fix

OpenAI-compatible action parsing now attaches provider-reported usage to ProtocolError when the response envelope contains valid usage. This also applies to normalized native Gemini complete responses. If usage is absent but the message is available, estimate the observed message rather than the entire generation cap. Transport failures and malformed/unfinished native envelopes remain separate cases.

111 infrastructure tests pass, including malformed action responses with and without usage. This fixes accounting evidence; it does not establish that the model will generate a valid repair.

## Next experiment

Three attempts produced zero verified repairs. Stop unchanged retries. Use an explicit, focused issue description on a fresh copy with the same fixed tests and budget to separate diagnosis/navigation difficulty from patch generation/protocol reliability. Keep the general discovery task as a separate benchmark rather than silently replacing it. If focused repair also fails, prioritize structured action-output enforcement and model comparisons once authorised evaluation access becomes available. Gemini results cannot predict DeepSeek/Qwen performance.
