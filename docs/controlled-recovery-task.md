# Controlled live edit-conflict recovery

Run: make benchmark-free ARGS=--synthetic-recovery.

This uses a fresh checkout synthetic fixture with its full 31-test suite and
five expected baseline failures. The first otherwise-valid production text
replacement is rejected before writing. The model is told the fault is
injected, receives explicit conflict feedback, and must recover and complete
the repair through independent final verification.

No source corruption or test weakening is injected. Invalid/protected/no-op
edits do not consume the fault. Subsequent eligible edits behave normally.
The runner records task mode/fault in the manifest and fault-result.json.
If the fault is never exercised, the benchmark is labelled invalid even if
some other path completes a repair.

This tests recovery from a controlled tool conflict. It must never be reported
as proof the model recovered from a naturally incorrect first patch. That
separate evidence remains pending. Native model/60,000-token/time/verification
settings match free-development tasks.

Local tests validate rejection without mutation, retry behavior and protected
paths. Baseline preparation passes without API calls. First live controlled recovery passed; see [result](controlled-recovery-result.md).
