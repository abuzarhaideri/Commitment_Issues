# Efficiency review and PRD checkpoint comparison

Reviewed September 26, 2026, using saved performance JSON and execution traces for five completed live runs. The subsequently supplied official submission PDF confirms the Makefile/key/text-only startup contract but specifies no evaluation model, numeric ceilings or efficiency scoring weights. See the [official guidelines audit](official-guidelines-audit.md). The PRD adds team design targets; this review does not claim numerical judging compliance or a competition score.

## What tokens mean

Follow-up: passing-test observation summaries and raw-line failure extraction are now implemented. Offline replay of five saved last-passing observations reduced their text by 61.48–90.55%; no paired live whole-run token saving has been measured. See [submission progress](submission-progress.md). The original run measurements below are unchanged.

Input tokens cover every model call's instructions, tool contracts, issue, repository information, and retained observations. Repeated material counts again when sent in another request. Output usage includes response/actions and Gemini thinking tokens as normalized by the adapter. A run's totals are cumulative across calls, not its single-call context size and not a count of users.

The current Free Tier launcher uses a **60,000 aggregate input/output token budget** and **8,000 estimated context-token budget**. These are our configurable development limits, not organiser limits. Accounting is checked between calls, so a call can exceed the aggregate ceiling before usage is returned. Context packing estimates are not exact wire-payload counts. Staying below 60,000 proves compliance with this internal check, not efficiency relative to another harness.

## Completed live runs

All five used Gemini 3.1 Flash-Lite native JSON actions with low reasoning and 12-second request-start spacing. Task/suite/context sizes differ, and each has only one live attempt.

| Task | Input | Output | Total | Model calls | Counted tools | Wall s | Pacing s | Context reduction |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Standalone label fixture | 4,448 | 999 | 5,447 | 3 | 6 | 29.647 | 17.940 | 0% |
| Standalone checkout fixture | 9,522 | 1,807 | 11,329 | 4 | 10 | 39.192 | 27.714 | 0% |
| Sequelize utility | 44,286 | 5,313 | 49,599 | 8 | 13 | 95.230 | 51.828 | 0% |
| Synthetic lab: label order | 6,681 | 1,151 | 7,832 | 4 | 7 | 41.174 | 24.465 | 0% |
| Synthetic lab: boolean config | 19,820 | 2,194 | 22,014 | 6 | 9 | 65.435 | 34.442 | 0% |

These five generation runs total **96,221 reported tokens**: 84,757 input and 11,464 output (about 88% input), over 25 model calls. This excludes probes, failed API runs, offline tests, and any unrecorded requests; it is not a complete account/quota usage total. No quota/service retries occurred in these five runs.

All passed their supplied final checks. Sequelize additionally has a review-discovered compatibility concern (new trailing-decimal acceptance), so visible PASS is not blanket correctness. A general success rate cannot be inferred from these hand-selected tasks.

## PRD/official-contract checkpoints

| Checkpoint | Evidence today | Remaining limitation |
| --- | --- | --- |
| Root setup/run/test and clean evaluator startup | Auto-loaded provisional profile; local clean-clone setup/test/simulated repair works | Prescribed model/input/runtime still requires live validation |
| External AI_API_KEY and text-only model | Evaluation credential path and text-only adapters implemented | Free development is a separate Gemini-key workflow; official adapter needs live validation |
| Configured one-model task | Same configured model per run; no paid fallback | Other adapters/native modes mainly mocked, not broadly proven live |
| Correctness before savings | Fresh final tests, integrity checks, complete diff review | Hidden cases/compatibility coverage incomplete; same-model semantic review is fallible |
| Selective repository retrieval | Search and bounded reads used live; no full-repo context dump | Search traversal/read metrics are conflated; query results can include generated files |
| Avoid resending known information | Recent history retained and capped | Relevant history and successful logs repeatedly resent; no durable summary memory |
| Filter observations | Bounded output and truncation implemented | Failure extraction occurs after JSON encoding; successful logs are not compact structured summaries |
| Cache reuse | Hits measured in all runs | Disk/search reuse is not provider-token saving; cached observations can still be resent |
| Context-budget packing/compaction | Configurable bounded packing with labeled estimates | Every completed run had 0% reduction by this metric; omission is not semantic compaction, latest oversized observation can stop the run |
| Three-tier memory | Issue/plan/recent failure anchors and persisted inspection state | Durable decisions/hypotheses and compact older history missing; no validated resume |
| Recovery | Failure feedback and clean limits; two recovery records | Sequelize record was build re-review; boolean record was expected baseline failure. Genuine failed-fix recovery still unproven |
| Token/call/wall limits | Configured checks and reported usage | Limits are internal, not confirmed official ceilings; waits/snapshot overhead and in-flight token overshoot need accurate reporting |
| Performance evidence | Console/JSON/log/diff output for all runs | Mocha/TAP counts require log review; no paired baseline/optimized benchmark yet |

The PRD gives correctness priority over efficiency. Neither it nor the supplied submission PDF establishes official numeric token, call, cost, wall-time ceilings or scoring weights. Retrieval, memory and optimization rows above assess team design goals rather than requirements stated in that PDF.

## What the data supports

1. Correct targeted repairs work on these tasks; broad compatibility remains a separate acceptance question.
2. Input is most of the recorded token usage. Repeated context/logs are credible optimization targets, but essential instructions/code are also input; not all input is waste.
3. Pacing is a large part of wall time. It is deliberate Free Tier quota protection, not solely model reasoning or tool latency. Do not reduce it blindly or confuse it with service-retry time.
4. Complete diff review adds model turns. Sequelize generated output and source-map copies increased review work. Keep integrity guarantees while reducing duplicated content.
5. Cache and bounded retrieval exist, but no measured token-saving benefit against an unoptimized alternative has been established. The 0% metric is relative to accumulated retained history, not a full-repository baseline.

## Prioritized improvements

1. **Structured observation summaries:** extract raw failure blocks before JSON encoding; summarize passing suites as command/status/count/duration. Retain complete raw evidence separately. Measure sent characters/tokens before and after.
2. **Baseline-aware failure handling:** expose the launcher's reproduction summary; classify expected baseline failures separately from failed fixes. Use focused reproduction where sufficient and retain full independent final tests.
3. **Compact durable memory:** retain current hypotheses, important file/range references, decisions, failed approaches, and latest verification; summarize or retrieve older observations rather than repeatedly sending full logs.
4. **Source/build-aware diff review:** retain hashes/integrity for regenerated files but avoid sending duplicated source-map content repeatedly. Never omit source changes or bypass final review.
5. **More accurate payload accounting:** count actual serialized system/tool/context content, avoid duplicate tool contracts, preserve exact usage on malformed responses, and separate reasoning output where the provider supplies it.
6. **Interpretably split runtime:** model latency, tool execution, pacing, service/quota backoff, snapshot/profile overhead; separate successful/failed model and tool operations.
7. **Fair optimization trials:** after finishing basic tasks, rerun fresh identical baselines with the same model/settings/test coverage, comparing current versus one optimization at a time. Record all attempts, median/range over repeats as quota permits, and reject any saving that reduces correctness or recovery ability.

Do not claim a specific percentage saving in advance. Do not remove regression verification or shorten output enough to hide failures. Quota availability varies; developer token budgeting is not a billing-tier guarantee. Continue using the user-confirmed Free Tier project with billing disabled.
