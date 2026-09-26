# Synthetic repository: four starter issues

This lab is a standard-library Python service with catalog labels, feature
configuration, pagination, and checkout pricing. It is deliberately small so
we can evaluate correctness before longer recovery/context tasks.

| Order | Issue ID | Bug | What it tests | Expected failures out of 31 tests |
| --- | --- | --- | --- | --- |
| 1 | `label-order` | Deduplication sorts labels | Order, Unicode, blanks, iterables, mutation | 4 |
| 2 | `boolean-config` | `false`/`0` enable features | Parsing, normalization, defaults, invalid input/types | 3 |
| 3 | `pagination` | First page skipped | Off-by-one indexing, last pages, empty input, boundaries | 4 |
| 4 | `checkout` | Quantity/discount/shipping totals wrong | Two-module changes and interacting rules | 5 |

The first/fourth issues revisit the earlier small fixtures inside a combined
repository with unrelated regression checks. Boolean configuration and
pagination are new tasks. None is a real upstream issue.

## Fair task preparation

`repo/` is a healthy template with 31 passing tests. The runner copies it to a
fresh `artifacts/synthetic/<run-id>/target`, overlays only the selected issue's
buggy implementation, and adds that issue as `ISSUE.md`. Other features stay
healthy. The agent's target contains neither the healthy reference version of
the selected module nor the bug/issue catalog. Preparation happens before its
initial snapshot, and no solution patch is sent to the model.

Each live run gets exactly one issue. Final verification runs the entire
31-test suite. Existing test files are protected by the harness. Every attempt
gets its own baseline log, hash manifest, target, final diff and evidence.
Reference templates/bugs are outside the agent's file-tool root; this is not
OS-level isolation against arbitrary shell access, so it is a development
benchmark, not a secured hidden evaluation.

## Run issues separately

```bash
make benchmark-free ARGS='--synthetic-issue label-order'
make benchmark-free ARGS='--synthetic-issue boolean-config'
make benchmark-free ARGS='--synthetic-issue pagination'
make benchmark-free ARGS='--synthetic-issue checkout'
```

Run one command, confirm `FREE`, enter the key privately, and review its result
before moving on. The selected Gemini Free Tier model, native route, hidden key
entry, budgets and no automatic paid fallback remain unchanged. Repeating a
command creates another fresh baseline rather than reusing a repaired tree.

Offline preparation check, requiring no key or generation:

```bash
.venv/bin/python benchmarks/run_synthetic.py --issue all --baseline-only
```

## Current evidence

- All four offline broken baselines have been executed and match expected counts.
- The healthy template passes all 31 tests in local verification.
- Issue 1, `label-order`, passed its first live run: all 31 checks pass, only `catalog.py` changed, 41.174 seconds and 7,832 total tokens. No recovery or API retries occurred; the current context-reduction metric is 0%.
- Issue 2, `boolean-config`, passed: all 31 checks, only `settings.py` changed, 65.435 seconds and 22,014 total tokens. Its recovery record is an expected baseline failure, not a failed first patch. Context reduction remains 0%.
- `pagination` and `checkout` have also passed all 31 checks; all four basic issues are complete. See [live results](results.md) and the [efficiency review](../../docs/efficiency-review.md).
- Prior label/checkout fixture successes remain separate results and do not
  establish results for this lab.

Record each live run's issue ID, status, independent test outcome, reviewed
behavior changes, tokens, calls, wall time and recovery cause. A passing report
still needs a compatibility review, as the Sequelize run demonstrated.

After these basics, add tasks involving a misleading stack trace, a failed
first fix, three-module refactoring, long logs, and held-out compatibility
cases. Change one difficulty dimension at a time.

Next difficulty level: [inventory reservations](../inventory_lab/README.md), a separate three-module task with distractors and independent acceptance cases.
