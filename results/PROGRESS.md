# Progress ledger

Updated 23 November 2026.

| Stage | State | Record |
|---|---|---|
| Freeze assignment-aligned protocol | Complete | 10 groups per model, 290 requests |
| Qwen2.5-VL-7B inference | Complete | 290/290 generations |
| Qwen3-VL-4B inference | Complete | 290/290 generations |
| Primary evaluation | Complete | 580 generations; 20 scored groups |
| English results + proposal deck | Complete locally | excluded from GitHub because it embeds supplied images |
| Phi-4 multimodal download | Complete | frozen revision `93f923e...` |
| Phi-4 smoke test | Complete | Slurm `21834265` |
| Phi-4 full matrix | Complete | Slurm `21834266`; 290 generations across 10 groups |
| Phi-4 scoring and deck refresh | Complete | Slurm `21834267`; 870 total generations across 30 groups |
| Error case, portion and RAG arithmetic analysis | Complete first pass | aggregate findings in `results/error_analysis/` |
| Generic CoT and least-to-most | Complete | 360 new outputs across the two primary models |
| Altered numeric-example diagnostic | Complete | both Qwen models returned the altered example totals on 50/50 questions |
| Neutral-total-schema control | Complete | three text conditions × 50 questions × two models; Slurm `23239664` |
| No-example schema control | Running | text baseline and CoT + RAG × 50 questions × two models; Slurm `23240137` |

The first Phi-4 smoke run (`21112395`) failed before model loading because the isolated Slurm environment could not import `_cffi_backend`. The second (`21809931`) exposed an incompatible mix of global `transformers 4.57.6` and pinned `peft 0.13.2`. The current run uses the model's official `transformers 4.48.2`, `tokenizers 0.21.4`, `accelerate 1.3.0`, and `peft 0.13.2` combination in scratch. These are execution-environment failures, not model results.

