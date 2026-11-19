from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import re
import math
from .core import Case, Knob
from .catalog import CASES


NAME = re.compile(r"[a-z][a-z0-9_]*")
RESERVED = {"case_id", "plugin", "seed", "use_sim_time", "t", "trial_time", "reset"}


def validate_cases(mapping):
    if not isinstance(mapping, dict):
        raise ValueError("CASES 应为 dict[str, Case]")
    for key, case in mapping.items():
        if not isinstance(key, str) or not NAME.fullmatch(key) or not isinstance(case, Case):
            raise ValueError(f"无效实例 {key!r}")
        signals = case.signals
        if not {"reference", "output"}.issubset(signals) or len(signals) != len(set(signals)):
            raise ValueError(f"{key} 需要 reference、output 以及唯一的信号名")
        for name in (*signals, *case.knobs):
            if not isinstance(name, str) or not NAME.fullmatch(name) or name in RESERVED:
                raise ValueError(f"{key} 使用了无效或保留名称 {name!r}")
        for name, knob in case.knobs.items():
            if not isinstance(knob, Knob) or not all(math.isfinite(v) for v in (knob.low, knob.default, knob.high)):
                raise ValueError(f"{key}.{name} 的范围和默认值必须有限")
            if not knob.low <= knob.default <= knob.high or knob.low == knob.high:
                raise ValueError(f"{key}.{name} 的默认值或范围无效")
        if not callable(case.factory):
            raise ValueError(f"{key} 的 factory 必须可调用")


def catalog(plugin=""):
    cases = dict(CASES)
    if plugin:
        path = Path(plugin).resolve()
        spec = spec_from_file_location("rm_user_cases", path)
        if spec is None or spec.loader is None:
            raise ValueError(f"无法加载 Python 模型 {path}")
        module = module_from_spec(spec)
        spec.loader.exec_module(module)
        if not hasattr(module, "CASES"):
            raise ValueError("插件应导出 CASES 字典")
        validate_cases(module.CASES)
        if cases.keys() & module.CASES.keys():
            raise ValueError("自定义实例 ID 与内置实例重复")
        cases.update(module.CASES)
    return cases
