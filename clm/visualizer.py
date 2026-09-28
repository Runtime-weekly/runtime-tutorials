#!/usr/bin/env python3
"""Create an offline, self-contained saved-result viewer. No model/API calls."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def build():
    records = []
    expected = {c['id']: c['expected'] for c in json.loads((ROOT / 'data' / 'cases.json').read_text())}
    for group in ('pilot', 'sorting', 'driving'):
        for path in sorted((ROOT / 'data' / group).glob('*/*.json')):
            records.append({'group': group, 'model': path.parent.name,
                            'name': path.stem, 'data': json.loads(path.read_text()),
                            'expected': expected.get(path.stem.rsplit('-', 1)[0])})
    payload = json.dumps(records, ensure_ascii=True).replace('<', '\\u003c')
    page = '''<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>RUNTIME: CLM, Jev and Laya saved results</title>
<style>body{background:#081b16;color:#eef7ef;font:17px system-ui;max-width:1100px;margin:30px auto;padding:20px}h1{font-size:30px}select,button{font:inherit;padding:10px;margin:5px;background:#173b30;color:white;border:1px solid #b4ed62;border-radius:5px}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#102c23;padding:18px;border-radius:8px}.muted{color:#b9cec4}.good{color:#b4ed62}.bad{color:#ffb983}#track{display:flex;gap:6px;flex-wrap:wrap}.cell{padding:10px;border:1px solid #abc;cursor:pointer}input{width:95%}</style>
<h1>CLM / Jev / Laya: inspect the saved decisions</h1>
<p class="muted">Recorded synthetic tests, September 2026. Offline replay, not live inference. Different local and hosted runtimes; call times are not an equal-hardware speed benchmark. Candidate probabilities are not calibrated accuracy.</p>
<label>Test <select id="group"><option>pilot</option><option>sorting</option><option>driving</option></select></label>
<label>System <select id="model"></select></label><label>Case <select id="case"></select></label>
<h2 id="summary"></h2><div id="track"></div>
<p><button id="prev">Previous step</button><button id="next">Next step</button><span id="step"></span></p>
<input id="slider" type="range" min="0" value="0" aria-label="Recorded step">
<h3>Request supplied to the model</h3><pre id="request"></pre>
<h3>Candidate distribution (not calibrated accuracy)</h3><div id="bars"></div>
<h3>Decision and outcome</h3><pre id="outcome"></pre>
<details><summary>Complete saved record</summary><pre id="raw"></pre></details>
<p class="muted">Sorting resets each item scenario. Driving is a discrete text-state simulation, not visual perception or autonomous driving. The rule baseline has privileged access to simulator transitions. The pilot reverses option insertion order without changing meanings; these repeats are paired, not independent cases.</p>
<script id="records" type="application/json">PAYLOAD</script>
<script>
const all=JSON.parse(document.getElementById('records').textContent),get=id=>document.getElementById(id);let index=0;
function modelLabel(v){return v==='rule-v2'?'Code v2: lane-keeping planner':v==='rule'?(get('group').value==='driving'?'Code original: shortest-path planner':'Code: sorting rules'):v}
function fill(id,values){get(id).replaceChildren(...values.map(v=>{let o=document.createElement('option');o.value=v;o.textContent=id==='model'?modelLabel(v):v;return o}))}
function models(){fill('model',[...new Set(all.filter(r=>r.group===get('group').value).map(r=>r.model))]);cases()}
function cases(){fill('case',all.filter(r=>r.group===get('group').value&&r.model===get('model').value).map(r=>r.name));index=0;draw()}
function current(){return all.find(r=>r.group===get('group').value&&r.model===get('model').value&&r.name===get('case').value)}
function show(id,obj){get(id).textContent=typeof obj==='string'?obj:JSON.stringify(obj,null,2)}
function draw(){let r=current();if(!r)return;let d=r.data,steps=d.steps||[d];index=Math.max(0,Math.min(index,steps.length-1));let s=steps[index];get('slider').max=steps.length-1;get('slider').value=index;
show('summary',modelLabel(r.model)+' / '+r.name+(r.group==='pilot'?'':(' / '+(d.passed?'passed':'not passed'))));
show('step',`${index+1} of ${steps.length} recorded steps`);show('request',s.request||{});
show('outcome',r.group==='pilot'?{expected:r.expected,response:s.response,seconds:s.seconds,raw_embedding_ablation:s.raw_embedding_ablation}: {selected:s.selected||s.action,expected:s.expected,correct:s.correct,before:s.before,after:s.after,event:s.event,seconds:s.seconds,response:s.response});show('raw',d);
let response=(s.response||{}),answers=(response.result||response).answers||{},answer=answers.action||answers.decision||{};
get('bars').replaceChildren(...Object.entries(answer.probabilities||{}).map(([label,value])=>{let row=document.createElement('div'),caption=document.createElement('span'),bar=document.createElement('div');caption.textContent=label+': '+(value*100).toFixed(2)+'%'+(label===answer.choice?' (selected)':'');bar.style.cssText='height:14px;background:#b4ed62;margin:5px 0 12px;width:'+Math.max(0,Math.min(100,value*100))+'%';row.append(caption,bar);return row}));
get('track').replaceChildren(...steps.map((x,i)=>{let b=document.createElement('button');b.className='cell '+(x.correct===true?'good':x.correct===false?'bad':'');b.textContent=(i+1)+': '+(x.selected||x.action||'decision');b.onclick=()=>{index=i;draw()};return b}));}
get('group').onchange=models;get('model').onchange=cases;get('case').onchange=()=>{index=0;draw()};get('prev').onclick=()=>{index--;draw()};get('next').onclick=()=>{index++;draw()};get('slider').oninput=e=>{index=Number(e.target.value);draw()};models();
</script></html>'''.replace('PAYLOAD', payload)
    target = ROOT / 'visualizer.html'
    target.write_text(page, encoding='utf-8')
    print('Created visualizer.html. Open it in a browser. No server is required.')
    return target

if __name__ == '__main__':
    build()
