# Phi-4 multimodal extension results

`microsoft/Phi-4-multimodal-instruct` (5.6B) was evaluated without fine-tuning on the same frozen 290 requests.

## Food recognition

| Task | Prompt | Item accuracy | Exact meal-set accuracy |
|---|---|---:|---:|
| Open-ended | BASELINE | 31.8% | 15.0% |
| Open-ended | COT | 27.3% | 15.0% |
| Closed-set | BASELINE | 56.8% | 35.0% |
| Closed-set | COT | 54.5% | 30.0% |

## Image nutrition with correct labels

Each nutrient cell is `MAE / MAPE`.

| Prompt | Coverage | Energy (kcal) | Carb (g) | Protein (g) | Fat (g) |
|---|---:|---:|---:|---:|---:|
| BASELINE | 100.0% | 223.7 / 40.4% | 45.3 / 45.4% | 6.7 / 57.2% | 12.3 / 118.9% |
| COT | 100.0% | 271.8 / 52.8% | 53.8 / 62.1% | 8.7 / 52.5% | 12.9 / 87.2% |
| COT + RAG | 95.0% | 234.5 / 53.0% | 54.9 / 83.4% | 9.1 / 65.3% | 13.2 / 122.5% |

## Free-text nutrition

Each nutrient cell is `MAE / MAPE`.

| Prompt | Coverage | Energy (kcal) | Carb (g) | Protein (g) | Fat (g) |
|---|---:|---:|---:|---:|---:|
| BASELINE | 100.0% | 193.3 / 37.1% | 19.1 / 34.1% | 11.3 / 65.6% | 7.7 / 67.1% |
| COT | 90.0% | 235.2 / 46.2% | 28.1 / 46.3% | 9.0 / 60.4% | 9.8 / 74.2% |
| COT + RAG | 98.0% | 238.6 / 48.0% | 32.8 / 56.8% | 10.2 / 52.2% | 12.2 / 62.7% |

The primary two-model results remain unchanged. This file is an additional model-family comparison.
