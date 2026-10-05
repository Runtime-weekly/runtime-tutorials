import unittest,json
from build_cases import build,conditions
from common import model_input,rules,probabilities,generation_choice
from analyze import gate,escalate,diagnostics
class Checks(unittest.TestCase):
 def setUp(self):self.cases=build();self.all=conditions(self.cases)
 def test_counts_split(self):
  self.assertEqual(len(self.cases),96);self.assertEqual(len(self.all),192)
  self.assertEqual(sum(c['split']=='dev' for c in self.cases),24)
  a={c['family_id'] for c in self.cases if c['split']=='dev'};b={c['family_id'] for c in self.cases if c['split']=='test'};self.assertFalse(a&b)
  self.assertEqual(len({c['id'] for c in self.all}),192)
 def test_transform_labels(self):
  parents={c['id']:c for c in self.cases}
  for c in self.all:
   self.assertIn(c['expected_key'],[o['key'] for o in c['options']])
   if c['parent_id']:self.assertEqual(c['expected_key'],parents[c['parent_id']]['expected_key'])
   if c['transform']=='attack':self.assertNotEqual(c['attack_target'],c['expected_key'])
 def test_rules_and_label_independence(self):
  for c in self.all:
   stripped={k:v for k,v in c.items() if k not in ['expected_key','label_reason','family_id','split','attack_target']};self.assertEqual(rules(c),rules(stripped));self.assertEqual(model_input(c),model_input(stripped))
 def test_probability_rejection(self):
  for x in [[1,0],[float('nan'),0,0,1],[.3,.3,.3,.3],[-1,1,1,0]]:
   with self.assertRaises(ValueError):probabilities(x,self.cases[0])
  self.assertEqual(probabilities([1,0,0,0],self.cases[0])['choice'],'billing')
 def test_generation_strict(self):
  self.assertEqual(generation_choice('{"choice":"billing"}',self.cases[0])['choice'],'billing')
  for x in ['billing','{"choice":"invented"}','{"choice":"billing","extra":1}']:
   with self.assertRaises(ValueError):generation_choice(x,self.cases[0])
 def test_rule_boundaries(self):
  for c in self.cases:
   if c['task']=='next_action':self.assertEqual(rules(c),c['expected_key'])
 def test_diagnostics(self):
  c=self.cases[0];r={('s1',c['id']):{'status':'ok','choice':'billing','score':1,'probabilities':[1,0,0,0]}}
  d=diagnostics([c],r,'s1');self.assertEqual(sum(b['n'] for b in d['bins']),1);self.assertEqual(d['multiclass_brier_mean'],0)
 def test_gate_boundary_and_failure(self):
  self.assertFalse(escalate({'status':'ok','score':.8},.8));self.assertTrue(escalate(None,.8));self.assertTrue(escalate({'status':'failed','score':1},.8))
  c=self.cases[0];r={('s1',c['id']):{'status':'ok','choice':c['expected_key'],'score':.7},('s2',c['id']):{'status':'ok','choice':c['expected_key']}}
  self.assertEqual(gate([c],r)['threshold'],.5)
if __name__=='__main__':unittest.main()
