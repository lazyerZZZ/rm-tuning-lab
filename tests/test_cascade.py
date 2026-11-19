import unittest
from rm_tuning_lab.catalog import CASES
from rm_tuning_lab.core import simulate


class CascadeTests(unittest.TestCase):
    def test_speed_and_drive_caps(self):
        for r in simulate(CASES["carriage_cap"]):
            self.assertLessEqual(abs(r["speed_reference"]), .4)
            self.assertLessEqual(abs(r["effort"]), 2.)

    def test_disabled_inner_loop_prevents_motion(self):
        rows = simulate(CASES["carriage_loops"], {"inner_kp": 0., "inner_ki": 0.})
        self.assertGreater(rows[-1]["speed_reference"], 0)
        self.assertEqual(rows[-1]["output"], 0)
