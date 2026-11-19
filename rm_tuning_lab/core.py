"""Shared contract for the ROS node, browser and user-written models."""
from dataclasses import dataclass
from typing import Callable
import math
import random

DT = 0.02
STEPS = 400


@dataclass(frozen=True)
class Knob:
    label: str
    default: float
    low: float
    high: float


@dataclass(frozen=True)
class Case:
    title: str
    group: str
    unit: str
    lesson: str
    knobs: dict
    factory: Callable
    # factory(rng) returns step(t, params) -> dict[str, float].
    signals: tuple = ("reference", "output", "effort")


def parameters(case, overrides=None):
    values = {k: p.default for k, p in case.knobs.items()}
    for key, value in (overrides or {}).items():
        if key not in values:
            raise ValueError(f"未知参数 {key}")
        p = case.knobs[key]
        if type(value) not in (int, float) or not p.low <= value <= p.high:
            raise ValueError(f"{key} 应在 [{p.low}, {p.high}] 内")
        values[key] = float(value)
    return values


class Trial:
    def __init__(self, case, seed=7):
        self.case = case
        self.step = case.factory(random.Random(seed))
        self.index = 0

    def tick(self, params):
        t = self.index * DT
        row = self.step(t, params)
        if row.keys() != set(self.case.signals) or not all(map(math.isfinite, row.values())):
            raise ValueError("模型输出需包含所有声明话题，且数值有限")
        self.index += 1
        return {"t": t, **row}


def simulate(case, overrides=None, seed=7):
    params = parameters(case, overrides)
    trial = Trial(case, seed)
    return [trial.tick(params) for _ in range(STEPS)]
