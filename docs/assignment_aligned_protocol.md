# Assignment-aligned Food VQA protocol

Status: frozen before the new main runs. The earlier volume-estimation work is
an optional extension and is not part of the primary evidence matrix below.

## Research questions

1. How well do two off-the-shelf vision-language models recognise foods in the
   20 supplied meal images under open-ended and closed-set prompting?
2. When the correct food labels are supplied, how accurately do the models
   estimate meal energy, carbohydrate, protein, and fat?
3. On the 50 supplied free-text nutrition questions, do stepwise prompting and
   USDA FoodData Central retrieval improve the same four nutrient estimates?

## Frozen models

| Model | Parameters | Checkpoint revision | Training in this project |
|---|---:|---|---|
| Qwen2.5-VL-7B-Instruct | 7B | `cc594898137f460bfe9f0759e9844b3ce807cfb5` | None |
| Qwen3-VL-4B-Instruct | 4B | `ebb281ec70b05090aa6165b016eac8ec08e71b17` | None |

Both checkpoints are instruction-tuned VLMs below the assignment's 70B limit.
They run locally with fixed checkpoints and no fine-tuning, calibration, or
target-set adaptation.

## Main experiment matrix

| Input/task | Baseline | CoT | CoT + RAG |
|---|:---:|:---:|:---:|
| Image: open-ended recognition | yes | yes | not applicable |
| Image: closed-set recognition | yes | yes | not applicable |
| Image: nutrition with correct labels | yes | yes | yes |
| Free-text nutrition questions | yes | yes | yes |

RAG is restricted to nutritional estimation. Applying a nutrition database to
recognition would either be irrelevant or leak the answer vocabulary into the
open-ended condition. Closed-set recognition receives the complete category
list in every prompting condition, as required by that task.

### Prompt conditions

- **Baseline:** direct task instruction and a fixed JSON response contract.
- **CoT:** the same information plus an instruction to assess the problem in
  explicit ordered steps and return a short `reasoning_summary` with the JSON.
- **CoT + RAG:** the CoT prompt plus deterministic top-k records retrieved from
  the supplied USDA FDC subset. The model must cite the FDC IDs used. Retrieval
  uses only food text in the input or the supplied correct label; target
  nutrient totals are never used for retrieval.

All decoding is greedy (`do_sample=False`) with one generation per example.
The response schema, maximum tokens, image resolution, and model checkpoint are
held fixed within each task.

## Data and leakage controls

- Images: all 20 provided meal photographs; 44 labelled food instances.
- Text: all 50 provided free-text questions.
- Recognition vocabulary: the 35 unique labels in the supplied image workbook.
- Image nutrition: the prompt supplies the correct labels, but no target meal
  totals or measured weights.
- RAG corpus: `data/raw/FDC_USDA_subset.csv`; retrieval is deterministic and the
  retrieved records are saved in each request manifest.
- Primary targets: values in the supplied workbooks. A documented Meal13 data
  repair is reported only as a sensitivity analysis, never silently substituted.

## Metrics

Recognition is multi-label. The primary recognition accuracy is micro item
recall, `TP / number of ground-truth food instances`, after frozen lexical
normalisation and one-to-one matching. We also report micro precision, micro F1,
and exact meal-set accuracy so false positives and full-meal correctness remain
visible. Closed-set predictions outside the supplied vocabulary are invalid.

For energy (kcal), carbohydrate (g), protein (g), and fat (g), report:

- MAE: `mean(abs(prediction - target))`
- MAPE: `100 * mean(abs(prediction - target) / abs(target))`
- valid-response coverage

No zero target occurs in the current meal-level or question-level totals. If a
future target is zero, that row is excluded from MAPE and its count is reported.
Metrics are paired by example across models and prompt conditions. Bootstrap
95% confidence intervals over meals/questions and paired absolute-error
differences are secondary uncertainty summaries.

## Evidence priority

The complete assignment matrix is the primary result. Existing Qwen open-image
results are labelled as preliminary because they used an earlier prompt and do
not cover the frozen matrix. Public-dataset training, geometric calibration,
segmentation, and transferable volume estimation appear only after the main
results as optional follow-up work.

