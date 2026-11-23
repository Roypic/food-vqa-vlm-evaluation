# Visual-model extension, 23 November 2026

Purpose: test independent vision-language families against the unchanged Food VQA evaluation after completing the primary assignment and error analysis. These are additional models, not a replacement for the primary two-model assignment. They are evaluated without fine-tuning and with deterministic decoding.

- SmolVLM2-2.2B-Instruct (`HuggingFaceTB/SmolVLM2-2.2B-Instruct`, revision `be92141c8d0ceb98596a923c308ac2bbb4a7c466`) is a compact SigLIP/Idefics-family VLM. Its smaller parameter count is a limitation for direct model ranking.
- InternVL3.5-4B (`OpenGVLab/InternVL3_5-4B`, revision `481f6e32467eab4e922ccd7fd6cf420441a62331`) provides a second vision-centered architecture at a size closer to Qwen3-VL-4B. Its configuration identifies a Qwen3 language backbone, so it is not independent of the Qwen language-model family. The checkpoint uses custom model code and its own image tiling; record these preprocessing differences and inspect the pinned code before execution.

Use the frozen 290-request primary matrix per model (20 image examples × seven conditions plus 50 text questions × three conditions). Also include the frozen 100 text requests for no-example baseline and no-example CoT + RAG. Keep each run's raw response, schema validity, coverage, checkpoint revision and preprocessing. The visual processor differs by model, so this is an end-to-end system comparison, not an architecture-only ablation. The prompt set was previously inspected; all findings are exploratory on this small dataset. Never send the supplied images or questions to a third-party API.

Additional local inference dependencies are listed in `requirements-visual-models.txt`. Select a PyTorch/torchvision pair compatible with the machine's CUDA runtime. The local queue scripts use cluster-specific paths and are not distributed here.

Score with the existing evaluator into a separate directory. Report recognition precision, recall, F1 and exact set, energy and macronutrient MAE/MAPE, valid response coverage, paired comparisons, numeric-schema echoes, and all-zero totals. Malformed responses are model outcomes, not reasons to silently omit a condition. A smoke test verifies executable image/text inference; schema noncompliance is recorded as a result, not a technical success requirement.

## Job record

The SmolVLM2 dependency `num2words==0.5.14` is isolated under scratch. Its earlier smoke `23221099` failed before inference because this dependency was missing. Replacement smoke/main/scoring are `23242772` → `23242773` → `23242774`. InternVL download `23242496` completed; its smoke/main/scoring are `23242775` → `23242776` → `23242777`. Smoke jobs on earlier nodes spent several minutes stalled during environment loading and were cancelled before any output; replacement jobs use previously working nodes for the smoke step. Both chains use the free preemptable GPU QoS and may require reruns if preempted. Main arrays and scorers depend on success, so pending jobs are not evidence of completed inference.

For InternVL, the runner checks the SHA-256 digests of the five pinned custom-code files before loading. A review of those files' imports and obvious process/network calls found no such calls. The model uses the official 448-pixel dynamic tiling scheme with at most 12 tiles plus thumbnail, greedy decoding and no external APIs. This limited code inspection is not a formal security audit.
