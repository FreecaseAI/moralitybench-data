# MoralityBench data

Open data for an exploratory benchmark of AI responses to adapted moral psychology questionnaires. The current release includes five runs for 13 scored LLM configurations and a separate Jev comparison.

- [Live leaderboard](https://moralitybench.ai): five-run averages, agreement, missing answers, and charts.
- [Five-run data and reproducible analysis](repeated-runs/2026-10-04/README.md): full repeat responses, original baselines, CSV/JSON summaries, scripts, and verification hashes.
- [Working academic paper](paper/moralitybench.md) and [LaTeX source](paper/moralitybench.tex). Authorship and disclosures still require human review before submission.

## Reading the results

Agreement compares answers to the same question across all ten pairs of the five runs, omitting missing answers. Average distance measures how close the foundation scores are to published US human reference means. Neither quantity measures moral correctness or deployment safety. Jev uses a different prompt and interface and stays outside the LLM ranking. See the release README for exact definitions and denominators.

## Original snapshot

Root-level instrument files, raw results, scored summaries, and `scripts/` preserve the original snapshot. `scored_combined.json` is the original single-run leaderboard, **not** the five-run aggregate. The current website uses `repeated-runs/2026-10-04/five-run-summary.json`. Original missing values labeled as refusals cannot be distinguished from other failures because the old LLM files do not retain response text or error receipts.

MFQ-2 has 36 items across six foundations. EPQ has 20 items across idealism and relativism. The benchmark adapts human wording and replaces four Purity items. Human validation of the original instruments does not establish validity of this AI adaptation.

## Research use

The archive is public for inspection and replication. Consult the original publications for instrument rights; this repository does not grant rights beyond those held by its contributors. Do not commit credentials.
