# Sequelize real-repository benchmark

## Scope and baseline

Repository: [sequelize/sequelize](https://github.com/sequelize/sequelize), pinned to commit `abf5936c77ad9c09ba1a3116b54e7558bb4528e5` from `main`. The separate local checkout is `artifacts/external/sequelize/source`; the harness project's source is not the target.

This is a locally reproduced behavior gap in original source, not an injected defect or a claim that maintainers accepted an upstream issue. The utility `isValidNumberSyntax` returns true for `e5`, `-e5`, and `E+10`, which have no numeric mantissa. The task is to reject these while retaining valid integer/fraction/scientific syntax and existing malformed-input rejection.

Setup/reproduction and regression authoring were performed by the development assistant, not autonomously by the harness. Five local regression tests were added before the agent's baseline in `test/harness-number-syntax.test.cjs`: three failed and two control tests passed at baseline. The existing utility suite had **158 passing tests**. Local baseline evidence and a commit/runtime/hash manifest are saved in `artifacts/external/sequelize/baseline.log` and `benchmark.json`. The first live run has now modified the original TypeScript source; its outcome and compatibility concern are recorded below.

## Prepared environment

The pinned packages require Node `^22.13.0 || >=24.0.0`. This machine's shell Node 20 does not meet that requirement; the benchmark uses the existing bundled Node 24.19.0 runtime. No global Node/Yarn change was made.

Dependencies were installed using the repository's Yarn 4.18.0 executable, focusing on `@sequelize/utils` and the root tooling workspace, with dependency lifecycle scripts disabled and the package cache under `artifacts/external/sequelize/yarn-cache`. The utility package builds and tests successfully. Preparation downloaded approximately 291 MiB of free public dependency packages; it did not enable billing or make LLM calls.

The verification wrapper rebuilds the utility package (including TypeScript declarations), runs all existing utility unit tests, and runs the five regression tests using Node's test runner. It needs no external database server. It does not run all Sequelize core/dialect/integration tests, and success must not be described as validating the entire ORM.

## Run locally

From the harness project root:

```bash
make benchmark-free ARGS=--sequelize
```

Confirm `FREE`, then enter the Gemini key in the hidden prompt. The launcher uses the selected Gemini 3.1 Flash-Lite native API, with no automatic provider fallback. Defaults are 20 model turns, 600 seconds, 60,000 aggregate tokens, and 120 seconds per verification command. The source/regression hashes and commit must match preparation; the baseline rebuild/tests run before any model call. A changed or already repaired target stops rather than silently resetting files.

The agent receives the behavior description and the verification command, not a reference patch. It must edit original TypeScript source and retain tests/configuration. Fresh final verification rebuilds generated code; changing only `lib` cannot pass that rebuild. Generated utility files may also appear in the filesystem diff after a source repair; review original-source changes separately from regenerated output.

Evidence is saved under `artifacts/external/sequelize/evidence/<run-id>/`. Preserve it before preparing another independent attempt. Automatic resume and reset are not provided. This local prepared launcher is not a portable installer: on another machine, prepare the pinned checkout/dependencies/regressions and regenerate its runtime/hash manifest before running it.

## Results and acceptance

- [x] Public source downloaded and pinned; required runtime identified.
- [x] Database-free build and 158-test original baseline pass.
- [x] Real behavior reproduced; five fixed regression checks, with three failures.
- [x] Source rebuild + original suite + regression verification command prepared.
- [x] Live autonomous repair run: `20260926-145231-50413f2e`.
- [x] All 158 original tests and five regression tests pass in independent final verification; tests unchanged.
- [x] Record model usage/runtime/recovery/context metrics and update README.
- [ ] Resolve review concern: trailing-decimal forms became accepted despite prior rejection; broaden compatibility checks before accepting behavior preservation.

See the [first-run report](sequelize-first-run-report.md): recorded `RESOLVED` / `PASS`, 95.230 seconds, 8 model calls, 49,599 tokens, and no measured context reduction. The reported three files are one source file plus its rebuilt JavaScript and source map. One recovery reflects review of changed build outputs, not a failed fix. Review found a coverage gap; passing supplied tests alone is insufficient to establish complete compatibility.

The repository is large, but this first task is deliberately narrow. The run demonstrates navigation and targeted TypeScript repair inside a real monorepo, not general coverage of every Sequelize component or database.
