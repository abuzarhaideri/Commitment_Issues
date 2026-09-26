# Synthetic lab live results

All runs use fresh copies, one active issue, and the full 31-test suite.

| Issue | Status | Final checks | Runtime | Model calls | Total tokens | Review |
| --- | --- | --- | --- | --- | --- | --- |
| label-order | RESOLVED / PASS | 31/31 | 41.174 s | 4 | 7,832 | Only catalog.py changed; no unintended change identified |
| boolean-config | RESOLVED / PASS | 31/31 | 65.435 s | 6 | 22,014 | Only settings.py changed; one expected baseline failure recorded as recovery |
| pagination | Not run | — | — | — | — | Pending |
| checkout | Not run | — | — | — | — | Pending |

Label evidence: `artifacts/synthetic/20260926-152448-label-order-c403efcf/evidence/20260926-152448-769e6d31/` from the project root. See the [label-order report](../../docs/synthetic-label-order-report.md).

Boolean evidence: `artifacts/synthetic/20260926-153056-boolean-config-0f34394f/evidence/20260926-153056-bd727f76/`. See the [boolean analysis](../../docs/synthetic-boolean-config-report.md) and [cross-run efficiency review](../../docs/efficiency-review.md).

Two small synthetic tasks have passed one live attempt each; this is not a general coding success rate. Original logs/diffs are preserved. Earlier standalone label and checkout results are separate benchmarks.
