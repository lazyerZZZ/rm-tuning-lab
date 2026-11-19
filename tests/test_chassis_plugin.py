"""Contract of the two loaded-wheel examples used by the rqt lesson."""
from pathlib import Path
import unittest

from rm_tuning_lab.core import simulate
from rm_tuning_lab.plugins import catalog


PLUGIN = Path(__file__).resolve().parents[1] / "examples" / "loaded_chassis.py"


class ChassisPluginTests(unittest.TestCase):
    def test_load_change_does_not_change_the_approach(self):
        case = catalog(str(PLUGIN))["chassis_drive_lag"]
        light = simulate(case, {"load_drag": .45})
        heavy = simulate(case, {"load_drag": .9})
        self.assertEqual(light[:200], heavy[:200])
        self.assertEqual((light[200]["load"], heavy[200]["load"]), (.45, .9))
        self.assertEqual(light[200]["output"], heavy[200]["output"])
        self.assertLess(heavy[201]["output"], light[201]["output"])

    def test_requested_drive_precedes_applied_drive(self):
        case = catalog(str(PLUGIN))["chassis_drive_lag"]
        rows = simulate(case, {"kp": 12., "ki": 16.})
        at_step, following = rows[50:52]
        self.assertEqual(at_step["effort"], 3.)
        self.assertEqual(at_step["drive_actual"], 0.)
        self.assertGreater(following["drive_actual"], 0.)
        self.assertLess(following["drive_actual"], at_step["effort"])
        self.assertLessEqual(max(abs(row["effort"]) for row in rows), 3.)
