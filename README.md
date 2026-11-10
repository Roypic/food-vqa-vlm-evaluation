# Food VQA: zero-shot VLM evaluation with CoT and RAG

This repository evaluates off-the-shelf vision-language models below 70B on food recognition and nutrition estimation, without fine-tuning. It implements the assignment's primary experiment: two comparable VLMs, open-ended and closed-set image recognition, image nutrition estimation with correct food labels, free-text nutrition questions, and baseline/CoT/CoT + RAG prompting.

## Current status

| Work package | Status | Evidence |
|---|---|---|
| Dataset audit and frozen protocol | Complete | 20 meal images, 44 food instances, 35 labels, 50 text questions |
| Qwen2.5-VL-7B evaluation | Complete | 290 generations across 10 task/prompt groups |
| Qwen3-VL-4B evaluation | Complete | 290 generations across 10 task/prompt groups |
| Primary scoring | Complete | 580 generations, 20 groups, paired valid-example checks |
| Phi-4-multimodal-5.6B extension | Running | dependency fixed; smoke `21809931`, matrix `21809932`, scoring `21809933` |
| Transferable volume/portion pipeline | Additional investigation | public-data training and held-out project-data testing remain separate from the required baseline |

Last updated: **10 November 2026**.

## Experiment design

| Input/task | Baseline | CoT | CoT + RAG |
|---|:---:|:---:|:---:|
| Open-ended image recognition | ✓ | ✓ | — |
| Closed-set image recognition | ✓ | ✓ | — |
| Image nutrition, correct food label supplied | ✓ | ✓ | ✓ |
| Free-text nutrition questions | ✓ | ✓ | ✓ |

RAG retrieves candidate per-100-g records from the supplied USDA FoodData Central subset. For image nutrition, the food identity is provided and the model must infer portion mass from the image. This separation tests whether retrieval helps nutrient grounding after recognition is controlled.

The primary models are `Qwen/Qwen2.5-VL-7B-Instruct` and `Qwen/Qwen3-VL-4B-Instruct`. The additional model-family comparison uses `microsoft/Phi-4-multimodal-instruct` at frozen revision `93f923e1a7727d1c4f446756212d9d3e8fcc5d81`.

## Main results

### Food recognition

Item accuracy is micro item recall. Exact-set accuracy requires the complete meal label set with no extra foods.

| Task | Prompt | Qwen2.5-VL-7B item / exact | Qwen3-VL-4B item / exact |
|---|---|---:|---:|
| Open-ended | Baseline | 31.8% / 10.0% | 38.6% / 15.0% |
| Open-ended | CoT | 34.1% / 10.0% | 43.2% / 20.0% |
| Closed-set | Baseline | 72.7% / 45.0% | **86.4% / 70.0%** |
| Closed-set | CoT | 77.3% / 60.0% | **86.4% / 70.0%** |

The category list produced the largest recognition gain. Qwen3 was stronger in all four recognition comparisons.

### Image nutrition with correct food labels

Each nutrient cell is `MAE / MAPE`; coverage is the share of responses with four valid numeric totals.

| Model | Prompt | Coverage | Energy (kcal) | Carb (g) | Protein (g) | Fat (g) |
|---|---|---:|---:|---:|---:|---:|
| Qwen2.5-VL-7B | Baseline | 100% | 170.9 / 35.3% | 44.9 / 36.0% | **6.0 / 44.9%** | 11.6 / 102.5% |
| Qwen2.5-VL-7B | CoT | 100% | 163.8 / 31.3% | 42.5 / 34.4% | 6.3 / 50.2% | 11.7 / 86.9% |
| Qwen2.5-VL-7B | CoT + RAG | 100% | 171.3 / 37.0% | 49.0 / 67.6% | 8.6 / 54.4% | 11.7 / 128.2% |
| Qwen3-VL-4B | Baseline | 100% | **152.4 / 33.2%** | **41.0 / 38.5%** | 6.3 / 48.8% | 11.6 / 98.1% |
| Qwen3-VL-4B | CoT | 100% | 172.6 / 38.7% | 41.7 / 42.2% | 6.2 / 52.5% | **11.2 / 109.9%** |
| Qwen3-VL-4B | CoT + RAG | 95% | 233.6 / 51.4% | 49.7 / 54.4% | 7.8 / 44.2% | 11.7 / 88.7% |

RAG did not improve image nutrition. Once food identity is known, uncertainty in visible portion mass remains the main bottleneck.

### Free-text nutrition questions

| Model | Prompt | Coverage | Energy (kcal) | Carb (g) | Protein (g) | Fat (g) |
|---|---|---:|---:|---:|---:|---:|
| Qwen2.5-VL-7B | Baseline | 100% | 213.8 / 41.1% | 28.0 / 46.5% | 8.6 / 64.8% | 10.1 / 95.9% |
| Qwen2.5-VL-7B | CoT | 98% | 175.9 / 39.1% | 24.0 / 40.0% | 9.1 / 77.1% | 9.2 / 97.4% |
| Qwen2.5-VL-7B | CoT + RAG | 98% | 214.3 / 43.3% | 23.0 / 39.9% | 12.2 / 57.8% | 9.0 / 74.3% |
| Qwen3-VL-4B | Baseline | 100% | 172.8 / 34.8% | 21.5 / 38.0% | 7.8 / 69.9% | 9.9 / 95.8% |
| Qwen3-VL-4B | CoT | 100% | 153.2 / 31.0% | 16.9 / 29.8% | **6.9 / 57.3%** | 8.7 / 49.9% |
| Qwen3-VL-4B | CoT + RAG | 98% | **134.9 / 26.5%** | **14.0 / 24.1%** | 7.3 / 32.8% | **6.7 / 59.8%** |

Qwen3 benefited consistently from CoT on text questions. CoT + RAG gave its lowest energy, carbohydrate, and fat MAE. The effect was model-dependent: Qwen2.5 did not gain the same energy improvement.

Three of 580 responses violated the numeric JSON contract. They remain invalid and reduce coverage; no result was manually repaired. See [`results/metrics.json`](results/metrics.json) for bootstrap intervals and paired comparisons. Per-example predictions remain in the private project workspace because they contain derived labels and targets from the supplied dataset.

## Reproduce the experiment

Use Python 3.10+ and install the lightweight data/scoring dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Install GPU dependencies only on the inference machine:

```bash
pip install -r requirements-gpu.txt
```

Place the supplied files under `data/raw/` as described in [`DATA.md`](DATA.md), then freeze the 290-request matrix:

```bash
python src/build_assignment_manifest.py \
  --data-root data/raw \
  --out-dir results/requests
```

Run one Qwen task/prompt group:

```bash
python src/run_assignment_vlm.py \
  --model Qwen/Qwen3-VL-4B-Instruct \
  --model-id qwen3_vl_4b \
  --input results/requests/image_closed__baseline.jsonl \
  --output results/predictions/qwen3_vl_4b/image_closed__baseline.jsonl
```

Score every model directory under `results/predictions/`:

```bash
python src/evaluate_assignment_vlm.py \
  --data-root data/raw \
  --predictions results/predictions \
  --out-dir results/scored
```

Slurm templates are in [`slurm/`](slurm/). Set the paths and cluster resource directives for your environment before submission.

## Repository layout

```text
.
├── DATA.md                         # expected private dataset layout
├── docs/assignment_aligned_protocol.md # frozen tasks, prompts, and metrics
├── results/                        # curated aggregate and per-example results
├── slurm/                          # configurable cluster templates
└── src/
    ├── build_assignment_manifest.py
    ├── run_assignment_vlm.py
    ├── run_assignment_phi4.py
    ├── evaluate_assignment_vlm.py
    └── summarize_phi4_extension.py
```

## Data and scope

The supplied archive is an evaluation set and is not redistributed here. Raw images, workbooks, the FDC subset, model weights, caches, raw generations, cluster logs, and the generated slide deck are excluded. The slide deck embeds supplied meal images, so it remains a local project artifact pending confirmation of redistribution rights.

The volume/portion work is an additional study: learn transferable geometry or portion cues from public datasets, then test once on the held-out project dataset. It complements the zero-shot VLM experiment and does not replace it.

No code license has been assigned yet.

