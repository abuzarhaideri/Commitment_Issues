# Sequelize compatibility — autonomous closure succeeded

Run: artifacts/external/sequelize/compatibility-runs/20260926-205833-a0f84a7f.
Evidence: evidence/20260927-022849-55aa519d.

**RESOLVED / PASS:** 158 original utility tests, five original regressions and all seventeen compatibility checks pass. Task-manifest protected hashes are unchanged. Model-authored TypeScript fix requires at least one digit after a decimal point in the integer-leading mantissa branch; generated JavaScript/source map match the rebuild. Diff +3/-3 across those three files. No developer production edits.

| Measure | Previous attempt | Successful attempt |
| --- | --- | --- |
| Session outcome | BUDGET_EXHAUSTED; independently passing patch | RESOLVED / PASS |
| Model calls | 10 | 5 |
| Provider tokens | 58,965 | 27,426 |
| Runtime | 117.419 s | 110.860 s |
| Recovery events | 3 | 0 |

Successful run input/output: 23,953 / 3,473. Tokens fell 53.5% and calls halved; runtime fell about 5.6%. These single runs took different model paths and harness revisions, so the differences are descriptive rather than a causal benchmark. Context-reduction metric was 4.16%; no failed-first-patch recovery was demonstrated.

The generated-output review gate completed autonomously this time. Known compatibility regressions are closed under the prepared corpus. This is a database-free utilities task, not all Sequelize tests, universal correctness or upstream merge readiness.

Next controlled task: make benchmark-free ARGS=--synthetic-recovery.
