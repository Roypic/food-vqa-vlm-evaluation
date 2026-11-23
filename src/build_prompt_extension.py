#!/usr/bin/env python3
"""Freeze generic zero-shot prompts from the original baseline requests."""
import hashlib
import json
from pathlib import Path

SOURCE = Path('results/main_assignment_vlm/requests')
DEST = Path('results/prompt_extension/requests')
DIRECTIVES = {
    'image_open': (' Set reasoning_summary to null and answer directly.', ' Think step by step. Put a brief reasoning summary in reasoning_summary.'),
    'image_closed': (' Set reasoning_summary to null and answer directly.', ' Think step by step. Put a brief reasoning summary in reasoning_summary.'),
    'image_nutrition': (" Answer directly from the model's existing knowledge. Set reasoning_summary to null and fdc_ids_used to [].", ' Think step by step. Put a brief reasoning summary in reasoning_summary and set fdc_ids_used to [].'),
    'text_nutrition': (" Answer directly from the model's existing knowledge. Set reasoning_summary to null and fdc_ids_used to [].", ' Think step by step. Put a brief reasoning summary in reasoning_summary and set fdc_ids_used to [].'),
}


def main():
    DEST.mkdir(parents=True, exist_ok=True)
    metadata = {'protocol': 'docs/prompt_extension_protocol.md', 'source_sha256': {}, 'output_sha256': {}, 'counts': {}}
    for task, (old, new) in DIRECTIVES.items():
        source = SOURCE / f'{task}__baseline.jsonl'
        target = DEST / f'{task}__zero_cot.jsonl'
        if target.exists():
            raise FileExistsError(target)
        rows = [json.loads(s) for s in source.read_text().splitlines() if s.strip()]
        for row in rows:
            if not row['prompt'].endswith(old):
                raise ValueError('Baseline directive changed: ' + row['request_id'])
            row['prompt'] = row['prompt'][:-len(old)] + new
            row['prompt_condition'] = 'zero_cot'
            row['request_id'] = row['request_id'].replace(':baseline:', ':zero_cot:')
        target.write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows))
        metadata['source_sha256'][source.name] = hashlib.sha256(source.read_bytes()).hexdigest()
        metadata['output_sha256'][target.name] = hashlib.sha256(target.read_bytes()).hexdigest()
        metadata['counts'][task] = len(rows)
    (DEST / 'manifest.json').write_text(json.dumps(metadata, indent=2) + '\n')
    print(json.dumps(metadata, indent=2))


if __name__ == '__main__':
    main()
