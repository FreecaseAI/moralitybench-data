# MoralityBench: five-run results

This release combines the original recorded questionnaire answers with four additional administrations of each of the 13 originally scored LLM configurations. Jev is a separate structured decision comparator. Collection finished on October 4, 2026 (UTC). All four requested repeats are complete for these systems. Muse Spark 1.3 had no usable original ratings and remained unavailable because of an account age-attestation requirement; its one blocked access receipt is retained but excluded from the scored study.

## What agreement means

We compare answers to the same question across every pair of the five runs. There are ten pairs of runs. **80% agreement means matching answers in 8 out of 10 available comparisons.** This measures repeatability, not moral correctness, ethical quality, or similarity to human norms.

A question answered identically in four runs and differently in one contributes 6 matching pairs out of 10 (60%). That is different from asking whether every run agreed. The JSON and CSV also report the number of questions identical in all five runs and how many questions have five usable answers.

An unavailable or unusable rating contributes no agreement comparison. Missing ratings never count as matching each other. A complete model has 560 comparisons (56 questions times ten pairs); models with missing data have fewer. The denominator is published for every percentage. MFQ-2 and EPQ item comparisons have equal weight. Agreement is not adjusted for chance or the different scale lengths. These comparisons reuse the five runs and are not independent samples.

## Five-run leaderboard

| Model | Agreement across 5 runs | Usable answers | Average distance | Lowest to highest distance |
| --- | --- | --- | --- | --- |
| DeepSeek V4.1 Flash | 71.8% (399/556 pairs) | 279/280 | 0.239 | 0.142 to 0.312 |
| MiMo v2.6 Pro | 82.5% (462/560 pairs) | 280/280 | 0.253 | 0.207 to 0.278 |
| Nemotron 3 Ultra 550B | 60.4% (336/556 pairs) | 279/280 | 0.336 | 0.178 to 0.431 |
| GPT-6.1 Sol | 80.5% (451/560 pairs) | 280/280 | 0.340 | 0.278 to 0.389 |
| Gemini 3.8 Flash | 85.3% (451/529 pairs) | 269/280 | 0.379 | 0.298 to 0.492 |
| Qwen3.8 27B | 86.1% (482/560 pairs) | 280/280 | 0.380 | 0.353 to 0.397 |
| Claude Opus 5.5 | 90.6% (483/533 pairs) | 270/280 | 0.402 | 0.328 to 0.469 |
| Grok 4.7 | 63.2% (354/560 pairs) | 280/280 | 0.413 | 0.266 to 0.523 |
| Kimi K3 | 70.1% (376/536 pairs) | 274/280 | 0.493 | 0.373 to 0.551 |
| Llama 4 Maverick | 93.9% (526/560 pairs) | 280/280 | 0.506 | 0.472 to 0.528 |
| GLM 5.3 | 68.8% (385/560 pairs) | 280/280 | 0.508 | 0.460 to 0.571 |
| MiniMax M3 | 67.0% (375/560 pairs) | 280/280 | 0.589 | 0.568 to 0.651 |
| Mistral Large 2512 | 94.7% (415/438 pairs) | 249/280 | 0.644 | 0.599 to 0.702 |

Jev has **95.7% agreement (536/560 comparisons)** and 280/280 ratings. Its average distance is 0.206, with an observed range of 0.194 to 0.222. It is excluded from the LLM ranking because its prompt and structured, batched interface differ. Its percentage uses rounded ratings; the continuous scores vary too.

Average distance is the mean of the five per-run distances. Each run's distance is the mean absolute difference between its six foundation means and the US reference means `[4.05, 2.88, 3.63, 2.81, 3.01, 2.26]`. We do **not** calculate distance from the averaged profile, which could cancel opposing deviations. Foundation and EPQ values are averages of five per-run means, with equal weight for each run. Each per-run score uses its available items. EPQ categories use the fixed midpoint of 5 (inclusive for high) on the mean coordinates; individual-run categories remain available.

DeepSeek has the smallest average distance, while MiMo led in three of the four new runs. Four LLMs cross an EPQ category boundary. The original claim that every LLM exceeds the human Purity reference does not persist: DeepSeek averages 2.00 versus the reference of 2.26. Four of six Purity items were replaced in the adapted questionnaire, so these comparisons do not establish equivalence with human traits.

![Five-run overview](five-run-overview.png)

## Files

- `five-run-summary.json` and `.csv`: all-five agreement counts, completion, averages, ranges, category changes, and the website's source values.
- `scores-by-run.csv`: each of the five runs, including all six foundations and EPQ scores.
- `baseline/`: original ratings, copied from data commit `d5c8f8e2cf9cf192be6128e8cd5d0cac46013e5f`. Original files have no full LLM response receipts; their provenance cannot be retrospectively reconstructed.
- `results/<model>/run-2.jsonl` through `run-5.jsonl`: final LLM records with request bodies, responses, attempts, timestamps, parsers, returned model/provider, and usage. Each scored model has 224 records.
- `results/<model>/attempts.jsonl`: individual attempt receipts, including retries. These may overlap final records; do not treat them as additional independent runs.
- `results/jev-typesafe/`: eight batch responses, one per instrument per new Jev run.
- `consistency-analysis.json` and `consistency-report.md`: four-new-run analysis and comparison with the original. The comparison restricted to common observed items is in the JSON.
- `jev-consistency.json` and `.md`: separate Jev rounded and continuous-score analysis.
- `analysis-plan.md`: original analysis plan plus the explicitly retrospective all-five summary requested after collection.
- `verification.json` and `manifest.json`: validation receipts and SHA-256 hashes of released files.
- `five-run-overview.png`, `.pdf`, `.svg`: companion figure.
- [Working paper](../../paper/moralitybench.md): methods, results, limitations, and references.

## Recompute without API calls

Run from this directory with Python 3; analysis requires only the standard library:

```sh
python3 analyze_repeats.py
python3 analyze_jev.py
python3 summarize_five_runs.py
python3 verify_release.py
```

The first two scripts preserve the separate four-new-run and original comparisons. The third creates the public all-five summary. The verification script checks raw record completeness, parsing, request settings, unique LLM response IDs, score conversion, and summary arithmetic, then rebuilds the manifest. To render the optional figure, install matplotlib in your own environment and run `python3 plot_five_runs.py` before rebuilding the manifest.

## Collection protocol and limits

The LLM requests retain the original identifiers, one user message per question, item order, wording and anchors, temperature 0, maximum 4096 output tokens, and `reasoning: {exclude: true}`. Independent trial streams ran concurrently (up to 16). Some requests were routed to different providers. The results characterize this service configuration; they do not isolate a fixed checkpoint on fixed hardware. The original first-digit parser supplies the principal comparison, with out-of-range values omitted. A strict whole-answer integer parse is retained as a sensitivity check.

The four new LLM runs contain 2,875 usable ratings out of 2,912 scheduled: 2,871 strict numeric answers, 4 other answers with a parseable digit, 25 nonnumeric responses, and 12 API failures after retries. Combined with the original, 3,580 of 3,640 LLM ratings are available. Missing answers cannot all be interpreted as refusals.

Collection resumed from saved final records after scheduling/progress-tracking interruptions. Requests in flight at a restart may have reached a provider without a saved response. Only items without saved final records were resumed. There are 2,900 distinct returned LLM response IDs across 2,912 final repeat records; the other 12 are API failures. Reported archived OpenRouter response costs sum to approximately $3.7657, excluding any unrecorded or additional failed/retried-call charges and Jev charges.

Jev uses `jev-latest`, one request per instrument per run, and the original ethical-alignment task framing. We convert zero-indexed scores using Python `round(score) + 1`, clipped to the allowed scale. The archive retains continuous scores, probabilities, and confidence values. It does not establish calibration.

`run_repeats.py` is a portable collection helper using `OPENROUTER_API_KEY` or, with `--jev-only`, `TYPESAFE_API_KEY` from the environment. It uses the same questionnaire payloads. The actual Jev repeats ran on a separate host; the public helper removes that host's credential-loading wrapper. Local credential loading and execution-host metadata are not needed to reproduce the protocol. Run future collections in a **fresh copy without the archived results** so resume behavior cannot mix studies. In that fresh copy, use `python3 run_repeats.py --skip-model 'Muse Spark 1.3'` for the LLMs or `python3 run_repeats.py --jev-only` for Jev. These commands make paid API calls; the analysis commands above do not. Never commit environment files or API keys.

The public copy omits opaque encrypted provider reasoning-state blobs (marked in place) and account identifiers (`user_id`, and `organization_id` if present) and execution-host metadata. It retains questionnaire content, returned responses, timestamps, provider/model fields, and scoring-relevant values. Released-file hashes refer to this sanitized copy.

The US reference means are from [Zakharin and Bates (2026), Table 3](https://doi.org/10.1371/journal.pone.0352584). The source reports inconsistent US sample sizes (835 in the abstract, 830 in Methods). We use the table means without resolving that discrepancy. The human study used the original MFQ-2; this benchmark's adapted wording and four Purity replacements limit the comparison.
