#!/usr/bin/env python3
"""Audit paired nutrition errors and meal-level predicted portion weights."""
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

from evaluate_assignment_vlm import has_valid_totals, number

ROOT = Path('results/main_assignment_vlm/predictions')
OUT = Path('results/main_assignment_vlm/error_analysis')
NUTRIENTS = {'energy_kcal': 'Energy (kcal)', 'carb_g': 'Carbohydrates (g)', 'protein_g': 'Protein (g)', 'fat_g': 'Fat (g)'}


def main():
    gt = pd.read_excel('data/raw/Images GT.xlsx', sheet_name='Ground truths')
    target_weight = gt.groupby('Meal_ID')['Weight (g)'].sum().to_dict()
    totals = gt.groupby('Meal_ID')[list(NUTRIENTS.values())].sum()
    q = pd.read_excel('data/raw/Questions 50.xlsx')
    text_columns = {'energy_kcal': 'Energy (kcal)', 'carb_g': 'Carbs (g)', 'protein_g': 'Protein (g)', 'fat_g': 'Fat (g)'}
    rows = []
    for path in sorted(ROOT.glob('*/*.jsonl')):
        for line in path.read_text().splitlines():
            r = json.loads(line)
            if r['task'] not in ('image_nutrition', 'text_nutrition'):
                continue
            parsed = r.get('parsed') if isinstance(r.get('parsed'), dict) else {}
            pred = parsed.get('totals') if isinstance(parsed.get('totals'), dict) else {}
            valid = has_valid_totals(r)
            image = r['task'] == 'image_nutrition'
            target = totals.loc[r['example_id']] if image else q.iloc[int(r['example_id'][1:]) - 1]
            cols = NUTRIENTS if image else text_columns
            item = dict(model=r['model_id'], task=r['task'], condition=r['prompt_condition'], example=r['example_id'], valid=valid)
            for metric, column in cols.items():
                value = number(pred.get(metric))
                item[metric + '_target'] = float(target[column])
                item[metric + '_prediction'] = value
                item[metric + '_error'] = value - float(target[column]) if valid else None
                item[metric + '_abs_error'] = abs(item[metric + '_error']) if valid else None
            portions = parsed.get('portion_estimates')
            if image and isinstance(portions, list) and portions:
                weights = [number(x.get('weight_g')) if isinstance(x, dict) else None for x in portions]
                if all(w is not None for w in weights):
                    item['predicted_weight_g'] = sum(weights)
                    item['weight_target_g'] = float(target_weight[r['example_id']])
                    item['weight_error_g'] = item['predicted_weight_g'] - item['weight_target_g']
                    item['portion_count'] = len(weights)
                    item['target_item_count'] = int((gt['Meal_ID'] == r['example_id']).sum())
            rows.append(item)
    frame = pd.DataFrame(rows)
    OUT.mkdir(parents=True, exist_ok=True)
    frame.to_csv(OUT / 'per_example.csv', index=False)
    summaries = []
    for (model, task), group in frame.groupby(['model', 'task']):
        base = group[group.condition == 'baseline'].set_index('example')
        for condition in ('cot', 'cot_rag'):
            alt = group[group.condition == condition].set_index('example')
            paired = base.join(alt, lsuffix='_base', rsuffix='_alt')
            paired = paired[paired.valid_base & paired.valid_alt]
            for metric in NUTRIENTS:
                difference = paired[metric + '_abs_error_alt'] - paired[metric + '_abs_error_base']
                summaries.append(dict(model=model, task=task, condition=condition, nutrient=metric, n=len(paired), base_mae=paired[metric + '_abs_error_base'].mean(), alt_mae=paired[metric + '_abs_error_alt'].mean(), mean_change=difference.mean(), improved=int((difference < 0).sum()), worsened=int((difference > 0).sum()), tied=int((difference == 0).sum())))
    pd.DataFrame(summaries).to_csv(OUT / 'paired_summary.csv', index=False)
    weight_rows = []
    image = frame[(frame.task == 'image_nutrition') & frame.valid]
    for (model, condition), g in image.groupby(['model', 'condition']):
        g = g.dropna(subset=['weight_error_g', 'energy_kcal_error'])
        complete = g[g.portion_count == g.target_item_count]
        for label, selected in [('all_reported', g), ('count_matches_target', complete)]:
            weight_rows.append(dict(model=model, condition=condition, subset=label, n=len(selected), mean_weight_error_g=selected.weight_error_g.mean(), weight_mae_g=selected.weight_error_g.abs().mean(), energy_signed_error_mean=selected.energy_kcal_error.mean(), signed_pearson=selected.weight_error_g.corr(selected.energy_kcal_error) if len(selected)>2 else np.nan, abs_error_pearson=selected.weight_error_g.abs().corr(selected.energy_kcal_abs_error) if len(selected)>2 else np.nan))
    pd.DataFrame(weight_rows).to_csv(OUT / 'portion_summary.csv', index=False)
    print('nutrition rows', len(frame), 'invalid', int((~frame.valid).sum()), 'output', OUT)


if __name__ == '__main__':
    main()
