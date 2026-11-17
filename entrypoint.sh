#!/bin/bash
# AUTENTICATE IN WANDB 
wandb login $WANDB_API_KEY  # Authenticate W&B
#PARSE STRING MODELS
IFS=',' read -r -a arr_models <<< $MODELS_TO_EVALUATE

umask 007

if [ "${CLEAN_RESULTS:-False}" = "True" ]; then
    EF_REAL=$(realpath "$EVALUATION_FOLDER" 2>/dev/null)
    if [ -z "$EF_REAL" ] || [ ! -d "$EF_REAL" ] || [ "$EF_REAL" = "/" ]; then
        echo "CLEAN_RESULTS: EVALUATION_FOLDER no válida ('$EVALUATION_FOLDER'); no se borra nada" >&2
        exit 1
    fi
    IFS=',' read -r -a arr_gold <<< "$EVALUATION_FOLDER_GOLD"
    for g in "${arr_gold[@]}"; do
        G_REAL=$(realpath "$g")
        case "$G_REAL/" in "$EF_REAL"/*) echo "CLEAN_RESULTS: $g está dentro de EVALUATION_FOLDER; no se borra nada" >&2; exit 1;; esac
        case "$EF_REAL/" in "$G_REAL"/*) echo "CLEAN_RESULTS: EVALUATION_FOLDER está dentro de la gold $g; no se borra nada" >&2; exit 1;; esac
    done
    echo "CLEAN_RESULTS: borrando $EF_REAL/results y $EF_REAL/reports"
    rm -rf "$EF_REAL/results" "$EF_REAL/reports"
fi

#Loop in order to evaluate a list of models
for model in "${arr_models[@]}"; do
    echo "Evaluating $model"
    model_dir=$model

    echo "./launch_scripts/execAllScripts_per_language.sh" $model_dir $WANDB_PROJECT $INSTRUCT_EVALUATION $SHOTS $LANGUAGES $OUTPUT_DIR $SRC_LANGUAGE $TGT_LANGUAGE $PROMPT_STYLE
    ./launch_scripts/execAllScripts_per_language.sh $model_dir $WANDB_PROJECT $INSTRUCT_EVALUATION $SHOTS $LANGUAGES $OUTPUT_DIR $SRC_LANGUAGE $TGT_LANGUAGE $PROMPT_STYLE 
done


python3 -m launch_scripts.format_results --evaluation_folder $EVALUATION_FOLDER --evaluation_folder_gold $EVALUATION_FOLDER_GOLD
