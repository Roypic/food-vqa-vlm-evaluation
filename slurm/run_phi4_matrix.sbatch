#!/usr/bin/env bash
# Adapt partition, account, GPU, memory, and time directives to your cluster.
#SBATCH --job-name=food-phi4
#SBATCH --nodes=1
#SBATCH --gpus-per-node=1
#SBATCH --cpus-per-task=6
#SBATCH --mem=64G
#SBATCH --time=03:00:00
#SBATCH --array=0-9%4
#SBATCH --output=results/slurm/%x_%A_%a.out
#SBATCH --error=results/slurm/%x_%A_%a.err

set -euo pipefail

: "${FOOD_VQA_PYTHON:=python}"
: "${PHI4_MODEL:=microsoft/Phi-4-multimodal-instruct}"

export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export TOKENIZERS_PARALLELISM=false

CONFIGS=(
  image_open__baseline
  image_open__cot
  image_closed__baseline
  image_closed__cot
  image_nutrition__baseline
  image_nutrition__cot
  image_nutrition__cot_rag
  text_nutrition__baseline
  text_nutrition__cot
  text_nutrition__cot_rag
)
config="${CONFIGS[$SLURM_ARRAY_TASK_ID]}"
input="results/requests/${config}.jsonl"
output="results/predictions/phi4_multimodal_5_6b/${config}.jsonl"

test -f "$input"
test ! -e "$output"
mkdir -p "$(dirname "$output")" results/slurm

"$FOOD_VQA_PYTHON" src/run_assignment_phi4.py \
  --model "$PHI4_MODEL" \
  --model-id phi4_multimodal_5_6b \
  --input "$input" \
  --output "$output"

