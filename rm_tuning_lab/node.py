import rclpy
from rclpy.node import Node
from rclpy.executors import ExternalShutdownException
from rcl_interfaces.msg import FloatingPointRange, ParameterDescriptor, SetParametersResult
from std_msgs.msg import Float64

from .core import DT, STEPS, Trial, parameters
from .plugins import catalog


class TuningNode(Node):
    def __init__(self):
        super().__init__("tuning_lab")
        startup = ParameterDescriptor(read_only=True)
        plugin = self.declare_parameter("plugin", "", startup).value
        case_id = self.declare_parameter("case_id", "wheel_step", startup).value
        self.seed = self.declare_parameter("seed", 7, startup).value
        cases = catalog(plugin)
        if case_id not in cases:
            raise ValueError("可用实例 " + ", ".join(cases))
        self.case = cases[case_id]
        for key, knob in self.case.knobs.items():
            bounds = FloatingPointRange(from_value=float(knob.low), to_value=float(knob.high))
            descriptor = ParameterDescriptor(description=knob.label, floating_point_range=[bounds])
            self.declare_parameter(key, float(knob.default), descriptor)
        self.add_on_set_parameters_callback(self.validate)
        self.trial = Trial(self.case, self.seed)
        self.channels = {s: self.create_publisher(Float64, "~/" + s, 10)
                         for s in self.case.signals}
        self.create_timer(DT, self.tick)
        self.get_logger().info(f"{case_id} | {self.case.lesson}")

    def validate(self, changes):
        overrides = {p.name: p.value for p in changes if p.name in self.case.knobs}
        try:
            parameters(self.case, overrides)
        except ValueError as error:
            return SetParametersResult(successful=False, reason=str(error))
        return SetParametersResult(successful=True)

    def tick(self):
        if self.trial.index >= STEPS:
            self.trial = Trial(self.case, self.seed)
        params = {k: self.get_parameter(k).value for k in self.case.knobs}
        row = self.trial.tick(params)
        for key, publisher in self.channels.items():
            publisher.publish(Float64(data=float(row[key])))


def main(args=None):
    rclpy.init(args=args)
    node = TuningNode()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()
