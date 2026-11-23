#!/usr/bin/env python3
"""Pair a visual model and Qwen3 on common valid examples with bootstrap CIs."""
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
from summarize_prompt_extension import interval


def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--model',required=True);a=p.parse_args()
    rows=[json.loads(s) for s in (a.root/'scored/per_example.jsonl').read_text().splitlines() if s.strip()]
    df=pd.DataFrame(rows); results=[]
    for task in ('image_open','image_closed','image_nutrition','text_nutrition'):
        conds=('baseline','cot') if task in ('image_open','image_closed') else (('baseline','cot','cot_rag') if task=='image_nutrition' else ('baseline','cot','cot_rag','baseline_noexample','cot_rag_noexample'))
        for cond in conds:
            g=df[(df.task==task)&(df.condition==cond)]
            ref=g[g.model_id=='qwen3_vl_4b'].set_index('example_id'); other=g[g.model_id==a.model].set_index('example_id')
            both=ref.join(other,lsuffix='_qwen',rsuffix='_visual'); both=both[both.valid_qwen & both.valid_visual]
            if task in ('image_open','image_closed'):
                if len(both):
                    delta=both.tp_visual.to_numpy(dtype=float)-both.tp_qwen.to_numpy(dtype=float)
                    counts=np.asarray([len(x) for x in both.target_qwen],dtype=float)
                    rng=np.random.default_rng(20261123);idx=rng.integers(0,len(both),size=(10000,len(both)))
                    boot=delta[idx].sum(axis=1)/counts[idx].sum(axis=1)
                    val=float(delta.sum()/counts.sum());ci=[float(np.quantile(boot,.025)),float(np.quantile(boot,.975))]
                else:val=None;ci=[None,None]
                results.append({'task':task,'condition':cond,'metric':'micro_recall','n_common':len(both),'visual_minus_qwen3':val,'bootstrap_95':ci})
            else:
                for nutrient in ('energy_kcal','carb_g','protein_g','fat_g'):
                    changes=[]
                    for _,r in both.iterrows():
                        target=r.target_qwen[nutrient]
                        changes.append(abs(r.prediction_visual[nutrient]-target)-abs(r.prediction_qwen[nutrient]-target))
                    results.append({'task':task,'condition':cond,'metric':nutrient+'_absolute_error','n_common':len(changes),'visual_minus_qwen3':float(np.mean(changes)) if changes else None,'bootstrap_95':interval(changes),'visual_better':sum(x<0 for x in changes),'visual_worse':sum(x>0 for x in changes),'tied':sum(x==0 for x in changes)})
    (a.root/'scored/paired_vs_qwen3.json').write_text(json.dumps(results,indent=2)+'\n')
    print('paired comparisons:',len(results))


if __name__=='__main__':main()
