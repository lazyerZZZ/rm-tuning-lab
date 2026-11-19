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

CASES.update({
    "wheel_reverse": pid("轮组正反转", "1 秒加速，4 秒反转。加大 Ki，比较反转后首次过零时间和最低轮速。", wheel(target=lambda t: 0 if t < 1 else (1 if t < 4 else -1))),
    "wheel_ramp": pid("斜坡速度指令", "目标在 1 至 4 秒间匀速增加。把 Ki 从 0 调到 4，比较斜坡段误差和停升后的误差。", wheel(target=lambda t: max(0, min(1.5, (t-1)*0.5)))),
    "wheel_bump": pid("越过阻力带", "3 至 4 秒施加短促阻力。固定 Kp，提高 Ki，比较离开阻力带后的回弹。", wheel(load=lambda t: 1.2 if 3 <= t < 4 else 0)),
    "wheel_limit": Case("电机限幅与积分饱和", "PID", "rad/s",
        "1 至 4 秒的目标为 2，驱动上限为 1。用 anti_windup = 0 和 1 对照，观察目标回落至 0.3 后的恢复时间。",
        dict(PID, anti_windup=Knob("条件积分 · 0 关 / 1 开（阈值 0.5）", 1., 0, 1)),
        wheel(limit=1, target=lambda t: 0 if t < 1 else (2 if t < 4 else 0.3))),
    "wheel_noise": Case("微分放大测速噪声", "PID", "rad/s",
        "设 Kd = 0.08。将微分滤波时间从 0 调至 0.08 秒，同时查看 effort，观察控制抖动。",
        dict(PID, d_filter=Knob("微分滤波时间 · s", 0., 0, 0.25)), wheel(noise=0.08, show_reading=True),
        ("reference", "output", "effort", "measurement")),
    "wheel_encoder": Case("低分辨率编码器", "PID", "rad/s",
        "目标为 0.35，编码器以 0.2 为一格。对照 measurement 与 output，观察 Ki 从 0 增至 4 后平均误差和周期摆动。",
        PID, wheel(encoder_step=0.2, show_reading=True, target=lambda t: 0.35 if t >= 1 else 0),
        ("reference", "output", "effort", "measurement")),
})
