#!/usr/bin/env python3
"""Score the frozen Food VQA assignment matrix without fitting parameters."""

from __future__ import annotations

import argparse
import json
import math
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


METRICS = ("energy_kcal", "carb_g", "protein_g", "fat_g")
IMAGE_COLUMNS = {
    "energy_kcal": "Energy (kcal)",
    "carb_g": "Carbohydrates (g)",
    "protein_g": "Protein (g)",
    "fat_g": "Fat (g)",
}
TEXT_COLUMNS = {
    "energy_kcal": "Energy (kcal)",
    "carb_g": "Carbs (g)",
    "protein_g": "Protein (g)",
    "fat_g": "Fat (g)",
}


def normalise(value: Any) -> str:
    text = "" if value is None else str(value).lower()
    text = text.replace("potatoes", "potato").replace("eggs", "egg")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


ALIASES = {
    "pita bread": "bread pita whole wheat",
    "whole wheat pita": "bread pita whole wheat",
    "whole wheat pita bread": "bread pita whole wheat",
    "chocolate donut": "donut with chocolate icing",
    "chocolate doughnut": "donut with chocolate icing",
    "doughnut with chocolate icing": "donut with chocolate icing",
    "meat lasagna": "lasagna with meat",
    "bread roll": "roll white hard bread roll",
    "white bread roll": "roll white hard bread roll",
    "beef stew": "stew beef pork",
    "pork stew": "stew beef pork",
    "beef pork stew": "stew beef pork",
    "grilled chicken": "grilled chicken breast",
    "chicken breast": "grilled chicken breast",
    "cheddar cheese": "cheddar cheese cubes",
    "cheese cubes": "cheddar cheese cubes",
    "green bean": "green bean",
}


def canonical(value: Any) -> str:
    value = normalise(value)
    return ALIASES.get(value, value)


def similarity(left: str, right: str) -> float:
    import difflib

    left, right = canonical(left), canonical(right)
    if left == right:
        return 1.0
    return difflib.SequenceMatcher(None, left, right).ratio()


def match_labels(predicted: list[str], targets: list[str]) -> tuple[int, int, int]:
    candidates = sorted(
        (
            (similarity(pred, target), pred_index, target_index)
            for pred_index, pred in enumerate(predicted)
            for target_index, target in enumerate(targets)
        ),
        reverse=True,
    )
    used_pred: set[int] = set()
    used_target: set[int] = set()
    for score, pred_index, target_index in candidates:
        if score < 0.78:
            break
        if pred_index not in used_pred and target_index not in used_target:
            used_pred.add(pred_index)
            used_target.add(target_index)
    tp = len(used_target)
    return tp, len(predicted) - tp, len(targets) - tp


def number(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        value = float(value)
    except (TypeError, ValueError):
        return None
    return value if math.isfinite(value) and value >= 0 else None


def bootstrap_mean_ci(values: list[float], iterations: int = 10_000) -> list[float] | None:
    if not values:
        return None
    array = np.asarray(values, dtype=float)
    rng = np.random.default_rng(20261102 + len(array))
    indices = rng.integers(0, len(array), size=(iterations, len(array)))
    means = array[indices].mean(axis=1)
    return [float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))]


def has_valid_totals(row: dict[str, Any]) -> bool:
    parsed = row.get("parsed") if isinstance(row.get("parsed"), dict) else {}
    totals = parsed.get("totals") if isinstance(parsed.get("totals"), dict) else {}
    return all(number(totals.get(metric)) is not None for metric in METRICS)


def load_predictions(root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted(root.glob("*/*.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                row = json.loads(line)
                row["source_file"] = str(path)
                rows.append(row)
    request_ids = [row["request_id"] + "::" + row["model_id"] for row in rows]
    if len(request_ids) != len(set(request_ids)):
        raise ValueError("Duplicate model/request prediction")
    return rows


def aggregate_image_targets(data_root: Path, clean: bool) -> tuple[dict[str, dict[str, float]], dict[str, list[str]]]:
    if clean:
        path = Path("results/audit/ground_truth_clean_items.csv")
        frame = pd.read_csv(path)
    else:
        frame = pd.read_excel(data_root / "Images GT.xlsx", sheet_name="Ground truths")
    totals: dict[str, dict[str, float]] = {}
    labels: dict[str, list[str]] = {}
    for meal_id, group in frame.groupby("Meal_ID", sort=True):
        totals[str(meal_id)] = {
            metric: float(group[column].sum()) for metric, column in IMAGE_COLUMNS.items()
        }
        labels[str(meal_id)] = group["Food"].dropna().astype(str).str.strip().tolist()
    return totals, labels


def text_targets(data_root: Path) -> dict[str, dict[str, float]]:
    frame = pd.read_excel(data_root / "Questions 50.xlsx")
    return {
        f"Q{index + 1:02d}": {metric: float(row[column]) for metric, column in TEXT_COLUMNS.items()}
        for index, row in frame.reset_index(drop=True).iterrows()
    }


def nutrition_summary(rows: list[dict[str, Any]], targets: dict[str, dict[str, float]]) -> dict[str, Any]:
    errors: dict[str, list[float]] = defaultdict(list)
    percentages: dict[str, list[float]] = defaultdict(list)
    valid_rows = 0
    details: list[dict[str, Any]] = []
    for row in rows:
        parsed = row.get("parsed") if isinstance(row.get("parsed"), dict) else {}
        totals = parsed.get("totals") if isinstance(parsed.get("totals"), dict) else {}
        predicted = {metric: number(totals.get(metric)) for metric in METRICS}
        valid = all(predicted[metric] is not None for metric in METRICS)
        if valid:
            valid_rows += 1
        target = targets[row["example_id"]]
        item = {"example_id": row["example_id"], "valid": valid, "prediction": predicted, "target": target}
        details.append(item)
        if not valid:
            continue
        for metric in METRICS:
            error = abs(float(predicted[metric]) - target[metric])
            errors[metric].append(error)
            if target[metric] != 0:
                percentages[metric].append(100.0 * error / abs(target[metric]))
    return {
        "n_expected": len(rows),
        "n_valid": valid_rows,
        "coverage": valid_rows / len(rows) if rows else 0.0,
        "metrics": {
            metric: {
                "mae": float(np.mean(errors[metric])) if errors[metric] else None,
                "mae_bootstrap_95": bootstrap_mean_ci(errors[metric]),
                "mape_percent": float(np.mean(percentages[metric])) if percentages[metric] else None,
                "n": len(errors[metric]),
                "mape_n": len(percentages[metric]),
            }
            for metric in METRICS
        },
        "details": details,
    }


def recognition_summary(
    rows: list[dict[str, Any]],
    labels: dict[str, list[str]],
    vocabulary: set[str],
) -> dict[str, Any]:
    tp = fp = fn = exact = valid = outside = 0
    details: list[dict[str, Any]] = []
    for row in rows:
        parsed = row.get("parsed") if isinstance(row.get("parsed"), dict) else {}
        raw_labels = parsed.get("food_labels")
        predicted = [str(value).strip() for value in raw_labels if str(value).strip()] if isinstance(raw_labels, list) else []
        row_valid = isinstance(raw_labels, list)
        valid += int(row_valid)
        if row["task"] == "image_closed":
            outside += sum(canonical(value) not in vocabulary for value in predicted)
        target = labels[row["example_id"]]
        row_tp, row_fp, row_fn = match_labels(predicted, target)
        tp += row_tp
        fp += row_fp
        fn += row_fn
        row_exact = row_fp == 0 and row_fn == 0
        exact += int(row_exact)
        details.append({
            "example_id": row["example_id"],
            "valid": row_valid,
            "predicted": predicted,
            "target": target,
            "tp": row_tp,
            "fp": row_fp,
            "fn": row_fn,
            "exact_set": row_exact,
        })
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    return {
        "n_expected": len(rows),
        "n_valid": valid,
        "coverage": valid / len(rows) if rows else 0.0,
        "true_positive": tp,
        "false_positive": fp,
        "false_negative": fn,
        "item_accuracy_micro_recall": recall,
        "micro_precision": precision,
        "micro_f1": 2 * precision * recall / (precision + recall) if precision + recall else 0.0,
        "exact_meal_set_accuracy": exact / len(rows) if rows else 0.0,
        "closed_set_out_of_vocabulary_predictions": outside,
        "details": details,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, default=Path("data/raw"))
    parser.add_argument("--predictions", type=Path, default=Path("results/main_assignment_vlm/predictions"))
    parser.add_argument("--out-dir", type=Path, default=Path("results/main_assignment_vlm/scored"))
    args = parser.parse_args()

    rows = load_predictions(args.predictions)
    raw_targets, labels = aggregate_image_targets(args.data_root, clean=False)
    clean_target_path = Path("results/audit/ground_truth_clean_items.csv")
    clean_targets = aggregate_image_targets(args.data_root, clean=True)[0] if clean_target_path.exists() else None
    q_targets = text_targets(args.data_root)
    vocabulary = {canonical(label) for values in labels.values() for label in values}
    groups: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[(row["model_id"], row["task"], row["prompt_condition"])].append(row)

    result: dict[str, Any] = {
        "protocol": "docs/assignment_aligned_protocol.md",
        "prediction_rows": len(rows),
        "groups": {},
        "paired_prompt_comparisons": {},
        "paired_model_comparisons": {},
    }
    detail_rows: list[dict[str, Any]] = []
    for (model, task, condition), group in sorted(groups.items()):
        group.sort(key=lambda row: row["example_id"])
        key = f"{model}::{task}::{condition}"
        if task in {"image_open", "image_closed"}:
            summary = recognition_summary(group, labels, vocabulary)
            details = summary.pop("details")
        elif task == "image_nutrition":
            summary = {"raw_primary": nutrition_summary(group, raw_targets)}
            if clean_targets is not None:
                summary["clean_sensitivity"] = nutrition_summary(group, clean_targets)
            details = summary["raw_primary"].pop("details")
            if "clean_sensitivity" in summary:
                summary["clean_sensitivity"].pop("details")
        elif task == "text_nutrition":
            summary = nutrition_summary(group, q_targets)
            details = summary.pop("details")
        else:
            raise ValueError(f"Unknown task: {task}")
        result["groups"][key] = summary
        for detail in details:
            detail_rows.append({"model_id": model, "task": task, "condition": condition, **detail})

    # Recompute nutrition summaries on shared valid examples. This prevents a
    # malformed response in one condition from silently changing the test set.
    for model in sorted({key[0] for key in groups}):
        for task, targets in (("image_nutrition", raw_targets), ("text_nutrition", q_targets)):
            condition_groups = {
                condition: group for (group_model, group_task, condition), group in groups.items()
                if group_model == model and group_task == task
            }
            valid_ids: list[set[str]] = []
            for group in condition_groups.values():
                valid_ids.append({
                    row["example_id"] for row in group
                    if has_valid_totals(row)
                })
            common = set.intersection(*valid_ids) if valid_ids else set()
            comparison: dict[str, Any] = {"common_example_ids": sorted(common), "n_common": len(common), "conditions": {}}
            for condition, group in sorted(condition_groups.items()):
                summary = nutrition_summary([row for row in group if row["example_id"] in common], targets)
                summary.pop("details")
                comparison["conditions"][condition] = summary
            result["paired_prompt_comparisons"][f"{model}::{task}"] = comparison

    for task, targets in (("image_nutrition", raw_targets), ("text_nutrition", q_targets)):
        for condition in ("baseline", "cot", "cot_rag"):
            model_groups = {
                model: group for (model, group_task, group_condition), group in groups.items()
                if group_task == task and group_condition == condition
            }
            valid_ids = []
            for group in model_groups.values():
                valid_ids.append({
                    row["example_id"] for row in group
                    if has_valid_totals(row)
                })
            common = set.intersection(*valid_ids) if valid_ids else set()
            comparison = {"common_example_ids": sorted(common), "n_common": len(common), "models": {}}
            for model, group in sorted(model_groups.items()):
                summary = nutrition_summary([row for row in group if row["example_id"] in common], targets)
                summary.pop("details")
                comparison["models"][model] = summary
            result["paired_model_comparisons"][f"{task}::{condition}"] = comparison

    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "metrics.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    pd.DataFrame(detail_rows).to_json(args.out_dir / "per_example.jsonl", orient="records", lines=True, force_ascii=False)
    print(json.dumps({"prediction_rows": len(rows), "groups": len(groups), "output": str(args.out_dir)}, indent=2))


if __name__ == "__main__":
    main()

