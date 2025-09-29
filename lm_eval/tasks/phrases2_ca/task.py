from lm_eval.api.registry import register_task
from lm_eval.api.mt_task import MTask

class _MTask(MTask):
    VERSION = 1
    DATASET_PATH = "gplsi/CA-VA_alignment_test"
    OUTPUT_TYPE = "generate_until"

    def __init__(self, config=None):
        super().__init__(config={'target_delimiter': ' ', 'test_split':'test'})


dataset_name = 'phrases'
languages = ['ca','va']
MAPPING_PHRASES = {'ca':'català', 'va':'valencià'}

task_definitions = []
for l1 in languages:
  for l2 in languages:
    if l1 != l2:
      item = (f'{dataset_name}2_{l1}-{l2}', l1, l2, MAPPING_PHRASES[l2])
      task_definitions.append(item)

for task_name, source_field, target_field, target_lang in task_definitions:

    task_class = type(
       task_name.upper(),
        (_MTask,),
        {
            'doc_to_text': (lambda self, doc, source_field=source_field: doc[source_field]),
            'doc_to_target': (lambda self, doc, target_field=target_field: doc[target_field]),
            'get_target': (lambda self, target_lang=target_lang: target_lang),
        }   
    )

    register_task(task_name)(task_class)