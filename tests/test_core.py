import unittest
from rm_tuning_lab.catalog import CASES
from rm_tuning_lab.core import STEPS, simulate
from rm_tuning_lab.plugins import catalog

class CoreTests(unittest.TestCase):
    def test_every_case_and_plugin(self):
        for name, case in catalog("examples/custom_lab.py").items():
            with self.subTest(name=name):
                rows = simulate(case)
                self.assertEqual(len(rows), STEPS)
                self.assertEqual(rows, simulate(case))
                self.assertEqual(rows[0].keys(), {"t", *case.signals})

    def test_invalid_parameter(self):
        with self.assertRaises(ValueError):
            simulate(CASES["wheel_step"], {"ki": -1})
