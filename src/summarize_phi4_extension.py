#!/usr/bin/env python3
"""Write a readable Phi-4 extension summary from the common evaluator output."""

from __future__ import annotations

import json
from pathlib import Path


METRICS = Path("results/main_assignment_vlm/scored/metrics.json")
OUTPUT = Path("results/main_assignment_vlm/phi4_multimodal/results_summary.md")
MODEL = "phi4_multimodal_5_6b"


def pct(value: float) -> str:
    return f"{100 * value:.1f}%"


def main() -> None:
    data = json.loads(METRICS.read_text(encoding="utf-8"))
    groups = data["groups"]
    required = [key for key in groups if key.startswith(MODEL + "::")]
    if len(required) != 10:
        raise ValueError(f"Expected 10 Phi-4 groups, found {len(required)}")

    lines = [
        "# Phi-4 multimodal extension results",
        "",
        "`microsoft/Phi-4-multimodal-instruct` (5.6B) was evaluated without fine-tuning on the same frozen 290 requests.",
        "",
        "## Food recognition",
        "",
        "| Task | Prompt | Item accuracy | Exact meal-set accuracy |",
        "|---|---|---:|---:|",
    ]
    for task, label in (("image_open", "Open-ended"), ("image_closed", "Closed-set")):
        for condition in ("baseline", "cot"):
            group = groups[f"{MODEL}::{task}::{condition}"]
            lines.append(
                f"| {label} | {condition.upper()} | {pct(group['item_accuracy_micro_recall'])} | {pct(group['exact_meal_set_accuracy'])} |"
            )

    for task, title in (("image_nutrition", "Image nutrition with correct labels"), ("text_nutrition", "Free-text nutrition")):
        lines.extend([
            "",
            f"## {title}",
            "",
            "Each nutrient cell is `MAE / MAPE`.",
            "",
            "| Prompt | Coverage | Energy (kcal) | Carb (g) | Protein (g) | Fat (g) |",
            "|---|---:|---:|---:|---:|---:|",
        ])
        for condition in ("baseline", "cot", "cot_rag"):
            group = groups[f"{MODEL}::{task}::{condition}"]
            if task == "image_nutrition":
                group = group["raw_primary"]
            cells = []
            for nutrient in ("energy_kcal", "carb_g", "protein_g", "fat_g"):
                metric = group["metrics"][nutrient]
                cells.append(f"{metric['mae']:.1f} / {metric['mape_percent']:.1f}%")
            lines.append(
                f"| {condition.upper().replace('_', ' + ')} | {pct(group['coverage'])} | " + " | ".join(cells) + " |"
            )

    lines.extend([
        "",
        "The primary two-model results remain unchanged. This file is an additional model-family comparison.",
        "",
    ])
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines), encoding="utf-8")
    print(OUTPUT)


if __name__ == "__main__":
    main()

