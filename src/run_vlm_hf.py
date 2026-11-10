#!/usr/bin/env python3
"""Run a Hugging Face Qwen-VL-style model over a prompt-manifest JSONL.

This runner is intentionally executed on a Slurm GPU node, not during the data
audit.  It keeps the model response separate from the evaluator's canonical
JSONL: malformed responses are retained as abstentions with the raw response
for debugging, while ``evaluate_predictions.py`` scores only valid totals.

The default model is a 3B Qwen2.5-VL checkpoint suitable for a 24 GB class GPU;
pass ``--model`` to use a local path or another compatible Qwen-VL checkpoint.
"""

from __future__ import annotations

import argparse
import difflib
import json
import re
from pathlib import Path
from typing import Any

import pandas as pd


def extract_json_object(text: str) -> dict[str, Any] | None:
    """Extract the last balanced JSON object from a model response."""
    candidates: list[str] = []
    for match in re.finditer(r"\{", text):
        start = match.start()
        depth = 0
        in_string = False
        escaped = False
        for position in range(start, len(text)):
            char = text[position]
            if in_string:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    in_string = False
                continue
            if char == '"':
                in_string = True
            elif char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    candidates.append(text[start : position + 1])
                    break
    parsed_objects: list[dict[str, Any]] = []
    for candidate in candidates:
        try:
            value = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            parsed_objects.append(value)
    # Prefer the contract object over a nested ``totals`` object when the
    # response contains both outer and inner JSON dictionaries.
    for value in reversed(parsed_objects):
        if "totals" in value or "food_items" in value:
            return value
    if parsed_objects:
        return parsed_objects[-1]
    return None


def coerce_number(value: Any) -> float | None:
    """Normalize JSON numbers and common model-emitted null strings."""
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, str):
        value = value.strip()
        if value.lower() in {"", "null", "none", "n/a", "na", "unknown"}:
            return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def normalize_food(value: Any) -> str:
    text = "" if value is None else str(value).lower().strip()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def rag_totals(food_items: Any, fdc: pd.DataFrame) -> tuple[dict[str, float] | None, str | None]:
    """Calculate nutrition from predicted food/grams using the local FDC CSV."""
    if not isinstance(food_items, list) or not food_items:
        return None, "RAG could not calculate totals because food_items is empty"
    names = {normalize_food(name): row for _, row in fdc.iterrows() for name in [row["food"]]}
    aliases = {
        normalize_food("green beans cooked"): normalize_food("Green beans, NS as to form, cooked"),
        normalize_food("fruit juice"): normalize_food("Fruit juice, NFS"),
        normalize_food("meat sauce bolognese"): normalize_food("MEAT SAUCE 'BOLOGNESE'"),
    }
    totals = {"energy_kcal": 0.0, "carb_g": 0.0, "protein_g": 0.0, "fat_g": 0.0}
    unresolved: list[str] = []
    for item in food_items:
        if not isinstance(item, dict):
            unresolved.append("non-dict food item")
            continue
        food = str(item.get("food", "")).strip()
        grams = coerce_number(item.get("weight_g"))
        key = normalize_food(food)
        key = aliases.get(key, key)
        if not food or grams is None or grams < 0 or key not in names:
            if key not in names and food:
                candidate = difflib.get_close_matches(key, list(names), n=1, cutoff=0.55)
                if candidate:
                    key = candidate[0]
            if grams is None or key not in names:
                unresolved.append(food or "unknown food")
                continue
        row = names[key]
        totals["energy_kcal"] += grams * float(row["Energy"]) / 100.0
        totals["carb_g"] += grams * float(row["Carbohydrate, by difference"]) / 100.0
        totals["protein_g"] += grams * float(row["Protein"]) / 100.0
        totals["fat_g"] += grams * float(row["Total lipid (fat)"]) / 100.0
    if unresolved:
        return None, "RAG unresolved food/weight fields: " + ", ".join(unresolved)
    return totals, None


def load_qwen(model_name: str, max_pixels: int):
    try:
        import torch
        from transformers import AutoProcessor
        import transformers
    except ImportError as exc:  # pragma: no cover - depends on the Slurm env.
        raise RuntimeError(
            "Install torch, transformers with Qwen2.5-VL support, and qwen-vl-utils "
            "in the Slurm environment before running this script."
        ) from exc

    if "Qwen3-VL" in model_name and hasattr(transformers, "Qwen3VLForConditionalGeneration"):
        model_class = transformers.Qwen3VLForConditionalGeneration
    elif hasattr(transformers, "Qwen2_5_VLForConditionalGeneration"):
        model_class = transformers.Qwen2_5_VLForConditionalGeneration
    else:  # pragma: no cover - depends on the Slurm environment.
        raise RuntimeError("Installed transformers has no supported Qwen-VL model class")
    model = model_class.from_pretrained(
        model_name,
        dtype="auto",
        device_map="auto",
    )
    processor = AutoProcessor.from_pretrained(
        model_name,
        min_pixels=256 * 28 * 28,
        max_pixels=max_pixels,
    )
    return torch, model, processor


def generate_one(torch, model, processor, image_path: str, prompt: str, max_new_tokens: int) -> str:
    try:
        from qwen_vl_utils import process_vision_info
    except ImportError as exc:  # pragma: no cover - depends on the Slurm env.
        raise RuntimeError("qwen-vl-utils is required by the Qwen-VL runner") from exc

    messages = [{
        "role": "user",
        "content": [
            {"type": "image", "image": image_path},
            {"type": "text", "text": prompt},
        ],
    }]
    text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    image_inputs, video_inputs = process_vision_info(messages)
    inputs = processor(
        text=[text],
        images=image_inputs,
        videos=video_inputs,
        padding=True,
        return_tensors="pt",
    )
    inputs = inputs.to(model.device)
    generated_ids = model.generate(**inputs, max_new_tokens=max_new_tokens)
    trimmed = [output_ids[len(input_ids):] for input_ids, output_ids in zip(inputs.input_ids, generated_ids)]
    return processor.batch_decode(trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False)[0]


def canonical_row(request: dict[str, Any], raw_response: str, fdc: pd.DataFrame | None = None) -> dict[str, Any]:
    parsed = extract_json_object(raw_response)
    if parsed is None:
        return {
            "meal_id": request["meal_id"],
            "condition": request.get("condition", "unknown"),
            "food_items": [],
            "totals": {"energy_kcal": None, "carb_g": None, "protein_g": None, "fat_g": None},
            "abstain": True,
            "abstain_reason": "model response did not contain valid JSON",
            "raw_response": raw_response,
        }
    totals = parsed.get("totals") if isinstance(parsed.get("totals"), dict) else {}
    normalized_totals = {
        key: coerce_number(totals.get(key))
        for key in ("energy_kcal", "carb_g", "protein_g", "fat_g")
    }
    rag_reason = None
    if request.get("condition") in {"rgb_rag", "agent_rag"} and fdc is not None:
        rag_result, rag_reason = rag_totals(parsed.get("food_items", []), fdc)
        if rag_result is not None:
            normalized_totals = rag_result
    abstain = bool(parsed.get("abstain", False)) or all(value is None for value in normalized_totals.values())
    if rag_reason is not None:
        abstain = True
    return {
        "meal_id": request["meal_id"],
        "condition": request.get("condition", "unknown"),
        "food_items": parsed.get("food_items", []),
        "totals": normalized_totals,
        "abstain": abstain,
        "abstain_reason": rag_reason or parsed.get("abstain_reason"),
        "raw_response": raw_response,
    }


def refinement_prompt(request: dict[str, Any], draft: dict[str, Any]) -> str:
    """Create the second, critic pass prompt for the structured agent flow."""
    draft_for_prompt = {key: value for key, value in draft.items() if key != "raw_response"}
    return (
        "Re-inspect the same meal image as a strict critic. Correct the draft below "
        "using visual evidence and the visible reference card. Return JSON only "
        "with the same schema. Every visible food item should have a numeric "
        "weight_g estimate and totals should be numeric; do not output string "
        "'null' and do not abstain merely because the estimate is approximate. "
        "Remove hallucinated items and preserve genuine items.\n\n"
        "Draft from pass 1:\n" + json.dumps(draft_for_prompt, ensure_ascii=False) + "\n\n"
        "Schema:\n" + json.dumps({
            "food_items": [{"food": "example food", "weight_g": 100, "confidence": 0.5}],
            "totals": {"energy_kcal": 100, "carb_g": 10, "protein_g": 10, "fat_g": 5},
            "abstain": False,
            "abstain_reason": None,
        }, ensure_ascii=False)
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True, help="Prompt-manifest JSONL")
    parser.add_argument("--output", type=Path, required=True, help="Prediction JSONL")
    parser.add_argument("--model", default="Qwen/Qwen2.5-VL-3B-Instruct")
    parser.add_argument("--fdc", type=Path, default=Path("data/raw/FDC_USDA_subset.csv"))
    parser.add_argument("--max-pixels", type=int, default=1280 * 28 * 28)
    parser.add_argument("--max-new-tokens", type=int, default=512)
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    requests = [json.loads(line) for line in args.input.read_text(encoding="utf-8").splitlines() if line.strip()]
    if args.limit is not None:
        requests = requests[: args.limit]
    if not requests:
        raise ValueError("No requests found")

    torch, model, processor = load_qwen(args.model, max_pixels=args.max_pixels)
    fdc = None
    if any(request.get("condition") == "rgb_rag" for request in requests):
        fdc = pd.read_csv(args.fdc)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        for index, request in enumerate(requests, start=1):
            raw = generate_one(torch, model, processor, request["image"], request["prompt"], args.max_new_tokens)
            row = canonical_row(request, raw, fdc=fdc)
            if request.get("condition") == "agent_rag":
                refined_request = dict(request)
                refined_request["prompt"] = refinement_prompt(request, row)
                refined_raw = generate_one(
                    torch,
                    model,
                    processor,
                    request["image"],
                    refined_request["prompt"],
                    args.max_new_tokens,
                )
                refined_row = canonical_row(request, refined_raw, fdc=fdc)
                refined_row["agent_stage1"] = row
                refined_row["raw_response_stage1"] = raw
                row = refined_row
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
            handle.flush()
            print(f"{index}/{len(requests)} {request['meal_id']}")


if __name__ == "__main__":
    main()
