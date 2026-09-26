# Free development setup

Development now uses **Gemini 3.1 Flash-Lite**, low reasoning, and JSON actions. Google currently lists free input/output for this model on the Free Tier. We selected it after repeated HTTP 503 failures from Gemini 3.8 Flash and HTTP 404 from Gemini 2.5 Flash on both routes. The native route passed a live connectivity probe and the first live repair benchmark. The harness retains other adapters for evaluation but does not switch to them automatically.

## First verified live repair — September 26, 2026

Run `artifacts/benchmarks/20260926-132009-ffb4c367` resolved the label normalization fixture using Gemini 3.1 Flash-Lite via the native API. The baseline had six tests with four expected failures; all six passed after the repair, including independent final verification. Only `catalog.py` changed (+9/-3); tests stayed unchanged. The diff uses a seen set and result list to preserve first occurrence order after stripping and Unicode case folding.

The run took 29.647 seconds, three model/HTTP calls and six repository tool calls, with provider-reported usage of 4,448 input and 999 output tokens. There were no quota or service retries. Evidence is saved under `evidence/20260926-132009-c9282193/` within that run. This validates one small live fixture, not broader coding performance or future service availability.

Sources: [Gemini pricing](https://ai.google.dev/gemini-api/docs/pricing), [OpenAI-compatible endpoint](https://ai.google.dev/gemini-api/docs/openai), [quotas](https://ai.google.dev/gemini-api/docs/rate-limits).

## First live benchmark

The second verified live run, `artifacts/benchmarks/20260926-132804-ac3d5bdd`, repaired `cart_checkout` across two modules. All ten tests passed in independent final verification after five baseline failures, with tests unchanged. It took 39.192 seconds, four model requests and ten tool calls, with 9,522 input / 1,807 output tokens and no quota/service retries. Run it with `make benchmark-free ARGS='--fixture cart_checkout'`. These two small fixtures establish initial repair evidence, not broader reliability.

1. Open [Google AI Studio API keys](https://aistudio.google.com/apikey).
2. Create/select a project and key with its billing tier showing **Free Tier**. Do not enable billing, link a billing account, or upgrade the project. Check the project's active model quota before testing.
3. From the project root, run:

```bash
make setup
make benchmark-free
```

The launcher asks you to confirm the Free Tier project, then prompts for a key with hidden input. The key is used only for that process, never written to source, a configuration file, or a credential file. It is not printed. Existing unrelated `AI_API_KEY` values are not reused.

If already using a Gemini key in this terminal, the launcher can read `GEMINI_API_KEY`. For a noninteractive invocation, set it locally and use:

```bash
make benchmark-free ARGS=--free-tier-confirmed
```

`--free-tier-confirmed` means **you checked** the exact key's project tier in AI Studio. The harness has no billing-tier introspection endpoint and cannot guarantee zero charges if the supplied key belongs to a billed project. The launcher does not configure billing or subscriptions.

The benchmark copies a fresh broken fixture and saves baseline failures, the modified target, telemetry, final diff, and performance under `artifacts/benchmarks/<run-id>/`. Its six tests cover ordering, case folding, blanks, generators, empty inputs, and mutation. Four tests fail before the repair. Only a live run demonstrates model coding ability; mocked tests only verify the integration.

## Quota behavior

If a model returns HTTP 404, inspect the model catalog using `make benchmark-free ARGS=--list-models`. This uses hidden key entry and only GETs model metadata. It does not run the benchmark or generate content. Share model names rather than credentials; listing alone does not prove Free Tier quota or access through the compatibility route.

- Initial request spacing is 12 seconds (at most five starts/minute). This is a cautious configuration, **not a promise about your quota**.
- Tune using AI Studio. For example, a one-request-per-minute account can use `make benchmark-free ARGS='--min-request-interval 60'`.
- HTTP 429 responses use provider retry guidance and exponential backoff, with at most three retries per model turn.
- Temporary HTTP 500/502/503/504 errors retry the same request and model, with 12/24/48-second backoff (or longer provider guidance), within the same three-retry limit. Persistent failures stop as `SERVICE_UNAVAILABLE`; they do not consume coding recovery attempts. Service retries and waits are recorded separately in `performance.json`.
- Recognized daily exhaustion stops immediately; unknown/repeated quota errors stop after bounded retries.
- Waits and requests obey the run's remaining wall-clock budget. Exhaustion preserves evidence and working-tree changes; automatic resume is not implemented.
- Defaults: 20 model turns, 600 seconds, 60,000 aggregate tokens, 8,000 estimated context tokens, 8,192 output tokens per call including model reasoning.
- `performance.json` records HTTP requests, retry count, and seconds spent waiting.

The `gemini-free.json` configuration blocks model/provider/endpoint overrides away from the selected free development setup. It requires `GEMINI_API_KEY` rather than selecting an unrelated generic key. Development uses the native `generateContent` API with JSON actions. `--gemini-api-route compatibility` remains available for evaluation. Native Gemini tool continuations and thought-signature replay are not implemented.

Use `make benchmark-free ARGS=--probe` to test the native route with one small request before a full repair. This generates a fixed connectivity action with a 2,048-token output cap (including thinking), 30-second timeout and no retries; no repository tool executes. A successful probe confirms connectivity and action formatting, not coding performance.

Google says free-tier content may be used to improve its products. The initial fixture contains only public test code. Consider that data policy before supplying a private repository.

## Evaluation

The official model/endpoint is still configurable and must follow organiser instructions. The `AI_API_KEY` evaluation contract remains supported outside this explicit free development configuration. We will not use a paid development provider without a new instruction authorizing it.
