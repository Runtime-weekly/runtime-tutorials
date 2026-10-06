"""Bounded native MiniCPM5 XML tool adapter for two read-only local functions."""
import json,re,xml.etree.ElementTree as ET
TOOLS=[{'type':'function','function':{'name':name,'description':desc,'parameters':{'type':'object','properties':{arg:{'type':'string'}},'required':[arg],'additionalProperties':False}}} for name,arg,desc in [('lookup_order','order_id','Read an order and its cached invoice reference.'),('lookup_invoice','invoice_id','Read an invoice, or a superseded error with a current invoice reference.')]]
def parse(text):
 text=text.replace('\u0120',' ').replace('<functionname=','<function name=').replace('<paramname=','<param name=')
 blocks=re.findall(r'<function\b.*?</function>',text,re.S);calls=[]
 remainder=re.sub(r'<function\b.*?</function>','',text,flags=re.S)
 if re.search(r'</?(?:function|param)\b',remainder):raise ValueError('Unconsumed tool markup')
 for b in blocks:
  node=ET.fromstring(b);name=node.attrib.get('name');required={'lookup_order':'order_id','lookup_invoice':'invoice_id'}
  if name not in required:raise ValueError('Unknown function')
  params=list(node)
  if len(params)!=1 or params[0].tag!='param' or params[0].attrib.get('name')!=required[name] or len(list(params[0])):raise ValueError('Expected one named string parameter')
  value=(params[0].text or '').strip()
  if not value:raise ValueError('Empty parameter')
  calls.append({'type':'function','function':{'name':name,'arguments':{required[name]:value}}})
 if '<function' in text and not blocks:raise ValueError('Incomplete function block')
 return calls
if __name__=='__main__':
 assert parse('<function name="lookup_order"><param name="order_id">ORD-72</param></function>')[0]['function']['arguments']=={'order_id':'ORD-72'}
 assert parse('<functionname="lookup_invoice"><paramname="invoice_id"><![CDATA[INV-NEW-72]]></param></function>')[0]['function']['arguments']=={'invoice_id':'INV-NEW-72'}
 for x in ['<function name="lookup_order"><param name="order_id">X</param></function><function', '<function name="bad"><param name="order_id">X</param></function>','<function name="lookup_order"><param name="wrong">X</param></function>','<function name="lookup_order"><param name="order_id">X</param><param name="order_id">Y</param></function>']:
  try:parse(x)
  except ValueError:pass
  else:raise AssertionError('Expected rejection')
 print('Native XML parser canaries passed; no model calls.')
