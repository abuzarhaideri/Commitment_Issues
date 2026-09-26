# Controlled edit-conflict recovery — live result

Run: artifacts/recovery/20260927-023439-checkout-2b5d60fe; evidence: evidence/20260927-023439-f2694ba4.

**RESOLVED / PASS.** fault-result.json confirms fault_injected=true and harness_exit=0. All 31 final tests pass, test hashes unchanged. Only checkout.py and pricing.py changed (+8/-2); no scratch file added.

The model recovered from the deliberately rejected valid edit and completed quantity pricing/post-discount shipping. Two failure-feedback events were recorded; successful_recoveries=1 denotes the final task-level verified recovery, not two independently proven recoveries. This is controlled tool-conflict evidence, not a naturally wrong first-patch benchmark.

Six model calls / twelve tool calls; 17,219 input + 4,754 output = 21,973 provider-reported tokens; 131.979 seconds. Context-reduction metric 11.60%. Two HTTP 503 retries consumed 36 seconds of service backoff; the same provider/model was retained and execution resumed.

Source review finds the patch consistent with the stated checkout contract. list(items) supports the one-pass input but is unnecessary for the single summation pass and adds memory use; this is an efficiency caveat, not an acceptance failure.

Next task is the separately labelled inventory helper/cleanup follow-up. Broader natural failed-patch recovery, repeated trials and final DeepSeek/Qwen validation remain pending.
