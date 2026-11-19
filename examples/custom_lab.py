"""Reuse a plant or implement a new one. Load this file in either interface."""
from rm_tuning_lab.catalog import pid
from rm_tuning_lab.core import Case, Knob, DT
from rm_tuning_lab.models import wheel

def tank(rng):
    level = 0.0

    def step(t, p):
        nonlocal level
        target = float(t >= 1)
        pump = max(0.0, min(2.0, p["kp"] * (target - level)))
        row = {"reference": target, "output": level, "effort": pump}
        level += DT * (pump - 0.25 * level)
        return row
    return step

CASES = {
    "slow_wheel": pid("自定义慢速轮组", "时间常数增至 0.8 秒，比较相同增益下的上升过程。", wheel(tau=0.8)),
    "tank": Case("自定义液位模型", "P", "m", "把 Kp 从 1 增至 4，观察泄流造成的稳态误差。",
                 {"kp": Knob("Kp", 1.0, 0, 8)}, tank),
}
