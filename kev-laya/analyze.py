#!/usr/bin/env python3
"""Recompute the published pilot with Python's standard library; no model or network."""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import statistics


def analyze(root):
    cases_path = root / 'cases.json'
    cases = json.loads(cases_path.read_text())
    data = json.loads((root / 'results.json').read_text())
    measurements = json.loads((root / 'measurements.json').read_text())
    digest = hashlib.sha256(cases_path.read_bytes()).hexdigest()
    if digest != data['case_sha256'] or digest != measurements['case_sha256']:
        raise ValueError('Frozen case hash mismatch')
    labels = {case['id']: case for case in cases['cases']}
    if len(labels) != 30:
        raise ValueError('Expected 30 unique cases')
    rows = data['results']
    if len(rows) != 180 or {r['model'] for r in rows} != {'laya', 'kev'}:
        raise ValueError('Expected exactly 90 decisions for each of two models')
    # The CSV is a second representation, not another dataset. Check it too.
    with (root / 'results.csv').open(newline='') as handle:
        csv_rows = list(csv.DictReader(handle))
    if len(csv_rows) != len(rows):
        raise ValueError('CSV/JSON length mismatch')
    for a, b in zip(rows, csv_rows):
        for key, value in a.items():
            other = json.loads(b[key]) if key in ('order', 'probabilities') else b[key]
            expected = value if key in ('order', 'probabilities') else str(value)
            if other != expected:
                raise ValueError(f'CSV/JSON mismatch: {a["model"]}/{a["id"]}/{key}')
    summary = {}
    for model in ('laya', 'kev'):
        selected = [r for r in rows if r['model'] == model]
        observed = {(r['id'], r['order_index']) for r in selected}
        expected_keys = {(key, order) for key in labels for order in range(3)}
        if len(selected) != 90 or observed != expected_keys:
            raise ValueError('Missing or duplicate case/order')
        for row in selected:
            case = labels[row['id']]
            for key in ('state', 'expected', 'group'):
                if row[key] != case[key]:
                    raise ValueError(f'Changed case field: {row["id"]}/{key}')
            if row['order'] != cases['permutations'][row['order_index']]:
                raise ValueError('Option-order mismatch')
            probs = row['probabilities']
            if set(probs) != set(cases['options']):
                raise ValueError('Missing probability option')
            if not all(math.isfinite(v) and 0 <= v <= 1 for v in probs.values()):
                raise ValueError('Invalid probability')
            if abs(sum(probs.values()) - 1) > .001:
                raise ValueError('Probability sum mismatch')
            if row['choice'] not in probs or row['correct'] != (row['choice'] == row['expected']):
                raise ValueError('Choice/score mismatch')
            if not math.isfinite(row['elapsed_ms']) or row['elapsed_ms'] <= 0:
                raise ValueError('Invalid latency')
        canonical = [r for r in selected if r['order_index'] == 0]
        unstable = [key for key in labels if len({r['choice'] for r in selected if r['id'] == key}) > 1]
        stable_correct = sum(all(r['correct'] for r in selected if r['id'] == key) for key in labels)
        latencies = sorted(r['elapsed_ms'] for r in selected)
        meta = measurements['models'][model]
        files = meta['asset_files']
        identities = {(f['repo'], f['revision'], f['file']) for f in files}
        if len(identities) != len(files):
            raise ValueError('Duplicate model asset entry')
        disk = sum(f['bytes'] for f in files)
        weights = sum(f['bytes'] for f in files if f['role'] == 'weight')
        summary[model] = {
            'unique_cases': 30,
            'decisions': 90,
            'canonical_correct': sum(r['correct'] for r in canonical),
            'canonical_by_group': {
                group: {'correct': sum(r['correct'] for r in canonical if r['group'] == group),
                        'n': sum(r['group'] == group for r in canonical)}
                for group in ('clear', 'ambiguous', 'boundary')
            },
            'all_orders_correct': sum(r['correct'] for r in selected),
            'stable_correct_cases': stable_correct,
            'order_unstable_cases': len(unstable),
            'order_unstable_ids': unstable,
            'wrong_max_probability_ge_0_9': sum(not r['correct'] and max(r['probabilities'].values()) >= .9 for r in selected),
            'median_ms': statistics.median(latencies),
            'p95_ms_nearest_rank': latencies[math.ceil(.95 * len(latencies)) - 1],
            'peak_process_rss_gib': meta['peak_process_rss_kib'] / 1024**2,
            'model_asset_bytes': disk,
            'model_asset_gib': disk / 1024**3,
            'weight_bytes': weights,
            'weight_gib': weights / 1024**3,
            'loaded_parameters': meta['loaded_parameters'],
        }
    return {'case_sha256': digest, 'models': summary}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Verify recomputation equals saved expected-summary.json')
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    result = analyze(root)
    if args.check:
        expected = json.loads((root / 'expected-summary.json').read_text())
        if result != expected:
            raise SystemExit('FAIL: summary mismatch')
        print('PASS: 30 frozen cases, 180 decisions, CSV/JSON consistency, and saved summary verified.')
    else:
        print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
