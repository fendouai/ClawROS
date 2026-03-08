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
