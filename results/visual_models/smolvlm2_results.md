# smolvlm2_2_2b visual-model extension

Inference is local and without fine-tuning. The preprocessing, language backbone and architecture differ by model, so this is a system comparison. InternVL3.5-4B uses a Qwen3 language backbone; SmolVLM2 has fewer parameters than the Qwen models.

## Recognition

| Task | Condition | Coverage | Item recall | Precision | F1 | Exact meal set |
|---|---|---:|---:|---:|---:|---:|
| image_open | baseline | 90.0% | 27.3% | 30.8% | 28.9% | 15.0% |
| image_open | cot | 100.0% | 29.5% | 29.5% | 29.5% | 10.0% |
| image_closed | baseline | 80.0% | 63.6% | 10.0% | 17.3% | 5.0% |
| image_closed | cot | 85.0% | 65.9% | 9.4% | 16.5% | 5.0% |

## Nutrition

Each metric is MAE; coverage requires all four non-negative numeric totals. Numeric validity alone does not guarantee a meaningful estimate.

| Task | Condition | Coverage | Energy kcal | Carb g | Protein g | Fat g |
|---|---|---:|---:|---:|---:|---:|
| image_nutrition | baseline | 95.0% | 336.0 | 62.3 | 10.7 | 15.3 |
| image_nutrition | cot | 95.0% | 347.0 | 61.9 | 10.9 | 15.8 |
| image_nutrition | cot_rag | 85.0% | 345.0 | 64.9 | 9.7 | 17.1 |
| text_nutrition | baseline | 94.0% | 410.7 | 48.3 | 15.8 | 15.0 |
| text_nutrition | cot | 92.0% | 6412.8 | 1269.4 | 370.3 | 483.2 |
| text_nutrition | cot_rag | 100.0% | 390.8 | 45.4 | 15.1 | 14.3 |
| text_nutrition | baseline_noexample | 100.0% | 395.3 | 53.0 | 18.5 | 18.9 |
| text_nutrition | cot_rag_noexample | 92.0% | 309.8 | 35.4 | 16.0 | 15.5 |

## Text output sensitivity

Exact four-total equality flags are descriptive and do not establish intent.

| Condition | Exact original example (100,10,10,5) | All-zero totals | Valid numeric totals |
|---|---:|---:|---:|
| baseline | 47/50 | 0/50 | 47/50 |
| cot | 29/50 | 0/50 | 46/50 |
| cot_rag | 30/50 | 0/50 | 50/50 |
| baseline_noexample | 0/50 | 26/50 | 50/50 |
| cot_rag_noexample | 0/50 | 0/50 | 46/50 |

See `scored/metrics.json` for all groups and `scored/per_example.jsonl` for local paired analysis. Original and no-example prompts differ in formatting, and CoT + RAG changes both prompting and retrieval. Results are exploratory on 20 meals and 50 questions.

## Raw format and extreme values

The frozen evaluator extracts JSON objects from responses containing extra text. A stricter raw-format check requires the entire stripped response to be one parseable JSON object. A separate fenced-object count records responses consisting solely of a Markdown JSON code block, which fails the strict first-character requirement but can be mechanically unwrapped. Neither check by itself validates the schema or numbers.

| Task | Condition | Strict JSON object / responses | Fenced JSON object / responses | Extracted object / responses |
|---|---|---:|---:|---:|
| image_closed | baseline | 16/20 | 0/20 | 16/20 |
| image_closed | cot | 17/20 | 0/20 | 17/20 |
| image_nutrition | baseline | 19/20 | 0/20 | 20/20 |
| image_nutrition | cot | 19/20 | 0/20 | 20/20 |
| image_nutrition | cot_rag | 17/20 | 0/20 | 20/20 |
| image_open | baseline | 10/20 | 0/20 | 18/20 |
| image_open | cot | 20/20 | 0/20 | 20/20 |
| text_nutrition | baseline | 10/50 | 0/50 | 50/50 |
| text_nutrition | baseline_noexample | 50/50 | 0/50 | 50/50 |
| text_nutrition | cot | 0/50 | 0/50 | 50/50 |
| text_nutrition | cot_rag | 0/50 | 0/50 | 50/50 |
| text_nutrition | cot_rag_noexample | 46/50 | 0/50 | 50/50 |

| Nutrition task | Condition | Numerically valid n | Energy MAE | Median absolute error | Maximum absolute error |
|---|---|---:|---:|---:|---:|
| image_nutrition | baseline | 19 | 336.0 | 267.3 | 974.7 |
| image_nutrition | cot | 19 | 347.0 | 267.3 | 974.7 |
| image_nutrition | cot_rag | 17 | 345.0 | 267.3 | 974.7 |
| text_nutrition | baseline | 47 | 410.7 | 395.0 | 1032.0 |
| text_nutrition | baseline_noexample | 50 | 395.3 | 383.5 | 898.0 |
| text_nutrition | cot | 46 | 6412.8 | 401.5 | 234617.0 |
| text_nutrition | cot_rag | 50 | 390.8 | 382.0 | 844.0 |
| text_nutrition | cot_rag_noexample | 46 | 309.8 | 274.0 | 998.0 |

The original text CoT MAE is heavily influenced by a retained extreme prediction; the median and maximum above show the distribution. Per-example data remain in the private workspace.
