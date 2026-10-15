
MODEL_ROUTE=$1
SHOTS=$2
WANDB=$3
INSTRUCT=$4
OUTPUT_MAIN_DIR=$5
OUTPUT_SUBFOLDER=$6
SRC_LANGUAGE=&7
TGT_LANGUAGE=$8
PROMPT_STYLE=$9



echo "Executing Catalan commands..."
#yes | ./launch_scripts/execute_task_love.sh "$MODEL_ROUTE" ca_en_flores_devtest $SHOTS False $WANDB 1_CA_EN $INSTRUCT cat_Latn eng_Latn $PROMPT_STYLE > "$OUTPUT_MAIN_DIR/$OUTPUT_SUBFOLDER/CA_EN.txt" 2>&1 || true
yes | ./launch_scripts/execute_task_love.sh "$MODEL_ROUTE" ca_es_flores_devtest $SHOTS False $WANDB 2_CA_ES $INSTRUCT cat_Latn spa_Latn $PROMPT_STYLE > "$OUTPUT_MAIN_DIR/$OUTPUT_SUBFOLDER/CA_ES.txt" 2>&1 || true
