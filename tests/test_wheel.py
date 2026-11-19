import unittest
from rm_tuning_lab.catalog import CASES
from rm_tuning_lab.core import simulate

class WheelTests(unittest.TestCase):
    def test_static_proportional_gain(self):
        for kp in (1., 3.):
            rows = simulate(CASES["wheel_step"], {"kp": kp, "ki": 0.})
            self.assertAlmostEqual(rows[-1]["output"], kp / (1 + kp), places=8)

    def test_antiwindup_recovers(self):
        case = CASES["wheel_limit"]
        fast, slow = [simulate(case, {"anti_windup": v}) for v in (1, 0)]
        self.assertLess(abs(fast[250]["output"]-0.3), abs(slow[250]["output"]-0.3))
        self.assertLessEqual(max(abs(row["effort"]) for row in slow), 1)
