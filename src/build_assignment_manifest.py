#!/usr/bin/env python3
"""Build the frozen request manifests for the assignment-aligned VLM study."""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import re
from pathlib import Path
from typing import Any

import pandas as pd


NUTRIENT_COLUMNS = {
    "energy_kcal": "Energy",
    "carb_g": "Carbohydrate, by difference",
    "protein_g": "Protein",
    "fat_g": "Total lipid (fat)",
}


def normalise(value: Any) -> str:
    text = "" if value is None else str(value).lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    tokens = re.sub(r"\s+", " ", text).strip().split()
    tokens = [token[:-1] if len(token) > 3 and token.endswith("s") and not token.endswith(("ss", "us")) else token for token in tokens]
    return " ".join(tokens)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def retrieve(query: str, fdc: pd.DataFrame, limit: int = 3) -> list[dict[str, Any]]:
    """Return deterministic lexical candidates without using target totals."""
    query_norm = normalise(query)
    query_tokens = set(query_norm.split())
    ranked: list[tuple[tuple[float, float, float, int], dict[str, Any]]] = []
    for _, row in fdc.iterrows():
        name = str(row["food"])
        name_norm = normalise(name)
        name_tokens = set(name_norm.split())
        overlap = query_tokens & name_tokens
        exact = float(query_norm == name_norm)
        coverage = len(overlap) / max(1, len(query_tokens))
        similarity = difflib.SequenceMatcher(None, query_norm, name_norm).ratio()
        if not exact and not overlap and similarity < 0.55:
            continue
        record = {
            "fdc_id": int(row["fdcid"]),
            "food": name,
            "nutrients_per_100g": {
                key: float(row[column]) for key, column in NUTRIENT_COLUMNS.items()
            },
        }
        key = (exact, coverage, similarity, -int(row["fdcid"]))
        ranked.append((key, record))
    ranked.sort(key=lambda item: item[0], reverse=True)
    return [record for _, record in ranked[:limit]]


def split_question_segments(question: str) -> list[str]:
    matches = list(re.finditer(r"\d+(?:\.\d+)?\s*g\b", question, flags=re.I))
    segments: list[str] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(question)
        segment = question[match.end():end]
        segment = re.sub(r"[\s,;.]+$", "", segment)
        segment = re.sub(r"\s*,?\s*(?:and|with)\s*$", "", segment, flags=re.I)
        segments.append(segment.strip(" ,;."))
    return [segment for segment in segments if segment]


def rag_block(queries: list[str], fdc: pd.DataFrame) -> tuple[str, list[dict[str, Any]]]:
    retrieved: list[dict[str, Any]] = []
    lines = ["Retrieved USDA FoodData Central candidates (values are per 100 g):"]
    for query in queries:
        candidates = retrieve(query, fdc)
        retrieved.append({"query": query, "candidates": candidates})
        lines.append(f"Query: {query}")
        for record in candidates:
            n = record["nutrients_per_100g"]
            lines.append(
                f"- FDC {record['fdc_id']}: {record['food']}; energy {n['energy_kcal']:.4g} kcal; "
                f"carbohydrate {n['carb_g']:.4g} g; protein {n['protein_g']:.4g} g; fat {n['fat_g']:.4g} g"
            )
    lines.append("Select only records that match the stated food and preparation. Cite selected FDC IDs in the JSON.")
    return "\n".join(lines), retrieved


def recognition_prompt(task: str, condition: str, vocabulary: list[str]) -> str:
    if task not in {"image_open", "image_closed"} or condition not in {"baseline", "cot"}:
        raise ValueError("Invalid recognition task/condition")
    text = (
        "Identify every distinct food visible in the meal image. Return one JSON object only with this schema: "
        '{"food_labels":["food name"],"reasoning_summary":null}. '
        "Your first character must be { and your last character must be }. Do not write analysis before or after the JSON. "
        "Do not estimate calories or nutrients. Do not include utensils, plates, or the reference card as food."
    )
    if task == "image_open":
        text += " This is open-ended recognition: use concise food names you infer from the image."
    else:
        text += " This is closed-set recognition. Use only labels from this list and copy their spelling exactly:\n- " + "\n- ".join(vocabulary)
    if condition == "baseline":
        text += " Set reasoning_summary to null and answer directly."
    else:
        text += (
            " Assess the image step by step: locate separate portions, use appearance and context, then check for omissions. "
            "Put a summary of at most 80 words in reasoning_summary; do not add text outside JSON."
        )
    return text


def nutrition_prompt(
    task: str,
    condition: str,
    content: str,
    labels: list[str],
    rag_context: str | None,
) -> str:
    schema = (
        '{"portion_estimates":[{"food":"name","weight_g":100}],'
        '"totals":{"energy_kcal":100,"carb_g":10,"protein_g":10,"fat_g":5},'
        '"fdc_ids_used":[],"reasoning_summary":null}'
    )
    if task == "image_nutrition":
        intro = (
            "Estimate energy and macronutrients for the meal image. Food recognition is assumed correct. "
            "Use exactly these supplied food labels: " + "; ".join(labels) + ". "
            "Estimate visible portion weights from the image; no measured weights or target totals are provided."
        )
    elif task == "text_nutrition":
        intro = "Answer this free-text nutrition question: " + content
    else:
        raise ValueError("Invalid nutrition task")
    prompt = intro + "\nReturn one JSON object only with this schema: " + schema + (
        ". Your first character must be { and your last character must be }. Do not write calculations before or after the JSON. "
        "All four totals must be numeric and non-negative. Keep reasoning_summary at or below 80 words."
    )
    if condition == "baseline":
        prompt += " Answer directly from the model's existing knowledge. Set reasoning_summary to null and fdc_ids_used to []."
    elif condition == "cot":
        prompt += (
            " Work step by step: estimate or read each portion mass, estimate per-100-g nutrition for each food, scale each value, "
            "and sum the foods. Put a brief ordered calculation summary in reasoning_summary and use fdc_ids_used=[]."
        )
    elif condition == "cot_rag":
        if not rag_context:
            raise ValueError("RAG condition requires retrieved context")
        prompt += (
            " Work step by step: choose the most appropriate retrieved record for each food, estimate or read mass, scale the "
            "per-100-g values, and sum the foods. Put a brief ordered calculation summary in reasoning_summary.\n\n" + rag_context
        )
    else:
        raise ValueError("Invalid prompt condition")
    return prompt


def build(data_root: Path) -> list[dict[str, Any]]:
    gt_path = data_root / "Images GT.xlsx"
    q_path = data_root / "Questions 50.xlsx"
    fdc_path = data_root / "FDC_USDA_subset.csv"
    gt = pd.read_excel(gt_path, sheet_name="Ground truths")
    questions = pd.read_excel(q_path)
    fdc = pd.read_csv(fdc_path)
    vocabulary = sorted(gt["Food"].dropna().astype(str).str.strip().unique())
    rows: list[dict[str, Any]] = []
    for image_path in sorted((data_root / "Meal Images").iterdir()):
        if image_path.suffix.lower() not in {".jpg", ".jpeg", ".png"}:
            continue
        meal_number = int(re.search(r"MEAL(\d+)", image_path.stem, flags=re.I).group(1))
        meal_id = f"Meal{meal_number:02d}"
        labels = gt.loc[gt["Meal_ID"].eq(meal_id), "Food"].dropna().astype(str).str.strip().tolist()
        for task in ("image_open", "image_closed"):
            for condition in ("baseline", "cot"):
                rows.append({
                    "request_id": f"{task}:{condition}:{meal_id}",
                    "task": task,
                    "prompt_condition": condition,
                    "example_id": meal_id,
                    "image": str(image_path.resolve()),
                    "prompt": recognition_prompt(task, condition, vocabulary),
                    "retrieval": [],
                })
        for condition in ("baseline", "cot", "cot_rag"):
            context, retrieval = rag_block(labels, fdc) if condition == "cot_rag" else (None, [])
            rows.append({
                "request_id": f"image_nutrition:{condition}:{meal_id}",
                "task": "image_nutrition",
                "prompt_condition": condition,
                "example_id": meal_id,
                "image": str(image_path.resolve()),
                "prompt": nutrition_prompt("image_nutrition", condition, "", labels, context),
                "retrieval": retrieval,
            })
    for index, row in questions.reset_index(drop=True).iterrows():
        question = str(row["Questions"])
        example_id = f"Q{index + 1:02d}"
        segments = split_question_segments(question)
        for condition in ("baseline", "cot", "cot_rag"):
            context, retrieval = rag_block(segments, fdc) if condition == "cot_rag" else (None, [])
            rows.append({
                "request_id": f"text_nutrition:{condition}:{example_id}",
                "task": "text_nutrition",
                "prompt_condition": condition,
                "example_id": example_id,
                "image": None,
                "prompt": nutrition_prompt("text_nutrition", condition, question, [], context),
                "retrieval": retrieval,
            })
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, default=Path("data/raw"))
    parser.add_argument("--out-dir", type=Path, default=Path("results/main_assignment_vlm/requests"))
    args = parser.parse_args()
    rows = build(args.data_root)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "protocol": "docs/assignment_aligned_protocol.md",
        "input_sha256": {
            name: sha256(args.data_root / name)
            for name in ("Images GT.xlsx", "Questions 50.xlsx", "FDC_USDA_subset.csv")
        },
        "counts": {},
    }
    for task in sorted({row["task"] for row in rows}):
        for condition in sorted({row["prompt_condition"] for row in rows if row["task"] == task}):
            selected = [row for row in rows if row["task"] == task and row["prompt_condition"] == condition]
            path = args.out_dir / f"{task}__{condition}.jsonl"
            path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in selected), encoding="utf-8")
            manifest["counts"][f"{task}__{condition}"] = len(selected)
    (args.out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()

