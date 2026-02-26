# ClawROS 模拟环境指南

## 概述

ClawROS 提供了完整的模拟环境，让您无需真实 ROS 硬件即可测试和开发机器人控制功能。

## 快速开始

### 1. 运行完整演示

```bash
# 进入项目目录
cd ClawROS

# 运行模拟演示
python examples/demo_simulation.py
```

### 2. 启动独立模拟器

```bash
# 启动模拟器（显示实时状态）
python examples/simulator_launcher.py
```

### 3. 在 Python 代码中使用

```python
from src.clawros_tools import ClawROSTools
from src.simple_simulator import create_simulated_bridge

# 创建模拟桥接
bridge = create_simulated_bridge()
tools = ClawROSTools(bridge=bridge)

# 初始化
tools.initialize()

# 控制机器人
tools.move_to("forward", speed=0.3)
tools.navigate_to(2.0, 1.0)

# 获取状态
state = tools.get_robot_state()
print(f"位置：{state['position']}")

# 关闭
tools.shutdown()
```

## 演示内容

### 演示 1: 基本移动控制
- 前进/后退
- 转向
- 速度控制

### 演示 2: 自主导航
- 多点导航
- 路径规划（简化版）
- 到达检测

### 演示 3: 传感器扫描
- 激光雷达模拟
- 电池状态
- 环境扫描

### 演示 4: 紧急停止
- 安全功能测试
- 立即停止

### 演示 5: 完整任务
- 仓库巡检场景
- 多步骤任务执行

## 模拟机器人规格

```
机器人类型：差速驱动
最大速度：1.0 m/s
更新频率：100 Hz
电池容量：100%
传感器：8 方向激光雷达
```

## 环境配置

### 障碍物

模拟器默认包含以下障碍物：
- (2.0, 2.0)
- (3.0, 1.0)
- (-1.0, 2.0)

### 工作空间

```
X 轴：-5.0 到 5.0 米
Y 轴：-5.0 到 5.0 米
```

## API 参考

### SimpleRobotSimulator

```python
simulator = SimpleRobotSimulator(
    initial_x=0.0,      # 初始 X 位置
    initial_y=0.0,      # 初始 Y 位置
    max_speed=1.0,      # 最大速度
    update_rate=100.0   # 更新频率 (Hz)
)

simulator.start()       # 启动模拟器
simulator.stop()        # 停止模拟器

simulator.set_velocity(linear=0.5, angular=0.0)  # 设置速度
simulator.stop_robot()  # 停止机器人

state = simulator.get_state()  # 获取状态
sensors = simulator.get_sensor_data()  # 获取传感器数据

simulator.navigate_to(2.0, 1.0)  # 导航到目标
```

### SimulatedROSBridge

```python
bridge = SimulatedROSBridge()
bridge.initialize()

# 执行 ClawROS 命令
from clawros_bridge import ROSCommand, CommandType

cmd = ROSCommand(
    type=CommandType.MOVE,
    target="forward",
    parameters={"linear": 0.3}
)
response = bridge.execute_command(cmd)

# 获取状态
state = bridge.get_robot_state()

bridge.shutdown()
```

## 自定义环境

### 添加障碍物

```python
from simple_simulator import SimpleRobotSimulator

simulator = SimpleRobotSimulator()

# 添加自定义障碍物
simulator.obstacles = [
    (1.0, 1.0),
    (2.0, 2.0),
    (-1.0, 3.0),
]
```

### 修改初始位置

```python
simulator = SimpleRobotSimulator(
    initial_x=3.0,
    initial_y=2.0
)
```

### 添加状态回调

```python
def on_state_update(state):
    print(f"新位置：({state.x:.2f}, {state.y:.2f})")

simulator.add_state_callback(on_state_update)
```

## 与真实 ROS 切换

### 使用模拟器（默认）

```python
from simple_simulator import create_simulated_bridge
bridge = create_simulated_bridge()
tools = ClawROSTools(bridge=bridge)
```

### 使用真实 ROS

```python
from clawros_bridge import create_bridge
bridge = create_bridge()  # 会尝试连接真实 ROS
tools = ClawROSTools(bridge=bridge)
```

### 自动检测

```python
import rclpy

try:
    rclpy.init()
    from clawros_bridge import create_bridge
    bridge = create_bridge()
except ImportError:
    from simple_simulator import create_simulated_bridge
    bridge = create_simulated_bridge()

tools = ClawROSTools(bridge=bridge)
```

## 故障排除

### 问题：演示运行但机器人不移动

**解决**:
- 确保调用了 `tools.initialize()`
- 检查是否有异常抛出
- 查看日志输出

### 问题：导航无法到达目标

**解决**:
- 检查目标是否在工作空间内
- 检查是否有障碍物阻挡
- 增加等待时间

### 问题：电池消耗过快

**解决**:
- 降低速度
- 减少频繁启停
- 调整功率消耗参数

## 性能优化

### 降低更新频率

```python
simulator = SimpleRobotSimulator(update_rate=50.0)  # 50 Hz 而不是 100 Hz
```

### 禁用日志

```python
logging.getLogger('simple_simulator').setLevel(logging.WARNING)
```

## 扩展模拟器

### 添加新传感器

```python
from simple_simulator import SimpleRobotSimulator

class CustomSimulator(SimpleRobotSimulator):
    def get_camera_data(self):
        # 实现摄像头数据
        return {"image": "..."}
    
    def get_depth_data(self):
        # 实现深度数据
        return {"depth_map": "..."}
```

### 添加物理引擎

```python
class PhysicsSimulator(SimpleRobotSimulator):
    def __init__(self):
        super().__init__()
        # 添加摩擦、惯性等
        self.friction = 0.1
    
    def _update_physics(self):
        # 扩展物理更新
        super()._update_physics()
        # 添加摩擦力等
```

## 示例代码

### 简单巡逻

```python
from clawros_tools import ClawROSTools
from simple_simulator import create_simulated_bridge

bridge = create_simulated_bridge()
tools = ClawROSTools(bridge=bridge)
tools.initialize()

try:
    while True:
        # 巡逻路线
        tools.navigate_to(2.0, 2.0)
        time.sleep(2)
        tools.navigate_to(-2.0, 2.0)
        time.sleep(2)
        tools.navigate_to(-2.0, -2.0)
        time.sleep(2)
        tools.navigate_to(2.0, -2.0)
        time.sleep(2)
except KeyboardInterrupt:
    tools.shutdown()
```

### 避障测试

```python
bridge = create_simulated_bridge()
bridge.initialize()

# 添加障碍物
bridge.simulator.obstacles = [(1.0, 0.0), (2.0, 0.0)]

# 尝试穿过障碍物
bridge.simulator.navigate_to(3.0, 0.0)
```

## 下一步

1. 运行 `demo_simulation.py` 查看完整演示
2. 修改参数测试不同场景
3. 集成到 OpenClaw 进行自然语言控制
4. 迁移到真实 ROS 环境

## 相关文档

- [ARCHITECTURE.md](../docs/ARCHITECTURE.md) - 系统架构
- [TESTING.md](../docs/TESTING.md) - 测试指南
- [README.md](../README.md) - 项目概述
