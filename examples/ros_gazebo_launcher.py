#!/usr/bin/env python3
"""
ROS Gazebo 模式启动器（骨架）

用途:
1) 读取 config/clawros_config.yaml 的 ros_gazebo 配置
2) 打印或执行仿真启动命令
3) 初始化 ClawROS 的 ros_gazebo 桥接并提供简单交互
"""

import argparse
import os
import subprocess
import sys
from typing import Any, Dict, List

import yaml

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from clawros_bridge import CommandType, ROSCommand, create_bridge


def load_config(config_path: str) -> Dict[str, Any]:
    with open(config_path, "r") as f:
        return yaml.safe_load(f) or {}


def get_launch_commands(config: Dict[str, Any]) -> List[str]:
    return (
        config.get("runtime", {})
        .get("ros_gazebo", {})
        .get("launch_commands", [])
    )


def run_launch_commands(commands: List[str]) -> List[subprocess.Popen]:
    processes: List[subprocess.Popen] = []
    for cmd in commands:
        print(f"[launch] {cmd}")
        proc = subprocess.Popen(cmd, shell=True)
        processes.append(proc)
    return processes


def interactive_loop(bridge: Any) -> None:
    print("\n进入 ros_gazebo 交互模式，输入 quit 退出。")
    print("命令: state | move <linear> [angular] | nav <x> <y> | stop\n")

    while True:
        line = input("ros-gazebo> ").strip()
        if not line:
            continue
        if line.lower() in {"quit", "exit"}:
            break

        parts = line.split()
        cmd = parts[0].lower()

        try:
            if cmd == "state":
                print(bridge.get_robot_state())
            elif cmd == "move":
                linear = float(parts[1])
                angular = float(parts[2]) if len(parts) > 2 else 0.0
                response = bridge.execute_command(
                    ROSCommand(
                        type=CommandType.MOVE,
                        target="cmd_vel",
                        parameters={"linear": linear, "angular": angular},
                    )
                )
                print(response.message)
            elif cmd == "nav":
                x = float(parts[1])
                y = float(parts[2])
                response = bridge.execute_command(
                    ROSCommand(
                        type=CommandType.NAVIGATE,
                        target="goal",
                        parameters={"x": x, "y": y},
                    )
                )
                print(response.message)
            elif cmd == "stop":
                response = bridge.execute_command(
                    ROSCommand(
                        type=CommandType.EMERGENCY_STOP,
                        target="all",
                    )
                )
                print(response.message)
            else:
                print("未知命令。可用: state/move/nav/stop/quit")
        except Exception as exc:
            print(f"命令执行失败: {exc}")


def main() -> None:
    parser = argparse.ArgumentParser(description="ClawROS ros_gazebo 启动器")
    parser.add_argument(
        "--config",
        default="config/clawros_config.yaml",
        help="配置文件路径",
    )
    parser.add_argument(
        "--print-commands",
        action="store_true",
        help="仅打印仿真启动命令，不执行",
    )
    parser.add_argument(
        "--run-commands",
        action="store_true",
        help="执行 runtime.ros_gazebo.launch_commands 中的命令",
    )
    args = parser.parse_args()

    config = load_config(args.config)
    launch_commands = get_launch_commands(config)

    if not launch_commands:
        print("配置中未定义 runtime.ros_gazebo.launch_commands")
    else:
        print("ros_gazebo 启动命令:")
        for idx, cmd in enumerate(launch_commands, start=1):
            print(f"  {idx}. {cmd}")

    processes: List[subprocess.Popen] = []
    if args.run_commands and launch_commands:
        processes = run_launch_commands(launch_commands)
    elif args.print_commands or launch_commands:
        print("\n提示: 加 --run-commands 可直接执行上述命令。")

    bridge = create_bridge(args.config, mode="ros_gazebo")
    if not bridge.initialize():
        print("ros_gazebo 桥接初始化失败。")
        return

    print("✓ ros_gazebo 桥接已初始化")
    try:
        interactive_loop(bridge)
    finally:
        bridge.shutdown()
        print("✓ 桥接已关闭")
        if processes:
            print("提示: 你启动的 Gazebo/Nav2/RViz 进程仍在运行，可按需手动关闭。")


if __name__ == "__main__":
    main()
