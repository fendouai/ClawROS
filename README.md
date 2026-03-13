# ClawROS 项目

## 项目概述

ClawROS 是一个连接 OpenClaw AI 助手系统与 ROS (Robot Operating System) 的桥接项目。它允许用户通过自然语言与 OpenClaw 交互，间接控制 ROS 机器人系统。

## 核心目标

1. **自然语言控制机器人**: 通过 OpenClaw 的 AI 能力，将用户的自然语言指令转换为 ROS 命令
2. **双向通信**: 支持从 ROS 系统获取状态信息并反馈给用户
3. **模块化设计**: 支持多种 ROS 版本（ROS1/ROS2）和多种通信协议
4. **安全性**: 实现多层安全验证，确保机器人操作安全

## 技术架构

### 系统架构图

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   User Input    │────▶│   OpenClaw AI    │────▶│   ClawROS Bridge │
│  (Natural Lang) │     │  (理解与决策)     │     │   (协议转换)     │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                                                          │
                                                          ▼
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Feedback to   │◀────│   ROS System     │◀────│   ROS Nodes    │
│    User         │     │  (状态与数据)     │     │   (执行命令)    │
└─────────────────┘     └──────────────────┘     └─────────────────┘
```

### 核心组件

1. **ClawROS Bridge**: 核心桥接层，负责协议转换
2. **ROS Adapter**: ROS 适配层，支持 ROS1/ROS2
3. **Command Parser**: 命令解析器，将自然语言转为 ROS 命令
4. **State Monitor**: 状态监控器，实时获取 ROS 系统状态
5. **Security Layer**: 安全层，验证所有操作

## 目录结构

```
ClawROS/
├── docs/              # 文档
├── src/               # 源代码
│   ├── nodes/         # ROS 节点
│   ├── launch/        # Launch 文件
│   ├── msgs/          # 自定义消息
│   ├── services/      # 自定义服务
│   ├── clawros_bridge.py      # 核心桥接
│   ├── clawros_tools.py       # OpenClaw 工具
│   └── simple_simulator.py    # 模拟器（新增）
├── tests/             # 测试
│   ├── unit/          # 单元测试
│   ├── integration/   # 集成测试
│   └── system/        # 系统测试
├── config/            # 配置文件
└── examples/          # 示例（包含模拟环境演示）
    ├── demo_simulation.py      # 完整演示
    ├── simulator_launcher.py   # 模拟器启动器
    └── SIMULATION_GUIDE.md     # 模拟环境指南
```

## 快速开始

### 前置要求

- Python 3.8+
- **可选**: ROS2 (Jazzy/Humble) 或 ROS1 (Noetic) - 不使用模拟环境时需要
- OpenClaw/ZeroClaw 环境（可选）

### 安装

```bash
# 克隆项目
cd ClawROS

# 安装依赖
pip install -r requirements.txt
```

### 🎮 模拟环境体验（无需 ROS）

```bash
# 运行完整演示
python examples/demo_simulation.py

# 启动独立模拟器
python examples/simulator_launcher.py
```

### 🧪 ROS Gazebo 仿真模式（骨架）

```bash
# 仅查看将要执行的 Gazebo/Nav2/RViz 命令
python examples/ros_gazebo_launcher.py --config config/clawros_config.yaml --print-commands

# 一键执行配置中的仿真命令并启动 ros_gazebo 桥接
./scripts/start_ros_gazebo_mode.sh
```

### 🦿 Humanoid 仿真模式（骨架）

```bash
# 1) 查看人形模式预设启动命令（不执行）
python examples/humanoid_sim_launcher.py --config config/clawros_config.yaml --print-commands

# 2) 进入人形模式交互（walk/step/arm/pose/sensor/stop）
python examples/humanoid_sim_launcher.py --config config/clawros_config.yaml

# 3) 一键执行配置里的外部仿真命令并进入交互
./scripts/start_humanoid_sim_mode.sh

# 4) 启动人形可视化骨架窗口（支持交互命令）
python examples/humanoid_visualizer.py
```

> 进一步技术调研与落地路线见: [docs/HUMANOID_SIM_ROADMAP.md](docs/HUMANOID_SIM_ROADMAP.md)

### 🤖 LeRobot Unitree G1 模式（v0.5.0 集成骨架）

LeRobot `v0.5.0` 已新增 Unitree G1 完整支持，包含：

- Unitree G1 23/29 DoF 支持
- MuJoCo 仿真 teleop
- `run_g1_server.py` 远端 DDS <-> ZMQ 桥
- `Pi0-FAST` 自回归 VLA
- `Real-Time Chunking`
- 流式视频编码

本仓库现已增加 `lerobot_unitree_g1` 集成骨架，用于把 ClawROS 的人形高层语义接到 LeRobot G1 后端。

```bash
# 1) 查看当前 LeRobot G1 集成配置与推荐命令
python examples/lerobot_unitree_g1_launcher.py --print-commands

# 2) 进入 LeRobot G1 交互骨架模式
python examples/lerobot_unitree_g1_launcher.py

# 3) 脚本方式启动
./scripts/start_lerobot_unitree_g1_mode.sh
```

当前这部分是“集成入口已整理好”，不是“真机已默认接通”。
原因是 LeRobot 的 G1 支持本质上是 `Python + Unitree SDK2 + MuJoCo/ZMQ` 工作流，不是原生 ROS2 topic/action 接口。
因此更稳的路线是让 ClawROS 做高层语义桥接，再由适配层落到 LeRobot 的 G1 robot / teleoperator / policy API。

> 详细调研和接入建议见: [docs/LEROBOT_UNITREE_G1_INTEGRATION.md](docs/LEROBOT_UNITREE_G1_INTEGRATION.md)

### 🦾 一键 Demo: Claw 文本 -> LeRobot Unitree G1 MuJoCo sim

这条链路会把 `walk / pose / stop` 直接映射到 LeRobot `UnitreeG1.send_action()`：

- `walk` -> `remote.lx / remote.rx`，交给 Holosoma 或 GR00T locomotion controller
- `pose` -> G1 上肢关节目标
- `stop` -> 清零 remote axes

```bash
# 需要先准备好 conda 环境 `lerobot-g1`
./scripts/demo_claw_lerobot_g1.sh

# 自定义任务文本
./scripts/demo_claw_lerobot_g1.sh "前进两步，右转，再做 tpose，最后停止"
```

默认使用 `HolosomaLocomotionController`。如需切换可设置：

```bash
LEROBOT_G1_CONTROLLER=GrootLocomotionController ./scripts/demo_claw_lerobot_g1.sh
```

macOS 下官方 MuJoCo viewer 通常要求 `mjpython`：

```bash
LEROBOT_G1_PYTHON=mjpython ./scripts/demo_claw_lerobot_g1.sh
```

如果当前会话是无界面环境，可先用 headless 验证 backend：

```bash
LEROBOT_G1_HEADLESS=1 LEROBOT_G1_PYTHON=python ./scripts/demo_claw_lerobot_g1.sh
```

当前仓库已经验证过 `headless` 路径可运行，并能返回 G1 关节/姿态摘要。

### 👁️ 一键 Demo: Claw -> LeRobot G1 sim -> 现有可视化窗口

这条链路会：

- 启动或复用 `ros2-sim` 的 `rosbridge`
- 启动或复用现有 [`docker_humanoid_visual.py`](/Users/f/GitHub/ClawROS/examples/docker_humanoid_visual.py)
- 运行 LeRobot G1 MuJoCo sim
- 将 sim 状态回灌到 `/joint_states` 和 `/odom`
- 在现有骨架 + 轨迹窗口里显示

![LeRobot G1 visual flow](/Users/f/GitHub/ClawROS/docs/images/lerobot_g1_visual_flow.png)

上图根据真实运行时的 `/joint_states` 和 `/odom` 数据生成，展示了 `Claw -> LeRobot G1 sim -> 可视化状态流` 的最终效果。

```bash
# 推荐先用 headless backend 验证状态流
LEROBOT_G1_HEADLESS=1 LEROBOT_G1_PYTHON=python ./scripts/demo_claw_lerobot_g1_visual.sh

# 自定义任务文本
LEROBOT_G1_HEADLESS=1 LEROBOT_G1_PYTHON=python ./scripts/demo_claw_lerobot_g1_visual.sh "前进，右转，再做 tpose，最后停止"
```

桌面图形会话里，如果你希望 LeRobot 自己的 MuJoCo viewer 也打开，可以改用：

```bash
LEROBOT_G1_HEADLESS=0 LEROBOT_G1_PYTHON=mjpython ./scripts/demo_claw_lerobot_g1_visual.sh
```

### 🐳 ROS2 Docker 仿真（更接近真实 ROS）

```bash
# 1) 构建镜像
./scripts/ros2_sim_docker.sh build

# 2) 启动仿真（rosbridge :9090 + mock Nav2 FollowWaypoints）
./scripts/ros2_sim_docker.sh up

# 3) 查看日志
./scripts/ros2_sim_docker.sh logs

# 4) 进入容器检查 topic/node
./scripts/ros2_sim_docker.sh shell

# 5) 停止
./scripts/ros2_sim_docker.sh down
```

### 🤖 一键 Demo: Claw 文本 -> Nav2 Waypoint Action -> Docker 可视化轨迹

```bash
# 一键运行（会自动：
# 1) 启动 ROS2 Docker
# 2) 调用 OpenClaw 将文本任务转 waypoint
# 3) 发送 FollowWaypoints goal
# 4) 启动/复用可视化窗口，显示来自 Docker /odom 的轨迹
./scripts/demo_claw_nav2_waypoints.sh

# 也可以传入自定义任务文本（建议包含坐标）
./scripts/demo_claw_nav2_waypoints.sh "请走到(0.8,0.0)，再到(1.2,0.4)，最后回到(0.0,0.0)"
```

### 🦿 一键 Demo: Claw 文本 -> Humanoid Task -> Docker 可视化

```bash
# 一键运行（会自动：
# 1) 启动 ROS2 Docker
# 2) 等待 rosbridge 和 /joint_states
# 3) 启动/复用人形可视化窗口（骨架 + 轨迹）
# 4) 调用 OpenClaw 把文本转 humanoid plan
# 5) 通过 rosbridge 执行 humanoid 任务
./scripts/demo_claw_humanoid.sh

# 传入自定义任务文本
./scripts/demo_claw_humanoid.sh "前进两步，左转小走，再做 crouch，最后站立停止"
```

> 若在无图形环境（headless）运行，脚本会继续执行任务但提示可视化窗口未启动；可在桌面会话中直接运行 `python examples/docker_humanoid_visual.py` 查看。

### 基本使用（真实 ROS 环境）

```bash
# 启动桥接节点
ros2 launch clawros clawros_bridge.launch.py

# 发送命令
ros2 service call /clawros/command clawros/srv/Command "{command: 'move forward'}"
```

## 功能特性

- ✅ **模拟环境** - 无需 ROS 硬件即可测试和开发
- ✅ 自然语言到 ROS 命令转换
- ✅ 支持 ROS2 Topics/Services/Actions
- ✅ 支持 ROS1 (通过桥接)
- ✅ 实时状态监控
- ✅ 安全验证层
- ✅ 可扩展的工具系统
- ✅ 完整的测试覆盖

## 支持的 ROS 操作

### 基础操作

- **移动控制**: 前进、后退、转向
- **机械臂控制**: 抓取、放置、移动
- **传感器读取**: 摄像头、激光雷达、IMU
- **导航**: 路径规划、避障

### 高级操作

- **任务编排**: 多步骤任务自动执行
- **异常处理**: 自动错误恢复
- **学习模式**: 从演示中学习动作

## 安全机制

1. **命令验证**: 所有命令在执行前经过安全验证
2. **权限控制**: 基于角色的访问控制
3. **速率限制**: 防止命令风暴
4. **紧急停止**: 一键停止所有操作
5. **审计日志**: 记录所有操作

## 配置示例

```yaml
# config/clawros_config.yaml
clawros:
  ros_version: "ros2"  # ros1 或 ros2
  default_frame: "base_link"
  safety:
    enabled: true
    max_velocity: 0.5
    emergency_stop_topic: "/emergency_stop"
  
  ai:
    provider: "openclaw"
    model: "default"
    timeout: 30.0
  
  channels:
    - telegram
    - cli
    - webhook
```

## 开发指南

### 添加新的 ROS 命令

1. 在 `src/nodes/` 创建新的命令处理器
2. 在 `src/services/` 定义服务接口
3. 在 `config/` 添加配置
4. 编写测试用例

### 添加新的 AI 提供商

1. 实现 `Provider` 接口
2. 在配置中注册
3. 更新文档

## 测试

```bash
# 运行单元测试
pytest tests/unit/

# 运行集成测试
pytest tests/integration/

# 运行系统测试
pytest tests/system/

# 生成覆盖率报告
pytest --cov=src tests/
```

## 贡献

欢迎贡献！请查看 [CONTRIBUTING.md](docs/CONTRIBUTING.md)

## 许可证

MIT License - 查看 [LICENSE](LICENSE)

## 联系方式

- 问题反馈：GitHub Issues
- 讨论：ROS Discourse

## 致谢

感谢 OpenClaw、ZeroClaw 和 ROS 社区的开源工作。
