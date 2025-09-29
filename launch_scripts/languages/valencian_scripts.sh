
MODEL_ROUTE=$1
SHOTS=$2
WANDB=$3
INSTRUCT=$4
OUTPUT_MAIN_DIR=$5
OUTPUT_SUBFOLDER=$6
SRC_LANGUAGE=&7
TGT_LANGUAGE=$8
PROMPT_STYLE=$9



echo "Executing Valencian commands..."
yes | ./launch_scripts/execute_task_love.sh "$MODEL_ROUTE" phrases2_es-va $SHOTS False $WANDB 1_TA $INSTRUCT spa_Latn va $PROMPT_STYLE > "$OUTPUT_MAIN_DIR/$OUTPUT_SUBFOLDER/1_TA.txt" 2>&1 || true
yes | ./launch_scripts/execute_task_love.sh "$MODEL_ROUTE" phrases2_va-es $SHOTS False $WANDB 2_TA $INSTRUCT va spa_Latn $PROMPT_STYLE > "$OUTPUT_MAIN_DIR/$OUTPUT_SUBFOLDER/2_TA.txt" 2>&1 || true
yes | ./launch_scripts/execute_task_love.sh "$MODEL_ROUTE" phrases2_ca-va $SHOTS False $WANDB 3_TA $INSTRUCT cat_Latn va $PROMPT_STYLE > "$OUTPUT_MAIN_DIR/$OUTPUT_SUBFOLDER/3_TA.txt" 2>&1 || true
yes | ./launch_scripts/execute_task_love.sh "$MODEL_ROUTE" phrases2_va-ca $SHOTS False $WANDB 4_TA $INSTRUCT va cat_Latn $PROMPT_STYLE > "$OUTPUT_MAIN_DIR/$OUTPUT_SUBFOLDER/4_TA.txt" 2>&1 || true