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
| Phi-4 smoke test | Running/queued | Slurm `21809931` |
| Phi-4 full matrix | Dependency queued | Slurm `21809932` |
| Phi-4 scoring and deck refresh | Dependency queued | Slurm `21809933` |

The previous Phi-4 smoke run (`21112395`) failed before model loading because the isolated Slurm environment could not import `_cffi_backend`. The dependency was installed into the scratch environment and the chain was resubmitted. This is an execution-environment failure, not a model result.

