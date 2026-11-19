from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from .catalog import CASES


def catalog(plugin=""):
    cases = dict(CASES)
    if plugin:
        path = Path(plugin).resolve()
        spec = spec_from_file_location("rm_user_cases", path)
        if spec is None or spec.loader is None:
            raise ValueError(f"无法加载 Python 模型 {path}")
        module = module_from_spec(spec)
        spec.loader.exec_module(module)
        if cases.keys() & module.CASES.keys():
            raise ValueError("自定义实例 ID 与内置实例重复")
        cases.update(module.CASES)
    return cases
