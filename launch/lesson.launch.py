from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, TimerAction
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    case = ParameterValue(LaunchConfiguration("case_id"), value_type=str)
    plugin = ParameterValue(LaunchConfiguration("plugin"), value_type=str)
    gui = IfCondition(LaunchConfiguration("gui"))
    return LaunchDescription([
        DeclareLaunchArgument("case_id", default_value="wheel_step"),
        DeclareLaunchArgument("plugin", default_value=""),
        DeclareLaunchArgument("gui", default_value="true"),
        Node(package="rm_tuning_lab", executable="tuning_node", output="screen",
             parameters=[{"case_id": case, "plugin": plugin}]),
        TimerAction(period=2.0, actions=[
            ExecuteProcess(cmd=["ros2", "run", "rqt_plot", "rqt_plot",
                                "/tuning_lab/reference/data", "/tuning_lab/output/data"], condition=gui),
            ExecuteProcess(cmd=["ros2", "run", "rqt_reconfigure", "rqt_reconfigure"], condition=gui),
        ]),
    ])
