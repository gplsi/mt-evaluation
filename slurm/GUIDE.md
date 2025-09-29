# Slurm configuration lm-evaluation-harness

This directory contains production-ready SLURM scripts for running evaluations using the **lm-evaluation-harness** framework on SLURM clusters. Supports both **Docker** and **Anaconda** environments.


## 🚀 Quick Reference

### Most Common Commands

```sh
# Submit a job using Conda
./submit_job.sh -c ../config/experiments/EXPERIMENT_NAME.yaml

# Submit a job using Docker
./submit_job.sh -c ../config/experiments/EXPERIMENT_NAME.yaml -d

# Submit a job with custom resources
./submit_job.sh -c ../config/experiments/instruct_evaluation_schema.yaml -d -g 1 -m 64G -p PARTITION_NAME

# Check job status
squeue -u $(whoami)

# Monitor logs
tail -f ./experiments/<<EXPERMIENT_ID>>/<<JOB_ID_LM_EVALUATION_HARNESS>>.out

```

**Quick Parameter Guide:**

* `-c`: Config file (required)
* `-d`: Execution via **Docker** (default execution with **Anaconda ENVIROMENT**)
* `-g`: GPU count (default: 2)
* `-m`: Memory (default: 32G)
* `-p`: Partition (default: **DGX**)


## 🧰 Getting Started

### Setting-up the enviroment

> ⚠️ Important: To run and monitor evaluations correctly, you must set up your **WANDB API key** and (if needed) your Hugging Face token. Some models require authentication to be downloaded.

Set the following enviroment variables:

```bash
export WANDB_API_KEY=wandb_api_key
export HF_TOKEN=hugging_face_token
```

### 🔧 First Job — Simplest Case

1. **Create an Experiment Config**

    Define your evaluation configuration inside the [../config/experiments](../config/experiments/) directory.

    You can use a predefined schema from .[../config/schema](../config/schema/) as a starting point.



    **Schema example**:
    ``` YAML
    # Description of the evaluation
    description: "Configuration file for evaluation of instruction-following models."

    # Name of the evaluation
    evaluation_name: "Aitana instruction evaluations"

    models:
    # Whether the models are stored locally
    local: true
    # List of model names to evaluate
    models_names: step-002756, step-005512
    # Path to local models
    models_path: /home/gplsi/GPLSI/ALIA/modelos/Instruction/Intruccion_v8_salamandra_2B/hf_models

    evaluation:
    # Output folder for evaluation results
    evaluation_folder: /home/gplsi/GPLSI/ALIA/modelos/Instruction/Intruccion_v8_salamandra_2B/evaluaciones
    # Path to gold-standard evaluations (optional)
    evaluation_folder_gold: /home/gplsi/GPLSI/ALIA/modelos/Evaluation/Instruction/gold
    # Instruction-following evaluation
    instruct: true
    # Number of shots
    shots: 0

    # WandB project name
    wandb_project: "Prueba"

    # Languages to include in the evaluation
    languages:
    - Spanish: false
    - English: false
    - Valencian: true
    - Catalan: false
    ```

2. **Submit the Job**
    
    Navigate to the `./slurm` directory and execute the `./submit_job.sh`. This script will validate the configuration file that you had set and launch the job in slurm in case everything is correct. 

    ``` bash
    ./submit_job.sh -c ../config/experiments/instruct_evaluation_shema.yaml -d
    ```
    **Output example**
    ```bash
        Docker mode: True
        Generating environment file for: Aitana instruction evaluations
        Environment file created: .env_20250728_163134_2126958
        Environment file created: .env_20250728_163134_2126958
        You can now run: bash launch_job.sh .env_20250728_163134_2126958
        Environment file generated.
        Expermient: 20250728_163134_2126958
        SLURM script: ./experiments/20250728_163134_2126958/slurm_job_20250728_163134_2126958.slurm
        Environment file: ./experiments/20250728_163134_2126958/.env_20250728_163134_2126958
        ##################################
        Submitted batch job 19838
    ```
3. **Monitor Job and Logs**
    Logs are stored in `./experiments/<job_timestamp>/`, where `<job_timestamp>` is the unique identifier for the evaluation.

    **Generated Files:**


    - `19838.err`: Error logs in slurm job. ##
    - `19838.out`: Output logs in slurm job.  
    - `outputLogs`: Evaluation process logs for the different models evalulated. 
    - `slurm_job_20250728_163134_2126958.slurm` : Slurm contract generated for the following job.
    


## 📄 Evaluation YAML configuration

| Key | Subkey | Type | Description | Required | Example |
|-----|--------|------|-------------|----------|---------|
| `description` | — | `string` | A short description of the evaluation. | ❌ | `"Instruction-following model evaluation"` |
| `evaluation_name` | — | `string` | The name assigned to the evaluation run. Used in logs and folders. | ❌| `"Aitana evaluation run"` |
| `models` | `local` | `bool` | Whether models are stored locally (`true`) or pulled from Hugging Face (`false`). | ✅ | `true` |
|  | `models_names` | `list` (comma-separated) or single `str` | List of model identifiers to evaluate. | ✅ | - List of models: `step-002756, step-005512` - Remote model `BSC-LT/salamandra-2b` |
|  | `models_path` | `string` | Path to the directory containing the models if `local` is `true`. | ✅ (if local) | `/path/to/models` |
| `evaluation` | `evaluation_folder` | `string` | Directory where evaluation results will be saved. | ✅ | `/path/to/results` |
|  | `evaluation_folder_gold` | `string` | Path to previous gold-standard evaluations (optional). Used for comparisons. | ❌ | `/path/to/gold` |
|  | `instruct` | `bool` | Indicates if the models are instruction-tuned. Activates instruct-specific evaluation logic. | ✅ | `true` |
|  | `shots` | `int` | Number of shots (examples) used in few-shot evaluation. **Should use 0 in case the models to evaluate are Instruct versions. **| ✅ | `0` |
| `wandb_project` | — | `string` | Name of the [Weights & Biases](https://wandb.ai) project to log results to. | ✅ | `"MyEvalProject"` |
| `languages` | — | `map` (language: bool) | Enable/disable evaluation tasks for specific languages. Each key is a language name, value is a boolean. | ✅ | `Valencian: true` |

> 💡 **Notes**: 
> * All file paths must be absolute to the root project directory.  
>  * Supported languages are **Spanish**, **Valencian**, **English**, and **Catalan**. 


### ✅ Minimal Valid Example

```yaml
description: "Test evaluation"
evaluation_name: "test_run"

models:
  local: true
  models_names: step-000001
  models_path: /home/user/models

evaluation:
  evaluation_folder: /home/user/results
  instruct: true
  shots: 0

wandb_project: "TestProject"

languages:
  - English: true

