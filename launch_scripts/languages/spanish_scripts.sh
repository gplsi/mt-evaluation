
MODEL_ROUTE=$1
SHOTS=$2
WANDB=$3
INSTRUCT=$4
OUTPUT_MAIN_DIR=$5
OUTPUT_SUBFOLDER=$6
SRC_LANGUAGE=&7
TGT_LANGUAGE=$8
PROMPT_STYLE=$9



echo "Executing Spanish commands..."
yes | ./launch_scripts/execute_task_love.sh "$MODEL_ROUTE" es_en_flores_devtest $SHOTS False $WANDB 1_ES_EN $INSTRUCT spa_Latn eng_Latn $PROMPT_STYLE > "$OUTPUT_MAIN_DIR/$OUTPUT_SUBFOLDER/ES_EN.txt" 2>&1 || true
yes | ./launch_scripts/execute_task_love.sh "$MODEL_ROUTE" es_ca_flores_devtest $SHOTS False $WANDB 2_ES_CA $INSTRUCT spa_Latn cat_Latn $PROMPT_STYLE > "$OUTPUT_MAIN_DIR/$OUTPUT_SUBFOLDER/ES_CA.txt" 2>&1 || true
