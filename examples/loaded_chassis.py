"""Reference solution for the loaded chassis wheel lesson."""
from math import exp

from rm_tuning_lab.catalog import pid
from rm_tuning_lab.core import Case, Knob, DT
from rm_tuning_lab.models import wheel

CASES = {}


def floor_drag(t):
    return 0.45 if t >= 4.0 else 0.0


CASES["chassis_step_load"] = pid(
    "底盘轮组 · 持续阻力",
    "4 秒进入阻力段，对照积分增益改变前后的掉速与恢复。",
    wheel(tau=0.35, load=floor_drag),
)


def lagged_wheel(rng):
    speed = drive = integral = 0.0
    wheel_gain = 1.0 - exp(-DT / 0.35)
    drive_gain = 1.0 - exp(-DT / 0.10)

    def step(t, p):
        nonlocal speed, drive, integral
        target = float(t >= 1.0)
        load = p["load_drag"] if t >= 4.0 else 0.0
        error = target - speed
        candidate = integral + DT * error
        raw = p["kp"] * error + p["ki"] * candidate
        command = max(-3.0, min(3.0, raw))
        if (raw - command) * error <= 0.0:
            integral = candidate

        row = dict(reference=target, output=speed, effort=command,
                   drive_actual=drive, load=load)
        speed += wheel_gain * (drive - load - speed)
        drive += drive_gain * (command - drive)
        return row

    return step


CASES["chassis_drive_lag"] = Case(
    "底盘轮组 · 驱动滞后", "PI", "rad/s",
    "固定同一组 PI，先改变路面负载，再调 PI。",
    {"kp": Knob("Kp · 比例", 2.0, 0.0, 12.0),
     "ki": Knob("Ki · 积分", 6.0, 0.0, 16.0),
     "load_drag": Knob("等效负载 · rad/s", 0.45, 0.0, 1.5)},
    lagged_wheel, ("reference", "output", "effort", "drive_actual", "load"),
    "rad/s",
)
