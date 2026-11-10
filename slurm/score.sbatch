#!/usr/bin/env bash
# Adapt CPU, memory, and time directives to your cluster.
#SBATCH --job-name=food-vlm-score
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=01:00:00
#SBATCH --output=results/slurm/%x_%j.out
#SBATCH --error=results/slurm/%x_%j.err

set -euo pipefail
: "${FOOD_VQA_PYTHON:=python}"
mkdir -p results/slurm

"$FOOD_VQA_PYTHON" src/evaluate_assignment_vlm.py \
  --data-root data/raw \
  --predictions results/predictions \
  --out-dir results/scored

