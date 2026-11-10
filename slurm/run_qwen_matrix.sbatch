#!/usr/bin/env bash
# Adapt partition, account, GPU, memory, and time directives to your cluster.
#SBATCH --job-name=food-vlm
#SBATCH --nodes=1
#SBATCH --gpus-per-node=1
#SBATCH --cpus-per-task=6
#SBATCH --mem=64G
#SBATCH --time=03:00:00
#SBATCH --array=0-19%4
#SBATCH --output=results/slurm/%x_%A_%a.out
#SBATCH --error=results/slurm/%x_%A_%a.err

set -euo pipefail

: "${FOOD_VQA_PYTHON:=python}"
: "${QWEN25_MODEL:=Qwen/Qwen2.5-VL-7B-Instruct}"
: "${QWEN3_MODEL:=Qwen/Qwen3-VL-4B-Instruct}"

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
MODELS=("$QWEN25_MODEL" "$QWEN3_MODEL")
MODEL_IDS=(qwen2_5_vl_7b qwen3_vl_4b)

model_index=$((SLURM_ARRAY_TASK_ID / 10))
config_index=$((SLURM_ARRAY_TASK_ID % 10))
model="${MODELS[$model_index]}"
model_id="${MODEL_IDS[$model_index]}"
config="${CONFIGS[$config_index]}"
input="results/requests/${config}.jsonl"
output="results/predictions/${model_id}/${config}.jsonl"

test -f "$input"
test ! -e "$output"
mkdir -p "$(dirname "$output")" results/slurm

"$FOOD_VQA_PYTHON" src/run_assignment_vlm.py \
  --model "$model" \
  --model-id "$model_id" \
  --input "$input" \
  --output "$output"

