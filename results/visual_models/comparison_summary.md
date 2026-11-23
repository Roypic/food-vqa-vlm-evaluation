# Five-model visual and nutrition comparison

Models use their native image processors and different parameter counts. InternVL3.5 has a Qwen3 language backbone. The provided dataset contains 20 images and 50 text questions; this is an exploratory system comparison, not a claim of general superiority. No model was fine-tuned on this dataset.

## Recognition

Each cell is item recall / precision / exact meal-set accuracy, with schema-list coverage. Invalid recognition outputs are treated as empty predictions by the frozen evaluator.

| Model | Open baseline | Open CoT | Closed baseline | Closed CoT |
|---|---:|---:|---:|---:|
| Qwen2.5-VL-7B | 31.8% / 30.4% / 10.0% (100% cov.) | 34.1% / 34.1% / 10.0% (100% cov.) | 72.7% / 71.1% / 45.0% (100% cov.) | 77.3% / 77.3% / 60.0% (100% cov.) |
| Qwen3-VL-4B | 38.6% / 37.8% / 15.0% (100% cov.) | 43.2% / 43.2% / 20.0% (100% cov.) | 86.4% / 90.5% / 70.0% (100% cov.) | 86.4% / 88.4% / 70.0% (100% cov.) |
| Phi-4 multimodal | 31.8% / 31.8% / 15.0% (100% cov.) | 27.3% / 38.7% / 15.0% (85% cov.) | 56.8% / 58.1% / 35.0% (100% cov.) | 54.5% / 60.0% / 30.0% (100% cov.) |
| SmolVLM2-2.2B | 27.3% / 30.8% / 15.0% (90% cov.) | 29.5% / 29.5% / 10.0% (100% cov.) | 63.6% / 10.0% / 5.0% (80% cov.) | 65.9% / 9.4% / 5.0% (85% cov.) |
| InternVL3.5-4B | 34.1% / 34.1% / 25.0% (100% cov.) | 34.1% / 34.9% / 20.0% (95% cov.) | 77.3% / 75.6% / 65.0% (100% cov.) | 72.7% / 76.2% / 60.0% (95% cov.) |

## Oracle-label image nutrition

Each cell is energy MAE (kcal) and coverage. MAEs can use different valid subsets; use the paired files for matched-example comparisons and uncertainty.

| Model | Baseline | CoT | CoT + RAG |
|---|---:|---:|---:|
| Qwen2.5-VL-7B | 170.9 (100% cov.) | 163.8 (100% cov.) | 171.3 (100% cov.) |
| Qwen3-VL-4B | 152.4 (100% cov.) | 172.6 (100% cov.) | 233.6 (95% cov.) |
| Phi-4 multimodal | 223.7 (100% cov.) | 271.8 (100% cov.) | 234.5 (95% cov.) |
| SmolVLM2-2.2B | 336.0 (95% cov.) | 347.0 (95% cov.) | 345.0 (85% cov.) |
| InternVL3.5-4B | 177.5 (100% cov.) | 196.5 (100% cov.) | 223.7 (95% cov.) |

## Text nutrition and schema sensitivity

The original numeric-example baseline is format-sensitive. For no-example conditions, the JSON example is replaced by a prose output contract. Values shown are energy MAE (kcal) and numeric coverage; zeros may satisfy the numeric contract.

| Model | Original baseline | Original CoT + RAG | No-example baseline | No-example CoT + RAG |
|---|---:|---:|---:|---:|
| Qwen2.5-VL-7B | 213.8 (100% cov.) | 214.3 (98% cov.) | 409.3 (100% cov.) | 278.3 (90% cov.) |
| Qwen3-VL-4B | 172.8 (100% cov.) | 134.9 (98% cov.) | 508.8 (100% cov.) | 111.9 (98% cov.) |
| Phi-4 multimodal | 193.3 (100% cov.) | 238.6 (98% cov.) | not run | not run |
| SmolVLM2-2.2B | 410.7 (94% cov.) | 390.8 (100% cov.) | 395.3 (100% cov.) | 309.8 (92% cov.) |
| InternVL3.5-4B | 312.2 (100% cov.) | 176.1 (96% cov.) | 243.9 (100% cov.) | 186.2 (96% cov.) |

Read `smolvlm2_results.md` and `internvl35_results.md` for full nutrient tables, exact-example and zero-output flags, and strict raw-format compliance. `smolvlm2_paired_vs_qwen3.json` and `internvl35_paired_vs_qwen3.json` provide paired model differences with bootstrap intervals on common valid examples. Raw per-example outputs remain local.
