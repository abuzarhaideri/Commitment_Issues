# Sequelize compatibility correction — patch passes, autonomous run incomplete

Run: artifacts/external/sequelize/compatibility-runs/20260926-205048-4d69f0da.
Saved evidence: evidence/20260927-022103-815bb593.

Original harness result remains **BUDGET_EXHAUSTED / NOT_RUN**. The patch is independently verified; these are separate conclusions.

## Patch and verification

The model changed the decimal digit quantifier from * to + after the decimal point. This restores rejection of trailing-decimal forms while preserving the earlier mantissa requirement. TypeScript source changed one line; generated JavaScript/source map account for the other reported files (+3/-3 overall).

The harness verification command actually passed 158 original utility tests, five original issue regressions and all seventeen compatibility checks. Its later build-diff review requirement prevented final acceptance. Independent rerun after the reported failure also passed all checks with protected hashes intact. Log: independent-verification.log in the run directory. No developer production fix was made, and original evidence/status was not altered.

This closes the known four-case compatibility gap under the verified corpus. It does not prove every possible numeric-input contract or upstream merge readiness.

## Why the session failed

Ten model calls / ten counted tool calls, 46,284 input + 12,681 output = 58,965 provider tokens; runtime 117.419 seconds. Context reduction metric 25.54%, request pacing 53.016 seconds.

The trace includes a malformed action response and a wrong test-directory lookup before editing. After patching, the harness required source diff review, ran the checks, then detected generated build outputs changed. It treated the re-review requirement as a verification failure and needed additional model calls despite passing tests. Remaining tokens were 1,035, insufficient for task context.

## Harness changes

- Deliver larger diff chunks, bounded by serialized size to preserve complete evidence while reducing repeated finish calls.
- Passing checks that change non-protected files set PASS_PENDING_REVIEW; tests/config changes still fail.
- Retain a snapshot of independently verified content. After updated diff review, do not rerun commands if the content is exactly unchanged.
- A subsequent source edit invalidates the snapshot cache and requires fresh checks.
- Semantic review and final diff gate still apply; test success alone cannot mark RESOLVED.

133 infrastructure tests cover build-output review, protected-file mutation, honest pending status and cache invalidation. Live effects of the revised gate remain unmeasured. The saved run is a successful patch with incomplete autonomous closure, not a retroactive RESOLVED result.
