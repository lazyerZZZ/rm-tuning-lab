from functools import lru_cache
from math import exp, sin

from .core import DT


def clamp(value, limit):
    return max(-limit, min(limit, value))


def wheel(tau=0.25, load=lambda t: 0.0, target=lambda t: 1.0 if t >= 1 else 0.0,
          noise=0.0, limit=3.0):
    """First-order speed plant. The effort unit is equivalent steady-state speed."""
    def factory(rng):
        speed = integral = last = 0.0

        def step(t, p):
            nonlocal speed, integral, last
            reference = target(t)
            reading = speed + rng.gauss(0, noise)
            error = reference - reading
            derivative = (last - reading) / DT
            last = reading
            candidate = integral + error * DT
            raw = p["kp"] * error + p["ki"] * candidate + p["kd"] * derivative
            effort = clamp(raw, limit)
            if (raw - effort) * error <= 0:
                integral = candidate
            speed_now = speed
            speed += (1 - exp(-DT / tau)) * (effort - load(t) - speed)
            return {"reference": reference, "output": speed_now, "effort": effort}
        return step
    return factory


@lru_cache(maxsize=128)
def gain(mass, qp, qv, r):
    """First gain of a 400-step discrete LQR, zero terminal cost, ZOH plant."""
    b, c = DT**2 / (2 * mass), DT / mass
    p00 = p01 = p11 = 0.0
    for _ in range(400):
        a = b * p00 + c * p01
        d = b * p01 + c * p11
        s = r + a * b + d * c
        h = a * DT + d
        k0, k1 = a / s, h / s
        p00, p01, p11 = (qp + p00 - a * k0,
                         DT * p00 + p01 - a * k1,
                         qv + DT**2 * p00 + 2 * DT * p01 + p11 - h * k1)
    return k0, k1


def cart(mass=1.0, load=lambda t: 0.0, target=lambda t: 1.0 if t >= 1 else 0.0):
    def factory(rng):
        position = velocity = 0.0

        def step(t, p):
            nonlocal position, velocity
            reference = target(t)
            kp, kv = gain(mass, p["q_position"], p["q_velocity"], p["r_effort"])
            effort = clamp(kp * (reference - position) - kv * velocity, 4.0)
            row = {"reference": reference, "output": position, "effort": effort}
            acceleration = (effort - load(t)) / mass
            position += DT * velocity + 0.5 * DT**2 * acceleration
            velocity += DT * acceleration
            return row
        return step
    return factory


def sensor(truth=lambda t: 1.0 if t >= 2 else 0.0, sigma=0.25):
    def factory(rng):
        estimate, variance = 0.0, 1.0

        def step(t, p):
            nonlocal estimate, variance
            actual = truth(t)
            reading = actual + rng.gauss(0, sigma)
            variance += p["q_process"]
            k = variance / (variance + p["r_measure"])
            estimate += k * (reading - estimate)
            variance *= 1 - k
            return {"reference": actual, "output": estimate, "measurement": reading}
        return step
    return factory
