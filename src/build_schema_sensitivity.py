#!/usr/bin/env python3
"""Freeze the text-baseline numeric-example sensitivity requests."""
import hashlib
import json
from pathlib import Path

source=Path('results/main_assignment_vlm/requests/text_nutrition__baseline.jsonl')
out=Path('results/prompt_extension/requests/text_nutrition__schema_alt.jsonl')
old='"totals":{"energy_kcal":100,"carb_g":10,"protein_g":10,"fat_g":5}'
new='"totals":{"energy_kcal":321,"carb_g":32,"protein_g":21,"fat_g":13}'
if out.exists(): raise FileExistsError(out)
rows=[json.loads(line) for line in source.read_text().splitlines() if line.strip()]
for row in rows:
    assert row['prompt'].count(old)==1
    row['prompt']=row['prompt'].replace(old,new)
    row['request_id']=row['request_id'].replace(':baseline:',':schema_alt:')
    row['prompt_condition']='schema_alt'
out.write_text(''.join(json.dumps(row,ensure_ascii=False)+'\n' for row in rows))
meta={'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'output_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'count':len(rows),'changed_values':[321,32,21,13]}
(out.parent/'schema_manifest.json').write_text(json.dumps(meta,indent=2)+'\n')
print(json.dumps(meta,indent=2))
