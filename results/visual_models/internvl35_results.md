# internvl35_4b visual-model extension

Inference is local and without fine-tuning. The preprocessing, language backbone and architecture differ by model, so this is a system comparison. InternVL3.5-4B uses a Qwen3 language backbone; SmolVLM2 has fewer parameters than the Qwen models.

## Recognition

| Task | Condition | Coverage | Item recall | Precision | F1 | Exact meal set |
|---|---|---:|---:|---:|---:|---:|
| image_open | baseline | 100.0% | 34.1% | 34.1% | 34.1% | 25.0% |
| image_open | cot | 95.0% | 34.1% | 34.9% | 34.5% | 20.0% |
| image_closed | baseline | 100.0% | 77.3% | 75.6% | 76.4% | 65.0% |
| image_closed | cot | 95.0% | 72.7% | 76.2% | 74.4% | 60.0% |

## Nutrition

Each metric is MAE; coverage requires all four non-negative numeric totals. Numeric validity alone does not guarantee a meaningful estimate.

| Task | Condition | Coverage | Energy kcal | Carb g | Protein g | Fat g |
|---|---|---:|---:|---:|---:|---:|
| image_nutrition | baseline | 100.0% | 177.5 | 43.2 | 7.8 | 11.0 |
| image_nutrition | cot | 100.0% | 196.5 | 46.3 | 7.0 | 11.6 |
| image_nutrition | cot_rag | 95.0% | 223.7 | 50.7 | 8.4 | 10.2 |
| text_nutrition | baseline | 100.0% | 312.2 | 38.1 | 12.3 | 12.2 |
| text_nutrition | cot | 100.0% | 268.8 | 32.6 | 10.5 | 10.2 |
| text_nutrition | cot_rag | 96.0% | 176.1 | 21.4 | 9.7 | 9.6 |
| text_nutrition | baseline_noexample | 100.0% | 243.9 | 33.2 | 12.2 | 11.2 |
| text_nutrition | cot_rag_noexample | 96.0% | 186.2 | 19.1 | 10.9 | 12.7 |

## Text output sensitivity

Exact four-total equality flags are descriptive and do not establish intent.

| Condition | Exact original example (100,10,10,5) | All-zero totals | Valid numeric totals |
|---|---:|---:|---:|
| baseline | 25/50 | 0/50 | 50/50 |
| cot | 2/50 | 0/50 | 50/50 |
| cot_rag | 0/50 | 0/50 | 48/50 |
| baseline_noexample | 0/50 | 10/50 | 50/50 |
| cot_rag_noexample | 0/50 | 0/50 | 48/50 |

See `scored/metrics.json` for all groups and `scored/per_example.jsonl` for local paired analysis. Original and no-example prompts differ in formatting, and CoT + RAG changes both prompting and retrieval. Results are exploratory on 20 meals and 50 questions.

## Raw format and extreme values

The frozen evaluator extracts JSON objects from responses containing extra text. A stricter raw-format check requires the entire stripped response to be one parseable JSON object. A separate fenced-object count records responses consisting solely of a Markdown JSON code block, which fails the strict first-character requirement but can be mechanically unwrapped. Neither check by itself validates the schema or numbers.

| Task | Condition | Strict JSON object / responses | Fenced JSON object / responses | Extracted object / responses |
|---|---|---:|---:|---:|
| image_closed | baseline | 20/20 | 0/20 | 20/20 |
| image_closed | cot | 19/20 | 0/20 | 19/20 |
| image_nutrition | baseline | 0/20 | 20/20 | 20/20 |
| image_nutrition | cot | 15/20 | 1/20 | 20/20 |
| image_nutrition | cot_rag | 1/20 | 18/20 | 20/20 |
| image_open | baseline | 20/20 | 0/20 | 20/20 |
| image_open | cot | 19/20 | 0/20 | 19/20 |
| text_nutrition | baseline | 50/50 | 0/50 | 50/50 |
| text_nutrition | baseline_noexample | 0/50 | 50/50 | 50/50 |
| text_nutrition | cot | 50/50 | 0/50 | 50/50 |
| text_nutrition | cot_rag | 48/50 | 0/50 | 50/50 |
| text_nutrition | cot_rag_noexample | 42/50 | 6/50 | 50/50 |

| Nutrition task | Condition | Numerically valid n | Energy MAE | Median absolute error | Maximum absolute error |
|---|---|---:|---:|---:|---:|
| image_nutrition | baseline | 20 | 177.5 | 123.8 | 763.5 |
| image_nutrition | cot | 20 | 196.5 | 102.0 | 813.5 |
| image_nutrition | cot_rag | 19 | 223.7 | 134.9 | 860.5 |
| text_nutrition | baseline | 50 | 312.2 | 276.0 | 1032.0 |
| text_nutrition | baseline_noexample | 50 | 243.9 | 200.0 | 740.0 |
| text_nutrition | cot | 50 | 268.8 | 242.0 | 882.0 |
| text_nutrition | cot_rag | 48 | 176.1 | 158.4 | 562.0 |
| text_nutrition | cot_rag_noexample | 48 | 186.2 | 103.2 | 1783.5 |
