# LeRobot v0.5.0 Unitree G1 Integration Notes

## Conclusion

可以接，而且官方基础已经很完整。

LeRobot `v0.5.0` 已经提供了 Unitree G1 的以下关键能力：

- `src/lerobot/robots/unitree_g1/`：G1 机器人实现、配置、运动学、SDK2 socket、locomotion 控制
- `src/lerobot/robots/unitree_g1/run_g1_server.py`：DDS <-> ZMQ 远程桥
- `src/lerobot/teleoperators/unitree_g1/`：G1 teleoperator 支持
- `docs/source/unitree_g1.mdx`：官方安装、仿真、真机连接说明
- `src/lerobot/policies/pi0_fast/`：Pi0-FAST 策略实现
- `docs/source/streaming_video_encoding.mdx`：流式视频编码说明

## Why it fits ClawROS

ClawROS 目前已经有：

- 高层自然语言控制入口
- humanoid 语义桥接层
- Docker ROS2 + 可视化链路

LeRobot G1 则提供：

- 更真实的 Unitree G1 机器人接口
- MuJoCo 仿真
- 真机 remote 控制
- 训练和推理策略入口

因此最合理的架构不是“把 LeRobot 改成 ROS2 节点”，而是：

`OpenClaw / ClawROS -> humanoid semantic adapter -> LeRobot Unitree G1 backend -> sim / real robot`

## Recommended integration layers

### Phase 1

先做运行模式级集成：

- 新增 `lerobot_unitree_g1` runtime mode
- 读取 LeRobot G1 配置
- 打印或启动官方推荐命令
- 复用现有 humanoid 高层动作语义

### Phase 2

增加动作适配器：

- `walk/turn/stop` -> LeRobot locomotion controller
- `pose/tpose/crouch` -> arm/waist/joint targets
- camera/video -> ZMQ camera feed

### Phase 3

增加真实联调：

- `run_g1_server.py` 接入远端机器人
- ClawROS 通过 ZMQ 发送动作 / 接收 lowstate
- 将状态重新映射为 ROS2 topic 或本地可视化数据流

### Phase 4

增加策略运行：

- Pi0-FAST 推理入口
- Real-Time Chunking 参数接入
- 流式视频编码用于数据采集和演示录制

## Current repo status

本仓库现在已经补了两层集成：

- `runtime.lerobot_unitree_g1` 配置段
- `examples/lerobot_unitree_g1_launcher.py`
- `scripts/start_lerobot_unitree_g1_mode.sh`
- `LeRobotUnitreeG1Bridge`
- `examples/lerobot_g1_sim_backend.py`
- `scripts/demo_claw_lerobot_g1.sh`

第二层已经能把 `walk / pose / stop` 映射到官方 `UnitreeG1.send_action()`：

- `walk` -> `remote.lx / remote.rx`
- `pose` -> 上肢 joint targets
- `stop` -> 清零 remote axes

并已在本地 `headless` 模式下验证 MuJoCo sim backend 可运行。

这仍然不是“真机已接通”，但已经不只是骨架，而是可执行的 sim backend 适配层。

## Official source links

- LeRobot repo: https://github.com/huggingface/lerobot/tree/v0.5.0
- Unitree G1 docs: https://github.com/huggingface/lerobot/blob/v0.5.0/docs/source/unitree_g1.mdx
- G1 robot code: https://github.com/huggingface/lerobot/tree/v0.5.0/src/lerobot/robots/unitree_g1
- G1 teleoperator: https://github.com/huggingface/lerobot/tree/v0.5.0/src/lerobot/teleoperators/unitree_g1
- Pi0-FAST docs: https://github.com/huggingface/lerobot/blob/v0.5.0/docs/source/pi0fast.mdx
- Streaming video encoding docs: https://github.com/huggingface/lerobot/blob/v0.5.0/docs/source/streaming_video_encoding.mdx
