from functools import lru_cache
from math import exp, sin

from .core import DT


def clamp(value, limit):
    return max(-limit, min(limit, value))


def wheel(tau=0.25, load=lambda t: 0.0, target=lambda t: 1.0 if t >= 1 else 0.0,
          noise=0.0, limit=3.0, encoder_step=0.0, show_reading=False):
    """First-order speed plant. The effort unit is equivalent steady-state speed."""
    def factory(rng):
        speed = integral = last = derivative = 0.0

        def step(t, p):
            nonlocal speed, integral, last, derivative
            reference = target(t)
            reading = speed + rng.gauss(0, noise)
            if encoder_step:
                reading = round(reading / encoder_step) * encoder_step
            error = reference - reading
            slope = (last - reading) / DT
            derivative += DT / (DT + p.get('d_filter', 0.0)) * (slope - derivative)
            last = reading
            candidate = integral + error * DT
            raw = p["kp"] * error + p["ki"] * candidate + p["kd"] * derivative
            effort = clamp(raw, limit)
            if p.get('anti_windup', 1.0) < 0.5 or (raw - effort) * error <= 0:
                integral = candidate
            speed_now = speed
            speed += (1 - exp(-DT / tau)) * (effort - load(t) - speed)
            row = {"reference": reference, "output": speed_now, "effort": effort}
            if show_reading:
                row["measurement"] = reading
            return row
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


def cart(mass=1.0, load=lambda t: 0.0, target=lambda t: 1.0 if t >= 1 else 0.0,
         initial_velocity=0.0, limit=4.0):
    def factory(rng):
        position, velocity = 0.0, initial_velocity

        def step(t, p):
            nonlocal position, velocity
            reference = target(t)
            kp, kv = gain(mass, p["q_position"], p["q_velocity"], p["r_effort"])
            effort = clamp(kp * (reference - position) - kv * velocity, limit)
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


def moving_sensor(truth, missing=lambda t: False, sigma=0.25):
    """Constant-velocity KF with an independent random acceleration each sample."""
    def factory(rng):
        position = velocity = last_reading = 0.0
        p00, p01, p11 = 1.0, 0.0, 1.0

        def step(t, p):
            nonlocal position, velocity, last_reading, p00, p01, p11
            qa, r = p["q_accel"], p["r_measure"]
            position += DT * velocity
            a = p00 + 2 * DT * p01 + DT**2 * p11 + DT**4 * qa / 4
            b = p01 + DT * p11 + DT**3 * qa / 2
            c = p11 + DT**2 * qa
            actual = truth(t)
            reading = actual + rng.gauss(0, sigma)
            valid = not missing(t)
            if valid:
                last_reading = reading
                innovation = reading - position
                position += a / (a + r) * innovation
                velocity += b / (a + r) * innovation
                p00, p01, p11 = a * r / (a + r), b * r / (a + r), c - b*b / (a+r)
            else:
                p00, p01, p11 = a, b, c
            return {"reference": actual, "output": position, "measurement": last_reading,
                    "velocity": velocity, "valid": float(valid)}
        return step
    return factory


def carriage(speed_limit=1.2, target=lambda t: float(t >= 1)):
    """Outer position P loop commands an inner velocity PI loop."""
    def factory(rng):
        position = velocity = integral = 0.0

        def step(t, p):
            nonlocal position, velocity, integral
            goal = target(t)
            command = clamp(p["outer_kp"] * (goal - position), speed_limit)
            error = command - velocity
            candidate = integral + DT * error
            raw = p["inner_kp"] * error + p["inner_ki"] * candidate
            drive = clamp(raw, 2.0)
            if (raw - drive) * error <= 0:
                integral = candidate
            row = dict(reference=goal, output=position, effort=drive,
                       speed_reference=command, velocity=velocity)
            # Exact held-input transition of dv/dt = (drive - v) / tau.
            tau = 0.2
            change = (drive - velocity) * (1 - exp(-DT / tau))
            position += drive * DT - tau * change
            velocity += change
            return row
        return step
    return factory
