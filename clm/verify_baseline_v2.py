"""Recompute code-v2 decisions and verify saved traces; no model or network calls."""
import json
from pathlib import Path
from baseline_v2 import env, choose, VERSION


def verify():
    result = {}
    for route in env.ROUTES:
        record = json.loads((Path(__file__).resolve().parent / 'data' / 'driving' / 'rule-v2' / (route + '.json')).read_text())
        assert record['baseline_version'] == VERSION
        state = env.initial(route)
        lane_changes = 0
        for saved in record['steps']:
            assert saved['before'] == state
            assert saved['request']['state'] == env.observe(state, route)
            action, plan = choose(state, route)
            assert action == saved['action'] == saved['response']['answers']['action']['choice']
            assert plan == saved['response']['search']
            state = env.step(state, action, route)
            assert saved['after'] == state
            lane_changes += int(action in ('left', 'right'))
        assert state == record['final'] and state['status'] == 'finished' and record['passed']
        result[route] = {'steps': len(record['steps']), 'lane_changes': lane_changes, 'passed': True}
    return result


if __name__ == '__main__':
    print(json.dumps(verify(), indent=2))
