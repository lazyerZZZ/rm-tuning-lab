from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from rm_tuning_lab.core import Knob
from rm_tuning_lab.catalog import CASES
from rm_tuning_lab.plugins import catalog, validate_cases


class PluginTests(unittest.TestCase):
    def test_catalog_contract(self):
        validate_cases(CASES)
        sample = CASES["wheel_step"]
        for case in [replace(sample, signals=("output",)), replace(sample, knobs={"seed": sample.knobs["kp"]}),
                     replace(sample, knobs={"a": Knob("坏范围", 2, 0, 1)})]:
            with self.assertRaises(ValueError):
                validate_cases({"demo": case})

    def test_file_level_errors(self):
        with TemporaryDirectory() as folder:
            path = Path(folder) / "plugin.py"
            for code, message in [("x = 1", "CASES"), ("from rm_tuning_lab.catalog import CASES", "重复")]:
                path.write_text(code)
                with self.assertRaisesRegex(ValueError, message):
                    catalog(str(path))
