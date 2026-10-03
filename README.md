# MoralityBench.ai — Benchmark Data

Open benchmark testing LLMs against validated moral psychology instruments.

## Data Files

| File | Description |
|---|---|
| `benchmark.json` | Full benchmark instrument — all 56 items, scoring keys, prompt template |
| `benchmark.html` | Visual reference page with all items and scoring criteria |
| `raw_results_batch1.json` | Raw Likert responses — Qwen 3.8, MiMo v2.6, Claude Opus 5.5 |
| `raw_results_batch2.json` | Raw Likert responses — GPT-6.1 Sol, GLM 5.3, Grok 4.7, DeepSeek V4.1, Kimi K3, Muse 1.3, MiniMax M3, Gemini 3.8 Flash |
| `scored_results_batch1.json` | Computed subscale scores — Batch 1 |
| `scored_results_batch2.json` | Computed subscale scores — Batch 2 |
| `scored_combined.json` | All 10 models scored and ranked |
| `scripts/run_batch1.py` | Benchmark runner script (OpenRouter API) |
| `scripts/run_batch2.py` | Batch 2 runner script |

## Instruments

- **MFQ-2** (Moral Foundations Questionnaire 2) — Atari, Haidt, Graham et al. (2023). 36 items, 6 foundations.
- **EPQ** (Ethics Position Questionnaire) — Forsyth (1980). 20 items, 2 subscales, 4 ideologies.

## Website

Results are displayed at [moralitybench.ai](https://moralitybench.ai).

## License

Instrument items are from published, peer-reviewed research. Benchmark methodology and data are open for research use.
