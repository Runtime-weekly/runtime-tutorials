"""A small adaptation: classify three short, synthetic project notes on CPU."""
import json, os
os.environ.update(HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1')
import torch, laya
from download_model import MODEL_DIR
torch.set_num_threads(3)
questions = {'note_type': {
    'type': 'choice',
    'instructions': 'What kind of project note is this?',
    'criteria': {
        'bug': 'something is broken or produces an error',
        'feature': 'a request for new functionality',
        'setup': 'help installing or configuring the project',
        'other': 'none of these categories',
    },
}}
messages = [
    'The app freezes every time I export a PDF.',
    'Could you add a dark mode option?',
    'Which Python version do I need to install this?',
]
agent = laya.load(str(MODEL_DIR), device='cpu')
rows = []
for message in messages:
    answer = agent.system_one(message, questions)['answers']['note_type']
    rows.append({'input': message, 'answer': answer})
print(json.dumps({'device': 'cpu', 'note': 'Three synthetic examples, not an accuracy evaluation.', 'results': rows}, indent=2))
