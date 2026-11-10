#!/usr/bin/env python3
"""Run one frozen assignment request manifest with a local Qwen VLM."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from run_vlm_hf import extract_json_object, load_qwen


def generate_one(torch, model, processor, request: dict[str, Any], max_new_tokens: int) -> str:
    try:
        from qwen_vl_utils import process_vision_info
    except ImportError as exc:  # pragma: no cover - cluster environment
        raise RuntimeError("qwen-vl-utils is required") from exc

    content: list[dict[str, Any]] = []
    if request.get("image"):
        content.append({"type": "image", "image": request["image"]})
    content.append({"type": "text", "text": request["prompt"]})
    messages = [{"role": "user", "content": content}]
    rendered = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    image_inputs, video_inputs = process_vision_info(messages)
    kwargs: dict[str, Any] = {
        "text": [rendered],
        "padding": True,
        "return_tensors": "pt",
    }
    if image_inputs:
        kwargs["images"] = image_inputs
    if video_inputs:
        kwargs["videos"] = video_inputs
    inputs = processor(**kwargs).to(model.device)
    with torch.inference_mode():
        generated = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            use_cache=True,
        )
    trimmed = [output[len(source):] for source, output in zip(inputs.input_ids, generated)]
    return processor.batch_decode(trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False)[0]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--model-id", required=True)
    parser.add_argument("--max-pixels", type=int, default=1280 * 28 * 28)
    parser.add_argument("--max-new-tokens", type=int, default=1024)
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()

    requests = [json.loads(line) for line in args.input.read_text(encoding="utf-8").splitlines() if line.strip()]
    if args.limit is not None:
        requests = requests[: args.limit]
    if not requests:
        raise ValueError("Input manifest is empty")
    if args.output.exists():
        raise FileExistsError(f"Refusing to overwrite {args.output}")

    torch, model, processor = load_qwen(args.model, max_pixels=args.max_pixels)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as handle:
        for index, request in enumerate(requests, start=1):
            raw = generate_one(torch, model, processor, request, args.max_new_tokens)
            parsed = extract_json_object(raw)
            output = {
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
            handle.write(json.dumps(output, ensure_ascii=False) + "\n")
            handle.flush()
            print(f"{index}/{len(requests)} {request['request_id']} valid_json={parsed is not None}", flush=True)


if __name__ == "__main__":
    main()

