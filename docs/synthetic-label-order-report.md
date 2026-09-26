# Synthetic lab — issue 1: label order

Reviewed September 26, 2026. Run: `artifacts/synthetic/20260926-152448-label-order-c403efcf/`. Evidence: `evidence/20260926-152448-769e6d31/` within that run.

## Outcome

**RESOLVED / PASS:** the baseline had 31 tests with four ordering-related failures. Both model-requested testing and fresh final verification passed all 31 tests. The baseline hash manifest confirms that only `catalog.py` changed; tests and unrelated feature implementations stayed unchanged.

The previous implementation sorted a set of normalized labels. The repair iterates over the input, strips and case-folds each label, tracks duplicates in a set, and appends each nonblank first occurrence to an ordered result list. Review found this consistent with the issue: order, duplicate/blank removal, Unicode case folding, iterable support, and input immutability are preserved. No unintended behavior change was identified in the reviewed patch; this is not exhaustive proof for inputs outside the task contract.

## Execution structure

1. Profile the repository and assemble the issue/tool context.
2. Search for `normalize_labels`.
3. Read its implementation in `catalog.py`.
4. Apply one targeted replacement to the implementation.
5. Run the full 31-test regression suite, covering labels, settings, pagination, and checkout.
6. Deliver the final diff for model review and require another completion request.
7. Run independent fresh verification; accept only after checks pass.

There was no explicit `update_plan` action in this trace. The loop followed a direct search/read/edit/test sequence. Seven counted tool calls include verification operations, not just the four model-selected development tools.

## Measurements

| Measure | Result |
| --- | --- |
| Model / route | Gemini 3.1 Flash-Lite / native JSON actions |
| Runtime | 41.174 seconds |
| Steps / model calls / counted tool calls | 4 / 4 / 7 |
| Provider-reported usage | 6,681 input + 1,151 output = 7,832 tokens |
| Aggregate token budget used | 13.1% of 60,000 |
| File/diff scope | `catalog.py` only, +9/-3 |
| Coding recoveries / quota retries / service retries | 0 / 0 / 0 |
| Pacing wait | 24.465 seconds, about 59% of runtime |
| Cache hits / misses | 2 / 11; search traversal contributes to misses |
| Current context reduction metric | 0% |

The report's 11 inspected files include search traversal; it does not mean the model requested full reads of all 11. The full suite was run twice; this is 31 distinct checks, not 62 distinct tests.

## Conclusions and improvements

- Correct targeted repair and full-suite verification work inside the combined synthetic repository.
- Unrelated healthy features remained unchanged and their tests passed; this is stronger regression coverage than the earlier standalone label fixture.
- This task does not demonstrate failure recovery or difficult context handling. No token-saving benefit is established by the 0% packing metric or cache counts.
- Runtime includes intentional Free Tier pacing; distinguish pacing from model/tool time when comparing runs.
- Preserve the simple implementation and fixed regression checks. Prioritize compact successful-test summaries, accurate traversal/read metrics, and later held-out compatibility checks rather than changing this passing source again.

Next: run `boolean-config` from a fresh baseline, then pagination and checkout. Each task should retain the full 31-test final verification. Keep the results of the earlier standalone fixtures separate from this combined lab.
