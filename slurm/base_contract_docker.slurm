#!/bin/bash
#SBATCH --job-name=llm_evaluation_harness          # Nombre del trabajo
#SBATCH --output=%j.out         # Nombre del archivo de salida
#SBATCH --error=%j.err          # Nombre del archivo de error
#SBATCH --cpus-per-task=16             # Número de CPUs por tarea
#SBATCH --mem=32G                      # Memoria por nodo
#SBATCH --partition=dgx          # Cola (partición) a la que enviar el trabajo
#SBATCH --gres=gpu:2
# Cargar variables de entorno desde el archivo .env
set -a
source .env
set +a

source /home/gplsi/santi/anaconda3/etc/profile.d/conda.sh

CPUSET=$(taskset -cp $$ | awk -F: '{print $2}' | tr -d ' ') #Número de gpus a usar
echo "SLURM-assigned CPU cores: $CPUSET"

umask 007
# Aquí empieza la sección de comandos que se van a ejecutar

echo "Iniciando trabajo en `hostname` a las `date` $SLURM_IDX"
nombrecont=$SLURM_JOBID"_nombrecont"
echo $nombrecont
echo "CUDA_VISIBLE_DEVICES: $CUDA_VISIBLE_DEVICES"
nvidia-smi
R=`pwd`
# Ejecuta tu programa aquí (reemplaza esto con lo que desees ejecutar)
# Ejecutar el contenedor con acceso a la GPU
#echo "Checking if the container still active."
#docker stop gplsi_lm-evaluation-harness_1
##
#docker rm gplsi_lm-evaluation-harness_1
#docker rmi lm-evaluation-harness
mkdir -p $EVALUATION_FOLDER
mkdir -p $EVALUATION_FOLDER_GOLD

echo "Building lm-evaluation-harness Docker image..."
echo "USER ID: $USER_ID"
echo "GROUP ID: $GROUP_ID"

docker ps
docker build \
  --network=host \
  --no-cache \
  --build-arg USER_ID=$USER_ID \
  --build-arg GROUP_ID=$GROUP_ID \
  -f ../Dockerfile \
  -t mt-evaluation:latest \
  ..
echo "Running mt-evaluation Docker container..."
docker run --rm \
  --cpuset-cpus="$CPUSET" \
  --ipc=host \
  --gpus all  \
  --network=host \
  --env CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES}" \
  --env NVIDIA_DRIVER_CAPABILITIES=compute,utility \
  --env WANDB_API_KEY="${WANDB_API_KEY}" \
  --env MODELS_TO_EVALUATE="${MODELS_TO_EVALUATE}" \
  --env HF_TOKEN="${HF_TOKEN}" \
  --env WANDB_PROJECT="${WANDB_PROJECT}" \
  --env USER_ID="${USER_ID}" \
  --env GROUP_ID="${GROUP_ID}" \
  --env INSTRUCT_EVALUATION="${INSTRUCT_EVALUATION}" \
  --env SHOTS="${SHOTS}" \
  --env OUTPUT_DIR="${OUTPUT_DIR}" \
  --env EVALUATION_FOLDER=/home/user/app/evaluaciones \
  --env EVALUATION_FOLDER_GOLD=/home/user/app/evaluaciones_gold \
  --env LANGUAGES="${LANGUAGES}" \
  --env SRC_LANGUAGE="${SRC_LANGUAGE}" \
  --env TGT_LANGUAGE="${TGT_LANGUAGE}" \
  --env PROMPT_STYLE="${PROMPT_STYLE}" \
  --volume $MODELS_FOLDER:/models \
  --volume $EVALUATION_FOLDER:/home/user/app/evaluaciones \
  --volume $EVALUATION_FOLDER_GOLD:/home/user/app/evaluaciones_gold \
  --volume ../outputLogs:/home/user/app/outputLogs/ \
  mt-evaluation:latest 
  



echo "Trabajo finalizado a las `date`"
