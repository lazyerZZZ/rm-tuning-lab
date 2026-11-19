# 轮迹 · RM 调参实验台

面向 RoboMaster 新队员的中文 ROS 2 教学项目。先猜改变一个参数后曲线会怎样，再在 rqt 里动手验证。所有实验使用模拟轮组、滑台和传感器。

[从轮速开始的四堂实验课](docs/lessons.md) · [全部 25 个实验及调参任务](docs/catalog.md) · [自定义模型示例](examples/custom_lab.py)

## 在 rqt 中做第一个实验

以下命令面向已安装 ROS 2 Jazzy 的 Ubuntu 24.04。安装工具并编译一次：

```bash
sudo apt install python3-colcon-common-extensions ros-jazzy-rqt-plot ros-jazzy-rqt-reconfigure
mkdir -p ~/rm_ws/src
git clone https://github.com/lazyerZZZ/rm-tuning-lab.git ~/rm_ws/src/rm-tuning-lab
cd ~/rm_ws
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install --packages-select rm_tuning_lab
source install/setup.bash
ros2 launch rm_tuning_lab lesson.launch.py case_id:=wheel_step
```

上面的 launch 会打开曲线和参数两个窗口。如果用了 `gui:=false`，可在另外两个已加载工作区环境的终端分别启动：

```bash
ros2 run rqt_plot rqt_plot /tuning_lab/reference/data /tuning_lab/output/data
ros2 run rqt_reconfigure rqt_reconfigure
```

在参数窗口选中 `/tuning_lab`，设 `ki=0.0`、`kd=0.0`，比较 `kp=1.0` 和 `kp=3.0`。每隔 8 秒自动从静止重跑，1 秒时目标轮速跳至 1 rad/s。比例控制下轮速应分别维持在 0.5 和 0.75 rad/s 左右。恢复 `ki=3.0` 后再看末段误差。运行中改增益从下一拍生效，等待下一个完整周期可以公平比较。

如果刚好在周期中途改了参数，可立即从同一初始状态重跑。参数保留，随机噪声序列复原。也可以在 rqt_plot 添加 `/tuning_lab/trial_time/data` 辨认周期边界。

```bash
ros2 service call /tuning_lab/reset std_srvs/srv/Trigger '{}'
```

## 选择实验

启动时改变 `case_id`。可从 `wheel_step` 的轮速、`cart_stop` 的滑台定位、`range_step` 的测距或 `carriage_loops` 的串级控制开始。完整的参数对照任务见[实验目录](docs/catalog.md)。PID 与 LQR 的第三条曲线是 `/tuning_lab/effort/data`，Kalman 的第三条曲线是 `/tuning_lab/measurement/data`。它的 reference 为仿真真值，output 为估计值。每个实验的操作与观察提示会打印在节点终端。

## 只有 Python 时

在仓库根目录运行 `python3 web_lab.py`，打开 <http://127.0.0.1:8765>。使用 Python 3.9+，无需安装第三方包。修改数字并按回车。浏览器与 ROS 节点共用模型，网页每次从相同初始状态整段重算。

## 添加实验与后端

[自定义实例文件](examples/custom_lab.py) 含两种写法。slow_wheel 复用轮组模型并改变惯性，tank 定义自己的状态、更新方程和可调参数。使用本机可信 Python 文件加载：

```bash
python3 web_lab.py --plugin examples/custom_lab.py
ros2 launch rm_tuning_lab lesson.launch.py case_id:=tank plugin:="$(ros2 pkg prefix --share rm_tuning_lab)/examples/custom_lab.py"
```

完整签名、信号约定和最小运行检查见[自定义后端指南](docs/plugins.md)。插件导出 `CASES: dict[str, Case]`。每次实验调用 `factory(rng)` 初始化状态，返回 `step(t, params)`。按 0.02 s 更新，返回声明的每个信号。只使用传入的随机数生成器以便复现。

## 验证与许可

`python3 -m unittest discover -s tests -v`。采用 [MIT 许可证](LICENSE)。
