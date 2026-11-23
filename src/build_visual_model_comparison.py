#!/usr/bin/env python3
"""Build five-model comparison tables after both visual model runs finish."""
import json
from pathlib import Path

root=Path('results/visual_models')


def main():
    smol=json.loads((root/'scored/metrics.json').read_text())['groups']
    intern=json.loads((root/'internvl35/scored/metrics.json').read_text())['groups']
    models=[('Qwen2.5-VL-7B','qwen2_5_vl_7b',smol),('Qwen3-VL-4B','qwen3_vl_4b',smol),('Phi-4 multimodal','phi4_multimodal_5_6b',smol),('SmolVLM2-2.2B','smolvlm2_2_2b',smol),('InternVL3.5-4B','internvl35_4b',intern)]
    lines=['# Five-model visual and nutrition comparison','',
      'Models use their native image processors and different parameter counts. InternVL3.5 has a Qwen3 language backbone. The provided dataset contains 20 images and 50 text questions; this is an exploratory system comparison, not a claim of general superiority. No model was fine-tuned on this dataset.','',
      '## Recognition','','Each cell is item recall / precision / exact meal-set accuracy, with schema-list coverage. Invalid recognition outputs are treated as empty predictions by the frozen evaluator.','','| Model | Open baseline | Open CoT | Closed baseline | Closed CoT |','|---|---:|---:|---:|---:|']
    for label,model,data in models:
        cells=[]
        for task,cond in [('image_open','baseline'),('image_open','cot'),('image_closed','baseline'),('image_closed','cot')]:
            x=data[f'{model}::{task}::{cond}']
            cells.append(f"{100*x['item_accuracy_micro_recall']:.1f}% / {100*x['micro_precision']:.1f}% / {100*x['exact_meal_set_accuracy']:.1f}% ({100*x['coverage']:.0f}% cov.)")
        lines.append(f'| {label} | '+' | '.join(cells)+' |')
    lines+=['','## Oracle-label image nutrition','','Each cell is energy MAE (kcal) and coverage. MAEs can use different valid subsets; use the paired files for matched-example comparisons and uncertainty.','','| Model | Baseline | CoT | CoT + RAG |','|---|---:|---:|---:|']
    for label,model,data in models:
        cells=[]
        for cond in ('baseline','cot','cot_rag'):
            x=data[f'{model}::image_nutrition::{cond}']['raw_primary']; val=x['metrics']['energy_kcal']['mae']
            cells.append(('—' if val is None else f'{val:.1f}')+f" ({100*x['coverage']:.0f}% cov.)")
        lines.append(f'| {label} | '+' | '.join(cells)+' |')
    lines+=['','## Text nutrition and schema sensitivity','','The original numeric-example baseline is format-sensitive. For no-example conditions, the JSON example is replaced by a prose output contract. Values shown are energy MAE (kcal) and numeric coverage; zeros may satisfy the numeric contract.','','| Model | Original baseline | Original CoT + RAG | No-example baseline | No-example CoT + RAG |','|---|---:|---:|---:|---:|']
    for label,model,data in models:
        cells=[]
        for cond in ('baseline','cot_rag','baseline_noexample','cot_rag_noexample'):
            x=data.get(f'{model}::text_nutrition::{cond}')
            if x is None:cells.append('not run');continue
            val=x['metrics']['energy_kcal']['mae'];cells.append(('—' if val is None else f'{val:.1f}')+f" ({100*x['coverage']:.0f}% cov.)")
        lines.append(f'| {label} | '+' | '.join(cells)+' |')
    lines+=['','Read `results_summary.md` and `internvl35/results_summary.md` for full nutrient tables, exact-example and zero-output flags, and strict raw-format compliance. `scored/paired_vs_qwen3.json` and `internvl35/scored/paired_vs_qwen3.json` provide paired model differences with bootstrap intervals on common valid examples. Raw per-example outputs remain local.','']
    (root/'comparison_summary.md').write_text('\n'.join(lines));print(root/'comparison_summary.md')


if __name__=='__main__':main()
