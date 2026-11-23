#!/usr/bin/env python3
"""Conservative, auditable checks of frozen nutrition responses and RAG citations."""
import json
from pathlib import Path

import numpy as np
import pandas as pd

from evaluate_assignment_vlm import match_labels, number

BASE = Path('results/main_assignment_vlm')
OUT = BASE / 'error_analysis'
METRICS = ('energy_kcal', 'carb_g', 'protein_g', 'fat_g')


def main():
    gt = pd.read_excel('data/raw/Images GT.xlsx', sheet_name='Ground truths')
    requests = {}
    for task in ('image_nutrition', 'text_nutrition'):
        path = BASE / 'requests' / f'{task}__cot_rag.jsonl'
        for line in path.read_text().splitlines():
            r = json.loads(line); requests[r['request_id']] = r
    details = []
    for path in sorted((BASE / 'predictions').glob('*/*nutrition__*.jsonl')):
        for line in path.read_text().splitlines():
            r = json.loads(line)
            parsed = r.get('parsed') if isinstance(r.get('parsed'), dict) else {}
            totals = parsed.get('totals') if isinstance(parsed.get('totals'), dict) else {}
            portions = parsed.get('portion_estimates') if isinstance(parsed.get('portion_estimates'), list) else None
            item = {'model': r['model_id'], 'task': r['task'], 'condition': r['prompt_condition'], 'example': r['example_id'], 'json_object': isinstance(r.get('parsed'),dict), 'numeric_totals': all(number(totals.get(k)) is not None for k in METRICS), 'schema_example_exact': all(number(totals.get(k)) == v for k,v in zip(METRICS,(100,10,10,5))), 'portion_list_present': portions is not None}
            if r['task'] == 'image_nutrition' and portions is not None:
                expected = gt.loc[gt.Meal_ID == r['example_id'], 'Food'].dropna().astype(str).tolist()
                predicted = [str(x.get('food','')) for x in portions if isinstance(x,dict)]
                tp, fp, fn = match_labels(predicted,expected)
                item.update(expected_items=len(expected), predicted_items=len(predicted), matched_items=tp, missing_items=fn, extra_items=fp)
            if r['prompt_condition'] == 'cot_rag':
                retrieved = requests[r['request_id']]['retrieval']
                available = {str(c['fdc_id']) for group in retrieved for c in group['candidates']}
                citations = parsed.get('fdc_ids_used')
                if isinstance(citations,list):
                    normalized = [str(i) for i in citations]
                    item.update(citation_list_present=True, cited_count=len(normalized), cited_not_retrieved=sum(i not in available for i in normalized), all_citations_retrieved=bool(normalized) and all(i in available for i in normalized))
                else:
                    item.update(citation_list_present=False, cited_count=np.nan, cited_not_retrieved=np.nan, all_citations_retrieved=False)
                item.update(retrieval_queries=len(retrieved), queries_without_candidates=sum(not g['candidates'] for g in retrieved))
            details.append(item)
    df = pd.DataFrame(details)
    OUT.mkdir(parents=True,exist_ok=True)
    df.to_csv(OUT/'automated_failure_flags.csv', index=False)
    groups=[]
    for key,g in df.groupby(['model','task','condition']):
        image=g.task.iloc[0]=='image_nutrition'
        rag=g.condition.iloc[0]=='cot_rag'
        groups.append({'model':key[0], 'task':key[1], 'condition':key[2], 'n':len(g), 'valid_numeric':int(g.numeric_totals.sum()), 'schema_example_exact':int(g.schema_example_exact.sum()), 'portion_list_present':int(g.portion_list_present.sum()), 'image_missing_any':int((g.missing_items.fillna(0)>0).sum()) if image else None, 'image_portion_list_missing':int((~g.portion_list_present).sum()) if image else None, 'retrieval_queries_without_candidates':int(g.queries_without_candidates.sum()) if rag else None, 'rag_no_citations':int((g.cited_count.fillna(0)==0).sum()) if rag else None, 'rag_any_nonretrieved_citation':int((g.cited_not_retrieved.fillna(0)>0).sum()) if rag else None})
    pd.DataFrame(groups).to_csv(OUT/'automated_failure_summary.csv',index=False)
    print('audited',len(df),'nutrition responses; schema-echo flags',int(df.schema_example_exact.sum()))


if __name__=='__main__':
    main()
