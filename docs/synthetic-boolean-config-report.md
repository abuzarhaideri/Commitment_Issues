# Synthetic lab — issue 2: boolean configuration

Reviewed September 26, 2026. Run: `artifacts/synthetic/20260926-153056-boolean-config-0f34394f/`. Evidence: `evidence/20260926-153056-bd727f76/` within that run.

## Outcome and process

**RESOLVED / PASS:** baseline 31 tests with three failures; both post-fix testing and fresh final verification passed all 31. Baseline hashes confirm only `settings.py` changed (+12/-1); tests and unrelated modules remained unchanged.

Execution: search `parse_bool` → read implementation → rerun the full broken baseline → receive failure feedback → read settings tests → targeted edit → full post-fix suite → final diff review → independent verification. There was no explicit `update_plan` event.

The fix handles None before other types, preserves bool inputs, trims/case-normalizes strings, explicitly maps the four true and four false spellings, raises ValueError for unknown strings and TypeError for other types. Using `lower()` instead of the template's `casefold()` still satisfies this task's specified ASCII boolean spellings. Review identified no unintended behavior change under the stated contract; invalid-default handling was not specified or established by this benchmark.

## Measurements

| Measure | Result |
| --- | --- |
| Model / route | Gemini 3.1 Flash-Lite / native JSON actions |
| Runtime | 65.435 seconds |
| Steps / model calls / counted tool calls | 6 / 6 / 9 |
| Provider-reported usage | 19,820 input + 2,194 output = 22,014 tokens |
| Aggregate token budget used | 36.7% of 60,000 |
| Pacing wait | 34.442 seconds, about 53% of runtime |
| Quota/service retries | 0 / 0 |
| Cache hits / misses | 3 / 11; search traversal contributes to misses |
| Current context reduction metric | 0% |
| Recorded recovery | 1 expected pre-fix test failure; no incorrect first patch observed |

The original 31-test suite was run once by the agent before editing, then twice successfully after editing (including final verification). The launcher had already established the baseline before the model ran. This extra reproduction may be useful, but the harness should expose its existing baseline evidence so the model can decide whether another full reproduction is necessary.

## Conclusions

- Strict parsing and invalid-input behavior were repaired correctly while unrelated features stayed healthy.
- This task used more calls/context than the lab label task, but the issues differ; the comparison is descriptive, not evidence of an optimization regression or a general performance ranking.
- Failed baseline output was recorded as `TOOL_FAILURE`/recovery. That overstates evidence of coding recovery and can add duplicate failure/log context.
- The primary efficiency targets are compact baseline/pass summaries, focused failure extraction, and less repeated history. Preserve independent full final verification.

See [cross-run efficiency review](efficiency-review.md) for all runs and PRD checkpoints. Next live task: `make benchmark-free ARGS='--synthetic-issue pagination'`.
