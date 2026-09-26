# Reliability work completed — September 27

## Implemented and locally verified

- Invalid action responses receive a concrete strict-JSON example and escaping guidance; rejected actions are not executed.
- Test failures on unchanged source are identified as PRE_EDIT_TEST_FAILURE baseline evidence, rather than counted as recovery from an attempted patch. Timeouts and failures without recognizable test evidence remain regular failures.
- successful_recoveries now means a 0/1 task-level outcome: the task passed final independent verification after failure feedback. A successful unrelated read is not a recovery. This is not a per-error causal proof; recoveries still counts feedback events.
- record_findings stores at most four model notes, each with bounded hypothesis/evidence/next_action fields, anchored in subsequent requests. These are model-authored claims, not independently validated truth.
- make reliability runs three scripted scenarios three times each: baseline diagnosis, incorrect patch followed by correction, malformed action followed by correction. Nine controls passed with unchanged tests and independent verification. These predetermined actions test orchestration, not model intelligence.
- All four synthetic baselines reproduced their expected failures; no API request was made.
- 120 infrastructure tests pass.
- GitHub Actions workflow configured for Python 3.11–3.13 on Ubuntu/macOS, including setup, tests and recovery controls. Remote CI execution is pending.
- Allowlisted packaging and local clean-clone simulated-HTTP rehearsal refreshed. This does not validate DeepSeek/Qwen or the organiser runtime.

## Which repositories to test

Use both, with distinct roles:

| Stage | Repository type | Purpose |
| --- | --- | --- |
| Mechanics | Small synthetic fixtures | Isolate malformed JSON, wrong first patch, budgets, noisy logs, test tampering and cross-module behavior |
| Controlled model testing | Synthetic tasks with hidden acceptance cases | Measure actual model repair/recovery and efficiency across identical fresh runs |
| Realism | Pinned open-source checkout with a reproduced defect | Validate navigation, build/test discovery, dependencies and behavior preservation |
| Final rehearsal | Fresh clone under organiser settings | Validate actual model, protocol, startup and submission |

Next live run: make benchmark-free ARGS=--fiber-focused. Then complete synthetic checkout with make benchmark-free ARGS='--synthetic-issue checkout'. Keep Fiber discovery failures in the record. Avoid whole-repository claims or arbitrary bug hunts; use one reproducible issue and unchanged acceptance checks per run.

## Still pending

- Verified focused Fiber repair and a live failed-first-patch recovery. Synthetic checkout has since passed all 31 tests; see its report.
- Harness-generated correction of Sequelize's compatibility regressions.
- Repeated provider-token comparisons and stronger held-out behavior checks.
- Robust project-derived command discovery, execution isolation and validated resume.
- Exact DeepSeek/Qwen access, task/runtime protocol and official limits; final evaluator rehearsal.
- Final secret/history/license review, repository publication and demo materials.

No live provider credentials were available during this batch; no paid model calls or external publication occurred.
