# Evaluator quickstart

Prerequisites: Python 3.11+ with venv, make, and git for cloning. No third-party Python runtime dependencies. Target repository test dependencies must be supplied/installed for that task.

```bash
git clone <TEAM_REPOSITORY>
cd <TEAM_REPOSITORY>
export AI_API_KEY="<PROVIDED_API_KEY>"
make setup
make run
```

make run automatically loads config/evaluation.json. Its Gemini 3.1 Flash-Lite native JSON profile is **provisional, not organiser-approved**. Before submission the team must commit prescribed provider/model/endpoint settings; evaluators should not edit configuration. This entry point reads only AI_API_KEY, does not reuse development keys and does not ask for FREE confirmation.

On a terminal it prompts for a local repository path and issue. Automated input is one JSON line:

```json
{"repo":"/path/to/checkout","issue":"Description with escaped\nnewlines","test_commands":["python -m unittest discover -s tests -v"]}
```

This protocol requires organiser confirmation. Local checkout paths are supported; automatic GitHub cloning or issue-URL fetching is not implemented. Multiline text files are supported:

```bash
make run ARGS='--repo /path/to/checkout --issue-file /path/to/issue.txt'
make test
make run ARGS=--launch-check
```

The launch check constructs the configured adapter without an API call/task/repair. HARNESS READY means ready for task input, not proof of authentication/quota/model access. Normal task execution makes live calls. Keep billing disabled for free development, using the separate make benchmark-free workflow.

Repeat --test-command for explicit tests, or use task test_commands; otherwise repository discovery is attempted. Missing runnable verification produces UNVERIFIED. Organiser overrides are HARNESS_OFFICIAL_PROVIDER, HARNESS_OFFICIAL_MODEL and HARNESS_OFFICIAL_BASE_URL; final settings should already be in the profile so extra variables are unnecessary.

Exit 0: RESOLVED/PASS. Unsuccessful repair: 1. Invalid setup/task: 2. Evidence under artifacts includes state/performance JSON, event logs and final.diff. Interrupted task execution preserves code. Reasoning/output/pacing/budgets are configured; sampling uses provider defaults and outputs are not guaranteed deterministic.

## Package and local rehearsal

```bash
make package
make rehearse
```

Packaging creates an allowlisted ZIP/hash manifest under artifacts/submission, excluding venv, local artifacts, temporary files and external checkouts. Its limited key-format scan does not replace a full secret/history audit. It does not publish anything.

Rehearsal creates a temporary Git repository and actual local clone, runs setup/test/launch, then completes a fixture repair through a localhost simulated HTTP model. Reports/evidence are retained per run under artifacts/submission/rehearsals. Local socket permission is required. No live/paid model is used; this does not validate another OS/runtime or the prescribed model.

Sequelize benchmarking requires its separately prepared Node/Yarn environment, not for harness startup. make clean removes Python caches and preserves evidence.
