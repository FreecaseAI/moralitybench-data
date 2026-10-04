# Repeat-study analysis plan

Four additional runs use the original 56 items, wording, anchors, stored order, one user message per item, temperature 0, 4096-token cap, and reasoning exclusion. Each model receives a separate sequence of requests for each run. The 13 configurations in the original scored release are the primary comparison set. Muse is an attempted secondary configuration with no usable original measurements and an account access block. Jev uses its original separate two-request-per-run protocol if a replacement credential becomes available.

The runner retains each request body and API response, timestamp, attempt status, returned model and provider, token usage, and reported cost. It stores both the original first-digit parse and a strict parse requiring the entire trimmed answer to be a single integer within the scale. No credentials are retained. Authentication, credit, and model access blocks are reported as blocks, not moral refusals.

The analysis will report:

1. Completion and format validity by model and run, keeping API failures separate from nonnumeric responses.
2. Exact item agreement across the four new runs and agreement with the original run, using only pairs with available valid ratings. Each agreement reports its denominator. A separate count identifies items complete and identical across all four new runs.
3. Each foundation and EPQ score by run, with the observed standard deviation and range. These describe variation among these runs, not a confidence interval over future requests.
4. Reference distance and rank by run, computed with unrounded foundation means. Missing subscales leave distance undefined. EPQ category changes use the original inclusive midpoint rule.
5. Sensitivity to the original parser versus strict parsing and to restricting scores to items observed in every compared run.
6. For Jev, stability of rounded ratings and continuous returned scores, reported separately from the generative comparison.

The comparison with the original run will remain separate from consistency among the new runs. A stable new result that differs from the archive may reflect backend changes, collection conditions, or problems in the original records. The new response receipts can document current behavior but cannot authenticate the old collection.

No arbitrary cutoff will turn these descriptive statistics into a claim that a model is universally consistent. Claims will name the quantity, agreement rate, score variation, and number of runs actually observed.

## Follow-up requested after collection

After the four repeats finished, the benchmark owner requested an agreement percentage across all five runs on the public leaderboard. The five-run summary pools all ten pairs (the six new-to-new pairs plus four original-to-new pairs), retaining the separate comparisons above. It reports all-five identical item counts as a distinct, stricter measure. This follow-up summary is descriptive and was specified after collection, not preregistered.

The public leaderboard ranks the mean of five per-run distances. Foundation and EPQ scores average five per-run means with equal weight per run. The distance is not recalculated from the averaged foundation profile, because that could cancel differences on opposite sides of a human reference. The table also reports missing counts, observed distance ranges, and EPQ category changes.
