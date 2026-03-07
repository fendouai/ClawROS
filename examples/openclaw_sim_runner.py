#!/usr/bin/env python3
"""
OpenClaw + ClawROS 模拟运行器

目标:
1) 一键启动 ClawROS 模拟桥
2) 自动尝试接入 OpenClaw 并注册工具
3) 若本机无 OpenClaw，回退到本地交互控制

运行:
    python examples/openclaw_sim_runner.py
"""

import os
import sys
from typing import Any, Callable, Optional

# 添加 src 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from clawros_tools import ClawROSTools, register_with_openclaw
from simple_simulator import create_simulated_bridge


def _build_openclaw_instance() -> Optional[Any]:
    """尽力创建 OpenClaw 实例，失败返回 None。"""
    candidates: list[tuple[str, str]] = [
        ("openclaw", "OpenClaw"),
        ("openclaw", "ZeroClaw"),
        ("zeroclaw", "ZeroClaw"),
    ]
    for module_name, class_name in candidates:
        try:
            module = __import__(module_name, fromlist=[class_name])
            cls = getattr(module, class_name, None)
            if cls is None:
                continue
            return cls()
        except Exception:
            continue
    return None


def _call_openclaw(instance: Any, user_text: str) -> str:
    """以常见方法名调用 OpenClaw。"""
    method_candidates: list[tuple[str, Callable[..., Any]]] = []
    for method_name in ("chat", "ask", "run", "process", "invoke"):
        method = getattr(instance, method_name, None)
        if callable(method):
            method_candidates.append((method_name, method))

    if not method_candidates:
        return "OpenClaw 已连接，但未发现可调用的 chat/ask/run/process/invoke 方法。"

    last_error: Optional[Exception] = None
    for method_name, method in method_candidates:
        try:
            result = method(user_text)
            return f"[OpenClaw:{method_name}] {result}"
        except Exception as exc:
            last_error = exc
            continue

    return f"OpenClaw 调用失败：{last_error}"


def _handle_local_command(tools: ClawROSTools, line: str) -> str:
    """
    本地兜底命令:
    - move <location> [speed]
    - nav <x> <y> [theta]
    - sensor <type>
    - state
    - stop
    """
    parts = line.strip().split()
    if not parts:
        return ""

    cmd = parts[0].lower()
    args = parts[1:]

    if cmd == "move":
        if len(args) < 1:
            return "用法: move <location> [speed]"
        speed = float(args[1]) if len(args) > 1 else 0.5
        return tools.move_to(args[0], speed=speed)

    if cmd == "nav":
        if len(args) < 2:
            return "用法: nav <x> <y> [theta]"
        x = float(args[0])
        y = float(args[1])
        theta = float(args[2]) if len(args) > 2 else None
        return tools.navigate_to(x, y, theta)

    if cmd == "sensor":
        if len(args) < 1:
            return "用法: sensor <type>"
        return tools.get_sensor_data(args[0])

    if cmd == "state":
        return tools.get_robot_state()

    if cmd == "stop":
        return tools.emergency_stop()

    return (
        "未知命令。可用命令: move/nav/sensor/state/stop。"
        "也可以输入任意自然语言（若 OpenClaw 可用则转交 OpenClaw）。"
    )


def main() -> None:
    print("\n" + "=" * 68)
    print("  OpenClaw + ClawROS 模拟运行器")
    print("  输入 quit/exit 退出")
    print("=" * 68 + "\n")

    bridge = create_simulated_bridge()
    tools = ClawROSTools(bridge=bridge)

    if not tools.initialize():
        print("初始化失败：无法启动模拟桥接。")
        return

    print("✓ 模拟桥已启动")

    openclaw = _build_openclaw_instance()
    if openclaw is not None:
        try:
            register_with_openclaw(tools, openclaw)
            print("✓ 已检测到 OpenClaw，并完成工具注册")
        except Exception as exc:
            openclaw = None
            print(f"! OpenClaw 注册失败，回退本地模式: {exc}")
    else:
        print("! 未检测到 OpenClaw，使用本地交互模式")

    print("\n提示:")
    print("  - 本地命令: move/nav/sensor/state/stop")
    print("  - 若 OpenClaw 可用，任意自然语言会转交 OpenClaw")
    print("")

    try:
        while True:
            try:
                line = input("openclaw-sim> ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n收到退出信号。")
                break

            if not line:
                continue
            if line.lower() in {"quit", "exit"}:
                break

            # 优先显式本地命令
            if line.split()[0].lower() in {"move", "nav", "sensor", "state", "stop"}:
                try:
                    print(_handle_local_command(tools, line))
                except Exception as exc:
                    print(f"本地命令执行失败: {exc}")
                continue

            # 自然语言路径: 先尝试 OpenClaw, 否则给出提示
            if openclaw is not None:
                print(_call_openclaw(openclaw, line))
            else:
                print(
                    "当前未连接 OpenClaw。请使用本地命令: move/nav/sensor/state/stop"
                )

    finally:
        tools.shutdown()
        print("✓ 已关闭模拟桥接")


if __name__ == "__main__":
    main()
