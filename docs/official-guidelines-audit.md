# Submission guidelines audit

Reviewed September 26, 2026 against **AI Harness Submission (1).pdf**, all 10 pages, including repeated sections on pages 4–7. This establishes the submission/startup contract. It does not specify a model, runtime, issue transport, scoring weights, numeric token/time/cost ceilings, cache requirement or memory architecture. PRD efficiency goals are team targets unless another official document establishes them.

## Verdict

The repair engine is functional, but **the submission is not ready: plain `make run` fails with only AI_API_KEY**, contrary to the prescribed launch sequence. The PDF expressly says evaluators will not repair the implementation or manually configure it. No percentage score can be derived from these guidelines.

## Requirement comparison

| PDF section | Evidence | Assessment |
| --- | --- | --- |
| 1. Root Makefile | setup/run/test/clean targets present | Interface present; mandatory successful run missing |
| 2. API key | Normal evaluator path reads AI_API_KEY without source edits | Aligned; free-development profile intentionally uses GEMINI_API_KEY and must stay separate |
| 3. Text-only model | Text issue, observations and requests; no image/audio/video dependency | Aligned |
| 4. Model configuration | Explicit model/provider/endpoint, organiser overrides, no automatic fallback | Architecture aligned; prescribed model unknown and live compatibility unverified |
| 5. Evaluation procedure | Setup/test work; terminal prompts accept local repo and issue | Launch blocked by missing default configuration; official issue delivery unspecified |
| 6. TUI | CLI entry point exists; no separate TUI | TUI is conditional, not mandatory; no extension/GUI requirement. Launch must work |
| 7. Standard environment | Standard-library harness; Python 3.11+ documented | Confirm organiser runtime/test infrastructure; Sequelize benchmark has local Node/dependency and machine-specific manifest requirements |
| 8. Credential security | Environment credentials, empty .env.example, .env/artifact ignores, sanitized transport errors | Good implementation; final tracked-file/history/artifact review pending; repo/log secret exposure remains possible |
| 9. Environment independence | Setup creates venv and imports harness without third-party Python dependencies | Partial: needs provided Python/venv/make and currently extra startup config; prescribed-runtime rehearsal pending |
| 10. Reproducibility | Explicit model/budgets, isolated synthetic targets, saved traces | Partial: sampling defaults not explicitly controlled/documented; repeated same-task trials pending |
| 11. Evaluation independence | Audit required no source changes by evaluator | Launch blocker must be fixed before submission |
| 12. Evaluator workflow | Fresh copy/setup/test demonstrated | Clone/key/setup/run sequence incomplete; final submitted repository/commit unverified |
| 13. Final checklist | Makefile, README, source/config/tests exist | Fresh local copy tested, not clean clone on prescribed OS/runtime; run failed |
| 14. Final requirement | Setup succeeds | Mandatory plain run remains blocked |

`make clean` appears with “where applicable” in the command table, but is not one of the three expressly mandatory targets or two minimum-success commands. Our clean currently removes Python caches only; document scope rather than deleting benchmark evidence automatically.

## Audit checks

Fresh temporary copy of Makefile, harness, tests, benchmarks, configuration and entry documents, excluding existing venv and artifacts. Removed inherited HARNESS_*, AI_*, GEMINI_* and OPENAI_* settings. Used a fake AI_API_KEY placeholder; **no live API request**.

- `make setup`: exit 0; new venv and successful harness import.
- `make test`: exit 0; **80 tests passed**.
- `make run`: exit 2; `Set provider, model, and base URL using CLI, HARNESS_* environment variables, or --config. No model is guessed.`
- Limited Google/OpenAI/GitHub key-format scan of 70 source/test/config/document files: no flagged files. This does not replace a full secret/history review.
- Root `.git` directory absent; actual submission repository and clean-clone reproducibility not verified.

This ran on the current Mac with installed Python/make, not a clean organiser machine. It stopped before authentication, so does not prove live model/key compatibility.

## Work already completed beyond startup

Five completed live repairs have saved logs, usage/runtime measurements and diffs: original label and checkout fixtures, Sequelize utility, synthetic label-order and boolean-config. All passed supplied checks. Sequelize has a separate review-discovered trailing-decimal compatibility concern; selected-check PASS is not blanket correctness. Synthetic pagination and checkout live runs remain pending. Eighty infrastructure tests are not eighty live repair tasks; five selected tasks do not establish a general success rate.

Search, bounded reads/context, caching, failure feedback, budgets and independent final test runs exist. They are useful engineering features, not proof of unnamed official efficiency scoring. Input repetition and durable memory remain improvement targets; see [efficiency review](efficiency-review.md).

## Priorities

1. Automatically load a committed evaluation profile through plain `make run`, using AI_API_KEY for credentials and the prescribed model when supplied. Do not silently substitute the Gemini development selection; keep Free Tier development separate.
2. Have the launched harness accept the organiser's repo/issue through the agreed text protocol. Existing terminal local-path/issue prompts may suffice for interactive evaluation; URL acquisition/noninteractive delivery depends on their contract.
3. Confirm runtime, endpoint/authentication, prescribed model and issue/test delivery. This PDF settles startup, not these details.
4. Prepare the actual submission repository, exclude local artifacts/secrets and rehearse clone → AI_API_KEY → setup → run → issue → verified result on the prescribed runtime without configuration edits.
5. Document/control supported generation settings and repeat identical fresh-task trials; optimize logs/context while preserving correctness and full final verification.

This audit changes documentation only; runtime fixes and paid API calls were not performed.
