"""Validate recorded evidence with the Python standard library; no downloads or inference."""
import json, math
from pathlib import Path
ROOT=Path(__file__).resolve().parent
LABELS=("READY","WAIT","UNCLEAR")
def read_json(path):
    return json.loads(Path(path).read_text())

def question(config, rule, reverse=False):
    keys = list(reversed(LABELS)) if reverse else list(LABELS)
    return {'readiness': {'type': 'choice', 'instructions': config['rules'][rule],
                         'criteria': {k: config['criteria'][k] for k in keys}}}

def gated_action(answer, threshold, streak):
    p = answer['probabilities']
    if set(p) != set(LABELS) or any(not math.isfinite(v) or not 0 <= v <= 1 for v in p.values()):
        raise ValueError('Invalid probability distribution')
    if abs(sum(p.values()) - 1) > .001 or answer['choice'] not in p:
        raise ValueError('Malformed typed answer')
    if abs(answer['confidence'] - p[answer['choice']]) > .001:
        raise ValueError('Confidence does not match selected option')
    pick = answer['choice']
    if pick == 'UNCLEAR' or answer['confidence'] < threshold:
        return 'UNCERTAIN', 0
    streak = streak + 1 if pick == 'READY' else 0
    return ('READY' if streak >= 3 else 'WAIT'), streak

def validate_recorded():
    config=read_json(ROOT/'experiment.json');photos={p['id']:p for p in read_json(ROOT/'photos.json')['assets']}
    calls=read_json(ROOT/'plan.json')['calls'];rows=read_json(ROOT/'recorded.json')['decisions']
    assert len(calls)==len(rows)==18
    for n,(c,r) in enumerate(zip(calls,rows),1):
        assert r['call']==n and all(r[k]==c[k] for k in ('asset','rule','condition'))
        assert r['question']==question(config,c['rule'],c['condition']=='reversed_options')
        assert r['image_sha256']==photos[c['asset']]['sha256']
        assert r['raw']['usage']['output_tokens']==0 and r['forward_count']==1
        gated_action(r['raw']['answers']['readiness'],.8,0)
    primary=[r for r in rows if r['condition']=='primary']
    assert len(primary)==6 and all(r['raw']['answers']['readiness']['choice']==r['expected'] for r in primary)
    controls=[r for r in rows if r['condition']=='image_removed']
    assert len(controls)==6 and len({json.dumps(r['question'],sort_keys=True) for r in controls})==2
    assert all(r['raw']['answers']['readiness']['choice']==('UNCLEAR' if r['rule']=='A' else 'READY') for r in controls)
    print('18 recorded calls, exact prompts, hashes and diagnostic scopes verified; no inference')

if __name__=="__main__":validate_recorded()
