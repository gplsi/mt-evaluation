#!/bin/bash
cd ../

export HF_HOME=./cache
#export SINGULARITY_CACHEDIR=./cache_singularity
#export SINGULARITY_TMPDIR=./cache_singularity
export TORCHDYNAMO_SUPPRESS_ERRORS=True

model=$1
dataset=$2
few_shot=$3
tensor_parallelism=$4
wandb=$5
execution_name=$6
instruct=$7

# src, tgt and prompt_style is used for translation tasks
src_language=$8
tgt_language=$9
prompt_style=${10}

if [ "$computer" == "polaris" ]; then
    job_id=$PBS_JOBID
else
    # job_id=$SLURM_JOB_ID
    job_id=$RANDOM
fi

# output_dir=results/$(basename ${model})/results:$(basename ${model}):${dataset}:${few_shot}-shot_${job_id}.json
# output_dir=results/$(basename ${model})/results:$(basename ${model}):${execution_name}:${few_shot}-shot_${job_id}

output_dir=$EVALUATION_FOLDER/results/$(basename ${model})/results:$(basename ${model}):${execution_name}:${few_shot}-shot_${job_id}

cuda_device_count=$(python -c "import torch; print(torch.cuda.device_count())")
echo "Available GPUs: $cuda_device_count"
echo "Instruct evaluation: $instruct"


if [[ $model == *".nemo"* ]]; then
    # If it contains ".nemo", do the following
    echo "The model name contains '.nemo'."
    if [ $((cuda_device_count)) =< 1]; then
        lm_eval --model nemo_lm \
            --model_args path=$model \
            --tasks ${dataset} \
            --num_fewshot $few_shot \
            --batch_size 1 \
            --output_path $output_dir \
            --log_samples \
            --seed 1234
    else
        if [ "${tensor_parallelism}" == "True" ]; then
            torchrun --nproc-per-node=$((cuda_device_count)) lm_eval \
                --model nemo_lm \
                --model_args path=$model,devices=$((cuda_device_count)),tensor_model_parallel_size=$((cuda_device_count)) \
                --tasks ${dataset} \
                --num_fewshot $few_shot \
                --batch_size 1 \
                --output_path $output_dir \
                --log_samples \
                --seed 1234
        else
            torchrun --nproc-per-node=$((cuda_device_count)) lm_eval \
                --model nemo_lm \
                --model_args path=$model,devices=$((cuda_device_count)) \
                --tasks ${dataset} \
                --num_fewshot $few_shot \
                --batch_size 1 \
                --output_path $output_dir \
                --log_samples \
                --seed 1234
        fi
    fi
else
    # If it doesn't contain ".nemo", assume it is hf
    
    
    if [ "${tensor_parallelism}" == "True" ]; then
        if [ "${instruct}" == "True" ]; then
            echo "The model name does not contain '.nemo' and is an instruct model."
            python -m lm_eval --model hf \
                --model_args pretrained=$model,trust_remote_code=True,parallelize=True,instruct=True \
                --tasks ${dataset} \
                --num_fewshot $few_shot \
                --batch_size 1 \
                --output_path $output_dir \
                --log_samples \
                --apply_chat_template \
                --seed 1234
        else
            echo "The model name does not contain '.nemo'."
            python -m lm_eval --model hf \
                --model_args pretrained=$model,trust_remote_code=True,parallelize=True \
                --tasks ${dataset} \
                --num_fewshot $few_shot \
                --batch_size 1 \
                --output_path $output_dir \
                --log_samples \
                --seed 1234
        fi
    else
        PORT=$((29500 + (RANDOM % 1000) + 1))
        if [ "${instruct}" == "True" ]; then
            echo "The model name does not contain '.nemo' and is an instruct model."
            
            accelerate launch --main_process_port  $PORT \
                         -m lm_eval --model hf \
                        --model_args pretrained=$model,trust_remote_code=True \
                        --tasks ${dataset} \
                        --num_fewshot $few_shot \
                        --batch_size 1 \
                        --output_path $output_dir \
                        --log_samples \
                        --seed 1234 \
                        --apply_chat_template \
                        --wandb_args project=$wandb,entity=gplsi_continual
        else
        echo "The model name does not contain '.nemo'."
            echo $(pwd)
            cd mt-evaluation
            accelerate launch \
                         -m lm_eval --model hf \
                        --model_args pretrained=$model,trust_remote_code=True \
                        --tasks ${dataset} \
                        --num_fewshot $few_shot \
                        --batch_size 4 \
                        --output_path $output_dir \
                        --gen_kwargs 'num_beams=5,max_new_tokens=400,early_stopping=True' \
                        --translation_kwargs "src_language=${src_language},tgt_language=${tgt_language},prompt_style=${prompt_style}" \
                        --log_samples \
                        --seed 1234 \
                        #--wandb_args project=$wandb,entity=gplsi_continual
                    # gen kwargs should be commented
        fi  #--main_process_port  $PORT 
    fi
fi
