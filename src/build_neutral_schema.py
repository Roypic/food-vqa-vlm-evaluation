#!/usr/bin/env python3
"""Freeze post-hoc text prompts with null example totals in all conditions."""
import hashlib
import json
from pathlib import Path

src=Path('results/main_assignment_vlm/requests')
dest=Path('results/prompt_extension/requests')
old='"totals":{"energy_kcal":100,"carb_g":10,"protein_g":10,"fat_g":5}'
new='"totals":{"energy_kcal":null,"carb_g":null,"protein_g":null,"fat_g":null}'
meta={}
for cond in ('baseline','cot','cot_rag'):
    path=src/f'text_nutrition__{cond}.jsonl'
    out=dest/f'text_nutrition__{cond}_neutral.jsonl'
    if out.exists(): raise FileExistsError(out)
    rows=[json.loads(s) for s in path.read_text().splitlines() if s.strip()]
    for r in rows:
        assert r['prompt'].count(old)==1
        r['prompt']=r['prompt'].replace(old,new)
        r['request_id']=r['request_id'].replace(f':{cond}:',f':{cond}_neutral:')
        r['prompt_condition']=cond+'_neutral'
    out.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows))
    meta[cond]={'n':len(rows),'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'output_sha256':hashlib.sha256(out.read_bytes()).hexdigest()}
(dest/'neutral_manifest.json').write_text(json.dumps(meta,indent=2)+'\n')
print(json.dumps(meta,indent=2))
