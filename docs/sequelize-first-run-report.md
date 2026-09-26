# First real-repository run: Sequelize

Reviewed September 26, 2026. Repository commit: `abf5936c77ad9c09ba1a3116b54e7558bb4528e5`. Evidence: `artifacts/external/sequelize/evidence/20260926-145231-50413f2e/`.

## Outcome

The harness autonomously located and edited a TypeScript numeric-syntax utility in the Sequelize monorepo. It rejects the reported exponent-only strings (`e5`, `-e5`, `E+10`). Source rebuild, all **158 original utility tests**, and all **5 added regression checks** passed in both final verification executions. Regression checks retained their prepared hash, and the tracked Git diff changes only one source line. The filesystem report also includes regenerated JavaScript and its source map.

The recorded result is `RESOLVED` / `PASS` against the supplied checks. Independent review nevertheless found an unrequested compatibility change, so this is **a successful targeted repair with an outstanding behavior-preservation concern**, not proof of a fully regression-free patch.

## Measurements

| Measure | Result |
| --- | --- |
| Model / route | Gemini 3.1 Flash-Lite / native JSON actions |
| Runtime | 95.230 seconds |
| Steps / model calls / counted tool calls | 8 / 8 / 13 |
| Provider-reported usage | 44,286 input + 5,313 output = 49,599 tokens |
| Configured aggregate token budget used | 82.7% of 60,000 |
| Pacing wait | 51.828 seconds; no quota/service retries |
| Current context reduction metric | 0%; candidate and sent estimates both 37,600 |
| Cache hits / misses | 3 / 1,274; includes search traversal, not just model reads |
| Diff | +3/-3 across source, generated JS and source map; tracked source +1/-1 |
| Recorded recovery | One rebuild-triggered diff re-review, not a failed coding attempt |

The 13 counted tool calls include verifier operations, not only model-selected development tools. Context figures are estimates under the current packing metric; they are not equal to the provider's actual input usage.

## Independent compatibility finding

The new regex allows zero digits after a decimal point in its integer branch. A read-only probe against the repaired build and the original source regex confirmed:

| Input | Original predicate | Repaired predicate |
| --- | --- | --- |
| `e5`, `-e5`, `E+10` | true | false — intended fix |
| `1.`, `-1.`, `1.e3` | false | true — additional behavior change |
| `1.0`, `.5`, `-.5`, `1e+3` | true | true — preserved controls |

Because `parseFiniteNumber` uses this predicate, the additional accepted forms also parse to numbers instead of returning null. The supplied tests did not cover these forms. Maintainer intent for trailing-decimal syntax has not been established; under this benchmark's requirement to preserve existing rejection behavior, they need explicit regression coverage and a narrower repair or an approved requirement change.

The original run artifacts/status and agent patch were preserved. Review did not edit the source or rerun a live model.

## Conclusions

1. Real monorepo navigation and TypeScript source repair work for this narrow prepared task. This is stronger evidence than the synthetic Python fixtures.
2. Rebuild-before-test verification prevents a generated-JavaScript-only fix and correctly forces review when build outputs change.
3. Passing visible checks and the same model's semantic review missed a compatibility change. Verification needs stronger behavior-preservation coverage.
4. Repeated diff review, source-map content, full successful test logs, and growing context create measurable efficiency opportunities. There is no measured token-saving win yet.
5. The environment, task, and regression checks were prepared by the development assistant. Autonomous installation, database-backed ORM behavior, broad TypeScript repair, and failed-fix recovery were not demonstrated.

## Next improvements, in order

1. Add fixed compatibility checks for trailing decimal forms and a broader valid/invalid numeric corpus; independently validate the next repair on held-out cases.
2. Strengthen semantic verification with explicit “which previously rejected/accepted inputs changed?” checks and accurate completion wording.
3. Make diff review aware of source versus regenerated build outputs while retaining integrity checks; avoid repeatedly sending source-map duplicates.
4. Send compact pass summaries and relevant failures instead of entire successful test logs; retain raw evidence on disk.
5. Improve bounded session memory and account for the actual provider request before claiming efficiency savings. Benchmark the same task/settings against the current run.
6. Separate infrastructure re-review from genuine failed-fix recovery; improve test counts for Mocha/Node TAP and distinguish traversal from targeted reads in metrics.
7. Try a harder issue spanning modules and requiring a failed-fix recovery, then a database-backed task if a reproducible database setup is available.

Evaluator startup and official model/runtime compatibility remain submission blockers independently of this result. Repeated trials must start from a fresh prepared baseline, never silently reset the reviewed checkout.
