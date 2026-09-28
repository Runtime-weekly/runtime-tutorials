import unittest

import driving
import sorting


class SortingTests(unittest.TestCase):
    def test_all_six_rule_runs(self):
        for case in sorting.SCENARIOS:
            state = sorting.initial(case)
            for _ in range(2):
                state, _ = sorting.execute(state, sorting.expected(state), case)
                if state['terminal']:
                    break
            self.assertTrue(state['terminal'])

    def test_inspect_updates_observation_without_finishing(self):
        case = sorting.SCENARIOS[2]
        before = sorting.initial(case)
        after, _ = sorting.execute(before, 'inspect', case)
        self.assertEqual(before['observed_color'], 'unknown')
        self.assertEqual(after['observed_color'], 'blue')
        self.assertFalse(after['terminal'])
        self.assertEqual(sorting.expected(after), 'blue')

    def test_damage_overrides_missing_color(self):
        self.assertEqual(sorting.expected(sorting.initial(sorting.SCENARIOS[5])), 'reject')

    def test_full_bin_blocks_without_increment(self):
        case = sorting.SCENARIOS[3]
        before = sorting.initial(case)
        after, _ = sorting.execute(before, 'red', case)
        self.assertEqual(after['disposition'], 'blocked')
        self.assertEqual(after['bins']['red'], 2)
        self.assertFalse(before['terminal'])

    def test_bins_reset_and_unrelated_full_bin_is_irrelevant(self):
        case = sorting.SCENARIOS[4]
        before = sorting.initial(case)
        self.assertEqual(sorting.expected(before), 'green')
        after, _ = sorting.execute(before, 'green', case)
        self.assertEqual(after['bins']['green'], 1)
        self.assertEqual(sorting.initial(case)['bins']['green'], 0)

    def test_unknown_action_rejected(self):
        case = sorting.SCENARIOS[0]
        with self.assertRaises(ValueError):
            sorting.execute(sorting.initial(case), 'invented', case)


class DrivingTests(unittest.TestCase):
    def test_collision_checks_every_speed_two_cell_without_tunneling(self):
        state = driving.initial("straight")
        state = driving.step(state, "accelerate", "straight")
        state = driving.step(state, "hold", "straight")  # progress 4, speed 2
        state = driving.step(state, "hold", "straight")  # progress 6, speed 2
        # A speed-two move must collide at row 7 rather than jump to row 8.
        state = driving.step(state, "hold", "straight")
        self.assertEqual(state["status"], "collision")
        self.assertEqual(state["progress"], 7)

    def test_off_road_after_lane_shift(self):
        state = driving.initial("narrowing")
        state.update({"lane": 1, "progress": 13, "speed": 1})
        state = driving.step(state, "left", "narrowing")
        self.assertEqual(state["status"], "off_road")
        self.assertEqual(state["progress"], 13)
        self.assertEqual(state["lane"], 0)

    def test_braking_to_zero_then_accelerating(self):
        state = driving.initial("straight")
        state = driving.step(state, "brake", "straight")
        self.assertEqual((state["speed"], state["progress"], state["stalled"]), (0, 0, 1))
        state = driving.step(state, "accelerate", "straight")
        self.assertEqual((state["speed"], state["progress"]), (1, 1))

    def test_terminal_step_is_rejected(self):
        state = driving.initial("straight")
        state["status"] = "finished"
        state["progress"] = 20
        rejected = driving.step(state, "hold", "straight")
        self.assertEqual(rejected["event"], "terminal_rejected")
        self.assertEqual(rejected["ticks"], state["ticks"])

    def test_rule_runs_all_routes_to_finish_inside_budget(self):
        for route in driving.ROUTES:
            state = driving.initial(route)
            actions = 0
            while state["status"] == "active":
                action = driving.rule_action(state, route)
                self.assertIn(action, driving.ACTIONS)
                state = driving.step(state, action, route)
                actions += 1
                self.assertLessEqual(actions, 40)
            self.assertEqual(state["status"], "finished", route)


if __name__ == "__main__":
    unittest.main()
