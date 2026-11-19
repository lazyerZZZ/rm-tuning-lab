from math import sqrt
import unittest
from rm_tuning_lab.catalog import CASES
from rm_tuning_lab.core import simulate


class KalmanTests(unittest.TestCase):
    def test_static_rmse_improves_after_warmup(self):
        rows = simulate(CASES["range_still"])[100:]
        def rmse(key):
            return sqrt(sum((r[key] - r["reference"])**2 for r in rows) / len(rows))
        self.assertLess(rmse("output"), rmse("measurement"))

    def test_missing_observations_use_only_prediction(self):
        rows = simulate(CASES["range_dropout"])
        for i in range(150, 250):
            self.assertEqual(rows[i]["valid"], 0)
            self.assertEqual(rows[i]["measurement"], rows[i-1]["measurement"])
            self.assertEqual(rows[i]["velocity"], rows[i-1]["velocity"])
            self.assertAlmostEqual(rows[i]["output"], rows[i-1]["output"] + .02*rows[i]["velocity"])
        self.assertEqual(rows[250]["valid"], 1)
