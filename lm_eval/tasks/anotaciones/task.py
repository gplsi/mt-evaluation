import datasets

from lm_eval.api.registry import register_task
from lm_eval.api.mt_task import MTask

# JSONL generados por conjunto_evaluacion_v2.ipynb (outputs/evaluacion_traduccion/mt_eval/)
DATA_DIR = "/home/gplsi/GPLSI/codigos/mt-evaluation/data/anotaciones"


class _MTask(MTask):
    VERSION = 1
    DATASET_PATH = "json"
    OUTPUT_TYPE = "generate_until"
    DATA_FILE = None

    def __init__(self, config=None):
        super().__init__(config={'target_delimiter': ' ', 'test_split': 'test'})

    def download(self, dataset_kwargs=None):
        self.dataset = datasets.load_dataset("json", data_files={"test": self.DATA_FILE})


# (task_name, archivo, text_field, target_field, target_lang)
# Un archivo por dirección: text_field es el texto de origen y target_field la referencia.
task_definitions = [
    ('ANOTACIONES_corregidas_es-va', 'anotaciones_corregidas_es-va.jsonl', 'es', 'va', 'Valencian'),
    ('ANOTACIONES_corregidas_va-es', 'anotaciones_corregidas_va-es.jsonl', 'va', 'es', 'Spanish'),
    ('ANOTACIONES_validadas_es-va',  'anotaciones_validadas_es-va.jsonl',  'es', 'va', 'Valencian'),
    ('ANOTACIONES_validadas_va-es',  'anotaciones_validadas_va-es.jsonl',  'va', 'es', 'Spanish'),
]

for task_name, archivo, text_field, target_field, target_lang in task_definitions:

    task_class = type(
        task_name.upper(),
        (_MTask,),
        {
            'DATA_FILE': f"{DATA_DIR}/{archivo}",
            'doc_to_text': (lambda self, doc, text_field=text_field: doc[text_field]),
            'doc_to_target': (lambda self, doc, target_field=target_field: doc[target_field]),
            'get_target': (lambda self, target_lang=target_lang: target_lang),
            'test_docs': (lambda self: self.dataset[self.config.test_split]),
        }
    )

    register_task(task_name)(task_class)
