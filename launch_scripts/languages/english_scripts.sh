
MODEL_ROUTE=$1
SHOTS=$2
WANDB=$3
INSTRUCT=$4
OUTPUT_MAIN_DIR=$5
OUTPUT_SUBFOLDER=$6
SRC_LANGUAGE=&7
TGT_LANGUAGE=$8
PROMPT_STYLE=$9



echo "Executing English commands..."
yes | ./launch_scripts/execute_task_love.sh "$MODEL_ROUTE" en_es_flores_devtest $SHOTS False $WANDB 1_EN_ES $INSTRUCT eng_Latn spa_Latn $PROMPT_STYLE > "$OUTPUT_MAIN_DIR/$OUTPUT_SUBFOLDER/EN_ES.txt" 2>&1 || true
yes | ./launch_scripts/execute_task_love.sh "$MODEL_ROUTE" en_ca_flores_devtest $SHOTS False $WANDB 2_EN_CA $INSTRUCT eng_Latn cat_Latn $PROMPT_STYLE > "$OUTPUT_MAIN_DIR/$OUTPUT_SUBFOLDER/EN_CA.txt" 2>&1 || true
