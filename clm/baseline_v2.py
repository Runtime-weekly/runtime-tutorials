"""Exact lexicographic route search; privileged simulator-transition access."""
import heapq
import itertools
import driving as env

VERSION = 'lane-keeping-lexicographic-r2'
ACTION_ORDER = ('hold', 'accelerate', 'left', 'right', 'brake')


def state_key(state):
    return tuple(state[k] for k in ('lane', 'progress', 'speed', 'ticks', 'stalled', 'status'))


def plan(state, route):
    """Minimize (remaining actions, lane changes), then ranked action sequence.

    Nonnegative edge costs permit Dijkstra search. Every transition is evaluated
    with the unchanged simulator; failed states are discarded. Search results
    are not carried between real decision calls and no model data is consulted.
    """
    if state['status'] != 'active':
        return None
    counter = itertools.count()
    zero = (0, 0, ())
    queue = [(zero, next(counter), dict(state), ())]
    best = {state_key(state): zero}
    expanded = 0
    while queue:
        cost, _, current, actions = heapq.heappop(queue)
        if cost != best.get(state_key(current)):
            continue
        if current['status'] == 'finished':
            return {'actions': list(actions), 'remaining_steps': cost[0],
                    'lane_changes': cost[1], 'expanded_states': expanded}
        expanded += 1
        for rank, action in enumerate(ACTION_ORDER):
            nxt = env.step(current, action, route)
            if nxt['status'] not in ('active', 'finished'):
                continue
            nxt_cost = (cost[0] + 1, cost[1] + int(action in ('left', 'right')), cost[2] + (rank,))
            key = state_key(nxt)
            if key not in best or nxt_cost < best[key]:
                best[key] = nxt_cost
                heapq.heappush(queue, (nxt_cost, next(counter), nxt, actions + (action,)))
    return None


def choose(state, route):
    result = plan(state, route)
    if result is None or not result['actions']:
        raise ValueError('No safe route within the unchanged action budget')
    return result['actions'][0], result
