# InternVL3.5-4B preliminary recognition results

These are the completed recognition groups on the same 20 meal images and frozen prompts as Qwen3-VL-4B. Closed CoT and other nutrition groups are still running. No fine-tuning was used. The models use different visual pipelines; InternVL3.5 also uses a Qwen3 language backbone. Validity requires a `food_labels` list; invalid outputs are scored as empty predictions by the frozen evaluator.

| Prompt | Model | Valid responses | Item recall | Micro precision | Micro F1 | Exact meal set |
|---|---|---:|---:|---:|---:|---:|
| Baseline | InternVL3.5-4B | 20/20 | 34.1% | 34.1% | 34.1% | 25.0% |
| Baseline | Qwen3-VL-4B | 20/20 | 38.6% | 37.8% | 38.2% | 15.0% |
| CoT | InternVL3.5-4B | 19/20 | 34.1% | 34.9% | 34.5% | 20.0% |
| CoT | Qwen3-VL-4B | 20/20 | 43.2% | 43.2% | 43.2% | 20.0% |

Closed-set baseline: InternVL3.5 has 20/20 valid outputs, 77.3% item recall, 75.6% precision and 65.0% exact-meal accuracy; Qwen3 has 20/20 valid, 86.4%, 90.5%, and 70.0%, respectively.

For image-nutrition baseline, both models have valid outputs on all 20 meals. Their paired energy MAEs are **177.5 kcal** (InternVL) and **152.4 kcal** (Qwen3). The paired absolute-error difference, InternVL minus Qwen3, is **25.1 kcal**, with an example-bootstrap 95% interval **[−14.8, 66.0]**. This interval is compatible with improvement or worsening in the sampled population and does not control for model or preprocessing differences.

These small-sample descriptive results show different metric tradeoffs, not conclusive overall model superiority. Full paired comparisons will be produced after the remaining groups complete.
