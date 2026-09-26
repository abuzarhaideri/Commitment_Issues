# Intermediate synthetic inventory task

Run: make benchmark-free ARGS=--synthetic-inventory.

The task repairs reserve_order across quantities.py, inventory.py and orders.py:
duplicate SKU aggregation, exact-stock acceptance and atomic failure handling.
Twelve legacy helpers act as search distractors. Positive integer validation,
generator input and receipt independence are part of the contract.

Each attempt gets a fresh broken copy. Eight visible tests reproduce three
assertion failures and one unexpected error; four tests pass. Full acceptance
requires those eight tests plus eleven independent scenarios through the
external verifier. The healthy reference passes both. No solution patch is
sent to the model. Tests remain protected; original references live outside
the file-tool root.

The external acceptance corpus is independently maintained, not a secured
hidden evaluation: scripts can access host files without an OS sandbox.
The same free model, 60,000 tokens and 600-second budget apply. This is a
synthetic defect set, not an upstream issue. The first live reserve_order repair passed eight visible tests and eleven independent scenarios. See [source review](../../docs/synthetic-inventory-report.md) for helper/cleanup caveats.

Offline baseline: .venv/bin/python benchmarks/run_inventory.py --baseline-only.
A single attempt covers several interacting defects; compare it separately
from earlier one-defect starter tasks. Do not report its baseline counts as
model performance.
