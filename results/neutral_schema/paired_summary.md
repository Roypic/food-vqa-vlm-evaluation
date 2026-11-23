# Prompt extension: paired comparisons

Delta is alternative minus baseline; neutral conditions use baseline_neutral and cot_rag_noexample uses baseline_noexample as reference. Negative is better for absolute error, positive is better for recognition. Bootstrap 95% intervals resample matched meals/questions.

| Model | Task | Condition | Metric | Paired n | Delta | 95% bootstrap CI | Improved / worse / tied |
|---|---|---|---|---:|---:|---:|---:|
| qwen2_5_vl_7b | text_nutrition | cot | energy_kcal_absolute_error | 49 | -41.80 | [-92.29, 6.00] | 23 / 9 / 17 |
| qwen2_5_vl_7b | text_nutrition | cot | carb_g_absolute_error | 49 | -4.49 | [-8.97, -0.30] | 22 / 12 / 15 |
| qwen2_5_vl_7b | text_nutrition | cot | protein_g_absolute_error | 49 | 0.31 | [-2.15, 3.02] | 14 / 11 / 24 |
| qwen2_5_vl_7b | text_nutrition | cot | fat_g_absolute_error | 49 | -1.13 | [-2.65, 0.37] | 17 / 9 / 23 |
| qwen2_5_vl_7b | text_nutrition | cot_rag | energy_kcal_absolute_error | 49 | 1.17 | [-68.49, 82.59] | 26 / 16 / 7 |
| qwen2_5_vl_7b | text_nutrition | cot_rag | carb_g_absolute_error | 49 | -5.16 | [-12.32, 1.80] | 21 / 23 / 5 |
| qwen2_5_vl_7b | text_nutrition | cot_rag | protein_g_absolute_error | 49 | 3.66 | [-0.27, 8.13] | 21 / 21 / 7 |
| qwen2_5_vl_7b | text_nutrition | cot_rag | fat_g_absolute_error | 49 | -0.97 | [-4.78, 4.64] | 31 / 12 / 6 |
| qwen2_5_vl_7b | text_nutrition | cot_neutral | energy_kcal_absolute_error | 0 | — | — | 0 / 0 / 0 |
| qwen2_5_vl_7b | text_nutrition | cot_neutral | carb_g_absolute_error | 0 | — | — | 0 / 0 / 0 |
| qwen2_5_vl_7b | text_nutrition | cot_neutral | protein_g_absolute_error | 0 | — | — | 0 / 0 / 0 |
| qwen2_5_vl_7b | text_nutrition | cot_neutral | fat_g_absolute_error | 0 | — | — | 0 / 0 / 0 |
| qwen2_5_vl_7b | text_nutrition | cot_rag_neutral | energy_kcal_absolute_error | 0 | — | — | 0 / 0 / 0 |
| qwen2_5_vl_7b | text_nutrition | cot_rag_neutral | carb_g_absolute_error | 0 | — | — | 0 / 0 / 0 |
| qwen2_5_vl_7b | text_nutrition | cot_rag_neutral | protein_g_absolute_error | 0 | — | — | 0 / 0 / 0 |
| qwen2_5_vl_7b | text_nutrition | cot_rag_neutral | fat_g_absolute_error | 0 | — | — | 0 / 0 / 0 |
| qwen3_vl_4b | text_nutrition | cot | energy_kcal_absolute_error | 50 | -19.64 | [-45.08, 1.64] | 19 / 15 / 16 |
| qwen3_vl_4b | text_nutrition | cot | carb_g_absolute_error | 50 | -4.59 | [-8.16, -1.67] | 21 / 7 / 22 |
| qwen3_vl_4b | text_nutrition | cot | protein_g_absolute_error | 50 | -0.90 | [-2.45, 0.27] | 13 / 9 / 28 |
| qwen3_vl_4b | text_nutrition | cot | fat_g_absolute_error | 50 | -1.21 | [-2.46, -0.04] | 22 / 12 / 16 |
| qwen3_vl_4b | text_nutrition | cot_rag | energy_kcal_absolute_error | 49 | -40.05 | [-85.35, 0.49] | 23 / 23 / 3 |
| qwen3_vl_4b | text_nutrition | cot_rag | carb_g_absolute_error | 49 | -7.56 | [-13.34, -2.33] | 28 / 18 / 3 |
| qwen3_vl_4b | text_nutrition | cot_rag | protein_g_absolute_error | 49 | -0.68 | [-3.03, 1.61] | 26 / 18 / 5 |
| qwen3_vl_4b | text_nutrition | cot_rag | fat_g_absolute_error | 49 | -3.37 | [-5.18, -1.50] | 31 / 13 / 5 |
| qwen3_vl_4b | text_nutrition | cot_neutral | energy_kcal_absolute_error | 50 | -21.56 | [-53.52, 7.08] | 20 / 14 / 16 |
| qwen3_vl_4b | text_nutrition | cot_neutral | carb_g_absolute_error | 50 | -1.60 | [-6.12, 2.25] | 18 / 21 / 11 |
| qwen3_vl_4b | text_nutrition | cot_neutral | protein_g_absolute_error | 50 | -1.08 | [-2.54, 0.28] | 22 / 18 / 10 |
| qwen3_vl_4b | text_nutrition | cot_neutral | fat_g_absolute_error | 50 | 0.03 | [-1.66, 1.66] | 19 / 25 / 6 |
| qwen3_vl_4b | text_nutrition | cot_rag_neutral | energy_kcal_absolute_error | 50 | -45.09 | [-81.27, -9.74] | 28 / 21 / 1 |
| qwen3_vl_4b | text_nutrition | cot_rag_neutral | carb_g_absolute_error | 50 | -4.39 | [-9.85, 0.52] | 24 / 25 / 1 |
| qwen3_vl_4b | text_nutrition | cot_rag_neutral | protein_g_absolute_error | 50 | 0.09 | [-2.09, 2.25] | 28 / 22 / 0 |
| qwen3_vl_4b | text_nutrition | cot_rag_neutral | fat_g_absolute_error | 50 | -2.86 | [-5.34, -0.42] | 31 / 19 / 0 |
