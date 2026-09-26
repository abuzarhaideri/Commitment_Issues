# Sequelize compatibility repair task

Prepared September 27. This corrects regressions introduced by the earlier
harness patch, rather than injecting an upstream defect.

Run: make benchmark-free ARGS=--sequelize-compat.

Every attempt copies the preserved earlier repaired checkout, including local
dependencies and relative workspace links, into a fresh compatibility-runs
target. No writable production file is shared with the original. No developer
fix is supplied. The explicit issue lists the four trailing-decimal forms that
must again be rejected, while preserving the original exponent-only repair
and valid number forms.

Prepared baseline verified: original 158 utility tests and five original
regression checks pass; the separate 17-case compatibility corpus has 13 passes
and four failures. Final verification rebuilds TypeScript, runs the original
suite/regressions and all compatibility checks. Protected test/config hashes
are checked before verification. The original source and evidence are preserved.

Baseline-only: .venv/bin/python benchmarks/run_sequelize_compat.py --baseline-only.
Uses the already prepared Node/dependency environment; this is machine-specific
benchmark setup, not an official portable evaluator runtime.

Live correction remains pending hidden local key entry. Only a final verified
patch resolves the known compatibility gap. Generic test-path/shell protections
are not OS isolation; independently maintained checks are not claimed secure
against arbitrary host access.

First live correction produced a patch that passes all prepared checks, independently rerun, but the autonomous session exhausted budget at generated-diff review. See [result](sequelize-compatibility-result.md). The updated gate requires live closure validation; original run status is preserved.

Latest fresh attempt completed autonomously with all checks passing. See [successful run](sequelize-compatibility-success.md).
