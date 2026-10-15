#!/bin/bash
#SBATCH --job-name=llm_evaluation_harness
#SBATCH --output=%j.out
#SBATCH --error=%j.err          
#SBATCH --cpus-per-task=8
#SBATCH --mem=16G                      
#SBATCH --partition=dgx       
#SBATCH --gres=gpu:1


nvidia-smi

# Cargar variables de entorno desde .env
set -a
source .env
set +a


huggingface-cli login --token $HF_TOKEN

cd ../

bash ./entrypoint.sh