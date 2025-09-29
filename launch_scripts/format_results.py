import os
import json
import pandas as pd
import re
from datetime import datetime
import argparse
import shutil


N=1 # CONSTANTE PARA RESALTAR VALORES



# -----------------------------------------------------------------------------
# UTILIDADES COMUNES
# -----------------------------------------------------------------------------
def extract_execution_datetime(file_path):
    """
    Extrae la fecha/hora de ejecución a partir del nombre del archivo, que tiene el formato:
    results_YYYY-MM-DDTHH-MM-SS.microseconds.json
    """
    basename = os.path.basename(file_path)
    match = re.search(r'results_(\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}\.\d+)\.json', basename)
    if match:
        date_str = match.group(1)
        # Convertir el string a formato ISO (reemplazando los guiones en la hora por dos puntos)
        date_str_fixed = re.sub(r'T(\d{2})-(\d{2})-(\d{2})', r'T\1:\2:\3', date_str)
        return datetime.fromisoformat(date_str_fixed)
    return None

def extract_model_info(file_name):
    """
    Dado un nombre de archivo con el formato:
    results_{model}_{num}_{language}_{shots}_{other}
    
    Extrae:
      - model_name: Ej. "Aitana-6.3B"
      - language: Ej. "English"
      - shots: Ej. "5_shot" (se reemplaza el guion por guion bajo)
      
    Se asume que la estructura es siempre la misma.
    """
    if file_name.startswith("results_") or file_name.startswith("results:"):
        parts = file_name[len("results_"):].split("_")
        if len(parts) >= 4:
            model_name = parts[0]
            language = parts[2]
            shots = parts[3].replace("-", "_")
            return model_name, language, shots
    return None, None, None

# -----------------------------------------------------------------------------
# EXTRACCIÓN DE INFORMACIÓN DE UN ARCHIVO (UNA SOLA LECTURA)
# -----------------------------------------------------------------------------
def process_file(file_path):
    """
    Lee el archivo JSON una sola vez y extrae dos listas de información:
    
    - results_list: Por cada tarea en la clave "results", se extraen los scores (omitiendo "alias")
      junto con el execution_datetime y el file_name.
    
    - config_list: Por cada tarea en la clave "configs", se extraen:
        • task (de "task" o la propia clave)
        • metric_list: lista de nombres (tomados de cada dict en "metric_list")
        • output_type
        • model (usando "model_name" si existe o desde "config")
        • Random: "No-Random" si "random_seed" es distinto de None, o "Random" en caso contrario
        • model_name_sanitized: extraído de la clave top-level "model_name_sanitized"
      Se añade también execution_datetime y file_name.
    """
    print(f"      📄 Leyendo JSON: {file_path}")  
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    execution_datetime = extract_execution_datetime(file_path)
    file_name = os.path.basename(file_path)
    
    # --- Extraer resultados ---
    results_list = []
    results = data.get("results", {})
    for task_key, metrics in results.items():
        task_data = {"file_name": file_name, "execution_datetime": execution_datetime, "task": task_key}
        for metric_name, metric_value in metrics.items():
            if metric_name != "alias":
                task_data[metric_name] = metric_value
        results_list.append(task_data)
    
    # --- Extraer configuración ---
    config_list = []
    top_config = data.get("config", {})
    random_seed = top_config.get("random_seed")
    random_col = "No-Random" if random_seed is not None else "Random"
    model_value = data.get("model_name", top_config.get("model", None))
    # Extraer model_name_sanitized (si existe a nivel top-level)
    model_name_sanitized = data.get("model_name_sanitized", None)
    
    configs = data.get("configs", {})
    for task_key, task_config in configs.items():
        task = task_config.get("task", task_key)
        metrics_list = []
        for m in task_config.get("metric_list", []):
            metric_name = m.get("metric")
            if metric_name:
                if 'rouge1' in metric_name:
                    metrics_list.append('rouge1')
                else:
                    metrics_list.append(metric_name)
        output_type = task_config.get("output_type")
        config_list.append({
            "file_name": file_name,
            "execution_datetime": execution_datetime,
            "task": task,
            "metric_list": metrics_list,
            "output_type": output_type,
            "model": model_value,
            "Random": random_col,
            "model_name_sanitized": model_name_sanitized
        })
    
    return results_list, config_list

# -----------------------------------------------------------------------------
# RECORRER LA ESTRUCTURA DE CARPETAS (UNA SOLA VUELTA)
# -----------------------------------------------------------------------------
def process_all_folders_combined(main_root_folder):
    """
    Recorre todas las carpetas dentro de 'main_root_folder' y sus subcarpetas,
    procesando cada archivo JSON (que cumpla con "results_*.json") una sola vez,
    y extrayendo tanto los datos de resultados como los de configuración.
    
    Se añaden las columnas:
      - root_folder: nombre de la carpeta raíz
      - model_folder: nombre de la carpeta del modelo
    """
    all_results = []
    all_configs = []
    
    for root_folder in os.listdir(main_root_folder):
        root_path = os.path.join(main_root_folder, root_folder)
        if os.path.isdir(root_path):
            print(f"\n📂 Procesando carpeta raíz: {root_folder}")
            for model_folder in os.listdir(root_path):
                model_path = os.path.join(root_path, model_folder)
                if os.path.isdir(model_path):
                    print(f"  📁 Explorando modelo: {model_folder}")
                    for results_folder in os.listdir(model_path):
                        results_path = os.path.join(model_path, results_folder)
                        if os.path.isdir(results_path):
                            print(f"    📂 Carpeta de resultados: {results_folder}")
                            for filename in os.listdir(results_path):
                                if filename.startswith("results_") and filename.endswith(".json"):
                                    file_path = os.path.join(results_path, filename)
                                    results_list, config_list = process_file(file_path)
                                    for r in results_list:
                                        r["root_folder"] = root_folder
                                        r["model_folder"] = model_folder
                                    for c in config_list:
                                        c["root_folder"] = root_folder
                                        c["model_folder"] = model_folder
                                    all_results.extend(results_list)
                                    all_configs.extend(config_list)
                                    
    df_results = pd.DataFrame(all_results)
    df_configs = pd.DataFrame(all_configs)
    return df_results, df_configs

# -----------------------------------------------------------------------------
# PROCESAMIENTO POSTERIOR: EXTRAER INFO DEL NOMBRE DEL ARCHIVO
# -----------------------------------------------------------------------------
def extract_model_info(folder_name):
    """
    Extrae la información del nombre de la carpeta según los siguientes formatos:

    1. Formato: "results_{model}_{num}_{language}_{shots}_{other}"
       Ejemplo: "results_Aitana-6.3B_5_Latin_5-shot_3064" se extrae:
         - model_name: "Aitana-6.3B"
         - language: "Latin"
         - shots: "5_shot"
    
    2. Formato: "results_iter-047999-ckpt.pth_{num}_{language}_{shots}_{other}"
       Ejemplo: "results_iter-047999-ckpt.pth_1_English_5-shot_13835" se extrae:
         - model_name: "iter-047999-ckpt.pth"
         - language: "English"
         - shots: "5_shot"
    
    Si la cadena no cumple el formato esperado, devuelve (None, None, None).
    """
    folder_name = folder_name.replace(":","_")
    if folder_name.startswith("results_"):
        content = folder_name[len("results_"):]
        parts = content.split("_")
        if len(parts) >= 4:
            model_name = parts[0]
            language = parts[2]
            shots = parts[3].replace("-", "_")
            return model_name, language, shots
    return None, None, None

def enrich_with_model_info(df, folder_col="model_folder"):
    """
    A partir de la columna con el nombre de la carpeta (por ejemplo, "model_folder"),
    extrae las columnas 'model_name', 'language' y 'shots' y las añade al DataFrame.
    """
    extracted = df[folder_col].apply(
        lambda x: pd.Series(extract_model_info(x), index=["model_name", "language", "shots"])
    )
    return pd.concat([df, extracted], axis=1)




def filter_columns(df):
    """
    Devuelve el DataFrame filtrando las columnas que contienen '_stderr'.
    """
    cols = df.columns.to_list()
    filtered_cols = [col for col in cols if '_stderr' not in col]
    return df[filtered_cols]

def reorder_columns(df, first_cols=None):
    """
    Reordena las columnas del DataFrame colocando al inicio las columnas en 'first_cols'.
    """
    if first_cols is None:
        first_cols = ["execution_datetime", "model_name_sanitized", "task", "language", "shots"]
    remaining_cols = [col for col in df.columns if col not in first_cols]
    new_order = first_cols + remaining_cols
    return df[new_order]

def pivot_results(df_results):
    """
    Realiza el filtrado, reordenamiento, melt y pivot del DataFrame de resultados.
    Devuelve el DataFrame pivotado con las siguientes columnas de índice:
    ["execution_datetime", "task", "language", "shots", "Metric", "Random"]
    y columnas correspondientes a cada 'model_name_sanitized'.
    """
    # 1. Filtrar columnas que contienen '_stderr'
    df_filtered = filter_columns(df_results)
    
    # 2. Reordenar columnas: primero las clave y luego el resto
    df_reordered = reorder_columns(df_filtered)
    
    # Copiar para trabajar
    df_final = df_reordered.copy()
    
    # Definir columnas identificadoras y de valores
    id_vars = ["execution_datetime", "model_name_sanitized", "task", "language", "shots"]
    value_vars = [col for col in df_final.columns if col not in id_vars]
    
    # 3. Melt: pasar las métricas a filas
    df_melted = df_final.melt(id_vars=id_vars, value_vars=value_vars,
                              var_name="metric_info", value_name="score")
    
    # 4. Separar 'metric_info' en 'Metric' y 'Random'
    df_melted[["Metric", "Random"]] = df_melted["metric_info"].str.split(",", expand=True)
    df_melted.drop(columns=["metric_info"], inplace=True)
    
    # 5. Pivot table: cada fila es una combinación única de identificadores, columnas según 'model_name_sanitized'
    df_final_pivot = df_melted.pivot_table(
        index=["execution_datetime", "task", "language", "shots", "Metric", "Random"],
        columns="model_name_sanitized",
        values="score",
        aggfunc="first"  # Se puede cambiar según el caso de duplicados
    ).reset_index()
    
    return df_final_pivot

def merge_dataframes(df_configs, df_results_pivot):
    """
    Realiza el merge entre el DataFrame de configuraciones y el DataFrame de resultados pivotado.
    La unión se realiza en las columnas:
      - df_configs: ['execution_datetime', 'task', 'metric_list']
      - df_results_pivot: ['execution_datetime', 'task', 'Metric']
    """
    merged_df = pd.merge(
        df_configs, df_results_pivot,
        left_on=['execution_datetime', 'task', 'metric_list'],
        right_on=['execution_datetime', 'task', 'Metric'],
        how='left'  # Se puede ajustar: inner, left, right, outer
    )
    return merged_df



###
# Función que genera una dataframe con los resultados unidos e enriquecidos.
###
def generate_results(main_root_folder):
    # Se procesan todas las carpetas y se extraen tanto resultados como configuraciones en una sola pasada
    df_results, df_configs = process_all_folders_combined(main_root_folder)
    
    # Enriquecer ambos DataFrames con la información extraída del nombre del archivo
    if not df_results.empty:
        df_results = enrich_with_model_info(df_results)
        df_results["model"] = df_results["root_folder"]
        df_results.drop(columns=['sources,none','targets,none','bleu_segments,none','ter_segments,none','chrf_segments,none','comet_segments,none','translations,none'],inplace=True)
        df_results = df_results.drop_duplicates()
    if not df_configs.empty:
        df_configs = enrich_with_model_info(df_configs)
        df_configs["model"] = df_configs["root_folder"]
        cols = ["execution_datetime", "model", "model_folder", "task", "metric_list", "output_type", "Random", "model_name_sanitized"]
        df_configs = df_configs[[c for c in cols if c in df_configs.columns]]

    df_reduced = df_configs[['execution_datetime', 'model_folder', 'model_name_sanitized']]
    df_results = pd.merge(df_results, df_reduced, on = ['execution_datetime', 'model_folder'])
    df_results = df_results.drop(['file_name', 'root_folder', "model_folder", "model", "model_name"],axis = 1)

    df_configs = df_configs.explode(['metric_list'])

    # Reordenamos 
    cols = df_results.columns.to_list()
    filtered_cols = [col for col in cols if '_stderr' not in col]
    df_results = df_results[filtered_cols]

    first_cols = ["execution_datetime", "model_name_sanitized", "task", "language", "shots"]

    # Crear una lista con el resto de columnas
    remaining_cols = [col for col in df_results.columns if col not in first_cols]

    # Concatenar ambas listas para definir el nuevo orden
    new_order = first_cols + remaining_cols

    # Reordenar el DataFrame
    df = df_results[new_order]

    # Pivotamos 
    df_final = df.copy()
    # Definir las columnas identificadoras y las columnas de métricas
    id_vars = ["execution_datetime","model_name_sanitized", "task", "language", "shots"]
    value_vars = [col for col in df_final.columns if col not in id_vars]

    # 1. "Meltear" el DataFrame para convertir las métricas en filas
    df_melted = df_final.melt(id_vars=id_vars, value_vars=value_vars,
                        var_name="metric_info", value_name="score")

    # 2. Separar 'metric_info' en dos columnas: 'Metric' y 'Random'
    df_melted[["Metric", "Random"]] = df_melted["metric_info"].str.split(",", expand=True)
    df_melted.drop(columns=["metric_info"], inplace=True)

    # 3. Pivotar la tabla para que cada fila tenga los scores de cada modelo (usando "model_name")
    df_final_pivot = df_melted.pivot_table(
        index=["execution_datetime", "task", "language", "shots", "Metric", "Random"],
        columns="model_name_sanitized",
        values="score",
        aggfunc="first"
    ).reset_index()

    merged_df = pd.merge(
    df_configs, df_final_pivot,
    left_on=['execution_datetime',  'task', 'metric_list'],
    right_on=['execution_datetime',   'task', 'Metric'],
    how='right'  # Puedes cambiar 'inner' por 'outer', 'left' o 'right' según necesites
    )
    #merged_df["Random"] = merged_df["Random_y"]
    merged_df = merged_df.drop(['model', 'metric_list', 'model_folder', "Random_y", "Random_x","model_name_sanitized"], axis=1)

    first_cols= ["execution_datetime", "task","Metric", "shots"]

    # Crear una lista con el resto de columnas
    remaining_cols = [col for col in merged_df.columns if col not in first_cols]

    # Concatenar ambas listas para definir el nuevo orden
    new_order = first_cols + remaining_cols

    # Reordenar el DataFrame
    df = merged_df[new_order]

    df_copy = df.copy()
    df_copy = df_copy.drop_duplicates()
    df_copy = df_copy.drop(['execution_datetime'], axis = 1)
    df_grouped = df_copy.groupby(['Metric', 'task'], as_index=False).max()
    df = df_grouped.drop_duplicates().drop(['shots'], axis=1)
    return df




#### -----------------------------------------------------------------------------
# Función para aplicar estilo
#### -----------------------------------------------------------------------------
def highlight_nsmallest_nlargest(s, n=N):
    is_min = s.isin(s.nsmallest(n))  # Identifica los N valores más pequeños
    is_max = s.isin(s.nlargest(n))   # Identifica los N valores más grandes

    if s.name[1] == 'ter':
        return ['background-color: lightcoral' if v else 
                'background-color: lightgreen' if w else 
                '' for v, w in zip(is_max, is_min)]
    else:
        is_min = s.isin(s.nsmallest(n))  # Identifica los N valores más pequeños
        is_max = s.isin(s.nlargest(n))   # Identifica los N valores más grandes
        return ['background-color: lightcoral' if v else 
                'background-color: lightgreen' if w else 
                '' for v, w in zip(is_min, is_max)]



#### ----------------------------------------------------------------------------#
# Función auxiliar para normalizar los scores de los modelos por idioma.
#### -----------------------------------------------------------------------------
def normalized_value(row, column):

    raw_metric = row[column] if row['metric'] in ['bleu', 'chrf', 'mcc', 'exact_match'] else row[column]*100
    #raw_metric = row[column]
    random_score = row['random']
    max_score = row['Max']
    return (raw_metric - random_score) / (max_score - random_score)

#### -----------------------------------------------------------------------------
# Función para normalizar los scores de los modelos por idioma.
def normalize_models_score_by_language(df):
    # Cargar el diccionario de normalización
    normalized_dict = 'task_normalized_dict_100.xlsx'
    df_normalized_dict = pd.read_excel(normalized_dict)
    df_normalized_dict.sort_values(by="task", inplace=True)

    df_copy = df.copy()
    df_copy.dropna(subset=['task'], inplace=True)
    df_copy.sort_values(by=['task'], inplace=True)

    df_copy = pd.merge(df_normalized_dict, df_copy,  on=['task', 'metric'])
    subset_columns = df_copy.columns[6:]
    
    for column in subset_columns:
        df_copy[column] = df_copy.apply(lambda row: normalized_value(row, column), axis=1)

    df_gropup = df_copy.groupby(['task','language'], as_index=False)[subset_columns].mean()
    subset_columns = ['language'] + list(df_gropup.columns[2:])

    df_subset = df_gropup[subset_columns]

    # Cálculo de la media aritmetica por idioma
    df_mean = df_subset.groupby('language').mean().reset_index()
    df_mean.set_index('language', inplace=True)
    df_mean = df_mean.T
    df_mean.sort_values(by=['Valencian','Catalan','Spanish', 'English'], inplace=True, ascending=False)
    df_mean = df_mean.style.apply(highlight_nsmallest_nlargest, axis=0)
    return df_mean


#### -----------------------------------------------------------------------------
# Aplicar estilos a los resultados para visualizar mejor los datos.
#### -----------------------------------------------------------------------------

def style_results(df,root_folder):
    df = df.rename(columns={'Metric':'metric'})
    #exclude_language = []
    #for i in df.language.unique():
    #    if 'shot' in i:
    #        exclude_language.append(i)

    #df = df[~df.language.isin(exclude_language)].reset_index(drop=True)
    df.drop(columns=['output_type','language'], inplace=True)
    df = df[df['metric'].apply(lambda x: '_norm' not in x )].reset_index(drop=True)
    #df_norm = normalize_models_score_by_language(df)
    df = df.set_index(['task', 'metric'])
    #df.sort_index(level='language',inplace=True)
    

    df = df.style.apply(highlight_nsmallest_nlargest, axis=1)
    name = "Resultados_unidos_"
    now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S") 
    file_name = name+now

    with pd.ExcelWriter(root_folder+file_name+'.xlsx', engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Resultados', index=True, header=True)
        #df_norm.to_excel(writer, sheet_name='Normalizados', index=True, header=True)

    
    print(f"\n✅ Archivos guardado como {root_folder+file_name}.xlsx")



if __name__ == "__main__":
    argparser = argparse.ArgumentParser(description="Generar y estilizar resultados de evaluación de modelos.")
    argparser.add_argument('--evaluation_folder', type=str, default="../results/",
                           help="Ruta al directorio principal donde se encuentran los resultados.")
    argparser.add_argument('--evaluation_folder_gold', type=str, default="../results/",
                           help="Ruta al directorio principal donde se encuentran los mejores resultados.")
    args = argparser.parse_args()
    
    main_root_folder = args.evaluation_folder + "/results/"
    
    main_root_folder_gold = args.evaluation_folder_gold + "/results/"
    
    if os.path.exists(main_root_folder_gold):
        temp_folder = args.evaluation_folder + "/temp/"
        # os.mkdir(temp_folder) if not os.path.exists(temp_folder) else None
        shutil.copytree(main_root_folder_gold, temp_folder, dirs_exist_ok=True)
        shutil.copytree(main_root_folder, temp_folder, dirs_exist_ok=True)
        main_root_folder = temp_folder
    else:
        
        print(f"❌ No se encontró la carpeta de resultados: {main_root_folder_gold}")
        exit(1)
    
    df = generate_results(main_root_folder)
    if "temp" in main_root_folder:
        shutil.rmtree(main_root_folder)
    
    results_folder = args.evaluation_folder + "/reports/"
    os.mkdir(results_folder) if not os.path.exists(results_folder) else None
    style_results(df,results_folder)
