import unittest
from rm_tuning_lab.models import gain
from rm_tuning_lab.catalog import CASES
from rm_tuning_lab.core import simulate

class LqrTests(unittest.TestCase):
    def test_common_cost_scale_preserves_gain(self):
        for original, scaled in zip(gain(1., 8., 2., 1.), gain(1., 24., 6., 3.)):
            self.assertAlmostEqual(original, scaled)

    def test_more_expensive_force_reduces_initial_effort(self):
        runs = [simulate(CASES["cart_stop"], {"r_effort": r}) for r in (1., 5.)]
        self.assertGreater(runs[0][50]["effort"], runs[1][50]["effort"])
        self.assertAlmostEqual(runs[0][-1]["output"], 1., places=2)

    def test_force_limit(self):
        rows = simulate(CASES["cart_limit"])
        self.assertAlmostEqual(max(abs(r["effort"]) for r in rows), 0.6)
