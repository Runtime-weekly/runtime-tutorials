import copy
import itertools
import unittest
from unittest.mock import patch
from baseline_v2 import env, plan, choose, ACTION_ORDER


class ControllerTests(unittest.TestCase):
    def run_route(self, route):
        state = env.initial(route)
        actions = []
        while state['status'] == 'active':
            before = copy.deepcopy(state)
            action, _ = choose(state, route)
            self.assertEqual(state, before)
            state = env.step(state, action, route)
            actions.append(action)
            self.assertLessEqual(len(actions), 40)
        return state, actions

    def test_original_routes_safe_and_ten_steps(self):
        for route in env.ROUTES:
            state, actions = self.run_route(route)
            self.assertEqual(state['status'], 'finished')
            self.assertEqual(len(actions), 10)

    def test_empty_road_stays_in_lane(self):
        spec = {'road': [[0, 1, 2] for _ in range(21)], 'obstacles': []}
        with patch.dict(env.ROUTES, {'empty': spec}):
            state, actions = self.run_route('empty')
        self.assertEqual(state['status'], 'finished')
        self.assertFalse(set(actions) & {'left', 'right'})
        self.assertEqual(actions, ['accelerate'] + ['hold'] * 9)

    def test_obstacle_counterfactual_changes_decisions(self):
        original = copy.deepcopy(env.ROUTES['straight'])
        moved = copy.deepcopy(original)
        moved['obstacles'] = [[0, 7]]
        with patch.dict(env.ROUTES, {'center_obstacle': original, 'left_obstacle': moved}):
            a, actions_a = self.run_route('center_obstacle')
            b, actions_b = self.run_route('left_obstacle')
        self.assertEqual(a['status'], 'finished')
        self.assertEqual(b['status'], 'finished')
        self.assertNotEqual(actions_a, actions_b)
        self.assertEqual(sum(x in ('left', 'right') for x in actions_a), 1)
        self.assertEqual(sum(x in ('left', 'right') for x in actions_b), 0)

    def test_blocked_road_has_no_safe_plan(self):
        spec = {'road': [[0, 1, 2] for _ in range(21)], 'obstacles': [[x, 1] for x in range(3)]}
        with patch.dict(env.ROUTES, {'blocked': spec}):
            self.assertIsNone(plan(env.initial('blocked'), 'blocked'))

    def test_matches_exhaustive_short_horizon_optimum(self):
        # Exhaustively enumerate all sequences up to three actions, independently
        # of the heap search, for a late-route obstacle counterfactual.
        spec = {'road': [[0, 1, 2] for _ in range(21)], 'obstacles': [[1, 19]]}
        with patch.dict(env.ROUTES, {'late': spec}):
            state = env.initial('late')
            state.update(progress=17, speed=2, ticks=37)
            candidates = []
            for n in range(1, 4):
                for actions in itertools.product(ACTION_ORDER, repeat=n):
                    current = state
                    for action in actions:
                        if current['status'] != 'active':
                            break
                        current = env.step(current, action, 'late')
                    else:
                        if current['status'] == 'finished':
                            candidates.append((n, sum(a in ('left', 'right') for a in actions),
                                               tuple(ACTION_ORDER.index(a) for a in actions), actions))
            best = min(candidates)
            result = plan(state, 'late')
        self.assertEqual((result['remaining_steps'], result['lane_changes']), best[:2])
        self.assertEqual(tuple(result['actions']), best[3])

    def test_plan_is_deterministic_and_original_routes_unchanged(self):
        before = copy.deepcopy(env.ROUTES)
        state = env.initial('straight')
        self.assertEqual(plan(state, 'straight'), plan(state, 'straight'))
        self.assertEqual(env.ROUTES, before)


if __name__ == '__main__':
    unittest.main()
