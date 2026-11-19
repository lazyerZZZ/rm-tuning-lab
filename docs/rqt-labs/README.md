# 轮速环之后的三次 rqt 实验

| 想回答的问题 | 实验 | 学会判断 |
|---|---|---|
| 滑台定位慢，应该先动速度环还是位置环？ | [串级控制：先跟上速度，再追位置](cascade/README.md) | 区分内环跟随误差、外环到位时间和位置过冲 |
| 车要停到 1 m，最多允许用 2 N 的力，该怎样选权重？ | [LQR：在推力预算内停车](lqr/README.md) | 同时看力的绝对峰值、到位用时和过冲 |
| 距离读数很吵，该信读数还是信上一步估计？ | [Kalman：降噪还能跟上台阶吗？](kalman/README.md) | 同时看跳变延迟和平稳段的均方根误差 |

第一次使用 ROS 先完成[安装与轮速环入门](../first-wheel/README.md)。沿用那一课的 Ubuntu 24.04、ROS 2 Jazzy 和 `~/rm_ws`。之前已克隆的队员在终端里更新一次，三篇都使用同一份代码。

```bash
cd ~/rm_ws/src/rm-tuning-lab
git pull --ff-only
source /opt/ros/jazzy/setup.bash
cd ~/rm_ws
colcon build --symlink-install --packages-select rm_tuning_lab
source ~/rm_ws/install/setup.bash
```

**每个终端的分工**：A 保持 launch 运行，B 可以开第二个曲线窗口，C 用于回读和验收。每开一个终端先执行两条 `source`。切换实验时，在 A 按 Ctrl+C 关闭这一组窗口；若 B 单独启动过 rqt_plot，也在 B 按 Ctrl+C。一次只启动一个教学节点，这样三个终端看到的 `/tuning_lab` 属于同一课。

**怎样比较一轮**：每个实验固定为 8 s、50 Hz。Param 面板里点左侧 `tuning_lab`，在右侧对应行的白色输入框里 Ctrl+A、输入数值、按 Enter。看下一次阶跃后的完整过程。在 C 运行下方命令，它会监听当前实例，等一个完整周期，打印当前参数、指标和本课的最终验收结果。保持参数不变，通常需 8–16 秒。想保存本次原始数据，可在命令末尾加 `--csv ~/trial.csv`；每次比较使用不同文件名。

```bash
source /opt/ros/jazzy/setup.bash
source ~/rm_ws/install/setup.bash
python3 ~/rm_ws/src/rm-tuning-lab/tools/score_trial.py
```

**怎样读时间**：rqt 横轴显示消息接收时间。把图上目标竖直跳变的那一刻当作计时起点；滑台在每轮第 1 秒跳变，测距在第 2 秒跳变。验收脚本使用节点的 `trial_time`，按发布端时间戳将各话题配成同一拍。教程里的对照图由逐拍数据绘制，各轮的仿真时间对齐。

**窗口空白时**：参数窗口点左下角 Refresh 再选节点；曲线窗口恢复播放、勾选 autoscroll。若 `+` 仍为灰色，先确认 A 正在运行，在 C 用 `ros2 topic list` 核对名字。rqt 输入的是消息字段，末尾有 `/data`；终端检查话题时用 `ros2 topic echo /tuning_lab/output --once`。如果参数名和教程对不上，用 `ros2 param get /tuning_lab case_id` 核对实例。

**数据来源**：在 ROS 2 Jazzy 和 Xvfb 虚拟显示器中启动项目与 rqt，用 Qt 鼠标和键盘事件操作真实输入框、添加绘图字段，再经 ROS 服务回读参数、订阅节点话题。三课共 11 组参数，每组采集完整的 400 拍；各课末尾提供保留参数列的 CSV。窗内截图显示 rqt 接收时的画面，量化指标由完整采样记录计算。[三课的图形实验记录](https://github.com/lazyerZZZ/rm-tuning-lab/actions/runs/44597224241)
