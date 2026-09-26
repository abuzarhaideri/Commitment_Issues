# Intermediate inventory live repair

Run: artifacts/inventory/20260926-204714-e54aa6db; evidence: evidence/20260927-021715-cf121c7e.

**RESOLVED / PASS:** all eight visible tests and eleven independent acceptance scenarios passed in final verification. Baseline hashes confirm only orders.py and quantities.py changed among original files. The model also added reproduce_issue.py; tests and distractors were unchanged.

Seven model calls, fifteen counted tool calls, 18,772 input + 3,447 output = 22,219 provider-reported tokens, 75.298 seconds. Context reduction metric 0.83%; recovery events zero. This does not demonstrate failed-patch recovery or a controlled efficiency gain.

## Source review

quantities.py now sums duplicate SKUs. orders.py validates all quantities against stock before applying deductions, preserving atomicity on rejection and accepting exact stock through its direct comparison. Positive-integer/type validation was already present and remained unchanged; the reason text should not imply this was newly implemented.

The supplied public contract is reserve_order. It passes the inspected cases, including generators, unknown SKUs, invalid inputs and independent receipt/stock dictionaries. The previously defective can_fulfill helper in inventory.py remains unchanged and is now bypassed; its direct API behavior was outside this task's stated acceptance. No claim is made that every module/helper is repaired.

## Patch quality caveats

The diff retains unused can_fulfill import and trailing whitespace. Added reproduction script has top-level execution and a stale comment describing the old duplicate behavior. These do not fail the acceptance contract, but should be cleaned by the harness before presenting a polished production patch. No developer cleanup was applied to the model's target; evidence is preserved.

## Next

The pending real-repository compatibility task is ready:
make benchmark-free ARGS=--sequelize-compat.

That task must preserve all original utility/regression checks and resolve all seventeen compatibility cases. Later add helper-API acceptance checks and model-driven cleanup/quality gates to the inventory benchmark, as a separately labelled task; do not retroactively change this run's acceptance result.
