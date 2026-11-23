#!/usr/bin/env python3
"""Audit raw JSON-only compliance and tail-sensitive nutrition error."""
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
from evaluate_assignment_vlm import has_valid_totals


def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--model',required=True);a=p.parse_args()
    detail=[]
    for path in sorted((a.root/'predictions'/a.model).glob('*.jsonl')):
        for line in path.read_text().splitlines():
            row=json.loads(line); raw=row.get('raw_response','')
            try: strict=isinstance(json.loads(raw.strip()),dict)
            except (TypeError,ValueError): strict=False
            detail.append({'model':a.model,'task':row['task'],'condition':row['prompt_condition'],'example':row['example_id'],'strict_json_object':strict,'extracted_json':bool(row.get('parse_valid')),'valid_nutrition_totals':has_valid_totals(row) if row['task'].endswith('nutrition') else None})
    df=pd.DataFrame(detail)
    summary=df.groupby(['model','task','condition'],as_index=False).agg(n=('example','size'),strict_json_object=('strict_json_object','sum'),extracted_json=('extracted_json','sum'))
    summary.to_csv(a.root/'scored/raw_format_summary.csv',index=False)
    scores=pd.read_json(a.root/'scored/per_example.jsonl',lines=True)
    scores=scores[(scores.model_id==a.model)&scores.task.isin(['image_nutrition','text_nutrition'])&scores.valid]
    stats=[]
    for (task,condition),group in scores.groupby(['task','condition']):
        errors=[abs(r['prediction']['energy_kcal']-r['target']['energy_kcal']) for _,r in group.iterrows()]
        stats.append({'model':a.model,'task':task,'condition':condition,'n':len(errors),'mean_absolute_error':float(np.mean(errors)),'median_absolute_error':float(np.median(errors)),'max_absolute_error':max(errors)})
    distributions=pd.DataFrame(stats)
    distributions.to_csv(a.root/'scored/energy_error_distribution.csv',index=False)
    report=a.root/'results_summary.md'
    if report.exists():
        marker='\n## Raw format and extreme values\n'
        text=report.read_text().split(marker,1)[0]
        lines=[marker,'The frozen evaluator extracts JSON objects from responses containing extra text. A stricter raw-format check requires the entire stripped response to be one parseable JSON object; it does not itself validate the schema or numbers. Numeric coverage in the tables above is therefore distinct from strict raw-format compliance.','', '| Task | Condition | Strict JSON object / responses | Extracted object / responses |','|---|---|---:|---:|']
        for _,r in summary.iterrows():
            lines.append(f"| {r['task']} | {r['condition']} | {int(r['strict_json_object'])}/{int(r['n'])} | {int(r['extracted_json'])}/{int(r['n'])} |")
        lines+=['','| Nutrition task | Condition | Numerically valid n | Energy MAE | Median absolute error | Maximum absolute error |','|---|---|---:|---:|---:|---:|']
        for _,r in distributions.iterrows():
            lines.append(f"| {r['task']} | {r['condition']} | {int(r['n'])} | {r['mean_absolute_error']:.1f} | {r['median_absolute_error']:.1f} | {r['max_absolute_error']:.1f} |")
        if a.model=='smolvlm2_2_2b':
            lines+=['','Illustrative extreme case: text CoT Q27 reports 235,000 kcal against a 383 kcal target. The raw answer has multiple JSON objects and a calculation that multiplies an already scaled energy by weight again. The frozen extraction picks the last contract-shaped object. The outlier is retained.']
        report.write_text(text+'\n'.join(lines)+'\n')
    print('raw-format and error-distribution audits completed')


if __name__=='__main__':main()
