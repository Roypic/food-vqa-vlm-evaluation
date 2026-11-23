#!/usr/bin/env python3
"""Paired prompt comparisons with example bootstrap intervals."""
import json
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path('results/prompt_extension')
NUTRIENTS = ('energy_kcal', 'carb_g', 'protein_g', 'fat_g')


def interval(differences):
    x = np.asarray(differences, dtype=float)
    if not len(x): return [None, None]
    rng = np.random.default_rng(20261123)
    boot = x[rng.integers(0, len(x), size=(10000,len(x)))].mean(axis=1)
    return [float(np.quantile(boot,.025)),float(np.quantile(boot,.975))]


def main():
    records = [json.loads(s) for s in (ROOT/'scored/per_example.jsonl').read_text().splitlines() if s.strip()]
    df = pd.DataFrame(records)
    output=[]
    for (model,task),g in df.groupby(['model_id','task']):
        base=g[g.condition=='baseline'].set_index('example_id')
        for condition in ('cot','cot_rag','zero_cot','least_to_most'):
            alternative=g[g.condition==condition].set_index('example_id')
            if alternative.empty: continue
            both=base.join(alternative,lsuffix='_base',rsuffix='_alt')
            both=both[both.valid_base & both.valid_alt]
            if task in ('image_open','image_closed'):
                for key in ('tp','exact_set'):
                    delta=both[key+'_alt'].astype(float)-both[key+'_base'].astype(float)
                    output.append({'model':model,'task':task,'condition':condition,'metric':key+'_per_meal','n':len(delta),'delta_mean':float(delta.mean()) if len(delta) else None,'delta_bootstrap_95':interval(delta),'improved':int((delta>0).sum()),'worsened':int((delta<0).sum()),'tied':int((delta==0).sum())})
            else:
                for nutrient in NUTRIENTS:
                    differences=[]; baseline_errors=[]; alternative_errors=[]
                    for _,r in both.iterrows():
                        target=r['target_base'][nutrient]
                        e0=abs(r['prediction_base'][nutrient]-target)
                        e1=abs(r['prediction_alt'][nutrient]-target)
                        baseline_errors.append(e0); alternative_errors.append(e1); differences.append(e1-e0)
                    delta=np.asarray(differences)
                    output.append({'model':model,'task':task,'condition':condition,'metric':nutrient+'_absolute_error','n':len(delta),'baseline_mae':float(np.mean(baseline_errors)) if len(delta) else None,'alternative_mae':float(np.mean(alternative_errors)) if len(delta) else None,'delta_mean':float(delta.mean()) if len(delta) else None,'delta_bootstrap_95':interval(delta),'improved':int((delta<0).sum()),'worsened':int((delta>0).sum()),'tied':int((delta==0).sum())})
    (ROOT/'scored/paired_bootstrap.json').write_text(json.dumps(output,indent=2)+'\n')
    lines=['# Prompt extension: paired comparisons','','Delta is alternative minus baseline; negative is better for absolute error, positive is better for recognition. Bootstrap 95% intervals resample matched meals/questions.','', '| Model | Task | Condition | Metric | Paired n | Delta | 95% bootstrap CI | Improved / worse / tied |','|---|---|---|---|---:|---:|---:|---:|']
    for x in output:
        lo,hi=x['delta_bootstrap_95']
        lines.append(f"| {x['model']} | {x['task']} | {x['condition']} | {x['metric']} | {x['n']} | {x['delta_mean']:.2f} | [{lo:.2f}, {hi:.2f}] | {x['improved']} / {x['worsened']} / {x['tied']} |")
    (ROOT/'scored/paired_summary.md').write_text('\n'.join(lines)+'\n')
    print('paired comparisons',len(output))


if __name__=='__main__': main()
