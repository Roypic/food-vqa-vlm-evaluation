#!/usr/bin/env python3
"""Run the frozen Food VQA requests with Phi-4-multimodal-instruct."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from PIL import Image

from run_vlm_hf import extract_json_object


def load_model(path: str):
    import torch
    from transformers import AutoModelForCausalLM, AutoProcessor, GenerationConfig

    processor = AutoProcessor.from_pretrained(path, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        path,
        device_map="cuda",
        torch_dtype="auto",
        trust_remote_code=True,
        _attn_implementation="sdpa",
    ).eval()
    generation_config = GenerationConfig.from_pretrained(path)
    generation_config.do_sample = False
    return torch, model, processor, generation_config


def generate_one(torch, model, processor, generation_config, request: dict[str, Any], max_new_tokens: int) -> str:
    if request.get("image"):
        prompt = f"<|user|><|image_1|>{request['prompt']}<|end|><|assistant|>"
        with Image.open(request["image"]) as source:
            image = source.convert("RGB")
        inputs = processor(text=prompt, images=image, return_tensors="pt")
    else:
        prompt = f"<|user|>{request['prompt']}<|end|><|assistant|>"
        inputs = processor(text=prompt, return_tensors="pt")
    inputs = inputs.to("cuda:0")
    with torch.inference_mode():
        generated = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            generation_config=generation_config,
            do_sample=False,
        )
    generated = generated[:, inputs["input_ids"].shape[1]:]
    return processor.batch_decode(generated, skip_special_tokens=True, clean_up_tokenization_spaces=False)[0]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--model-id", default="phi4_multimodal_5_6b")
    parser.add_argument("--max-new-tokens", type=int, default=1024)
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()

    requests = [json.loads(line) for line in args.input.read_text(encoding="utf-8").splitlines() if line.strip()]
    if args.limit is not None:
        requests = requests[:args.limit]
    if not requests:
        raise ValueError("Input manifest is empty")
    if args.output.exists():
        raise FileExistsError(f"Refusing to overwrite {args.output}")

    torch, model, processor, generation_config = load_model(args.model)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as handle:
        for index, request in enumerate(requests, start=1):
            raw = generate_one(torch, model, processor, generation_config, request, args.max_new_tokens)
            parsed = extract_json_object(raw)
            row = {
                "request_id": request["request_id"],
                "task": request["task"],
                "prompt_condition": request["prompt_condition"],
                "example_id": request["example_id"],
                "model_id": args.model_id,
                "checkpoint": args.model,
                "parsed": parsed,
                "parse_valid": parsed is not None,
                "raw_response": raw,
            }
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
            handle.flush()
            print(f"{index}/{len(requests)} {request['request_id']} valid_json={parsed is not None}", flush=True)


if __name__ == "__main__":
    main()

