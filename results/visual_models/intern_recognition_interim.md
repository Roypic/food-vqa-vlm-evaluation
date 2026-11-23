# InternVL3.5-4B preliminary recognition results

These are the completed recognition groups on the same 20 meal images and frozen prompts as Qwen3-VL-4B. The remaining nutrition groups are still running. No fine-tuning was used. The models use different visual pipelines; InternVL3.5 also uses a Qwen3 language backbone. Validity requires a `food_labels` list; invalid outputs are scored as empty predictions by the frozen evaluator.

| Prompt | Model | Valid responses | Item recall | Micro precision | Micro F1 | Exact meal set |
|---|---|---:|---:|---:|---:|---:|
| Baseline | InternVL3.5-4B | 20/20 | 34.1% | 34.1% | 34.1% | 25.0% |
| Baseline | Qwen3-VL-4B | 20/20 | 38.6% | 37.8% | 38.2% | 15.0% |
| CoT | InternVL3.5-4B | 19/20 | 34.1% | 34.9% | 34.5% | 20.0% |
| CoT | Qwen3-VL-4B | 20/20 | 43.2% | 43.2% | 43.2% | 20.0% |

| Closed-set prompt | Model | Valid responses | Item recall | Precision | Exact meal set |
|---|---|---:|---:|---:|---:|
| Baseline | InternVL3.5-4B | 20/20 | 77.3% | 75.6% | 65.0% |
| Baseline | Qwen3-VL-4B | 20/20 | 86.4% | 90.5% | 70.0% |
| CoT | InternVL3.5-4B | 19/20 | 72.7% | 76.2% | 60.0% |
| CoT | Qwen3-VL-4B | 20/20 | 86.4% | 88.4% | 70.0% |

All three image-nutrition conditions have completed. Results below use meals with valid four-nutrient totals from both models. Delta is InternVL minus Qwen3 absolute energy error; all values are kcal.

| Prompt | InternVL / Qwen3 valid | Paired n | InternVL MAE | Qwen3 MAE | Delta [95% CI] | InternVL better / worse / tied |
|---|---:|---:|---:|---:|---:|---:|
| Baseline | 20/20 / 20/20 | 20 | 177.5 | 152.4 | 25.1 [−14.8, 66.0] | 6 / 10 / 4 |
| CoT | 20/20 / 20/20 | 20 | 196.5 | 172.6 | 23.9 [−13.3, 60.8] | 5 / 10 / 5 |
| CoT + RAG | 19/20 / 19/20 | 18 | 228.7 | 227.6 | 1.1 [−41.2, 46.3] | 6 / 7 / 5 |

The 95% intervals resample paired meals, not the broader population. They are compatible with improvement or worsening, and do not control for model or preprocessing differences. The three rows use different valid subsets.

For the original text baseline, InternVL produced 50/50 numeric totals; **25/50 exactly match** the four numeric examples in the JSON schema. Qwen3 has 12/50 such matches. Exact equality is an output-sensitivity flag, not proof of copying intent; the prose-only no-example condition is still pending.

These small-sample descriptive results show different metric tradeoffs, not conclusive overall model superiority. Full paired comparisons will be produced after the remaining groups complete.
