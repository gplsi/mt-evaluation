import datasets

from lm_eval.api.registry import register_task
from lm_eval.api.mt_task import MTask

DATA_FILE = "/home/gplsi/GPLSI/ALIA/datos/Alignment/translation/v2/dpo_test_processed.jsonl"

class _MTask(MTask):
    VERSION = 1
    DATASET_PATH = "json"
    OUTPUT_TYPE = "generate_until"

    def __init__(self, config=None):
        super().__init__(config={'target_delimiter': ' ', 'test_split': 'test'})

    def download(self, dataset_kwargs=None):
        self.dataset = datasets.load_dataset("json", data_files={"test": DATA_FILE})


# (task_name, filter_lang, text_field, target_field, target_lang)
# filter_lang selects the subset of rows (by the original source_lang column);
# text_field/target_field pick which column is the prompt input vs. the reference,
# which lets the same Spanish/English<->Valencian pairs be evaluated in either direction.
task_definitions = [
    ('NEWS_es-va', 'Spanish', 'input', 'target', 'Valencian'),
    ('NEWS_en-va', 'English', 'input', 'target', 'Valencian'),
    ('NEWS_va-es', 'Spanish', 'target', 'input', 'Spanish'),
    ('NEWS_va-en', 'English', 'target', 'input', 'English'),
]

for task_name, filter_lang, text_field, target_field, target_lang in task_definitions:

    task_class = type(
        task_name.upper(),
        (_MTask,),
        {
            'doc_to_text': (lambda self, doc, text_field=text_field: doc[text_field]),
            'doc_to_target': (lambda self, doc, target_field=target_field: doc[target_field]),
            'get_target': (lambda self, target_lang=target_lang: target_lang),
            'test_docs': (
                lambda self, filter_lang=filter_lang: self.dataset[self.config.test_split]
                    .filter(lambda x: x['source_lang'] == filter_lang)
            ),
        }
    )

    register_task(task_name)(task_class)
