from math import sin
from .core import Case, Knob
from .models import cart, sensor, wheel


PID = dict(kp=Knob("Kp · 比例", 1.5, 0, 12), ki=Knob("Ki · 积分", 3.0, 0, 16),
           kd=Knob("Kd · 微分", 0.0, 0, 0.18))
LQR = dict(q_position=Knob("Q · 位置代价", 8.0, 0.05, 50),
           q_velocity=Knob("Q · 速度代价", 2.0, 0.05, 30),
           r_effort=Knob("R · 力代价", 1.0, 0.05, 15))
KF = dict(q_process=Knob("Q · 每步过程方差", 0.002, 0.00001, 0.2),
          r_measure=Knob("R · 观测方差", 0.0625, 0.0001, 1))
FILTER = ("reference", "output", "measurement")


def pid(title, lesson, model):
    return Case(title, "PID", "rad/s", lesson, PID, model)


def lqr(title, lesson, model):
    return Case(title, "LQR", "m", lesson, LQR, model)


def kf(title, lesson, model):
    return Case(title, "Kalman", "m", lesson, KF, model, FILTER)


CASES = {
    "wheel_step": pid("轮速阶跃", "先把 Ki 和 Kd 设为 0。将 Kp 从 1 调到 3，比较最终轮速与目标的差距。再恢复 Ki = 3。", wheel()),
    "wheel_load": pid("轮组持续负载", "3 秒时增加阻力。分别用 Ki = 0 和 3 运行，观察轮速恢复到目标需要多久。", wheel(load=lambda t: 0.6 if t >= 3 else 0)),
    "cart_stop": lqr("滑台定位", "将 R 从 1 增至 5，比较施力峰值与到达 1 米位置的时间。", cart()),
    "cart_heavy": lqr("重载滑台", "滑台质量增至 3 kg。固定 R，将位置权重从 8 增至 24，观察施力是否触及 4 N。", cart(3)),
    "range_step": kf("测距读数突变", "2 秒时距离跳变。先把 R 从 0.0625 增至 0.3，观察估计抖动和跟随延迟。", sensor()),
    "range_wave": kf("往复距离估计", "固定 R，将 Q 从 0.002 增至 0.02，比较估计峰值与真实峰值出现的时间。", sensor(lambda t: sin(2 * t))),
}
