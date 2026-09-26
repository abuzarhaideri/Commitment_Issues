# Commitment Issues

This project is released under the [MIT License](LICENSE). See
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for benchmark-source and CI
action attribution notes.

Commitment Issues is a Python 3.11+ command-line harness that gives a configured text model bounded tools to inspect a software repository, edit code, run checks, and produce a reviewable result.

## Submission status

The root `Makefile`, CLI, package layout, and local clean-clone flow are in place. The evaluation profile remains provisional Gemini because the organisers have named DeepSeek and Qwen but have not supplied exact model IDs, endpoints, authentication details, runtime, or task protocol. **Do not treat the current profile as final evaluator configuration.** The supplied judging PDF does not publish numeric scoring weights or token ceilings.

The latest integrated infrastructure run passed 172 tests. The clean-clone rehearsal passed setup, tests, launch, and a fixture repair using a simulated local HTTP model. This does not validate live DeepSeek/Qwen access or repair quality. See the [current checklist](docs/hackathon-checklist.md), [requirements mapping](docs/judging-action-matrix.md), and [remaining reserve/adapter work](docs/reserve-adapter-progress.md).

## Quick start

```bash
make setup
make test
export AI_API_KEY="<PROVIDED_API_KEY>"
make run
```

`make run` reads `config/evaluation.json`, then prompts for the repository path and issue in an interactive terminal. For automated input, it accepts one JSON line:

```json
{"repo":"/path/to/checkout","issue":"Describe the defect","test_commands":["python -m unittest discover -s tests -v"]}
```

The issue may also be supplied from a text file:

```bash
make run ARGS='--repo /path/to/checkout --issue-file /path/to/issue.txt'
```

`AI_API_KEY` is the evaluator credential. The harness does not save it. It does not automatically change providers or models. The current committed profile is marked provisional; configure the organisers' prescribed model before final submission. `make run ARGS=--launch-check` checks local configuration without calling a model; “HARNESS READY” does not confirm credentials, quota, or live endpoint access.

## What the harness does

1. Profiles the repository and selects relevant navigation context.
2. Sends the issue and available tool descriptions to one configured text model.
3. Validates model actions and applies exact, unique edits through repository tools.
4. Runs requested or discovered checks, reviews the diff, and independently verifies completion.
5. Writes a status report, structured state, performance metrics, event log, and final diff under `artifacts/`.

The harness bounds requests, tool output, wall time, context and a total token allowance. An adaptive reserve keeps part of that allowance available for correction and review. Usage estimates are not a strict provider-side token or billing ceiling. Shell commands run on the host with basic guards; they are not isolated in an OS or container sandbox.

## Models and development

Provider adapters support compatible Chat Completions, a Responses route, and Gemini native or compatibility routes. Native Gemini requests use a tool-specific JSON response schema. Compatible routes have bounded transient-error retries and task deadlines. Incomplete or malformed actions are rejected before execution; exhausted transport retries do not trigger provider switching.

For no-cost development, use a Gemini AI Studio project that shows Free Tier, keep billing disabled, and run:

```bash
make benchmark-free
```

The development runner asks for Free Tier confirmation and accepts the key through a hidden prompt. It does not save the key or fall back to a paid provider. Free-tier quota and model availability can vary. Use `make benchmark-free ARGS=--probe` for a small connectivity probe; it makes a live API request.

## Evidence and limits

Recorded successes include the starter synthetic issues, inventory workflows, Sequelize compatibility repair, and three fresh checkout trials. All three checkout attempts passed the same 31 checks with unchanged tests. The [trial report](docs/submission-candidate.md) shows token and runtime variation.

On the final prepared Fiber Range task, the harness reached the relevant code and recorded the right diagnosis, but exhausted its token allowance without producing a patch. An isolated Sol/low attempt repaired the issue and passed the prepared regressions, full suite/vet, and range race checks. This was a comparison between different models and tools, not evidence that the harness is better than Sol. The [comparison report](docs/final-comparison-result.md) records both outcomes. These selected tasks do not establish dependable repair across arbitrary repositories.

The README does not count offline infrastructure tests as live model repair successes. Full organiser-model compatibility, broad unfamiliar-repository reliability, OS isolation, and remote CI remain open; see the [checklist](docs/hackathon-checklist.md). A high-confidence credential scan found no matches across all local Git objects and the allowlisted release files; this reduces exposure risk but does not prove that no secret exists.

## Repository layout

```text
.
├── Makefile                 # setup, run, test, clean, package, rehearsal
├── harness/                 # CLI, adapters, context, tools, orchestration, state
├── config/                  # provisional evaluator and development profiles
├── tests/                   # offline unit and harness-infrastructure checks
├── benchmarks/              # isolated fixtures, prepared external-repo runners
├── docs/                    # current plan, criteria mapping, reports and limitations
├── tools/                   # packaging and local rehearsal utilities
└── .github/workflows/       # Ubuntu/macOS Python CI definition
```

Local `.venv/`, `artifacts/`, and `tmp/` are ignored and excluded from the submission ZIP. The checked-in source layout does not depend on those local results.

## Package and rehearsal

```bash
make package
make rehearse
```

`make package` creates an allowlisted ZIP and SHA-256 manifest under `artifacts/submission/`. It performs a limited scan for common credential formats; it is not a complete secret or Git-history audit. `make rehearse` extracts the package into a temporary repository, clones it, runs setup/tests/launch, and repairs a small fixture using a local simulated model. It makes no live or paid API calls and does not replace the prescribed-model rehearsal.

`make clean` removes Python cache directories and preserves benchmark evidence. Remote publication and pushing a repository are separate release steps; neither is performed by these commands.

## Current references

- [Evaluator quickstart](docs/submission-quickstart.md)
- [Current checklist](docs/hackathon-checklist.md)
- [Official guidelines audit](docs/official-guidelines-audit.md)
- [Criteria-to-action matrix](docs/judging-action-matrix.md)
- [Final Fiber comparison](docs/final-comparison-result.md)
- [Reserve and adapter report](docs/reserve-adapter-progress.md)
- [Synthetic and external benchmark reports](benchmarks/README.md)
