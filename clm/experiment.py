"""Run a new deterministic simulator experiment, without any model or network."""
import argparse
import json
import driving
import sorting


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('task', choices=('sorting', 'driving'))
    parser.add_argument('--case', default='03', choices=[s['id'] for s in sorting.SCENARIOS])
    parser.add_argument('--route', default='straight', choices=list(driving.ROUTES))
    parser.add_argument('--actions', help='Comma-separated explicit actions; otherwise use the programmed rule/planner')
    args = parser.parse_args()
    explicit = args.actions.split(',') if args.actions is not None else None
    records = []
    if args.task == 'sorting':
        case = next(s for s in sorting.SCENARIOS if s['id'] == args.case)
        state = sorting.initial(case)
        for index in range(2):
            if explicit is not None and index >= len(explicit):
                break
            action = explicit[index] if explicit is not None else sorting.expected(state)
            after, event = sorting.execute(state, action, case)
            records.append({'before': state, 'action': action, 'after': after, 'event': event,
                            'correct': action == sorting.expected(state)})
            state = after
            if state['terminal']:
                break
    else:
        state = driving.initial(args.route)
        for index in range(40):
            if explicit is not None and index >= len(explicit):
                break
            action = explicit[index] if explicit is not None else driving.rule_action(state, args.route)
            after = driving.step(state, action, args.route)
            records.append({'before': state, 'action': action, 'after': after})
            state = after
            if state['status'] != 'active':
                break
    print(json.dumps({'source': 'New deterministic simulator execution; no model inference',
                      'task': args.task, 'steps': records, 'final': state}, indent=2))


if __name__ == '__main__':
    main()
