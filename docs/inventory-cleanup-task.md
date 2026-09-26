# Inventory helper and cleanup follow-up

Run: make benchmark-free ARGS=--inventory-cleanup.

Uses a fresh copy of the latest successful inventory target, preserving original
model-produced evidence. Existing reserve_order checks must remain passing:
eight visible tests and eleven independent acceptance scenarios.

Additional acceptance checks target can_fulfill directly: exact stock,
multi-SKU exact boundaries, insufficient/missing stock, empty requests and
input immutability. Seven helper cases currently have five passes/two failures.
The checker also identifies unused helper imports, trailing whitespace and an
unguarded/stale temporary reproduction script.

The task asks the harness to fix the helper and clean these defects while
preserving working behavior. It may remove the scratch script or retain a
main-guarded useful demonstration. No developer production patch is supplied.
Protected test hashes are checked; no source/code from the successful seed is
changed in place. This is a follow-up contract, not retroactive failure of the
earlier reserve_order acceptance.

Baseline preparation passes. Live follow-up passed all checks; see [result](inventory-cleanup-result.md). Like other development
checks, this is independently maintained acceptance rather than secure hidden
evaluation under OS isolation.
