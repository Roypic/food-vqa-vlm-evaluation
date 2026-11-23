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

The SmolVLM2 image-nutrition baseline has also completed. It produced valid numeric totals for 19/20 images and energy MAE of **336.0 kcal** on those 19. Qwen3 produced valid totals for 20/20 images; on the same 19 valid images, its energy MAE is **157.7 kcal**. The paired mean difference in absolute error (SmolVLM2 minus Qwen3) is **178.3 kcal**, bootstrap 95% interval **[115.3, 238.2]**; SmolVLM2 improved on 1 meal, worsened on 17, and tied on 1. The interval resamples these 19 meals, not the broader population, and model size and image preprocessing differ.
