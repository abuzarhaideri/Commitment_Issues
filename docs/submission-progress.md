# Progress on the four priorities

Updated September 26, 2026. The original [audit](official-guidelines-audit.md) records the earlier launch failure; this report records the subsequent changes.

> Historical checkpoints below; current completed work and final gates are consolidated in the [checklist](hackathon-checklist.md) and [candidate report](submission-candidate.md).

## 1. Evaluation entry point

- [x] Plain make run automatically loads config/evaluation.json.
- [x] AI_API_KEY-only evaluation credential path, no FREE prompt or development key reuse.
- [x] Terminal/JSON task intake and multiline issue-file support.
- [x] Provisional-profile banner and no-API launch check.
- [x] Missing key, invalid input, organiser override and profile-separation tests.
- [ ] Replace provisional settings with prescribed organiser configuration and validate live.
- [ ] Confirm the input protocol with organisers.

Missing default-configuration startup is fixed; official model/input compliance is not assumed.

## 2. Organiser details

- [x] [Six focused questions](organiser-questions.md) drafted; provisional choices documented.
- [ ] Obtain answers. No external message has been sent.

## 3. Packaging and rehearsal

- [x] Local Git initialized; credentials, venv, artifacts and temporary files ignored.
- [x] Allowlisted candidate ZIP, file hashes and limited credential-format check.
- [x] Actual temporary local Git clone: setup, **93 tests**, startup and plain make run simulated HTTP repair.
- [x] Three fixture tests passed, hashes unchanged; four simulated HTTP model requests.
- [x] Raw rehearsal report/diff/performance retained.
- [x] Reviewed package allowlist/ignored paths and whitespace; local source-control candidate checkpoint prepared using the existing configured Git identity.
- [ ] Final security/attribution review, official settings/release commit and remote location.
- [ ] Prescribed-runtime/model clean-clone live rehearsal.

No repository published and no paid model called. The local candidate checkpoint is separate from the final official-settings release. The local simulation is not official evaluation validation.

## 4. Compatibility and efficiency

- [x] Recognized passing tests summarized, warnings/status/counts retained; arbitrary command data preserved.
- [x] Interior failure extraction fixed before JSON encoding; raw event output retained.
- [x] Five observation tests and eight evaluation tests added: 80 → **93**, all pass.
- [x] Last passing observation from five saved runs replayed: **61.48–90.55% observation-text reduction**. Not whole-run API token savings.
- [x] Read-only Sequelize compatibility corpus: **17 checks, 13 pass / 4 fail**. Trailing-decimal compatibility remains open; original artifacts/checkout untouched.
- [ ] Harness-generated narrower Sequelize repair and fresh full/held-out verification.
- [ ] Live synthetic pagination and checkout.
- [ ] Repeated paired live token/runtime trials, compact durable memory and baseline-aware failure classification.

Component evidence: artifacts/submission/observation-comparison.json and number-compatibility.log. Checker: benchmarks/check_number_compatibility.cjs. Rehearsal records: artifacts/submission/rehearsals.

## Next priority

Finalize organiser model/runtime/input details, then rehearse that exact configuration from a clean clone. Meanwhile fix the known Sequelize compatibility gap through the harness and complete pagination/checkout before claiming broader SDE capability. Continue using the confirmed Free Tier project.

September 27 follow-up: latest-source packaging/clean-clone rehearsal refreshed; current suite 120 tests and nine offline recovery controls. DeepSeek/Qwen families are known, exact access/runtime/input remain pending. See [reliability progress](reliability-progress.md) for current status; prior counts above are historical.
