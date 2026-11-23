#!/usr/bin/env python3
"""Recompute energy with predicted masses and workbook item energy densities."""
import json
from pathlib import Path
import pandas as pd
from evaluate_assignment_vlm import has_valid_totals, number, similarity


def matched_weights(portions, target):
    if not isinstance(portions, list) or len(portions) != len(target): return None
    if any(not isinstance(p, dict) or number(p.get('weight_g')) is None for p in portions): return None
    candidates=sorted(((similarity(p.get('food',''), t['Food']),i,j) for i,p in enumerate(portions) for j,t in enumerate(target)),reverse=True)
    used_i=set(); used_j=set(); matches={}
    for score,i,j in candidates:
        if score < .78: break
        if i not in used_i and j not in used_j:
            used_i.add(i); used_j.add(j); matches[j]=float(portions[i]['weight_g'])
    return matches if len(matches)==len(target) else None


def main():
    root=Path('results/main_assignment_vlm'); out=root/'error_analysis'
    gt=pd.read_excel('data/raw/Images GT.xlsx',sheet_name='Ground truths')
    rows=[]
    for path in sorted((root/'predictions').glob('*/image_nutrition__*.jsonl')):
        for line in path.read_text().splitlines():
            r=json.loads(line); meal=gt[gt.Meal_ID==r['example_id']].to_dict('records')
            parsed=r.get('parsed') if isinstance(r.get('parsed'),dict) else {}
            matches=matched_weights(parsed.get('portion_estimates'),meal)
            predicted=number((parsed.get('totals') or {}).get('energy_kcal')) if isinstance(parsed.get('totals'),dict) else None
            valid=matches is not None and has_valid_totals(r) and all(number(t.get('Weight (g)')) not in (None,0) and number(t.get('Energy (kcal)')) is not None for t in meal)
            item={'model':r['model_id'],'condition':r['prompt_condition'],'example':r['example_id'],'strict_matching_valid':valid}
            if valid:
                target=sum(t['Energy (kcal)'] for t in meal)
                recomputed=sum(matches[j]*float(t['Energy (kcal)'])/float(t['Weight (g)']) for j,t in enumerate(meal))
                item.update(target_kcal=target,model_kcal=predicted,oracle_density_kcal=recomputed,model_abs_error=abs(predicted-target),oracle_density_abs_error=abs(recomputed-target))
            rows.append(item)
    df=pd.DataFrame(rows);out.mkdir(parents=True,exist_ok=True)
    df.to_csv(out/'portion_counterfactual_cases.csv',index=False)
    summaries=[]
    for (model,cond),g in df.groupby(['model','condition']):
        v=g[g.strict_matching_valid]
        summaries.append({'model':model,'condition':cond,'total':len(g),'matched_n':len(v),'reported_energy_mae':v.model_abs_error.mean(),'oracle_density_energy_mae':v.oracle_density_abs_error.mean()})
    pd.DataFrame(summaries).to_csv(out/'portion_counterfactual_summary.csv',index=False)
    print('counterfactual',len(df),'responses;',int(df.strict_matching_valid.sum()),'strict matches')


if __name__=='__main__': main()
