# 🎮 ClawROS 模拟环境快速指南

## 立即运行（无需 ROS！）

### 方式 0: OpenClaw 一键接入（推荐）

```bash
cd ClawROS
python examples/openclaw_sim_runner.py
```

**说明**:
- 自动启动模拟桥接
- 若检测到 OpenClaw/ZeroClaw，自动注册 ClawROS 工具
- 若未检测到 OpenClaw，可直接用本地命令控制（move/nav/sensor/state/stop）

### 方式 1: 运行完整演示

```bash
cd ClawROS
python examples/demo_simulation.py
```

**演示内容**:
- ✅ 基本移动控制（前进、转向）
- ✅ 自主导航（多点巡逻）
- ✅ 传感器扫描（激光雷达、电池）
- ✅ 紧急停止功能
- ✅ 完整任务执行（仓库巡检）

### 方式 2: 启动独立模拟器

```bash
python examples/simulator_launcher.py
```

**功能**:
- 实时显示机器人状态
- 位置、电量、状态更新
- 按 Ctrl+C 退出

## 代码示例

### 最简单的使用方式

```python
from clawros_tools import ClawROSTools
from simple_simulator import create_simulated_bridge

# 创建模拟环境
bridge = create_simulated_bridge()
tools = ClawROSTools(bridge=bridge)
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

### 5 行代码控制机器人

```python
from clawros_tools import ClawROSTools
from simple_simulator import create_simulated_bridge

tools = ClawROSTools(bridge=create_simulated_bridge())
tools.initialize()
tools.navigate_to(3.0, 2.0)  # 导航到目标
print(tools.get_robot_state())
tools.shutdown()
```

## 模拟器特性

### 机器人规格
```
类型：差速驱动移动机器人
最大速度：1.0 m/s
传感器：8 方向激光雷达
电池：100% 初始电量
工作空间：10m x 10m
```

### 环境特性
- 🚧 3 个固定障碍物
- 📡 模拟激光雷达数据
- 🔋 电池消耗模拟
- 💥 碰撞检测
- 🎯 自主导航

## 输出示例

```
============================================================
  ClawROS 模拟环境演示
  无需真实 ROS 环境!
============================================================

初始化模拟环境...
✓ 模拟环境初始化成功

============================================================
  演示 1: 基本移动控制
============================================================

1.1 前进 3 秒
   Successfully moved to forward

1.2 获取机器人状态
  位置：(0.90, 0.00)
  电量：99.8%
  状态：idle
```

## 下一步

1. **修改参数测试**
   - 改变导航坐标
   - 调整速度
   - 添加障碍物

2. **查看完整演示**
   ```bash
   cat examples/demo_simulation.py
   ```

3. **阅读详细文档**
   ```bash
   cat examples/SIMULATION_GUIDE.md
   ```

4. **集成到 OpenClaw**
   - 使用真实 OpenClaw 项目
   - 注册 ClawROS 工具
   - 实现自然语言控制

## 常见问题

**Q: 需要安装 ROS 吗？**
A: 不需要！模拟环境完全独立，无需 ROS。

**Q: 模拟器和真实 ROS 有什么区别？**
A: API 完全相同，模拟器简化了物理和传感器模型。

**Q: 如何切换到真实 ROS？**
A: 修改导入：
```python
# 从模拟器切换到真实 ROS
from clawros_bridge import create_bridge  # 替代 create_simulated_bridge
```

**Q: 可以添加自定义障碍物吗？**
A: 可以！
```python
bridge.simulator.obstacles = [(1.0, 1.0), (2.0, 2.0)]
```

## 文件说明

| 文件 | 说明 |
|------|------|
| `simple_simulator.py` | 模拟器核心代码 |
| `demo_simulation.py` | 完整演示脚本 |
| `simulator_launcher.py` | 独立启动器 |
| `SIMULATION_GUIDE.md` | 详细指南 |

## 立即试试！

```bash
python examples/demo_simulation.py
```

🤖 祝您使用愉快！
