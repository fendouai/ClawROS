# ClawROS 人形机器人方向调研与落地路线

更新时间: 2026-03-10

## 1. 结论

ClawROS 现有架构（OpenClaw 文本层 + ROS2 Bridge + Action/Topic 抽象）可以扩展到人形机器人控制。  
建议采用分层路线:

1. 文本任务层（OpenClaw）
2. 任务编排层（导航/足步/双臂/全身）
3. 控制执行层（ros2_control + controllers）
4. 仿真与可视化层（Gazebo/Isaac/MuJoCo + RViz/Foxglove）

## 2. 关键技术栈调研

### 2.1 ROS2 控制基础

- `ros2_control` 是标准控制框架，支持控制器管理、硬件抽象和 mock 组件。
- `ros2_controllers` 提供 `joint_trajectory_controller`、`joint_state_broadcaster` 等标准控制器。

参考:
- https://control.ros.org/humble/doc/ros2_control/hardware_interface/doc/hardware_interface_types_userdoc.html
- https://control.ros.org/humble/doc/ros2_controllers/doc/controllers_index.html

### 2.2 仿真侧

- Gazebo 侧可使用 `gz_ros2_control`（或 `gazebo_ros2_control`）接入 ros2_control 控制链。
- 对于高保真和感知任务，可选 Isaac Sim 的 ROS2 Bridge。

参考:
- https://control.ros.org/humble/doc/gz_ros2_control/doc/index.html
- https://docs.omniverse.nvidia.com/isaacsim/latest/features/external_communication/ext_omni_isaac_ros_bridge.html
- https://docs.omniverse.nvidia.com/isaacsim/latest/installation/install_ros.html

### 2.3 真实人形平台可接入性

- Unitree 官方 `unitree_ros2` 明确提到 H1 可在 ROS2 体系下通信与控制（推荐 Humble）。

参考:
- https://github.com/unitreerobotics/unitree_ros2

### 2.4 研究/算法验证模型

- MuJoCo Menagerie 提供包含 Unitree H1 在内的开源模型，适合控制策略迭代与验证。

参考:
- https://mujoco.readthedocs.io/en/3.1.3/models.html

## 3. 对 ClawROS 的映射（建议）

### 3.1 文本到能力映射

- 走路/转向: `MOVE` -> gait/velocity/footstep
- 足步目标: `NAVIGATE` -> FollowFootsteps/Waypoint
- 双臂姿态: `MANIPULATE` -> arm trajectory
- 全身姿态: `MANIPULATE` -> whole_body_control
- 感知查询: `SENSOR` -> IMU/力传感/JointState/Camera

### 3.2 建议补充的 ROS 接口

- Topic: `/humanoid/gait_cmd`, `/humanoid/whole_body_cmd`, `/joint_states`, `/imu/data`, `/humanoid/foot_force`
- Service: `/humanoid/plan_footsteps`, `/humanoid/whole_body_ik`
- Action: `/humanoid/follow_footsteps`, `/humanoid/left_arm/follow_joint_trajectory`, `/humanoid/right_arm/follow_joint_trajectory`, `/humanoid/whole_body_control`

## 4. 三阶段落地

### 阶段 A（当前仓库已可做）

- `humanoid_sim` 语义骨架桥接
- 人形状态与关节可视化骨架
- Claw 文本到人形动作语义映射

### 阶段 B（控制器闭环）

- 引入 `ros2_control` + `joint_trajectory_controller`
- 用 Gazebo/Isaac/MuJoCo 中的真实关节模型替换语义 mock
- 以 `/joint_states`、`tf` 实时驱动 RViz/Foxglove

### 阶段 C（真机/高保真）

- 接入真实机器人驱动（如 Unitree H1 ROS2）
- 增加安全层（速度/姿态/力矩/足底接触）
- 增加任务审计与回放

## 5. 风险与注意事项

1. 仿真平台与 ROS 发行版匹配要提前确认（尤其 Gazebo + Humble/Jazzy 组合）。
2. 人形控制需加入更严格的安全约束（比移动底盘更敏感）。
3. 先做语义闭环，再做动力学闭环，迭代成本最低。

