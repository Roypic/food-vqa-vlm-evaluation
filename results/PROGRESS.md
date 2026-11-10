# Progress ledger

Updated 10 November 2026.

| Stage | State | Record |
|---|---|---|
| Freeze assignment-aligned protocol | Complete | 10 groups per model, 290 requests |
| Qwen2.5-VL-7B inference | Complete | 290/290 generations |
| Qwen3-VL-4B inference | Complete | 290/290 generations |
| Primary evaluation | Complete | 580 generations; 20 scored groups |
| English results + proposal deck | Complete locally | excluded from GitHub because it embeds supplied images |
| Phi-4 multimodal download | Complete | frozen revision `93f923e...` |
| Phi-4 smoke test | Running/queued | Slurm `21834265` |
| Phi-4 full matrix | Dependency queued | Slurm `21834266` |
| Phi-4 scoring and deck refresh | Dependency queued | Slurm `21834267` |

The first Phi-4 smoke run (`21112395`) failed before model loading because the isolated Slurm environment could not import `_cffi_backend`. The second (`21809931`) exposed an incompatible mix of global `transformers 4.57.6` and pinned `peft 0.13.2`. The current run uses the model's official `transformers 4.48.2`, `tokenizers 0.21.4`, `accelerate 1.3.0`, and `peft 0.13.2` combination in scratch. These are execution-environment failures, not model results.

