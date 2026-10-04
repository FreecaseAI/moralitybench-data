# MoralityBench repeat-study results

Collection complete for the 13 originally scored LLMs.

The four new administrations preserve the original requests. The comparison with the original archive is reported separately from agreement among new runs. Primary agreement uses the original first-digit parser, limited to valid scale values; the archive also contains strict-parser results.

| Model | New runs complete | Numeric / 224 | Pairwise agreement, new runs | Agreement with original | Distance, new mean (SD) | New distance range |
| --- | --- | --- | --- | --- | --- | --- |
| DeepSeek V4.1 Flash | 4/4 | 223 / 224 | 73.3% (333 pairs) | 69.5% (223 comparisons) | 0.264 (0.052) | 0.209 to 0.312 |
| Nemotron 3 Ultra 550B | 4/4 | 223 / 224 | 61.6% (333 pairs) | 58.7% (223 comparisons) | 0.376 (0.062) | 0.321 to 0.431 |
| MiMo v2.6 Pro | 4/4 | 224 / 224 | 82.7% (336 pairs) | 82.1% (224 comparisons) | 0.246 (0.030) | 0.207 to 0.278 |
| Gemini 3.8 Flash | 4/4 | 215 / 224 | 84.2% (316 pairs) | 86.9% (213 comparisons) | 0.399 (0.098) | 0.298 to 0.492 |
| Qwen3.8 27B | 4/4 | 224 / 224 | 86.0% (336 pairs) | 86.2% (224 comparisons) | 0.384 (0.021) | 0.353 to 0.397 |
| GPT-6.1 Sol | 4/4 | 224 / 224 | 83.0% (336 pairs) | 76.8% (224 comparisons) | 0.328 (0.036) | 0.278 to 0.361 |
| GLM 5.3 | 4/4 | 224 / 224 | 68.5% (336 pairs) | 69.2% (224 comparisons) | 0.519 (0.054) | 0.460 to 0.571 |
| Claude Opus 5.5 | 4/4 | 216 / 224 | 91.2% (319 pairs) | 89.7% (214 comparisons) | 0.386 (0.040) | 0.328 to 0.420 |
| Kimi K3 | 4/4 | 218 / 224 | 71.7% (318 pairs) | 67.9% (218 comparisons) | 0.493 (0.081) | 0.373 to 0.551 |
| Llama 4 Maverick | 4/4 | 224 / 224 | 94.0% (336 pairs) | 93.8% (224 comparisons) | 0.507 (0.027) | 0.472 to 0.528 |
| Grok 4.7 | 4/4 | 224 / 224 | 61.0% (336 pairs) | 66.5% (224 comparisons) | 0.387 (0.106) | 0.266 to 0.523 |
| MiniMax M3 | 4/4 | 224 / 224 | 69.3% (336 pairs) | 63.4% (224 comparisons) | 0.594 (0.038) | 0.576 to 0.651 |
| Mistral Large 2512 | 4/4 | 212 / 224 | 97.0% (301 pairs) | 89.8% (137 comparisons) | 0.630 (0.042) | 0.599 to 0.691 |

Pairwise agreement pools the six pairs of new runs, comparing only items with valid ratings in both members. Agreement with the original pools the four baseline-to-new comparisons. Missing responses never count as agreement. Means and standard deviations describe these observations and are not estimates of uncertainty over all future queries.

## Completion and output format

| Model | Strict numeric | Other numeric text | Nonnumeric | API failures | Items present in all four | Identical in all four |
| --- | --- | --- | --- | --- | --- | --- |
| Qwen3.8 27B | 224 | 0 | 0 | 0 | 56 | 42 |
| MiMo v2.6 Pro | 224 | 0 | 0 | 0 | 56 | 40 |
| Claude Opus 5.5 | 212 | 4 | 8 | 0 | 53 | 44 |
| GPT-6.1 Sol | 224 | 0 | 0 | 0 | 56 | 39 |
| GLM 5.3 | 224 | 0 | 0 | 0 | 56 | 26 |
| Grok 4.7 | 224 | 0 | 0 | 0 | 56 | 20 |
| DeepSeek V4.1 Flash | 223 | 0 | 1 | 0 | 55 | 31 |
| Kimi K3 | 218 | 0 | 6 | 0 | 50 | 26 |
| MiniMax M3 | 224 | 0 | 0 | 0 | 56 | 27 |
| Gemini 3.8 Flash | 215 | 0 | 9 | 0 | 51 | 37 |
| Nemotron 3 Ultra 550B | 223 | 0 | 1 | 0 | 55 | 20 |
| Mistral Large 2512 | 212 | 0 | 0 | 12 | 45 | 42 |
| Llama 4 Maverick | 224 | 0 | 0 | 0 | 56 | 50 |

## EPQ and distance by run

| Model | Run | Distance | Idealism | Relativism | Category | Numeric items |
| --- | --- | --- | --- | --- | --- | --- |
| Qwen3.8 27B | 1 | 0.366 | 5.100 | 4.900 | Absolutist | 56/56 |
| Qwen3.8 27B | 2 | 0.353 | 5.600 | 5.200 | Situationist | 56/56 |
| Qwen3.8 27B | 3 | 0.397 | 5.700 | 5.100 | Situationist | 56/56 |
| Qwen3.8 27B | 4 | 0.393 | 5.500 | 4.800 | Absolutist | 56/56 |
| Qwen3.8 27B | 5 | 0.393 | 5.500 | 4.700 | Absolutist | 56/56 |
| MiMo v2.6 Pro | 1 | 0.278 | 5.100 | 4.800 | Absolutist | 56/56 |
| MiMo v2.6 Pro | 2 | 0.207 | 5.300 | 4.900 | Absolutist | 56/56 |
| MiMo v2.6 Pro | 3 | 0.278 | 5.300 | 4.700 | Absolutist | 56/56 |
| MiMo v2.6 Pro | 4 | 0.259 | 5.400 | 5.400 | Situationist | 56/56 |
| MiMo v2.6 Pro | 5 | 0.242 | 5.300 | 4.900 | Absolutist | 56/56 |
| Claude Opus 5.5 | 1 | 0.469 | 4.900 | 4.200 | Exceptionist | 54/56 |
| Claude Opus 5.5 | 2 | 0.392 | 4.900 | 4.000 | Exceptionist | 54/56 |
| Claude Opus 5.5 | 3 | 0.420 | 4.900 | 4.100 | Exceptionist | 53/56 |
| Claude Opus 5.5 | 4 | 0.328 | 4.900 | 4.100 | Exceptionist | 55/56 |
| Claude Opus 5.5 | 5 | 0.403 | 5.000 | 4.100 | Absolutist | 54/56 |
| GPT-6.1 Sol | 1 | 0.389 | 4.800 | 4.800 | Exceptionist | 56/56 |
| GPT-6.1 Sol | 2 | 0.361 | 4.100 | 4.700 | Exceptionist | 56/56 |
| GPT-6.1 Sol | 3 | 0.341 | 4.800 | 4.800 | Exceptionist | 56/56 |
| GPT-6.1 Sol | 4 | 0.278 | 4.300 | 4.600 | Exceptionist | 56/56 |
| GPT-6.1 Sol | 5 | 0.333 | 4.200 | 4.900 | Exceptionist | 56/56 |
| GLM 5.3 | 1 | 0.460 | 4.700 | 4.600 | Exceptionist | 56/56 |
| GLM 5.3 | 2 | 0.460 | 4.900 | 4.200 | Exceptionist | 56/56 |
| GLM 5.3 | 3 | 0.488 | 4.900 | 4.500 | Exceptionist | 56/56 |
| GLM 5.3 | 4 | 0.559 | 4.400 | 4.800 | Exceptionist | 56/56 |
| GLM 5.3 | 5 | 0.571 | 4.800 | 4.800 | Exceptionist | 56/56 |
| Grok 4.7 | 1 | 0.516 | 5.500 | 4.000 | Absolutist | 56/56 |
| Grok 4.7 | 2 | 0.266 | 5.400 | 4.400 | Absolutist | 56/56 |
| Grok 4.7 | 3 | 0.364 | 5.600 | 4.800 | Absolutist | 56/56 |
| Grok 4.7 | 4 | 0.396 | 5.300 | 4.200 | Absolutist | 56/56 |
| Grok 4.7 | 5 | 0.523 | 5.500 | 4.300 | Absolutist | 56/56 |
| DeepSeek V4.1 Flash | 1 | 0.142 | 5.300 | 5.700 | Situationist | 56/56 |
| DeepSeek V4.1 Flash | 2 | 0.209 | 4.900 | 5.800 | Subjectivist | 56/56 |
| DeepSeek V4.1 Flash | 3 | 0.229 | 5.400 | 4.700 | Absolutist | 56/56 |
| DeepSeek V4.1 Flash | 4 | 0.304 | 4.900 | 4.667 | Exceptionist | 55/56 |
| DeepSeek V4.1 Flash | 5 | 0.312 | 4.900 | 5.100 | Subjectivist | 56/56 |
| Kimi K3 | 1 | 0.496 | 5.000 | 4.400 | Absolutist | 56/56 |
| Kimi K3 | 2 | 0.523 | 5.800 | 4.700 | Absolutist | 54/56 |
| Kimi K3 | 3 | 0.373 | 5.200 | 4.600 | Absolutist | 54/56 |
| Kimi K3 | 4 | 0.551 | 5.300 | 4.500 | Absolutist | 56/56 |
| Kimi K3 | 5 | 0.523 | 5.200 | 4.600 | Absolutist | 54/56 |
| MiniMax M3 | 1 | 0.568 | 5.500 | 4.700 | Absolutist | 56/56 |
| MiniMax M3 | 2 | 0.576 | 5.800 | 4.900 | Absolutist | 56/56 |
| MiniMax M3 | 3 | 0.576 | 5.900 | 4.900 | Absolutist | 56/56 |
| MiniMax M3 | 4 | 0.651 | 5.400 | 4.200 | Absolutist | 56/56 |
| MiniMax M3 | 5 | 0.576 | 5.400 | 4.200 | Absolutist | 56/56 |
| Gemini 3.8 Flash | 1 | 0.298 | 4.100 | 4.600 | Exceptionist | 54/56 |
| Gemini 3.8 Flash | 2 | 0.473 | 4.300 | 4.200 | Exceptionist | 54/56 |
| Gemini 3.8 Flash | 3 | 0.333 | 3.800 | 4.900 | Exceptionist | 54/56 |
| Gemini 3.8 Flash | 4 | 0.492 | 4.200 | 4.600 | Exceptionist | 53/56 |
| Gemini 3.8 Flash | 5 | 0.298 | 4.300 | 4.600 | Exceptionist | 54/56 |
| Nemotron 3 Ultra 550B | 1 | 0.178 | 5.800 | 5.000 | Situationist | 56/56 |
| Nemotron 3 Ultra 550B | 2 | 0.324 | 5.500 | 5.300 | Situationist | 56/56 |
| Nemotron 3 Ultra 550B | 3 | 0.428 | 5.400 | 5.000 | Situationist | 56/56 |
| Nemotron 3 Ultra 550B | 4 | 0.321 | 5.200 | 5.300 | Situationist | 56/56 |
| Nemotron 3 Ultra 550B | 5 | 0.431 | 5.300 | 5.200 | Situationist | 55/56 |
| Mistral Large 2512 | 1 | 0.702 | 7.000 | 5.167 | Situationist | 37/56 |
| Mistral Large 2512 | 2 | 0.599 | 7.000 | 5.900 | Situationist | 55/56 |
| Mistral Large 2512 | 3 | 0.604 | 7.000 | 5.900 | Situationist | 54/56 |
| Mistral Large 2512 | 4 | 0.627 | 7.250 | 5.900 | Situationist | 53/56 |
| Mistral Large 2512 | 5 | 0.691 | 7.000 | 5.875 | Situationist | 50/56 |
| Llama 4 Maverick | 1 | 0.500 | 5.200 | 5.000 | Situationist | 56/56 |
| Llama 4 Maverick | 2 | 0.472 | 5.200 | 5.000 | Situationist | 56/56 |
| Llama 4 Maverick | 3 | 0.500 | 5.200 | 5.000 | Situationist | 56/56 |
| Llama 4 Maverick | 4 | 0.528 | 5.200 | 5.000 | Situationist | 56/56 |
| Llama 4 Maverick | 5 | 0.528 | 5.700 | 5.000 | Situationist | 56/56 |

## Access limits

Muse Spark 1.3 requires an age attestation in the OpenRouter account before it can serve requests. Its original record contains no usable ratings, and it is excluded from the primary comparison. Jev is reported separately in jev-consistency.md.

Reported OpenRouter cost for archived result responses: $3.7657. This may exclude charges for failed or retried requests.
