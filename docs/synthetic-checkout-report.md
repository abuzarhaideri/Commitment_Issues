# Synthetic lab — issue 4: checkout

Reviewed September 27, 2026. Run: artifacts/synthetic/20260927-020547-checkout-f13e20b4; evidence: evidence/20260927-020547-394d013d.

**RESOLVED / PASS.** Five failures in the 31-test baseline became 31/31 passing checks, including independent final verification. Baseline hashes confirm only checkout.py and pricing.py changed; tests and unrelated modules remained unchanged.

## Repair and process

The harness profiled the repository, read both production modules, reproduced the failing suite, edited both files, ran post-fix tests and completed the diff/final verification gate.

pricing.py now multiplies unit price by quantity. checkout.py exempts zero-subtotal carts from shipping and evaluates the free-shipping threshold against the post-discount net. A nonzero subtotal discounted to zero still incurs shipping. The diff is +5/-2; independent source review found the changes consistent with the supplied task. No attempted edit failed and no no-op update was recorded.

| Measure | Result |
| --- | --- |
| Model | Gemini 3.1 Flash-Lite |
| Runtime | 26.805 seconds |
| Model / counted tool calls | 3 / 10 |
| Provider-reported tokens | 8,913 input + 2,363 output = 11,276 |
| Token budget used | 18.8% of 60,000 |
| Context reduction metric | 17.97% |
| Request pacing | 13.762 seconds |
| Quota / service retries | 0 / 0 |
| Recovery feedback / verified recovery | 0 / 0 |

The expected pre-edit failing suite is now correctly recorded as baseline evidence, not patch recovery. All four synthetic issues have passed one live attempt each. Their differing harness revisions and issue complexity prevent a controlled claim about optimization gains. This successful multi-file repair validates this task; it does not negate the four unsuccessful Fiber attempts or prove general repository reliability.

## Next validation

Add a more demanding controlled task: several source modules, distracting files, noisy diagnostics and an independently checked compatibility corpus. Test actual failed-patch recovery and repeat identical fresh tasks to measure reliability. Correct Sequelize's known compatibility regressions through the harness before expanding success claims. Keep pinned open-source bugs as the realism check after controlled tests.
