"""Measure one complete, unmodified 50 Hz teaching trial from live ROS topics."""
import argparse
import csv
import math
import time
from collections import defaultdict

import rclpy
from rclpy.parameter_client import AsyncParameterClient
from std_msgs.msg import Float64

SIGNALS = {
    "wheel_step": ("reference", "output"),
    "carriage_loops": ("reference", "output", "speed_reference", "velocity"),
    "cart_stop": ("reference", "output", "effort"),
    "range_step": ("reference", "output", "measurement"),
    "chassis_step_load": ("reference", "output", "effort"),
    "chassis_drive_lag": ("reference", "output", "effort", "load", "drive_actual"),
}
KNOBS = {
    "wheel_step": ("kp", "ki", "kd"),
    "carriage_loops": ("outer_kp", "inner_kp", "inner_ki"),
    "cart_stop": ("q_position", "q_velocity", "r_effort"),
    "range_step": ("r_measure", "q_process", "seed"),
    "chassis_step_load": ("kp", "ki", "kd"),
    "chassis_drive_lag": ("kp", "ki", "load_drag"),
}


def read_params(node, client, names):
    future = client.get_parameters(names)
    rclpy.spin_until_future_complete(node, future, timeout_sec=5.)
    if not future.done() or future.result() is None:
        raise ValueError("读取参数超时，请确认节点仍在运行。")
    from rclpy.parameter import parameter_value_to_python
    return dict(zip(names, (parameter_value_to_python(v) for v in future.result().values)))


def full_trial(streams, keys, start, end):
    # Each timer callback publishes trial_time first, then each Float64 signal.
    # Pair by DDS publisher timestamps so cross-topic delivery order is irrelevant.
    samples = {k: sorted((s, v) for s, v in streams[k] if start <= s < end) for k in keys}
    clock = samples["trial_time"]
    if any(len(seq) != 400 for seq in samples.values()):
        return None
    rows = []
    for i, (stamp, t) in enumerate(clock):
        next_stamp = clock[i+1][0] if i+1 < len(clock) else end
        if abs(t - i * .02) > 1e-8:
            return None
        if any(not stamp <= samples[k][i][0] < next_stamp for k in keys):
            return None
        rows.append({k: samples[k][i][1] for k in keys})
    return rows


def collect(node, case):
    streams = defaultdict(list)
    keys = ("trial_time", *SIGNALS[case])
    def callback(key):
        def receive(msg, info):
            streams[key].append((info["source_timestamp"], msg.data))
        return receive
    for key in keys:
        node.create_subscription(Float64, "/tuning_lab/" + key, callback(key), 100)
    deadline = time.monotonic() + 35.
    while time.monotonic() < deadline:
        rclpy.spin_once(node, timeout_sec=.15)
        # Only scan for completed cycles after the end marker has arrived.
        if len(streams["trial_time"]) < 401:
            continue
        starts = [s for s, t in streams["trial_time"] if t == 0.]
        if len(starts) >= 2:
            rows = full_trial(streams, keys, starts[-2], starts[-1])
            if rows:
                return rows
    raise ValueError("未收到完整对齐的 400 拍。确认只有一个 /tuning_lab 节点并在同机重试。")


def rmse(rows, value, reference):
    return math.sqrt(sum((r[value] - r[reference])**2 for r in rows) / len(rows))


def chassis_scores(case, rows):
    post = [r for r in rows if r["trial_time"] >= 4.]
    minimum = min(r["output"] for r in post)
    drop = post[0]["output"] - minimum
    pre_error = max(abs(r["output"] - 1.) for r in rows[175:200])
    tail_error = max(abs(r["output"] - 1.) for r in post[-25:])
    last_bad = max((i for i, r in enumerate(post) if abs(r["output"] - 1.) > .02), default=-1)
    next_index = last_bad + 1
    recovery = post[next_index]["trial_time"] - 4. if next_index < len(post) else math.inf

    # The built-in wheel exposes speed and command. Invert its exact sampled
    # update to independently check the applied load on each observable interval.
    if case == "chassis_step_load":
        gain = -math.expm1(-.02 / .35)
        loads = [(r["trial_time"], r["effort"] - r["output"] -
                  (nxt["output"] - r["output"]) / gain)
                 for r, nxt in zip(rows, rows[1:])]
        required = .45
    else:
        loads = [(r["trial_time"], r["load"]) for r in rows]
        required = .90
    load_ok = all(abs(v - (required if t >= 4. else 0.)) < 1e-6 for t, v in loads)
    ref_ok = all(r["reference"] == float(r["trial_time"] >= 1.) for r in rows)
    recovery_text = f"{recovery:.2f} s" if math.isfinite(recovery) else "周期结束仍未恢复"
    print(f"工况核对（1 s 阶跃，4 s 持续加载 {required:.2f}）："
          + ("符合" if load_ok and ref_ok else "不符合"))
    print(f"加载前半秒最大误差 = {pre_error:.4f} rad/s；加载后最低轮速 = {minimum:.4f} rad/s")
    print(f"相对加载瞬间掉速 = {drop:.4f} rad/s；恢复并留在 ±2% 带 = {recovery_text}")
    print(f"末半秒最大误差 = {tail_error:.4f} rad/s")
    return (load_ok and ref_ok and pre_error <= .02 and minimum >= .74
            and recovery <= 1.20 + 1e-9 and tail_error <= .01)


def scores(case, rows):
    if case in ("chassis_step_load", "chassis_drive_lag"):
        return chassis_scores(case, rows)
    if case == "wheel_step":
        tail = [r["output"] for r in rows[-25:]]
        peak = max(r["output"] for r in rows if r["reference"] == 1.)
        print(f"最后半秒轮速范围 = {min(tail):.5f}–{max(tail):.5f} rad/s；阶跃峰值 = {peak:.5f} rad/s")
        return min(tail) >= .99 and max(tail) <= 1.01 and peak <= 1.01
    start = next(r["trial_time"] for r in rows if r["reference"] == 1.)
    hit = next((r["trial_time"] for r in rows if r["trial_time"] >= start and r["output"] >= .9), None)
    # Events fall on the 0.02 s grid. Compare exact hundredths at the deadline.
    delay = round(hit - start, 2) if hit is not None else math.inf
    peak = max(r["output"] for r in rows)
    if case == "carriage_loops":
        inner = rmse(rows[50:150], "velocity", "speed_reference")
        tail = max(abs(r["output"] - 1.) for r in rows[-25:])
        print(f"速度跟随 RMSE [1,3) s = {inner:.4f} m/s；位置末段最大误差 = {tail:.4f} m")
        print(f"首次到 0.90 m 用时 = {delay:.2f} s；位置峰值 = {peak:.4f} m")
        return delay <= 1.2 and peak <= 1.05 and tail <= .01
    if case == "cart_stop":
        force = max(abs(r["effort"]) for r in rows)
        print(f"峰值 |力| = {force:.4f} N；首次到 0.90 m 用时 = {delay:.2f} s；位置峰值 = {peak:.4f} m")
        return force <= 2. and delay <= 2.4 and peak <= 1.01
    estimate = rmse(rows[300:], "output", "reference")
    raw = rmse(rows[300:], "measurement", "reference")
    print(f"首次到 0.90 m 用时 = {delay:.2f} s；末 2 秒估计 RMSE = {estimate:.4f} m；原始观测 RMSE = {raw:.4f} m")
    return delay <= .3 and estimate <= .09


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", help="另存本轮所有采样行")
    args = parser.parse_args()
    rclpy.init()
    node = rclpy.create_node("lesson_score")
    try:
        client = AsyncParameterClient(node, "/tuning_lab")
        if not client.wait_for_services(timeout_sec=12.):
            raise ValueError("找不到 /tuning_lab，请先启动实验并加载同一工作区。")
        case = read_params(node, client, ["case_id"])["case_id"]
        if case not in SIGNALS:
            raise ValueError("本工具适用于 " + "、".join(SIGNALS))
        before = read_params(node, client, KNOBS[case])
        print(case, before, "等待一个完整周期，请保持参数不变。", flush=True)
        rows = collect(node, case)
        if before != read_params(node, client, KNOBS[case]):
            raise ValueError("采样期间参数发生变化，请重测。")
        if args.csv:
            with open(args.csv, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=list(rows[0]))
                writer.writeheader()
                writer.writerows(rows)
        passed = scores(case, rows)
        if case == "range_step" and before["seed"] != 7:
            print("本课使用相同的噪声序列比较参数，请将 seed 设为 7 后重测。")
            passed = False
        print("本课最终验收：" + ("通过" if passed else "尚未通过"))
    except ValueError as exc:
        raise SystemExit(str(exc))
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
