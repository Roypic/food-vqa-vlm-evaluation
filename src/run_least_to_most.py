#!/usr/bin/env python3
"""Two-stage nutrition harness with retained intermediate model output."""
import argparse
import json
from pathlib import Path
from run_assignment_vlm import generate_one
from run_vlm_hf import extract_json_object, load_qwen


def extract_portions(text):
    """Find a complete contract object rather than an inner food object."""
    decoder = json.JSONDecoder()
    for index, char in enumerate(text):
        if char != '{':
            continue
        try:
            obj, _ = decoder.raw_decode(text[index:])
        except (ValueError, TypeError):
            continue
        if isinstance(obj, dict) and isinstance(obj.get('portion_estimates'), list):
            return obj
    return None


def extract_bare_portion_list(text):
    """Recognize a usable bare list separately from the required JSON object."""
    decoder = json.JSONDecoder()
    for index, char in enumerate(text):
        if char != '[':
            continue
        try:
            obj, _ = decoder.raw_decode(text[index:])
        except (ValueError, TypeError):
            continue
        if isinstance(obj, list) and obj and all(isinstance(x, dict) and 'food' in x and 'weight_g' in x for x in obj):
            return obj
    return None


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--input', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--model', required=True)
    p.add_argument('--model-id', required=True)
    args = p.parse_args()
    rows = [json.loads(line) for line in args.input.read_text().splitlines() if line.strip()]
    if not rows or args.output.exists():
        raise ValueError('Empty input or output already exists')
    torch, model, processor = load_qwen(args.model, max_pixels=1280*28*28)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x') as out:
        for row in rows:
            # Take only the original task introduction, which contains the input question
            # or supplied image labels, never the workbook target or measured weight.
            introduction = row['prompt'].split('\nReturn one JSON object only', 1)[0]
            first_prompt = introduction + '\nFirst list the foods and their portion weights in grams. Read stated weights or estimate from the image. Do not estimate nutrients yet. Return JSON only: {"portion_estimates":[{"food":"name","weight_g":100}]}.'
            stage1 = generate_one(torch, model, processor, {**row, 'prompt': first_prompt}, 512)
            stage1_parsed = extract_portions(stage1)
            second_prompt = row['prompt'] + '\n\nThe following preliminary portion estimates may contain mistakes. Recheck them against the input, then answer the original task using the required JSON schema:\n' + stage1
            raw = generate_one(torch, model, processor, {**row, 'prompt': second_prompt}, 1024)
            parsed = extract_json_object(raw)
            result = {'request_id':row['request_id'].replace(':baseline:', ':least_to_most:'), 'task':row['task'], 'prompt_condition':'least_to_most', 'example_id':row['example_id'], 'model_id':args.model_id, 'checkpoint':args.model, 'stage1_raw':stage1, 'stage1_parsed':stage1_parsed, 'stage1_valid':isinstance(stage1_parsed,dict) and isinstance(stage1_parsed.get('portion_estimates'),list), 'raw_response':raw, 'parsed':parsed, 'parse_valid':parsed is not None}
            out.write(json.dumps(result, ensure_ascii=False)+'\n'); out.flush()
            print(result['request_id'], 'stage1_valid',result['stage1_valid'], 'final_json',parsed is not None,flush=True)


if __name__ == '__main__':
    main()
