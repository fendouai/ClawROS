#!/usr/bin/env python3
"""
LeRobot Unitree G1 启动器（骨架）

用途:
1) 读取 config/clawros_config.yaml 的 runtime.lerobot_unitree_g1 配置
2) 打印官方推荐的 LeRobot G1 启动命令
3) 初始化 ClawROS 的 lerobot_unitree_g1 桥接状态
"""

import argparse
import os
import sys
from typing import Any, Dict, List

import yaml

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from clawros_bridge import CommandType, ROSCommand, create_bridge


def load_config(config_path: str) -> Dict[str, Any]:
    with open(config_path, "r") as f:
        return yaml.safe_load(f) or {}


def get_lerobot_cfg(config: Dict[str, Any]) -> Dict[str, Any]:
    return config.get("runtime", {}).get("lerobot_unitree_g1", {})


def get_launch_commands(config: Dict[str, Any]) -> List[str]:
    return get_lerobot_cfg(config).get("launch_commands", [])


def print_summary(cfg: Dict[str, Any]) -> None:
    print("LeRobot Unitree G1 配置:")
    print(f"  simulation: {cfg.get('is_simulation', True)}")
    print(f"  robot_profile: {cfg.get('robot_profile', 'g1_29dof')}")
    print(f"  teleop_id: {cfg.get('teleop_id', 'wbc_unitree')}")
    print(f"  policy: {cfg.get('policy', 'none')}")
    print(f"  lerobot_repo: {cfg.get('lerobot_repo', '~/src/lerobot')}")
    print(
        "  server: "
        f"{cfg.get('server_host', '127.0.0.1')}:"
        f"{cfg.get('lowcmd_port', 6000)}/"
        f"{cfg.get('lowstate_port', 6001)} "
        f"video={cfg.get('video_port', 5555)}"
    )


def interactive_loop(bridge: Any) -> None:
    print("\n进入 lerobot_unitree_g1 交互模式，输入 quit 退出。")
    print("命令:")
    print("  state")
    print("  walk <linear> [angular]")
    print("  pose <stand|crouch|tpose>")
    print("  stop\n")

    while True:
        try:
            line = input("lerobot-g1> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n收到退出信号。")
            break
        if not line:
            continue
        if line.lower() in {"quit", "exit"}:
            break

        parts = line.split()
        cmd = parts[0].lower()

        try:
            if cmd == "state":
                print(bridge.get_robot_state())
            elif cmd == "walk":
                linear = float(parts[1])
                angular = float(parts[2]) if len(parts) > 2 else 0.0
                response = bridge.execute_command(
                    ROSCommand(
                        type=CommandType.MOVE,
                        target="g1_locomotion",
                        parameters={"linear": linear, "angular": angular, "gait": "walk"},
                    )
                )
                print(response.message, response.data)
            elif cmd == "pose":
                posture = parts[1]
                response = bridge.execute_command(
                    ROSCommand(
                        type=CommandType.MANIPULATE,
                        target="g1_pose",
                        parameters={"arm": "both", "posture": posture},
                    )
                )
                print(response.message, response.data)
            elif cmd == "stop":
                response = bridge.execute_command(
                    ROSCommand(type=CommandType.EMERGENCY_STOP, target="all")
                )
                print(response.message)
            else:
                print("未知命令。可用: state/walk/pose/stop/quit")
        except Exception as exc:
            print(f"命令执行失败: {exc}")


def main() -> None:
    parser = argparse.ArgumentParser(description="ClawROS LeRobot Unitree G1 启动器")
    parser.add_argument(
        "--config",
        default="config/clawros_config.yaml",
        help="配置文件路径",
    )
    parser.add_argument(
        "--print-commands",
        action="store_true",
        help="仅打印 LeRobot G1 启动命令",
    )
    args = parser.parse_args()

    config = load_config(args.config)
    cfg = get_lerobot_cfg(config)
    cmds = get_launch_commands(config)

    print_summary(cfg)
    if cmds:
        print("\n推荐启动命令:")
        for idx, cmd in enumerate(cmds, start=1):
            print(f"  {idx}. {cmd}")
    else:
        print("\n配置中未定义 runtime.lerobot_unitree_g1.launch_commands")

    if args.print_commands:
        return

    bridge = create_bridge(args.config, mode="lerobot_unitree_g1")
    if not bridge.initialize():
        print("lerobot_unitree_g1 桥接初始化失败。")
        return

    print("\n✓ lerobot_unitree_g1 桥接已初始化")
    try:
        interactive_loop(bridge)
    finally:
        bridge.shutdown()
        print("✓ 桥接已关闭")


if __name__ == "__main__":
    main()
