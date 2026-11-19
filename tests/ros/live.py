"""Exercise an installed ROS executable through DDS and parameter services."""
import os
import signal
import subprocess
import time
import unittest
from contextlib import contextmanager

import rclpy
from rclpy.parameter import Parameter
from rclpy.parameter_client import AsyncParameterClient
from std_msgs.msg import Float64


@contextmanager
def simulator(*args):
    process = subprocess.Popen(
        ["ros2", "run", "rm_tuning_lab", "tuning_node", "--ros-args", *args],
        start_new_session=True,
    )
    try:
        yield
    finally:
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGINT)
        process.wait(timeout=10)


class RosTests(unittest.TestCase):
    def test_live_interfaces(self):
        rclpy.init()
        node = rclpy.create_node("lab_probe")
        try:
            for case, key, new_value, topic in [
                ("wheel_step", "kp", 3., "effort"),
                ("cart_stop", "q_position", 12., "output"),
                ("range_wave", "r_measure", 0.3, "measurement"),
            ]:
                with self.subTest(case=case), simulator("-p", "case_id:=" + case):
                    received = []
                    sub = node.create_subscription(Float64, "/tuning_lab/" + topic, received.append, 10)
                    client = AsyncParameterClient(node, "/tuning_lab")
                    self.assertTrue(client.wait_for_services(timeout_sec=15.))
                    future = client.set_parameters([Parameter(key, value=new_value)])
                    rclpy.spin_until_future_complete(node, future, timeout_sec=5.)
                    self.assertTrue(future.result().results[0].successful)
                    end = time.monotonic() + 5
                    while len(received) < 10 and time.monotonic() < end:
                        rclpy.spin_once(node, timeout_sec=0.1)
                    self.assertGreaterEqual(len(received), 10)
                    node.destroy_subscription(sub)
        finally:
            node.destroy_node()
            rclpy.shutdown()


if __name__ == "__main__":
    unittest.main()
