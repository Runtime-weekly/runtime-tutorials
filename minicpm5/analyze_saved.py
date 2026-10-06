"""Recompute the saved final-answer checks offline using only Python's standard library."""
import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def parse(text):
    if not isinstance(text, str):
        return False, None
    try:
        return True, json.loads(text)
    except ValueError:
        return False, None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--results', type=Path, help='Score a new run_text.py results.jsonl instead of the bundled data')
    args = parser.parse_args()
    frozen = (ROOT / 'tasks.frozen.json').read_bytes()
    assert hashlib.sha256(frozen).hexdigest() == (ROOT / 'tasks.sha256.txt').read_text().strip()
    cases = {row['id']: row for row in json.loads(frozen)}
    assert len(cases) == 12
    paths = [args.results] if args.results else sorted((ROOT / 'data').glob('*.json'))
    for path in paths:
        rows = json.loads(path.read_text()) if path.suffix == '.json' else [json.loads(line) for line in path.read_text().splitlines()]
        assert len(rows) == len(cases)
        assert len({r['id'] for r in rows}) == len(cases)
        assert {r['id'] for r in rows} == set(cases)
        strict = relaxed = valid_count = 0
        for row in rows:
            case = cases[row['id']]
            assert all(row[k] == case[k] for k in ('kind', 'prompt', 'expected'))
            final = row['final_answer']
            if final is None:
                assert row['truncated'] and row['final_status'] == 'no_completed_answer'
            valid, parsed = parse(final)
            correct = valid and parsed == case['expected']
            assert valid == row['valid_json'] and correct == row['correct']
            strict += correct
            valid_count += valid
            fence = re.fullmatch(r'```(?:json)?\s*\n(.*?)\n```', final.strip(), re.S) if final else None
            relaxed_valid, relaxed_value = parse(fence.group(1).strip() if fence else final)
            relaxed += relaxed_valid and relaxed_value == case['expected']
        print(json.dumps({'configuration': path.stem, 'cases': len(rows),
                          'strict_exact': strict, 'one_fence_relaxed_exact': relaxed,
                          'parseable_json': valid_count,
                          'truncated': sum(r['truncated'] for r in rows)}))


if __name__ == '__main__':
    main()
