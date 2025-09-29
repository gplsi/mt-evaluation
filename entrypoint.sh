#!/bin/bash
# AUTENTICATE IN WANDB 
wandb login $WANDB_API_KEY  # Authenticate W&B
#PARSE STRING MODELS
IFS=',' read -r -a arr_models <<< $MODELS_TO_EVALUATE

umask 007



#Loop in order to evaluate a list of models
for model in "${arr_models[@]}"; do
    echo "Evaluating $model"
    model_dir=$model

    echo "./launch_scripts/execAllScripts_per_language.sh" $model_dir $WANDB_PROJECT $INSTRUCT_EVALUATION $SHOTS $LANGUAGES $OUTPUT_DIR $SRC_LANGUAGE $TGT_LANGUAGE $PROMPT_STYLE
    ./launch_scripts/execAllScripts_per_language.sh $model_dir $WANDB_PROJECT $INSTRUCT_EVALUATION $SHOTS $LANGUAGES $OUTPUT_DIR $SRC_LANGUAGE $TGT_LANGUAGE $PROMPT_STYLE 
done


python3 -m launch_scripts.format_results --evaluation_folder $EVALUATION_FOLDER --evaluation_folder_gold $EVALUATION_FOLDER_GOLD
