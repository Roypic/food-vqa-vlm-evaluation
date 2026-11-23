#!/usr/bin/env python3
"""Freeze text requests with prose-only output contract and no numeric example."""
import hashlib
import json
from pathlib import Path

src=Path('results/main_assignment_vlm/requests'); dest=Path('results/prompt_extension/requests')
old='{"portion_estimates":[{"food":"name","weight_g":100}],"totals":{"energy_kcal":100,"carb_g":10,"protein_g":10,"fat_g":5},"fdc_ids_used":[],"reasoning_summary":null}'
new='an object containing portion_estimates (an array of objects with food and numeric weight_g), totals (an object with numeric energy_kcal, carb_g, protein_g, fat_g), fdc_ids_used (an array), and reasoning_summary (a string or null)'
meta={}
for cond in ('baseline','cot_rag'):
    path=src/f'text_nutrition__{cond}.jsonl'; out=dest/f'text_nutrition__{cond}_noexample.jsonl'
    if out.exists(): raise FileExistsError(out)
    rows=[json.loads(s) for s in path.read_text().splitlines() if s.strip()]
    for r in rows:
        assert r['prompt'].count(old)==1
        r['prompt']=r['prompt'].replace(old,new)
        r['request_id']=r['request_id'].replace(f':{cond}:',f':{cond}_noexample:')
        r['prompt_condition']=cond+'_noexample'
    out.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows))
    meta[cond]={'n':len(rows),'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'output_sha256':hashlib.sha256(out.read_bytes()).hexdigest()}
(dest/'noexample_manifest.json').write_text(json.dumps(meta,indent=2)+'\n')
print(json.dumps(meta,indent=2))
