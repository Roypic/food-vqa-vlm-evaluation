#!/usr/bin/env python3
"""Flag energy arithmetic differences only when RAG mapping is unambiguous."""
import json
from pathlib import Path
import pandas as pd
from evaluate_assignment_vlm import number, similarity

BASE=Path('results/main_assignment_vlm')


def main():
    requests={}
    for task in ('image_nutrition','text_nutrition'):
        for line in (BASE/'requests'/f'{task}__cot_rag.jsonl').read_text().splitlines():
            row=json.loads(line); requests[row['request_id']]=row
    results=[]
    for file in sorted((BASE/'predictions').glob('*/*nutrition__cot_rag.jsonl')):
        for line in file.read_text().splitlines():
            r=json.loads(line); parsed=r.get('parsed') if isinstance(r.get('parsed'),dict) else {}
            portions=parsed.get('portion_estimates'); ids=parsed.get('fdc_ids_used'); totals=parsed.get('totals')
            item={'model':r['model_id'],'task':r['task'],'example':r['example_id'],'eligible':False,'reason':None}
            if not isinstance(portions,list) or not portions or not isinstance(ids,list) or len(ids)!=len(portions) or len({str(i) for i in ids})!=len(ids) or not isinstance(totals,dict) or number(totals.get('energy_kcal')) is None:
                item['reason']='missing/invalid portions, energy or unique one-per-portion citations'; results.append(item); continue
            groups=requests[r['request_id']]['retrieval']; ids={str(i) for i in ids}
            mapping=[]
            for portion in portions:
                if not isinstance(portion,dict) or number(portion.get('weight_g')) is None:
                    break
                matches=[]
                for group in groups:
                    if similarity(portion.get('food',''),group['query']) < .78: continue
                    for c in group['candidates']:
                        if str(c['fdc_id']) in ids: matches.append(c)
                unique={str(c['fdc_id']):c for c in matches}
                if len(unique)!=1: break
                cid,candidate=next(iter(unique.items()))
                mapping.append((cid,number(portion['weight_g']),candidate))
            if len(mapping)!=len(portions) or len({x[0] for x in mapping})!=len(ids):
                item['reason']='ambiguous portion-to-citation mapping';results.append(item);continue
            calc=sum(weight*float(c['nutrients_per_100g']['energy_kcal'])/100 for _,weight,c in mapping)
            stated=number(totals['energy_kcal']); tol=max(2.0,.02*abs(calc))
            item.update(eligible=True,reason='unambiguous lexical mapping; 2 kcal or 2% tolerance',recomputed_kcal=calc,reported_kcal=stated,difference_kcal=stated-calc,tolerance_kcal=tol,flag=abs(stated-calc)>tol)
            results.append(item)
    frame=pd.DataFrame(results); out=BASE/'error_analysis';out.mkdir(exist_ok=True)
    frame.to_csv(out/'rag_arithmetic_cases.csv',index=False)
    summary=[]
    for (model,task),g in frame.groupby(['model','task']):
        e=g[g.eligible]; summary.append({'model':model,'task':task,'total':len(g),'eligible':len(e),'outside_tolerance':int(e.flag.fillna(False).sum())})
    pd.DataFrame(summary).to_csv(out/'rag_arithmetic_summary.csv',index=False)
    print('RAG arithmetic eligible',int(frame.eligible.sum()),'of',len(frame))


if __name__=='__main__':main()
