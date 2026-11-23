# SmolVLM2 preliminary recognition results

All four SmolVLM2 recognition groups have completed on the same 20 meal images and frozen prompts used by Qwen3-VL-4B. The nutrition groups are still running. No fine-tuning was used. Scores use the existing lexical evaluator; micro recall and precision count all examples, including invalid recognition outputs as empty predictions. Validity indicates whether `food_labels` is a list. SmolVLM2 is smaller (2.2B vs 4B), with different image preprocessing.

| Task | Prompt | Model | Valid responses | Item recall | Micro precision | Exact meal set |
|---|---|---|---:|---:|---:|---:|
| Open | Baseline | SmolVLM2-2.2B | 18/20 | 27.3% | 30.8% | 15.0% |
| Open | Baseline | Qwen3-VL-4B | 20/20 | 38.6% | 37.8% | 15.0% |
| Open | CoT | SmolVLM2-2.2B | 20/20 | 29.5% | 29.5% | 10.0% |
| Open | CoT | Qwen3-VL-4B | 20/20 | 43.2% | 43.2% | 20.0% |
| Closed | Baseline | SmolVLM2-2.2B | 16/20 | 63.6% | 10.0% | 5.0% |
| Closed | Baseline | Qwen3-VL-4B | 20/20 | 86.4% | 90.5% | 70.0% |
| Closed | CoT | SmolVLM2-2.2B | 17/20 | 65.9% | 9.4% | 5.0% |
| Closed | CoT | Qwen3-VL-4B | 20/20 | 86.4% | 88.4% | 70.0% |

In the closed CoT condition, the 17 parseable list outputs contain a median of 21 predicted labels per meal (range 1–33). Large numbers of extra labels explain the low precision. Recognition coverage is schema-list validity, not semantic validity; invalid predictions are not silently excluded. These aggregate results are exploratory and should not be interpreted as a size-matched model comparison.

## Image nutrition baseline (interim)

All three SmolVLM2 image-nutrition conditions have completed. The table compares energy MAE only on meals for which both models returned all four valid totals; delta is SmolVLM2 minus Qwen3 absolute error.

| Prompt | Smol / Qwen3 valid | Paired n | Smol MAE | Qwen3 MAE | Paired delta [95% CI] | Smol better / worse / tied |
|---|---:|---:|---:|---:|---:|---:|
| Baseline | 19/20 / 20/20 | 19 | 336.0 | 157.7 | 178.3 [115.3, 238.2] | 1 / 17 / 1 |
| CoT | 19/20 / 20/20 | 19 | 347.0 | 176.1 | 170.9 [113.1, 224.7] | 1 / 17 / 1 |
| CoT + RAG | 17/20 / 19/20 | 16 | 353.3 | 241.5 | 111.8 [48.9, 173.4] | 2 / 14 / 0 |

Units are kcal. The 95% intervals resample the paired meals (10,000 draws, seed 20261123), not the broader population. Model size and image preprocessing differ, and the three rows use different valid subsets.

## Text baseline and schema (interim)

In the 50-question SmolVLM2 text baseline, 47 responses have all four valid numeric totals. All 47 valid responses return exactly `(100 kcal, 10 g carbohydrate, 10 g protein, 5 g fat)`, the four values shown in the JSON schema. The other three do not meet the numeric contract. This is a strong exact-match signal of output-format sensitivity, not proof of model intent. Under the prose-only no-example baseline, all 50 responses have numeric totals but **26/50 return all four totals as zero**. A numeric output is not necessarily a meaningful nutrition estimate. Other text conditions remain in progress.
