# Error analysis: primary predictions

The CSVs in this directory summarize completed analyses of the original three-model experiment. They contain aggregate numbers only. Per-example targets, portions, prompts and raw predictions are retained in the private project workspace.

Selected findings:

- Qwen3 image CoT + RAG had a 73.8 kcal larger energy absolute error on average than baseline on the 19 examples valid in both conditions: 3 improved and 16 worsened. The paired bootstrap interval was [15.3, 134.1] kcal.
- Qwen3 text CoT + RAG improved average energy absolute error by 40.1 kcal on 49 paired valid examples, but 23 improved, 23 worsened and 3 tied; the paired bootstrap interval for alternative minus baseline was [−85.3, 0.5] kcal.
- In a selected audit of Qwen3 text RAG, 40 of 45 responses with an unambiguous mapping differed by more than 2 kcal or 2% from the energy recomputed using their reported portions and cited retrieved records. Five did not satisfy the mapping requirements. This flags inconsistency, not necessarily its cause.
- In Qwen3 image baseline, summing predicted portions against reference item energy densities gives 160.4 kcal MAE on 20 fully matched meals. This is an oracle diagnostic using workbook densities, not a deployable prediction or a causal decomposition.

The source scripts expect the private workspace layout `results/main_assignment_vlm/{requests,predictions}` and the supplied workbooks under `data/raw`; these inputs are intentionally not distributed. The lexical matcher may miss synonyms; citation identity and record suitability still need manual review. The sample is small and findings are exploratory.
