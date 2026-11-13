# Changelog

## 2026-11-12 (OpenRouter reruns: Muse Spark 1.3 & Mistral Large 2512)

- Added the `repeated-runs/2026-11-12/` cohort with five fresh concurrent 56-item runs each for **Muse Spark 1.3** (280/280 strict via Google after OpenRouter 18+ age attestation) and **Mistral Large 2512** (280/280 strict via `provider={only:["mistral/eu"], allow_fallbacks:false}`).
- Replaced the incomplete October 4 Mistral Large 2512 entry (`249/280`) with the complete November 12 run (`280/280`, `93.9%` repeatability tying Llama 4 Maverick at `526/560` pairs, distance `0.637`), preserving the superseded record under `superseded_models` and adding an offline October-4 12-item recovery diagnostic (`oct4-recovery/`, `261/280`). Combined questionnaire coverage across all 21 LLMs is `5,726 / 5,880` (`97.4%`, or `6,006 / 6,160` including Jev).
- Added the `scenarios/2026-11-12-muse-spark-1-3/` addendum (`20` fresh scenario trials: `5/5 [B]` on Chlorine diversion and `5/5 [A]` on Pipeline confidentiality under both prompt wordings), bringing combined forced-choice counts across all 22 systems to `440` trials (`37A/70B/3X` and `41A/68B/1X` chlorine; `97A/5B/8X` and `101A/5B/4X` pipeline) while keeping all frozen November 1 files unchanged.
- Left working papers in `paper/` untouched.

## 2026-11-12 (later)

- Replaced the DIT-2 human reference with the Center's updated norms (Gungordu et al., 2024; 73,740 US respondents tested 2011-2020, including 73,707 N2 scores). The pooled reference is calculated from rounded published group values. The 2003 Guide norms remain in `summary.json` as `human_norms.earlier_norms_2003`. The 2003 Ph.D./Ed.D. group (169 respondents, N2 48.99) is replaced by the 2023 doctoral group (3,672 respondents, N2 38.47). Model scores are unchanged.

## 2026-11-12

- Published DIT-2 scores computed by the Center for the Study of Ethical Development (University of Alabama) for 15 LLM configurations and Jev, two runs each: 32 scored questionnaires, none purged (`dit2/2026-10-15/`).
- Included the Center's score workbook and scorer report as returned, per-run and per-model tables, all 34 attempts with the two unsubmitted Mistral Large 2512 runs, and a build-and-check script.
- Left the Utilizer score blank for the one run where the Center returned its missing-value code (9.99), and documented that the Center's printed Utilizer average includes that code.
- Withheld the DIT-2 instrument text, prompts, raw replies and item-level answers. The working paper is unchanged.

## 2026-11-04

- Added working paper v2 manuscript (`moralitybenchv2.md`) and compiled PDF (`moralitybenchv2.pdf`).

- Updated the working paper manuscript (`moralitybench.md`), LaTeX source (`moralitybench.tex`), and compiled PDF (`moralitybench.pdf`).
- Expanded the Discussion section with empirical findings on model size vs. moral response patterns, questionnaire-to-action divergence on harm dilemmas, and Jev's internal probability distributions.
- Added institutional and non-commercial research disclosures.

## 2026-11-01

- Published full dataset and verification records for two forced-choice operational dilemmas: Chlorine Diversion (AI trolley dilemma) and Pipeline Confidentiality (duty-to-warn dilemma) across 20 LLM configurations and Jev (210 trials).
- Published prompt sensitivity study evaluating five fresh trials per system after removing "reasoning or" from the standard preamble (210 trials, 420 scenario trials total).
- Updated repository documentation to present all benchmark data neutrally for public review, removing internal model instructions and redundant research use boilerplate.

## 2026-10-29

- Added five fresh MFQ-2/EPQ administrations for GPT-6.1 Terra, Claude Haiku 5.5, Kimi K3.1 Pro and MiniMax M3.1 Flash: all 1,120 responses are valid whole-answer integers.
- Published raw receipts, model catalog metadata, strict scores, first-digit diagnostics, CSV/JSON summaries, figures and verification hashes.
- Expanded the combined archive to 20 LLM configurations plus the unchanged Jev comparison; preserved all prior observations and cohort/parser labels.
- Updated the working paper and downloadable PDF for the three dated cohorts.

## 2026-10-14

- Applied the requested Humanizer skill to the working paper and response-viewer prose, preserving quoted answers, calculations and citations; rebuilt the paper PDF and release hashes.
- Added five fresh administrations for GPT-6 Astra, Muse Wonder and Gemini 4 Argon: 840 response records.
- Published strict numeric primary scores (715 valid/840), archived first-digit diagnostics, raw responses, payload verification and file hashes.
- Preserved all earlier model/Jev observations; combined 16-model display labels cohort dates and parser policies.
- Added the Gemini instruction-following addendum and standalone 280-answer HTML viewer, as directed by Jim.
- Updated working manuscript Markdown/LaTeX and compiled PDF; retained the original cohort findings and disclosed sparse-response/cross-time limits.

## 2026-10-04

- Added four further administrations for each of the 13 originally scored LLMs and Jev, preserving original baselines.
- Published all-five pairwise agreement, available-pair denominators, completion, per-run scores, observed ranges, and EPQ category changes.
- Added reproducible analysis, verification hashes, a companion figure, and the revised working paper.
- Removed account and execution-host metadata from public repeat records.
- Retained original root-level scores as a separately labeled single-run snapshot.
