import argparse
import os
import yaml
import re
import uuid
from pathlib import Path
import openpyxl

def parse_arguments():
    parser = argparse.ArgumentParser(description="Generate environment file from YAML configuration")
    parser.add_argument("--config", type=str, required=True, help="Path to the YAML configuration file")
    parser.add_argument("--env-id", type=str, required=True, help="Identifier for the enviroment file")
    parser.add_argument('--docker', action='store_true', help='Run in Docker mode')

    return parser.parse_args()

def read_config(config_path):
    with open(config_path, 'r') as file:
        return yaml.safe_load(file)

def sanitize_filename(name):
    """Convert a string to a valid filename by removing invalid characters"""
    return re.sub(r'[^a-zA-Z0-9_-]', '_', name)


def generate_env_file(config, env_id, docker_mode):

    
    # Use evaluation_name for the experiment name
    experiment_name = sanitize_filename(config['evaluation_name']) 
    # Parse model names
    models_names = config['models']['models_names']
    output_dir= str(os.path.abspath('./experiments'))+'/'+str(env_id)
    if docker_mode == True:
        output_dir= '.'
    # Create the env file content
    env_content = [
        f"USER_ID=$(id -u)",
        f"GROUP_ID=$(id -g)",
        f"MODELS_TO_EVALUATE={models_names}",
        f"MODELS_FOLDER={config['models'].get('models_path','')}",
        f"EVALUATION_FOLDER={config['evaluation']['evaluation_folder']}",
        f"EVALUATION_FOLDER_GOLD={config['evaluation']['evaluation_folder_gold']}",
        f"WANDB_PROJECT={config['wandb_project']}",
        f"INSTRUCT_EVALUATION={str(config['evaluation']['instruct']).capitalize()}",
        f"SHOTS={config['evaluation']['shots']}",
        # Read sensitive tokens from environment if available
        f"WANDB_API_KEY={os.environ.get('WANDB_API_KEY', '')}",
        f"HF_TOKEN={os.environ.get('HF_TOKEN', '')}",
        f"LANGUAGES={config['languages']}",
        f"OUTPUT_DIR={output_dir}",
        f"SRC_LANGUAGE={config['evaluation'].get('src_language','')}",
        f"TGT_LANGUAGE={config['evaluation'].get('tgt_language','')}",
        f"PROMPT_STYLE={config['evaluation'].get('prompt_style','')}"
    ]
    
    # Write the env file
    env_file = Path('./'+ f".env_{env_id}")
    env_file.write_text("\n".join(env_content))
    print(f"Environment file created: {env_file}")
    
    return env_file

def check_model_configuration(config,docker_mode):
    """Check if the model configuration is valid"""
    required_fields = ['local', 'models_names'] if config['models']['local'] == False else ['local', 'models_names','models_path']

    for field in required_fields:
        if field not in config['models']:
            raise ValueError(f"Missing required field in models configuration: {field}")
    print(config['models']['local'])
    if config['models']['local'] == False:
        print("Using models from Hugging Face")
        pass
    else:
        models_names = config['models']['models_names'].split(',')
        models_path = Path(config['models']['models_path'])
        if not models_path.exists():
            raise ValueError(f"Models path does not exist: {models_path}")

        # Check if all specified models exist in the models path
        for model_name in models_names:
            model_name = model_name.strip()
            model_path = Path(str(models_path) +'/'+ model_name)
            if not model_path.exists():
                raise ValueError(f"Model not found in models path: {model_path}")
        
        # DOCKER MODEL IMPLIES MAPPING TO THE /models/ directory in the container where the volumes are mounted
        if docker_mode:
            models_list_str = ""
            count_models = 0
            for i in range(len(models_names)):
                if count_models != 0:
                    models_list_str += ','
                
                models_list_str += '/models/'+models_names[i]
                count_models += 1
            
            
            config['models']['models_names'] = models_list_str
        # OTHERWISE, THE EXECUTION MODE WILL USE CONDA AND ABSOLUTE PATHS MUST BE ADDED.
        else:
            models_list_str = ""
            count_models = 0
            models_path_str = config['models']['models_path']
            for i in range(len(models_names)):
                if count_models != 0:
                    models_list_str += ','

                models_list_str += models_path_str +'/'+models_names[i]
                count_models += 1

            config['models']['models_names'] = models_list_str


def check_evaluation_configuration(config):
    """Check if the evaluation configuration is valid"""
    # Check if evaluation configuration has all required fields
    required_fields = ['evaluation_folder', 'evaluation_folder_gold','instruct','shots']
    for field in required_fields:
        if field not in config['evaluation']:
            raise ValueError(f"Missing required field in evaluation configuration: {field}")
    
    # Check if instruct evaluation is a boolean and shots is a non-negative integer
    if config['evaluation']['instruct'] not in [True, False]:
        raise ValueError("Instruct evaluation must be a boolean value (True or False)")
    # Check if shots is a non-negative integer
    if not isinstance(config['evaluation']['shots'], int) or config['evaluation']['shots'] < 0:
        raise ValueError("Shots must be a non-negative integer")

    if not os.path.exists(config['evaluation']['evaluation_folder']):
        raise ValueError(f"Evaluation folder does not exist: {config['evaluation']['evaluation_folder']}")
    if not os.path.exists(config['evaluation']['evaluation_folder_gold']):
        raise ValueError(f"Evaluation folder gold does not exist: {config['evaluation']['evaluation_folder_gold']}")
    

def check_languages_configuration(config):
    """Check if the languages configuration is valid"""
    if 'languages' not in config or not isinstance(config['languages'], list):
        raise ValueError("Languages configuration must be a list of language objects")
    
    supported_languages = ['Spanish', 'English', 'Valencian', 'Catalan']
    
    dict_languages = {
        'Spanish': 'es',
        'English': 'en',
        'Valencian': 'va',
        'Catalan': 'ca'
    }

    count_languages_to_evaluate = 0
    languages_text_to_evaluate = ""
    for lang_obj in config['languages']:
        if not isinstance(lang_obj, dict):
            raise ValueError("Each language entry must be a dictionary")
        
        for lang_name, enabled in lang_obj.items():
            if lang_name not in supported_languages:
                raise ValueError(f"Unsupported language: {lang_name}. Supported languages are: {supported_languages}")
            
            if not isinstance(enabled, bool):
                raise ValueError(f"Language '{lang_name}' value must be a boolean (true/false)")
            
            else:
                if enabled:
                    if count_languages_to_evaluate == 0:
                        languages_text_to_evaluate += dict_languages[lang_name]
                    else:
                        languages_text_to_evaluate += "," + dict_languages[lang_name]
                    count_languages_to_evaluate += 1

    if count_languages_to_evaluate == 0:
        raise ValueError("At least one language must be enabled for evaluation") 
                   
    config['languages'] = languages_text_to_evaluate


        
def check_config(config,docker_mode):
    """Check if the config has all required fields"""
    required_fields = [
        'models', 'evaluation','languages' 
    ]
    for field in required_fields:
        if field not in config:
            raise ValueError(f"Missing required field in config: {field}")
    
    # Check models configuration
    check_model_configuration(config,docker_mode)
    check_evaluation_configuration(config)
    check_languages_configuration(config)
    
    if 'evaluation_folder' not in config['evaluation'] or 'evaluation_folder_gold' not in config['evaluation']:
        raise ValueError("Missing evaluation folder paths in evaluation configuration")

def main():
    args = parse_arguments()
    config = read_config(args.config)
    env_id = args.env_id
    docker_mode = args.docker

    print("Docker mode:", docker_mode)
    check_config(config,docker_mode)
    print(f"Generating environment file for: {config['evaluation_name']}")
    
    # Generate environment file from config
    env_file = generate_env_file(config, env_id,docker_mode)
    
    print(f"Environment file created: {env_file}")
    print(f"You can now run: bash launch_job.sh {env_file}")
    
if __name__ == "__main__":
    main()