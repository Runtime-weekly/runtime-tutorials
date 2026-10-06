"""Original checks preserved; two explicitly post-hoc prompt interpretations separate."""
import hashlib,json
from pathlib import Path
D=Path(__file__).resolve().parent
def get_check(task,mode):
 data=(D/'tasks.frozen.json').read_bytes()
 assert hashlib.sha256(data).hexdigest()==(D/'tasks-checksum.txt').read_text().strip()
 if mode=='boundary':
  if task not in ['energy-shop','repair-cart']:raise ValueError('Boundary probes apply only to saved carts')
  return 'import subprocess,json\nr=subprocess.run([\'node\',\'-e\',"const make=require(\'./shop.js\').createCart;let out=[];\\nfor(const name of [\'zero_existing\',\'set_quantity_fresh\',\'prototype_unknown\']){let c=make(),error=null;try{if(name===\'zero_existing\'){c.add(\'citrus\');c.setQuantity(\'citrus\',0)}else if(name===\'set_quantity_fresh\'){c.setQuantity(\'berry\',2)}else{c.add(\'citrus\');try{c.add(\'toString\')}catch(e){}}}catch(e){error=String(e)}let count,total;try{count=c.getCount();total=c.getTotalCents()}catch(e){error=String(e)}let expected=name===\'zero_existing\'?[0,0]:name===\'set_quantity_fresh\'?[2,698]:[1,299];out.push({name,count,total,error,expected,passed:error===null&&count===expected[0]&&total===expected[1]})}console.log(JSON.stringify(out))"],capture_output=True,text=True)\nprint(r.stdout,end=\'\')\nassert r.returncode==0,r.stderr\nassert all(x[\'passed\'] for x in json.loads(r.stdout)), \'Exploratory boundary failure\'\n'
 code=next(t['check'] for t in json.loads(data) if t['id']==task)
 if mode=='prompt-faithful' and task in ['energy-shop','repair-cart']:
  code=code.replace("assert(d.querySelector('[data-testid=cart-total]').textContent.includes('10.47'))", "assert(/(?:10\\.47|1047\\s*cents)/i.test(d.querySelector('[data-testid=cart-total]').textContent))")
  code=code.replace('assert.throws(f);','try{f()}catch(e){};')
 return code
