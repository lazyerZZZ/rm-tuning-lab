# 写一个可以在 rqt 调参的后端

复制 [custom_lab.py](../examples/custom_lab.py) 到自己的工作目录。这个文件导出两个可单独启动的实例。运行时只需把 launch 的 plugin 参数指向文件的绝对路径。插件是随本地进程执行的 Python 代码。

**只改场景。** 参照 `slow_wheel`，使用 `pid(标题, 教学任务, wheel(...))`。例如指定 `tau=0.8` 改电机时间常数，或传入 `load=lambda t: 0.5 if t >= 3 else 0` 在第 3 秒加负载。已有模型还包括滑台 cart 和标量传感器 sensor。每次使用一个新的小写实例 ID。

**自己写状态更新。** 参照 `tank`。外层工厂接收本次实验专用的 `random.Random` 并初始化状态。返回的 `step(t, params)` 每拍读取最新参数，计算当前观测和控制量，更新闭包里的状态，并返回本拍的样本。每次重置都重新调用工厂。步长由 `rm_tuning_lab.core.DT` 提供。节点和浏览器各自创建独立实例。

| Case 字段 | 怎样填写 |
|---|---|
| title、group、unit、lesson | 实验名、系列、主输出单位和一条可执行的对照任务 |
| knobs | 参数名映射到 `Knob(标签, 默认值, 下限, 上限)`，默认值需在有限区间内 |
| factory | 接收 rng，返回单步更新函数 |
| signals | 至少含 reference、output。默认另含 effort。每拍返回的键应与此处完全相同，值为有限数值 |
| effort_unit | 后端驱动量的单位，供网页副图使用 |

参数名和信号名用小写字母开头，可包含数字和下划线。启动参数、服务名和实验时间名由框架保留。reference 表示目标或仿真真值，output 表示实际响应或估计；两者使用相同单位。模型运行时，ROS 节点自动为每个参数生成可编辑描述和范围，为每个信号发布 `std_msgs/msg/Float64`。例如 tank.kp 对应节点参数 `kp`，tank 的 effort 对应话题 `/tuning_lab/effort`，绘图字段为 `/tuning_lab/effort/data`。

## 从同一文件验证两个入口

```bash
# 从仓库根目录执行，绝对路径可替换成自己的文件
model="$(pwd)/examples/custom_lab.py"
python3 -c 'import sys; from rm_tuning_lab.plugins import catalog; from rm_tuning_lab.core import simulate; case = catalog(sys.argv[1])["tank"]; print(simulate(case, {"kp": 4})[-1])' "$model"

# 已加载 Jazzy 工作区的终端
ros2 launch rm_tuning_lab lesson.launch.py case_id:=tank plugin:="$model"
```

另开一个已加载工作区的终端，执行 `ros2 param set /tuning_lab kp 4.0`。同样的变更也可以在 rqt 的参数面板完成。查看目标和液位曲线，以默认负载比较稳态偏差。运行 `python3 web_lab.py --plugin "$model"` 时，在网页下拉菜单中选择「自定义液位模型」。
