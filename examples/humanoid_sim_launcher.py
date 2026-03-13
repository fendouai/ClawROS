#!/usr/bin/env python3
"""
Humanoid 仿真模式启动器（骨架）

用途:
1) 读取 config/clawros_config.yaml 的 runtime.humanoid_sim 配置
2) 打印或执行仿真启动命令
3) 初始化 ClawROS humanoid_sim 桥接并提供交互控制
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
        .get("humanoid_sim", {})
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
    print("\n进入 humanoid_sim 交互模式，输入 quit 退出。")
    print("命令:")
    print("  state")
    print("  walk <linear> [angular]")
    print("  step <x> <y> [yaw]")
    print("  arm <left|right|both> <x> <y> <z>")
    print("  pose <stand|crouch|tpose>")
    print("  sensor <imu|joint_states|force_torque|camera|lidar>")
    print("  stop\n")

    while True:
        try:
            line = input("humanoid-sim> ").strip()
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
                        target="gait",
                        parameters={"linear": linear, "angular": angular, "gait": "walk"},
                    )
                )
                print(response.message)
            elif cmd == "step":
                x = float(parts[1])
                y = float(parts[2])
                yaw = float(parts[3]) if len(parts) > 3 else 0.0
                response = bridge.execute_command(
                    ROSCommand(
                        type=CommandType.NAVIGATE,
                        target="footstep_goal",
                        parameters={"x": x, "y": y, "yaw": yaw},
                    )
                )
                print(response.message)
            elif cmd == "arm":
                arm = parts[1]
                x = float(parts[2])
                y = float(parts[3])
                z = float(parts[4])
                response = bridge.execute_command(
                    ROSCommand(
                        type=CommandType.MANIPULATE,
                        target="arm_pose",
                        parameters={"arm": arm, "x": x, "y": y, "z": z, "posture": "stand"},
                    )
                )
                print(response.message)
            elif cmd == "pose":
                posture = parts[1]
                response = bridge.execute_command(
                    ROSCommand(
                        type=CommandType.MANIPULATE,
                        target="whole_body_pose",
                        parameters={"arm": "both", "posture": posture},
                    )
                )
                print(response.message)
            elif cmd == "sensor":
                sensor_type = parts[1]
                response = bridge.execute_command(
                    ROSCommand(
                        type=CommandType.SENSOR,
                        target=sensor_type,
                    )
                )
                print(response.message, response.data)
            elif cmd == "stop":
                response = bridge.execute_command(
                    ROSCommand(
                        type=CommandType.EMERGENCY_STOP,
                        target="all",
                    )
                )
                print(response.message)
            else:
                print("未知命令。可用: state/walk/step/arm/pose/sensor/stop/quit")
        except Exception as exc:
            print(f"命令执行失败: {exc}")


def main() -> None:
    parser = argparse.ArgumentParser(description="ClawROS humanoid_sim 启动器")
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
        help="执行 runtime.humanoid_sim.launch_commands 中的命令",
    )
    args = parser.parse_args()

    config = load_config(args.config)
    launch_commands = get_launch_commands(config)

    if not launch_commands:
        print("配置中未定义 runtime.humanoid_sim.launch_commands")
    else:
        print("humanoid_sim 启动命令:")
        for idx, cmd in enumerate(launch_commands, start=1):
            print(f"  {idx}. {cmd}")

    processes: List[subprocess.Popen] = []
    if args.run_commands and launch_commands:
        processes = run_launch_commands(launch_commands)
    elif args.print_commands or launch_commands:
        print("\n提示: 加 --run-commands 可直接执行上述命令。")

    bridge = create_bridge(args.config, mode="humanoid_sim")
    if not bridge.initialize():
        print("humanoid_sim 桥接初始化失败。")
        return

    print("✓ humanoid_sim 桥接已初始化")
    try:
        interactive_loop(bridge)
    finally:
        bridge.shutdown()
        print("✓ 桥接已关闭")
        if processes:
            print("提示: 你启动的外部仿真进程仍在运行，可按需手动关闭。")


if __name__ == "__main__":
    main()
