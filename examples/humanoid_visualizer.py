#!/usr/bin/env python3
"""
Humanoid 可视化模拟器（骨架）

功能:
1) 使用 humanoid_sim 桥接实时绘制人形姿态
2) 提供基础命令交互：walk/pose/stop/state
3) 在无交互终端时自动演示步态
"""

import os
import queue
import sys
import threading
import time
import tkinter as tk
from math import cos, sin
from typing import Any

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from clawros_bridge import CommandType, ROSCommand, create_bridge


def _joint(state: dict, name: str) -> float:
    return float(state.get("humanoid", {}).get("joint_positions", {}).get(name, 0.0))


def _cmd_walk(bridge: Any, linear: float, angular: float = 0.0) -> str:
    r = bridge.execute_command(
        ROSCommand(
            type=CommandType.MOVE,
            target="gait",
            parameters={"linear": linear, "angular": angular, "gait": "walk"},
        )
    )
    return r.message


def _cmd_pose(bridge: Any, posture: str) -> str:
    r = bridge.execute_command(
        ROSCommand(
            type=CommandType.MANIPULATE,
            target="whole_body_pose",
            parameters={"arm": "both", "posture": posture},
        )
    )
    return r.message


def _cmd_stop(bridge: Any) -> str:
    r = bridge.execute_command(
        ROSCommand(type=CommandType.EMERGENCY_STOP, target="all")
    )
    return r.message


def command_loop(bridge: Any, msgs: "queue.Queue[str]", running: dict) -> None:
    print("可用命令: walk <linear> [angular] | pose <stand|crouch|tpose> | stop | state | quit")
    while running["value"]:
        try:
            line = input("humanoid-vis> ").strip()
        except (EOFError, KeyboardInterrupt):
            time.sleep(0.5)
            continue
        if not line:
            continue
        if line.lower() in {"quit", "exit"}:
            running["value"] = False
            break
        parts = line.split()
        cmd = parts[0].lower()
        try:
            if cmd == "walk":
                linear = float(parts[1])
                angular = float(parts[2]) if len(parts) > 2 else 0.0
                msgs.put(_cmd_walk(bridge, linear, angular))
            elif cmd == "pose":
                msgs.put(_cmd_pose(bridge, parts[1]))
            elif cmd == "stop":
                msgs.put(_cmd_stop(bridge))
            elif cmd == "state":
                msgs.put(str(bridge.get_robot_state().get("humanoid", {})))
            else:
                msgs.put("未知命令")
        except Exception as exc:
            msgs.put(f"命令失败: {exc}")


def autoplay_loop(bridge: Any, msgs: "queue.Queue[str]", running: dict) -> None:
    try:
        msgs.put(_cmd_pose(bridge, "stand"))
        time.sleep(1.0)
        msgs.put(_cmd_walk(bridge, 0.35, 0.0))
        time.sleep(4.0)
        msgs.put(_cmd_walk(bridge, 0.2, 0.45))
        time.sleep(4.0)
        msgs.put(_cmd_pose(bridge, "tpose"))
        time.sleep(2.0)
        msgs.put(_cmd_stop(bridge))
    except Exception as exc:
        msgs.put(f"自动演示失败: {exc}")
    finally:
        running["value"] = False


def main() -> None:
    bridge = create_bridge("config/clawros_config.yaml", mode="humanoid_sim")
    if not bridge.initialize():
        print("humanoid_sim 初始化失败")
        return

    msgs: "queue.Queue[str]" = queue.Queue()
    running = {"value": True}

    if sys.stdin.isatty():
        t = threading.Thread(target=command_loop, args=(bridge, msgs, running), daemon=True)
    else:
        t = threading.Thread(target=autoplay_loop, args=(bridge, msgs, running), daemon=True)
    t.start()

    root = tk.Tk()
    root.title("ClawROS Humanoid Visualizer")
    root.geometry("900x760")
    canvas = tk.Canvas(root, width=860, height=680, bg="#0b1220")
    canvas.pack(padx=12, pady=10)
    status = tk.StringVar(value="humanoid_sim ready")
    tk.Label(root, textvariable=status, anchor="w").pack(fill="x", padx=12)

    def draw_body(state: dict) -> None:
        canvas.delete("all")
        cx, cy = 430, 340
        scale = 120.0

        hip_l = _joint(state, "left_hip_pitch")
        hip_r = _joint(state, "right_hip_pitch")
        knee_l = _joint(state, "left_knee")
        knee_r = _joint(state, "right_knee")
        sh_l = _joint(state, "left_shoulder_pitch")
        sh_r = _joint(state, "right_shoulder_pitch")
        waist = _joint(state, "waist_yaw")

        torso_top = (cx + 30 * sin(waist), cy - 170)
        pelvis = (cx, cy)
        canvas.create_line(pelvis[0], pelvis[1], torso_top[0], torso_top[1], fill="#f8fafc", width=8)
        canvas.create_oval(torso_top[0] - 16, torso_top[1] - 26, torso_top[0] + 16, torso_top[1] + 6, fill="#22d3ee", outline="")

        sh_y = torso_top[1] + 25
        left_shoulder = (torso_top[0] - 55, sh_y)
        right_shoulder = (torso_top[0] + 55, sh_y)
        l_hand = (left_shoulder[0] - scale * cos(sh_l), left_shoulder[1] + scale * sin(sh_l))
        r_hand = (right_shoulder[0] + scale * cos(sh_r), right_shoulder[1] + scale * sin(sh_r))
        canvas.create_line(left_shoulder[0], left_shoulder[1], l_hand[0], l_hand[1], fill="#94a3b8", width=6)
        canvas.create_line(right_shoulder[0], right_shoulder[1], r_hand[0], r_hand[1], fill="#94a3b8", width=6)

        l_knee = (pelvis[0] - 38 + scale * sin(hip_l) * 0.55, pelvis[1] + 95)
        r_knee = (pelvis[0] + 38 + scale * sin(hip_r) * 0.55, pelvis[1] + 95)
        l_ankle = (l_knee[0] + scale * sin(knee_l) * 0.45, l_knee[1] + 110)
        r_ankle = (r_knee[0] + scale * sin(knee_r) * 0.45, r_knee[1] + 110)
        canvas.create_line(pelvis[0] - 36, pelvis[1], l_knee[0], l_knee[1], fill="#e2e8f0", width=7)
        canvas.create_line(l_knee[0], l_knee[1], l_ankle[0], l_ankle[1], fill="#e2e8f0", width=7)
        canvas.create_line(pelvis[0] + 36, pelvis[1], r_knee[0], r_knee[1], fill="#e2e8f0", width=7)
        canvas.create_line(r_knee[0], r_knee[1], r_ankle[0], r_ankle[1], fill="#e2e8f0", width=7)

        canvas.create_text(18, 18, text="Humanoid Sim Skeleton", anchor="nw", fill="#cbd5e1", font=("Menlo", 16, "bold"))

    def tick() -> None:
        if not running["value"] and not sys.stdin.isatty():
            # 自动演示结束后保持窗口可观察，不自动退出
            running["value"] = True

        while True:
            try:
                status.set(msgs.get_nowait())
            except queue.Empty:
                break

        state = bridge.get_robot_state()
        draw_body(state)
        if "humanoid" in state and not msgs.qsize():
            h = state["humanoid"]
            status.set(f"model={h.get('robot_model')} gait={h.get('gait_mode')} pose={h.get('pose')}")
        root.after(80, tick)

    def on_close() -> None:
        try:
            bridge.shutdown()
        finally:
            root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)
    tick()
    root.mainloop()


if __name__ == "__main__":
    main()
