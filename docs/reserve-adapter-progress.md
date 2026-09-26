# Budget reserve and evaluator adapter progress

September 27, 2026. Two Sol/low agents implemented bounded resource allocation and compatible transport robustness, with integrated review. No live API calls or Fiber retries were made.

## Budget reserve

The default reserve is min(12,000, floor(15% of the total allowance)): 9,000 inside a 60,000-token budget. Normal calls hold it back; corrective/protocol phases retain half for later review. A meaningful production edit makes the next request eligible for verification/review, releasing the remainder. A no-op edit does not unlock funds. Finish/diff/test verification can access review allowance. Explicit excessive reserves fail clearly instead of silently increasing the limit.

CLI `--token-reserve N`, environment HARNESS_TOKEN_RESERVE or config token_reserve controls the amount. Zero disables reservation; omitted selects the adaptive default. The total budget is unchanged. Event token_reserve_decision records phase, held allowance, remaining budget, request estimate and output-cap enforcement. performance.json includes token_reserve. Unknown adapters without output caps are marked unenforced; estimates and provider accounting can still overshoot. This is allocation discipline, not a strict provider token ceiling or guaranteed repair.

Offline tests exercise ordinary reservation, protocol/correction access, low-funds post-edit finish with independent PASS, no-op non-release, unaffordable requests and output-limit restoration.

## Evaluator adapter robustness

Configured compatible Chat Completions and Responses use bounded transport retries (default two; max 0–5). Existing --max-rate-retries / HARNESS_MAX_RATE_RETRIES / config max_rate_retries also configure those routes. Retry payload, model, endpoint and authentication stay identical. Fatal 400/401/403/404 are not retried. Transient 408/500/502/503/504 and hinted 429 observe bounded backoff/Retry-After within request and task deadlines. Bare 429 is stopped without asserting it is a daily quota error. Exhausted transport attempts stop as SERVICE_UNAVAILABLE instead of spending coding-recovery turns.

http_requests, transport_retries and transport_retry events expose attempts. Request estimates include serialized instructions/tools and wire overhead, including non-ASCII escaping. Responses requests canonical single actions; legacy responses still decode. Reasoning content is not executable content, incomplete messages and partially malformed tool batches yield no actions, and valid usage is preserved. Error text omits raw response bodies and credentials.

Representative offline Chat/Responses fixtures establish wire-contract handling, not exact deployed DeepSeek/Qwen compatibility. These transports assume an organiser-selected compatible protocol; no model IDs or hosting URLs were guessed. Authentication, actual reasoning/tool support, runtime and task protocol still require organiser details. The provisional Gemini evaluation profile was not replaced.

## Evidence and score boundary

172 infrastructure tests passed in the integrated suite. Targeted provider contracts also passed after correcting Unicode serialization estimates. Clean-clone startup/test/simulated HTTP repair passed: artifacts/submission/rehearsals/20260926-221233-23e3bc51/rehearsal.json. The refreshed local package contains 131 allowlisted files. Subsequent documentation records this result only.

This advances PRD correctness/recovery/efficiency targets and PDF prescribed-model/reproducibility requirements as mapped in judging-action-matrix.md. It does not establish an official or validated 7+/10 score. The five failed Fiber harness attempts remain failures, and exact evaluator-model repair performance is still unproven. A score increase requires new representative acceptance evidence, not counting unit tests as repaired issues.
