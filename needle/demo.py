"""Inspect recorded outputs or run seven CPU examples; never execute tool calls."""
import argparse
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import time

ROOT = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--saved', action='store_true', help='Read historical results; no inference or downloads')
    parser.add_argument('--output', type=Path, help='Save a fresh run to a new JSON file')
    args = parser.parse_args()
    if args.saved:
        if args.output:
            parser.error('--output is only for fresh inference')
        print('Recorded video results, not a new inference run:')
        print((ROOT / 'example-results.json').read_text())
        return
    if args.output and args.output.exists():
        parser.error('Output already exists; choose a new filename to preserve earlier results')
    os.environ['NEEDLE_TELEMETRY'] = '0'
    os.environ['DO_NOT_TRACK'] = '1'
    import needle
    cases = json.loads((ROOT / 'cases.json').read_text())
    started = time.perf_counter()
    agent = needle.Needle(tools=cases['tools'])
    load_seconds = time.perf_counter() - started
    rows = []
    for query in cases['queries']:
        agent.reset()
        started = time.perf_counter()
        response = agent.complete(query)
        rows.append({'input': query, 'response': response,
                     'wall_ms': round((time.perf_counter() - started) * 1000, 2)})
    result = {'package': importlib.metadata.version('cactus-needle'),
              'machine': platform.machine(), 'load_seconds': load_seconds,
              'tools': cases['tools'], 'cases': rows,
              'scope': 'Seven synthetic demonstrations; no tool calls executed. CPU runtime; telemetry disabled.'}
    rendered = json.dumps(result, indent=2) + '\n'
    print(rendered)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        # Exclusive create also prevents a race from overwriting an existing receipt.
        with args.output.open('x') as handle:
            handle.write(rendered)


if __name__ == '__main__':
    main()
