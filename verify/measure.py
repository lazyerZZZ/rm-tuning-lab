import csv
from pathlib import Path
import sys, time
import rclpy
from std_msgs.msg import Float64
from std_srvs.srv import Trigger

stage = sys.argv[1]
rclpy.init()
node = rclpy.create_node("wheel_readback")
values = []
sub = node.create_subscription(Float64, "/tuning_lab/output", lambda m: values.append(m.data), 100)
reset = node.create_client(Trigger, "/tuning_lab/reset")
assert reset.wait_for_service(timeout_sec=15.)
deadline = time.monotonic() + 20
while not values and time.monotonic() < deadline:
    rclpy.spin_once(node, timeout_sec=.1)
assert values
f = reset.call_async(Trigger.Request())
rclpy.spin_until_future_complete(node, f, timeout_sec=5.)
assert f.result().success
values.clear()
deadline = time.monotonic() + 20
while time.monotonic() < deadline:
    rclpy.spin_once(node, timeout_sec=.1)
    # The recharge/reset boundary shows up as a jump to exactly zero.
    if len(values) > 1 and values[-1] == 0. and values[-2] > .1:
        if len(values) > 345: break
        values.clear()
else:
    raise TimeoutError("missing trial boundary")
tail = values[-26:-1]
peak = max(values)
print(stage, "tail range", min(tail), max(tail), "peak", peak, "samples", len(values), flush=True)
goal = {"p1": .5, "p3": .75, "pi": 1.0}[stage]
assert max(abs(v-goal) for v in tail) <= .01 and peak <= goal+.01
with (Path.home()/"evidence"/(stage+".csv")).open("w") as out:
    writer=csv.writer(out);writer.writerow(["sample","wheel_rad_s"]);writer.writerows(enumerate(values))
node.destroy_node()
rclpy.shutdown()
