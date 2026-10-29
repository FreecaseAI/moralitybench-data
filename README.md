# MoralityBench data

Open data for an exploratory benchmark of AI responses to adapted moral psychology questionnaires. The current display includes five runs for 20 scored LLM configurations across three dated cohorts and a separate Jev comparison. The [October 29 extension](repeated-runs/2026-10-29/README.md) adds GPT-6.1 Terra, Claude Haiku 5.5, Kimi K3.1 Pro and MiniMax M3.1 Flash, with 1,120 valid responses. The [October 14 extension](repeated-runs/2026-10-14/README.md) added GPT-6 Astra, Muse Wonder and Gemini 4 Argon. Earlier configurations and Jev were not retested. October 14 and October 29 results use strict whole-answer integers because Gemini’s verbose nonanswers contain misleading digits; historical first-digit results remain preserved.

- [Live leaderboard](https://moralitybench.ai): five-run averages, agreement, missing answers, and charts.
- [Five-run data and reproducible analysis](repeated-runs/2026-10-04/README.md): full repeat responses, original baselines, CSV/JSON summaries, scripts, and verification hashes.
- [Working academic paper](paper/moralitybench.md) and [LaTeX source](paper/moralitybench.tex) and [PDF](paper/moralitybench.pdf). Authorship and disclosures still require human review before submission.

## Reading the results

Agreement compares answers to the same question across all ten pairs of the five runs, omitting missing answers. Average distance measures how close the foundation scores are to published US human reference means. Neither quantity measures moral correctness or deployment safety. Jev uses a different prompt and interface and stays outside the LLM ranking. See the release README for exact definitions and denominators.

## Original snapshot

Root-level instrument files, raw results, scored summaries, and `scripts/` preserve the original snapshot. `scored_combined.json` is the original single-run leaderboard, **not** the five-run aggregate. The current website uses `repeated-runs/2026-10-29/combined-five-run-summary.json`, combining preserved historical values with the two strictly parsed extensions. Original missing values labeled as refusals cannot be distinguished from other failures because the old LLM files do not retain response text or error receipts.

MFQ-2 has 36 items across six foundations. EPQ has 20 items across idealism and relativism. The benchmark adapts human wording and replaces four Purity items. Human validation of the original instruments does not establish validity of this AI adaptation.

## Research use

The archive is public for inspection and replication. Consult the original publications for instrument rights; this repository does not grant rights beyond those held by its contributors. Do not commit credentials.
