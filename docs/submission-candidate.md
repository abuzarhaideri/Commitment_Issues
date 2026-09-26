# Local submission candidate and testing stop criteria

September 27, 2026. The current milestone is a reviewable local candidate. Final DeepSeek/Qwen evaluation is not validated and the Gemini profile remains explicitly provisional.

## Evidence now sufficient for the current fixture set

Three fresh checkout trials independently passed all 31 tests, with protected test hashes unchanged. Source review confirmed quantity multiplication, shipping threshold after discount, zero-subtotal shipping exemption and preserved inputs. Only checkout.py and pricing.py changed.

| Trial | Provider tokens | Model calls | Seconds | Result |
| --- | ---: | ---: | ---: | --- |
| 1 | 10,713 | 4 | 40.041 | RESOLVED / PASS |
| 2 | 12,344 | 4 | 38.787 | RESOLVED / PASS |
| 3 | 26,214 | 7 | 74.907 | RESOLVED / PASS |

Median tokens: 12,344. The third run used about 2.45 times the first run's tokens for equivalent behavior. This is stochastic variability, not a controlled efficiency comparison. Three successes on one fixture cannot establish general reliability.

Source evidence: artifacts/comparisons/20260926-212302-66c42724/summary.json, with all three linked per-run folders. Saved statuses remain unchanged.

Other substantive evidence: inventory multi-module repair and helper cleanup; Sequelize original/regression/compatibility closure; controlled tool conflict and real protocol/edit/cleanup recovery. Fiber remains unresolved after four attempts. Present both successes and failures.

## Demo walkthrough (no new live calls required)

1. Explain the loop: issue → source navigation → exact edit → checks → diff review → independent final verification → evidence/report.
2. Show docs/sequelize-compatibility-success.md and its saved final.diff: a real utility repair that preserves the original checks and closes four independently discovered regressions. Clarify that this is prepared issue repair, not whole-repository bug discovery.
3. Show docs/inventory-cleanup-result.md for multi-module behavior and recovery. Explain protected tests and independent scenarios.
4. Show the table above for cost/repeatability, then docs/fiber-focused-first-run-report.md for an honest bounded failure.
5. If an executable demonstration is needed, run `make demo`. It uses predetermined offline actions on a small fixture; it demonstrates infrastructure only, not live model intelligence. `make rehearse` additionally exercises HTTP and clean-clone startup through a simulated server.
6. End with current evaluator gates in docs/hackathon-checklist.md, without claiming final model compatibility.

## Proportionate testing policy

The current benchmark set is frozen. No additional live checkout/inventory/Fiber repetition is needed for this candidate.

For a code change, run a targeted regression that tests the failure, then the infrastructure suite once. Run a clean-clone rehearsal after candidate source/config/packaging changes. Stop when these pass unless new failures or evidence justify another check.

Do not spend quota on unchanged Fiber retries. A further Fiber run needs a specific improvement hypothesis and acceptance condition. New live model calls require the locally entered key; credentials are not saved or available to this agent.

Final model validation is a separate gate: after organisers supply details, configure the exact transports/models, test connectivity/action parsing and one representative repair per family, then rehearse prescribed startup. Do not guess undocumented organiser requirements or silently switch to paid providers.

## Release boundary

The repository's `main` branch is published at https://github.com/abuzarhaideri/Commitment_Issues. Remote CI passed on all six Ubuntu/macOS × Python 3.11–3.13 combinations at https://github.com/abuzarhaideri/Commitment_Issues/actions/runs/36280421015. The allowlisted ZIP remains a local artifact; no formal tagged release was requested or created. An MIT license and attribution notes are present. A high-confidence credential-pattern review found no matches across the local Git object database (including unreachable objects) or allowlisted files. This does not guarantee absence of every secret. Target commands execute on the host with basic guards, not OS isolation. Token budgets are estimates, not strict billing ceilings. See the checklist for additional unproven capabilities.

## Candidate verification

145 infrastructure tests passed once after the response-validation fix; git diff --check passed. Clean-clone setup/test/default launch and simulated HTTP repair passed: artifacts/submission/rehearsals/20260926-213259-c52fed09/rehearsal.json. The local package contains 126 allowlisted files. Rehearsal uses a simulator, not DeepSeek/Qwen. Subsequent edits only record this result in documentation.

A high-confidence scan covered all 277 local Git blobs and the 133 current allowlisted package files with no matches. Package generation succeeded, and a clean-clone simulated HTTP rehearsal passed after allowing its loopback-only test server. These checks do not guarantee the absence of every secret or substitute for GitHub push protection and remote CI.
