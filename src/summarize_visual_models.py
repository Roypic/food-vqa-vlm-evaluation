#!/usr/bin/env python3
"""Summarize SmolVLM2 coverage, original matrix and schema sensitivity."""
import argparse
import json
from pathlib import Path
from evaluate_assignment_vlm import number

NUTRIENTS=('energy_kcal','carb_g','protein_g','fat_g')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,default=Path('results/visual_models'));parser.add_argument('--model',default='smolvlm2_2_2b');args=parser.parse_args()
    root=args.root; model=args.model
    data=json.loads((root/'scored/metrics.json').read_text()); groups=data['groups']
    keys=[k for k in groups if k.startswith(model+'::')]
    if len(keys)!=12: raise ValueError(f'Expected 12 groups for {model}, found {len(keys)}')
    lines=[f'# {model} visual-model extension','','Inference is local and without fine-tuning. The preprocessing, language backbone and architecture differ by model, so this is a system comparison. InternVL3.5-4B uses a Qwen3 language backbone; SmolVLM2 has fewer parameters than the Qwen models.','','## Recognition','','| Task | Condition | Coverage | Item recall | Precision | F1 | Exact meal set |','|---|---|---:|---:|---:|---:|---:|']
    for task in ('image_open','image_closed'):
        for condition in ('baseline','cot'):
            g=groups[f'{model}::{task}::{condition}']
            lines.append(f"| {task} | {condition} | {100*g['coverage']:.1f}% | {100*g['item_accuracy_micro_recall']:.1f}% | {100*g['micro_precision']:.1f}% | {100*g['micro_f1']:.1f}% | {100*g['exact_meal_set_accuracy']:.1f}% |")
    lines+=['','## Nutrition','','Each metric is MAE; coverage requires all four non-negative numeric totals. Numeric validity alone does not guarantee a meaningful estimate.','','| Task | Condition | Coverage | Energy kcal | Carb g | Protein g | Fat g |','|---|---|---:|---:|---:|---:|---:|']
    for task in ('image_nutrition','text_nutrition'):
        conditions=('baseline','cot','cot_rag') if task=='image_nutrition' else ('baseline','cot','cot_rag','baseline_noexample','cot_rag_noexample')
        for condition in conditions:
            g=groups[f'{model}::{task}::{condition}']
            if task=='image_nutrition':g=g['raw_primary']
            values=['—' if g['metrics'][m]['mae'] is None else f"{g['metrics'][m]['mae']:.1f}" for m in NUTRIENTS]
            lines.append(f"| {task} | {condition} | {100*g['coverage']:.1f}% | " + ' | '.join(values) + ' |')
    lines+=['','## Text output sensitivity','','Exact four-total equality flags are descriptive and do not establish intent.','','| Condition | Exact original example (100,10,10,5) | All-zero totals | Valid numeric totals |','|---|---:|---:|---:|']
    for cond in ('baseline','cot','cot_rag','baseline_noexample','cot_rag_noexample'):
        rows=[json.loads(s) for s in (root/'predictions'/model/f'text_nutrition__{cond}.jsonl').read_text().splitlines() if s.strip()]
        totals=[]
        for r in rows:
            parsed=r.get('parsed') if isinstance(r.get('parsed'),dict) else {}
            t=parsed.get('totals') if isinstance(parsed.get('totals'),dict) else {}
            values=tuple(number(t.get(k)) for k in NUTRIENTS)
            if all(v is not None for v in values):totals.append(values)
        example=sum(v==(100,10,10,5) for v in totals);zero=sum(v==(0,0,0,0) for v in totals)
        lines.append(f'| {cond} | {example}/{len(rows)} | {zero}/{len(rows)} | {len(totals)}/{len(rows)} |')
    lines+=['','See `scored/metrics.json` for all groups and `scored/per_example.jsonl` for local paired analysis. Original and no-example prompts differ in formatting, and CoT + RAG changes both prompting and retrieval. Results are exploratory on 20 meals and 50 questions.','']
    (root/'results_summary.md').write_text('\n'.join(lines))
    print(root/'results_summary.md')


if __name__=='__main__':main()
