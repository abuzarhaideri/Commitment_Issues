# Live repair benchmarks

`label_normalization` is intentionally broken: it sorts normalized labels instead of preserving first occurrence order. Six tests cover ordering, blanks, Unicode case folding, generators, empty input, and mutation. The baseline has exactly four failures; an order-preserving fix passes all six.

The selected zero-cost workflow is `make benchmark-free`; see [free setup](../docs/free-development.md).

`cart_checkout` is the second fixture. It requires fixes in two modules: line quantities in `pricing.py`, and discounted shipping thresholds/zero-subtotal shipping in `checkout.py`. Ten tests cover regression and boundary behavior; exactly five fail at baseline. Gemini 3.1 Flash-Lite passed its live repair on September 26, 2026: all ten tests passed in independent verification, only the two implementation modules changed, and no retries were needed. The run took 39.192 seconds and four model calls; evidence is in `artifacts/benchmarks/20260926-132804-ac3d5bdd/evidence/20260926-132804-bee9c759/` from the project root.

```bash
make benchmark-free ARGS='--fixture cart_checkout'
```

The default fixture is `label_normalization`. Both runners accept `--fixture`; fixture names are constrained to the built-in registry. Baseline test and failure counts are checked before any model invocation.

For other explicitly configured providers, after setting `HARNESS_PROVIDER`, `HARNESS_MODEL`, `HARNESS_BASE_URL`, and `AI_API_KEY` for a cloud endpoint:

```bash
.venv/bin/python benchmarks/run_live.py
```

Optional CLI configuration is forwarded to the harness:

```bash
.venv/bin/python benchmarks/run_live.py --config /path/to/model-config.json
```

Use `--config config/openai-luna.json` for the prepared OpenAI Responses JSON-action run. Use `--native-tools` only with the Chat Completions compatible adapter and a model/configuration that supports it. Each invocation copies a fresh broken fixture into `artifacts/benchmarks/<id>/target`, saves the baseline log, and calls the real adapter. Model edits, final diff, telemetry, and performance remain available for review under that run directory. Defaults cap the run at 30 model turns, 300 seconds, and 60,000 total tokens.

The committed fixture stays broken deliberately. Do not include its tests in the harness's own `make test` suite. No live run is claimed unless an actual configured endpoint executes the repair.
