# Assignment-aligned VLM results

The frozen run completed 580 generations: two models, 20 image examples, 50
text questions, and the task/prompt matrix in
`docs/assignment_aligned_protocol.md`. All 20 Slurm array tasks completed.

## Food recognition

Item accuracy is micro item recall. Exact-set accuracy requires every food in a
meal, and no extra food, to match after the frozen lexical normalisation.

| Task | Prompt | Qwen2.5-VL-7B item / exact | Qwen3-VL-4B item / exact |
|---|---|---:|---:|
| Open-ended | Baseline | 31.8% / 10.0% | 38.6% / 15.0% |
| Open-ended | CoT | 34.1% / 10.0% | 43.2% / 20.0% |
| Closed-set | Baseline | 72.7% / 45.0% | 86.4% / 70.0% |
| Closed-set | CoT | 77.3% / 60.0% | 86.4% / 70.0% |

The category list produced the largest recognition gain. Qwen3 was stronger in
all four recognition comparisons. CoT improved open-ended item accuracy for
both models and improved Qwen2.5 closed-set accuracy; Qwen3 closed-set item
accuracy was unchanged.

## Image nutrition with correct labels

Each cell is `MAE / MAPE`; primary targets are the supplied workbook totals.

| Model | Prompt | Coverage | Energy (kcal) | Carb (g) | Protein (g) | Fat (g) |
|---|---|---:|---:|---:|---:|---:|
| Qwen2.5-VL-7B | Baseline | 100% | 170.9 / 35.3% | 44.9 / 36.0% | 6.0 / 44.9% | 11.6 / 102.5% |
| Qwen2.5-VL-7B | CoT | 100% | 163.8 / 31.3% | 42.5 / 34.4% | 6.3 / 50.2% | 11.7 / 86.9% |
| Qwen2.5-VL-7B | CoT + RAG | 100% | 171.3 / 37.0% | 49.0 / 67.6% | 8.6 / 54.4% | 11.7 / 128.2% |
| Qwen3-VL-4B | Baseline | 100% | **152.4 / 33.2%** | **41.0 / 38.5%** | 6.3 / 48.8% | 11.6 / 98.1% |
| Qwen3-VL-4B | CoT | 100% | 172.6 / 38.7% | 41.7 / 42.2% | **6.2 / 52.5%** | **11.2 / 109.9%** |
| Qwen3-VL-4B | CoT + RAG | 95% | 233.6 / 51.4% | 49.7 / 54.4% | 7.8 / 44.2% | 11.7 / 88.7% |

RAG did not improve the image task. The correct food name and per-100-g record
do not resolve the dominant uncertainty in portion mass from a single image.
Qwen3 baseline had the lowest energy MAE. Qwen2.5 CoT improved its own energy
and carbohydrate errors but not protein or fat MAE.

## Free-text nutrition questions

Each cell is `MAE / MAPE`.

| Model | Prompt | Coverage | Energy (kcal) | Carb (g) | Protein (g) | Fat (g) |
|---|---|---:|---:|---:|---:|---:|
| Qwen2.5-VL-7B | Baseline | 100% | 213.8 / 41.1% | 28.0 / 46.5% | **8.6 / 64.8%** | 10.1 / 95.9% |
| Qwen2.5-VL-7B | CoT | 98% | **175.9 / 39.1%** | 24.0 / 40.0% | 9.1 / 77.1% | 9.2 / 97.4% |
| Qwen2.5-VL-7B | CoT + RAG | 98% | 214.3 / 43.3% | **23.0 / 39.9%** | 12.2 / 57.8% | **9.0 / 74.3%** |
| Qwen3-VL-4B | Baseline | 100% | 172.8 / 34.8% | 21.5 / 38.0% | 7.8 / 69.9% | 9.9 / 95.8% |
| Qwen3-VL-4B | CoT | 100% | 153.2 / 31.0% | 16.9 / 29.8% | **6.9 / 57.3%** | 8.7 / 49.9% |
| Qwen3-VL-4B | CoT + RAG | 98% | **134.9 / 26.5%** | **14.0 / 24.1%** | 7.3 / 32.8% | **6.7 / 59.8%** |

Qwen3 benefited consistently from CoT on the text questions. Adding RAG gave
its lowest energy, carbohydrate, and fat MAE, while protein MAE was slightly
lower with CoT alone. Qwen2.5 did not show the same RAG energy benefit, so the
effect of grounding is model-dependent.

## Coverage and paired comparison

Three responses violated the numeric JSON contract by emitting arithmetic
expressions or a comment. They remain unscored and reduce coverage rather than
being manually repaired. Prompt comparisons are also recomputed on shared valid
examples: 20/20 and 48/50 examples for Qwen2.5 image/text nutrition, and 19/20
and 49/50 for Qwen3. The common-example conclusions agree with the full
coverage-aware tables. Per-group bootstrap intervals, common-example metrics,
and per-example predictions are in `scored/metrics.json` and
`scored/per_example.jsonl`.

