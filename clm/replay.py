"""Verify saved decisions against deterministic environments; never calls a model."""
import argparse
import json
import math
import statistics
from pathlib import Path
import sorting
import driving

MODELS = ('clm', 'jev', 'laya', 'rule')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def answer(response, key):
    return response.get('result', response)['answers'][key]['choice']


def verify(data):
    report = {'sorting': {}, 'driving': {}, 'pilot': {}}
    transitions = 0
    for task, environment, names in (
        ('sorting', sorting, [s['id'] for s in sorting.SCENARIOS]),
        ('driving', driving, list(driving.ROUTES)),
    ):
        for model in MODELS:
            passed = 0
            times = []
            correct_actions = 0
            for name in names:
                record = json.loads((data / task / model / (name + '.json')).read_text())
                if task == 'sorting':
                    scenario = next(s for s in sorting.SCENARIOS if s['id'] == name)
                    require(record['scenario'] == scenario, 'Scenario changed')
                    state = environment.initial(scenario)
                    require(1 <= len(record['steps']) <= 2, 'Invalid sorting action count')
                else:
                    require(record['route'] == name, 'Route changed')
                    state = environment.initial(name)
                    require(1 <= len(record['steps']) <= 40, 'Invalid driving action count')
                for item in record['steps']:
                    require(item['before'] == state, 'Before-state mismatch')
                    observation = environment.observe(state) if task == 'sorting' else environment.observe(state, name)
                    require(item['request']['state'] == observation, 'Observation mismatch')
                    choice = item['selected'] if task == 'sorting' else item['action']
                    require(choice == answer(item['response'], 'action'), 'Output/action mismatch')
                    if task == 'sorting':
                        expected = sorting.expected(state)
                        require(item['expected'] == expected, 'Expected action mismatch')
                        require(item['correct'] == (choice == expected), 'Action score mismatch')
                        correct_actions += int(choice == expected)
                        state, event = sorting.execute(state, choice, scenario)
                        require(item['event'] == event, 'Event mismatch')
                    else:
                        require(state['status'] == 'active', 'Action after termination')
                        state = driving.step(state, choice, name)
                    require(item['after'] == state, 'After-state mismatch')
                    require(math.isfinite(item['seconds']) and item['seconds'] >= 0, 'Invalid timing')
                    times.append(item['seconds'])
                    transitions += 1
                if task == 'sorting':
                    expected_pass = all(s['correct'] for s in record['steps']) and state['terminal']
                    require(record['terminal'] == state['terminal'], 'Terminal flag mismatch')
                    require(record['budget_exhausted'] == (not state['terminal']), 'Budget flag mismatch')
                else:
                    require(record['final'] == state and state['status'] != 'active', 'Final state mismatch')
                    expected_pass = state['status'] == 'finished'
                require(record['passed'] == expected_pass, 'Run score mismatch')
                passed += int(expected_pass)
            report[task][model] = {'passed': passed, 'runs': len(names), 'actions': len(times),
                                  'median_call_ms': round(statistics.median(times) * 1000, 3),
                                  'maximum_call_ms': round(max(times) * 1000, 3)}
            if task == 'sorting':
                report[task][model]['correct_actions'] = correct_actions
    cases = json.loads((data / 'cases.json').read_text())
    require(len(cases) == 24 and len({c['id'] for c in cases}) == 24, 'Expected 24 unique pilot cases')
    for model in MODELS[:3]:
        scores = {}
        choices = {}
        for order in ('original', 'reversed'):
            count = 0
            for case in cases:
                record = json.loads((data / 'pilot' / model / f"{case['id']}-{order}.json").read_text())
                require(record['case'] == case['id'] and record['order'] == order, 'Pilot identity mismatch')
                require(record['request']['state'] == case['state'], 'Pilot state mismatch')
                require(record['request']['questions'] == case['questions'], 'Pilot question mismatch')
                criteria = record['request']['questions']['decision']['criteria']
                expected_order = list(case['questions']['decision']['criteria'])
                if order == 'reversed':
                    expected_order.reverse()
                require(list(criteria) == expected_order, 'Option order mismatch')
                chosen = answer(record['response'], 'decision')
                require(chosen in criteria, 'Unknown pilot choice')
                choices[(case['id'], order)] = chosen
                count += int(chosen == case['expected'])
            scores[order] = count
        scores['unchanged_choices'] = sum(choices[(c['id'], 'original')] == choices[(c['id'], 'reversed')] for c in cases)
        report['pilot'][model] = scores
    report['verified_transitions'] = transitions
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', type=Path, default=Path(__file__).resolve().parent / 'data')
    args = parser.parse_args()
    print(json.dumps(verify(args.data), indent=2))
