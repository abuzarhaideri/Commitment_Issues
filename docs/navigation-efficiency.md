# Navigation and token efficiency — September 27

Implemented after the first Fiber attempt exhausted 60,000 tokens without an edit.

## Changes

- search_code defaults to scope=auto: search production/non-test files first, fall back to all files only when no source match exists. scope=all explicitly includes tests; scope=source excludes test files in directory searches. Literal matching and path guards remain intact.
- Empty searches explain shorter-symbol navigation and flag repeated queries.
- Context retains twelve bounded navigation records (search hits, visited/edited files, command outcomes). The last four observations stay detailed; older observations are compacted to 350 characters with an explicit reread instruction. Original history and raw event evidence remain unchanged. This is bounded tool-derived memory, not an inferred semantic diagnosis.
- Expected failed unittest output omits routine passing lines while preserving failure diagnostics, counts and raw evidence. Arbitrary command output is not treated as test output.
- Before each model call, the harness estimates input with a 25% margin plus 256 tokens. It requires room for at least 512 output tokens and reduces the configured generation cap to fit the remaining estimated allowance. It logs a request_budget_guard event if another call cannot fit. Caps are restored after success/error; failed-call accounting uses that request's cap.
- Full independent final verification and test protection are unchanged.

## Local evidence

107 infrastructure tests pass, including test-heavy search navigation using rg and its Python fallback, explicit all-file search, compaction/evidence preservation, failure diagnostics, no-call budget exhaustion and generation-limit restoration.

A read-only search of the untouched Fiber source for ' Range(' returns req.go:1550 (the implementation), alongside documentation signatures, without test-output noise. No Fiber production source was changed.

A controlled ten-observation context check used 6,504 estimated tokens versus 13,662 with full history: 52.4% reduction. This is an offline constructed workload using the character-based estimator, not provider token usage or measured Fiber repair savings.

## Remaining validation and limits

Run make benchmark-free ARGS=--fiber with the hidden local key prompt. Each invocation gets a fresh target; compare repair correctness, calls, tokens, search progression and independent verification against the failed first attempt. No live model run was made for these changes.

Provider tokenization, hidden protocol overhead and retries can differ from estimates, so the guard is not a strict provider/billing ceiling. It avoids requests predicted not to fit; it does not guarantee a repair can finish within budget. Model quality and held-out compatibility still need testing.

Search ranking is source-first, not a complete language symbol index. Memory is bounded, older source may need rereading, and full diagnosis/plan still belongs to the model. DeepSeek/Qwen endpoint compatibility remains pending organiser details.

## Follow-up after second Fiber attempt

Guidance alone did not prevent guessed signatures and reading unrelated chunks. Search now performs a clearly labelled method-symbol fallback for unsuccessful automatic signature searches. Default large-file reads expose definition locations; explicit ranges remain exact. Context packing tightens with remaining token allowance. 109 tests pass, including the exact receiver-mismatch scenario and large-file location discovery. See the [second attempt](fiber-second-run-report.md); no live third attempt has been run.
