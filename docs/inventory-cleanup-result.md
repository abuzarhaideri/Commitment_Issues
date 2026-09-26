# Inventory helper/cleanup — verified live result

Run: artifacts/inventory-cleanup/20260926-211212-0423f1a0; evidence: evidence/20260927-024212-0122afbc.

**RESOLVED / PASS:** eight order tests, eleven independent order scenarios,
seven helper cases and cleanup checks all passed in actual final verification.
Protected test hashes are unchanged. The phrase 'verification scripts are
expected to succeed' in the model's reason is weaker than the recorded evidence;
the gates actually ran and passed.

The helper now accepts exact capacity using >=. orders.py uses the corrected
helper before deductions. Trailing whitespace was removed; the reproduction
script now runs only under its main guard and omits its obsolete comment.
quantities.py lost its final newline: valid Python and outside the declared
cleanup acceptance, but this exposed a malformed multi-file diff boundary.

Eight model calls / 23 counted tool calls; 28,559 input + 5,171 output = 33,730
provider-reported tokens; runtime 88.776 seconds; context reduction 9.80%.
Five recovery-feedback events, one task-level verified recovery. The trace
contains malformed response, unmatched edit, rejected no-op, denied command
and a failing cleanup check after edits. The model subsequently corrected the
remaining work and passed. No controlled fault was injected in this task.
This demonstrates real protocol/edit/partial-cleanup recovery, not a naturally
wrong algorithmic first patch or five separately proven recoveries.

Diff reporting now marks lines without terminal newline and separates the next
file header correctly. Original evidence and model source are preserved.
Latest suite: 143 infrastructure tests.

Next: repeated same-task fresh trials, including failures and provider/estimated
usage distinctions. Broader SDE reliability and DeepSeek/Qwen validation remain
pending.
