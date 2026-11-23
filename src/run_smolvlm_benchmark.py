#!/usr/bin/env python3
"""Run frozen requests with SmolVLM2 using the Transformers harness."""
import argparse
import json
from pathlib import Path
import torch
from transformers import AutoProcessor, AutoModelForImageTextToText
from run_vlm_hf import extract_json_object


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--model', required=True)
    p.add_argument('--input', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--limit', type=int)
    args = p.parse_args()
    rows = [json.loads(s) for s in args.input.read_text().splitlines() if s.strip()]
    rows = rows[:args.limit] if args.limit is not None else rows
    if not rows or args.output.exists():
        raise ValueError('Empty input or existing output')
    processor = AutoProcessor.from_pretrained(args.model, local_files_only=True)
    model = AutoModelForImageTextToText.from_pretrained(args.model, torch_dtype=torch.bfloat16, _attn_implementation='sdpa', local_files_only=True).to('cuda').eval()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x') as f:
        for row in rows:
            content = []
            if row.get('image'):
                content.append({'type': 'image', 'path': row['image']})
            content.append({'type': 'text', 'text': row['prompt']})
            inputs = processor.apply_chat_template([{'role': 'user', 'content': content}], add_generation_prompt=True, tokenize=True, return_dict=True, return_tensors='pt').to(model.device, dtype=torch.bfloat16)
            with torch.inference_mode():
                generated = model.generate(**inputs, do_sample=False, max_new_tokens=1024)
            raw = processor.batch_decode(generated[:, inputs['input_ids'].shape[-1]:], skip_special_tokens=True)[0]
            parsed = extract_json_object(raw)
            out = {'request_id':row['request_id'], 'task':row['task'], 'prompt_condition':row['prompt_condition'], 'example_id':row['example_id'], 'model_id':'smolvlm2_2_2b', 'checkpoint':args.model, 'parsed':parsed, 'parse_valid':parsed is not None, 'raw_response':raw}
            f.write(json.dumps(out, ensure_ascii=False)+'\n'); f.flush()
            print(row['request_id'], 'valid_json=', parsed is not None, flush=True)


if __name__ == '__main__':
    main()
