import json, math, statistics, unittest
import validate as record

class RecordTests(unittest.TestCase):
    def test_exact_calls(self):record.validate_recorded()
    def test_order_stability(self):
        rows=record.read_json(record.ROOT/'recorded.json')['decisions']
        primary={(r['asset'],r['rule']):r['raw']['answers']['readiness']['choice'] for r in rows if r['condition']=='primary'}
        checks=[r for r in rows if r['condition']=='reversed_options']
        self.assertEqual(len(checks),6)
        for r in checks:self.assertEqual(primary[r['asset'],r['rule']],r['raw']['answers']['readiness']['choice'])
    def test_missing_images_are_two_unique_inputs(self):
        rows=[r for r in record.read_json(record.ROOT/'recorded.json')['decisions'] if not r['image_supplied']]
        self.assertEqual(len(rows),6)
        self.assertEqual(len({json.dumps(r['question'],sort_keys=True) for r in rows}),2)
    def test_warm_timing_scope(self):
        rows=record.read_json(record.ROOT/'recorded.json')['decisions']
        warm=[r['api_wall_ms'] for r in rows if r['image_supplied'] and not r['cold_first_api_call']]
        self.assertEqual(len(warm),11);self.assertAlmostEqual(statistics.median(warm),61.692067)
    def test_invalid_distribution_rejected(self):
        with self.assertRaises(ValueError):record.gated_action({'choice':'READY','confidence':math.nan,'probabilities':{'READY':math.nan,'WAIT':0,'UNCLEAR':0}},.8,0)

if __name__=='__main__':unittest.main()
