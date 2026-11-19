# 三次对照实验，学会读一条曲线

每轮保持相同模型、采样时间和随机种子，只改一个参数。在 rqt 里可以热调；要对比两个完整的 8 秒周期，设好参数后调用 reset。网页的「保留本次响应作对照」会将当前输出画成点线。网页数字是整个周期的均方根误差，下面的稳态指标会注明各自的统计区间。

## 第一课 · 轮子为什么一直慢一点？

启动 `wheel_step`。主图中的物理量是轮速（rad/s）；驱动指令用等效空载稳态轮速表示。模型时间常数为 0.25 s，指令幅值上限为 3。用 rqt_plot 对照 `reference/data` 和 `output/data`，它们都位于 `/tuning_lab` 下。

1. 设 `kp=1.0, ki=0.0, kd=0.0`。1 秒时目标从 0 变 1。先猜最终读数，再看曲线末端。
2. 只把 `kp` 改为 3。两次稳态约为 **0.50、0.75 rad/s**。稳态时电机输出等于驱动，驱动又等于 Kp × (1 − 输出)；因此输出为 Kp/(1+Kp)。
3. 保留 `kp=3`，设 `ki=3.0`。积分累计过去的误差，即使当前误差很小，驱动仍可维持转速。7.98 秒时轮速约为 **0.999 rad/s**。
4. 换 `wheel_limit` 看积分的代价。目标超出驱动能力时比较条件积分开关；观察设定值降低后，驱动还贴着上限多久。换 `wheel_noise`，同时看测量与驱动抖动。微分使用测量值变化率。[条件积分背景](https://controlguru.com/integral-reset-windup-jacketing-logic-and-the-velocity-pi-form/) · [测量微分](https://controlguru.com/pid-control-and-derivative-on-measurement/)

## 第二课 · 小车能更省力地停下来吗？

[跟着真实 rqt 面板做：LQR 限力停车](rqt-labs/lqr/README.md)

启动 `cart_stop`。小车质量 1 kg，状态为位置和速度，驱动力限制为 ±4 N。先用目标与位置曲线看时间，再单独查看 `/tuning_lab/effort/data` 看力。位置单位为米，力单位为牛顿。

1. 保持 `q_position=8.0, q_velocity=2.0`。比较 `r_effort=1.0` 与 `5.0`。R 表示代价函数中使用驱动力的成本。
2. 目标在第 1 秒变为 1 m。默认仿真里，**最大驱动力从 2.75 N 降到 1.24 N**，从目标跳变到首次达到 0.9 m 的用时从 **1.84 s 增至 2.54 s**。记录这两个数，选一个更符合任务要求的组合。
3. 在 `cart_bias` 加入恒定外力。稳态需要持续施力，纯状态反馈会留下位置偏差。比较提高位置权重后的偏差和控制量。

模型按零阶保持离散化。控制器针对固定参考点计算 400 步有限时域、终端代价为零的离散 Riccati 递推，每拍使用首步反馈增益。代价为位置误差平方、速度平方、驱动力平方的加权和。执行器随后限幅；进入饱和段时，无约束 LQR 的最优性条件失效。[MIT 离散 LQR 推导](https://underactuated.mit.edu/lqr.html#section3)

## 第三课 · 更平滑的距离估计会迟到多久？

[跟着真实 rqt 面板做：Kalman 距离估计](rqt-labs/kalman/README.md)

启动 `range_step`。在 rqt_plot 再添加 `/tuning_lab/measurement/data`。reference 是仿真真值，measurement 是含噪测量，output 是滤波估计。标量随机游走模型用 Q 表示每步过程方差，用 R 表示测量方差，单位均为 m²。

1. 保持 `q_process=0.002`，先设 `r_measure=0.0625`。真值在 2 秒时从 0 跳到 1 m。R 对应 0.25 m 标准差的平方。
2. 只把 R 增至 0.3。固定种子 7 时，阶跃后估计首次达 0.9 m 的时间从 **0.20 s** 延至 **0.48 s**；最后 2 秒的估计 RMSE 从 **0.072 m** 降至 **0.048 m**。用多个种子重复才可比较跨噪声实现的表现。
3. 换 `range_dropout`。它用位置、速度两个状态，Q 参数改为每拍随机加速度方差。3–5 秒观测中断，valid=0，估计按速度外推。measurement 保持最后读数，滤波器在此期间只执行预测。[Welch 与 Bishop 的 Kalman 滤波入门](https://www.cs.unc.edu/~welch/media/pdf/kalman_intro.pdf)

## 第四课 · 速度环和位置环先调哪一个？

[跟着真实 rqt 面板做：串级滑台定位](rqt-labs/cascade/README.md)

启动 `carriage_loops`。用一组曲线比较 `speed_reference/data` 与 `velocity/data`（m/s），用另一组比较 `reference/data` 与 `output/data`（m）。位置外环产生限幅后的速度目标，速度内环据此驱动滑台。

先把 outer_kp 保持在 1，改变 inner_ki，找出让内环跟得上且没有明显振荡的一组参数。固定内环，再从 1 增大 outer_kp，观察位置过冲与外环限速的持续时间。如果速度目标已经长时间贴住上限，继续增大外环增益对最高速度有什么影响？用 `carriage_cap` 把推断与限速往返的曲线对照。

## 曲线没有动时

- 在节点终端确认实验 ID。运行 `ros2 node list`，应有 `/tuning_lab`。各终端加载同一工作区，并使用相同的 ROS_DOMAIN_ID。
- 用 `ros2 topic echo /tuning_lab/output --once` 检查数据。rqt_plot 输入的是消息字段，例如 `/tuning_lab/output/data`。暂停键应处于松开状态。
- 在参数窗口刷新节点列表，选中 `/tuning_lab` 后编辑。用 `ros2 param get /tuning_lab kp` 确认输入已生效。整数外观的浮点参数在 ROS 命令行写成 `3.0`。
- 仿真按 50 Hz 推进；rqt 横轴是接收时间，系统负载可能引入抖动。加入 trial_time 话题可以识别每个周期的起点。
