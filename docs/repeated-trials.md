# Repeated live trials

Run three fresh checkout attempts:

```bash
make benchmark-free ARGS='--synthetic-issue checkout --repeat 3'
```

One Free Tier confirmation/hidden key prompt is used. Credentials remain only
in process memory/environment and are restored after execution; not saved.
Default repeat=1 preserves existing commands. Explicit repeat accepts 1–5.

Each attempt gets a fresh target and the same model/task settings. Comparison
summary JSON under artifacts/comparisons records every completed attempt,
including failures, requested/completed counts and pass count. Provider-only
token median excludes estimated-usage runs, with sample count visible. It
includes both successful and failed trials with fully reported usage.

Quota exhaustion, terminal service unavailability, interruption, fatal access
errors, setup failure or missing evidence stop remaining trials. Interrupted
between-trial input may leave only the last completed summary. No provider
fallback is added. Diagnostic and legacy non-fresh Sequelize repetitions are
rejected before key entry.

Three runs permit up to three per-run 60,000-token allowances; estimates are
not a strict total-provider ceiling. Repeat count is explicit; no scheduled or
background calls occur. Rate pacing applies throughout the process.
This consumes more free quota than a single attempt, so start with checkout.

The sample is small and stochastic. This measures same-task repeatability,
not a controlled old-versus-new comparison or general SDE success rate.
All per-run raw evidence remains in its benchmark folder. A result summary
does not replace independent source/behavior review.

Local tests cover failed-trial retention, exclusion of estimated totals from
provider medians, quota stop and validation before credentials. Live checkout series completed: 3/3 resolved, independently rerun with 31 passing checks each and unchanged test hashes. Provider-token median 12,344. See [candidate evidence](submission-candidate.md). No further repetition is planned for this fixture.
