#!/usr/bin/env python3
"""
ClawROS 可视化模拟器（Tkinter）

功能：
1) 打开本地可视化窗口显示机器人、轨迹、障碍物
2) 终端输入命令控制（move/nav/stop/state）
3) 自然语言输入会转给 OpenClaw CLI（若可用）
"""

import json
import os
import queue
import re
import subprocess
import sys
import threading
import time
import tkinter as tk
from dataclasses import dataclass, field
from math import cos, sin
from typing import Optional, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from clawros_tools import ClawROSTools
from simple_simulator import create_simulated_bridge


WORLD_MIN = -5.0
WORLD_MAX = 5.0
CANVAS_SIZE = 720


class RosbridgeCmdVelPublisher:
    def __init__(self, host: str = "127.0.0.1", port: int = 9090):
        self.client = None
        self.topic = None
        try:
            import roslibpy

            self.client = roslibpy.Ros(host=host, port=port)
            self.client.run(timeout=2.5)
            time.sleep(0.3)
            if self.client.is_connected:
                self.topic = roslibpy.Topic(
                    self.client,
                    "/cmd_vel",
                    "geometry_msgs/msg/Twist",
                )
        except Exception:
            self.client = None
            self.topic = None

    def publish(self, linear: float, angular: float) -> None:
        if not self.client or not self.topic or not self.client.is_connected:
            return
        try:
            import roslibpy

            self.topic.publish(
                roslibpy.Message(
                    {
                        "linear": {"x": linear, "y": 0.0, "z": 0.0},
                        "angular": {"x": 0.0, "y": 0.0, "z": angular},
                    }
                )
            )
        except Exception:
            return

    def close(self) -> None:
        if self.client:
            try:
                self.client.terminate()
            except Exception:
                pass


def find_openclaw_cli() -> Optional[str]:
    candidates = [
        os.path.expanduser("~/.openclaw/bin/openclaw"),
        "/usr/local/bin/openclaw",
        "/opt/homebrew/bin/openclaw",
    ]
    for path in candidates:
        if os.path.isfile(path) and os.access(path, os.X_OK):
            return path
    return None


def openclaw_health_ok(cli_path: str) -> bool:
    try:
        p = subprocess.run(
            [cli_path, "gateway", "health", "--json"],
            text=True,
            capture_output=True,
            timeout=8,
            check=False,
        )
        return p.returncode == 0
    except Exception:
        return False


def call_openclaw(cli_path: str, text: str, agent_id: str = "main") -> str:
    p = subprocess.run(
        [cli_path, "agent", "--agent", agent_id, "--message", text, "--json"],
        text=True,
        capture_output=True,
        timeout=120,
        check=False,
    )
    if p.returncode != 0:
        return f"OpenClaw 调用失败: {(p.stderr or p.stdout).strip()}"
    try:
        data = json.loads(p.stdout)
        payloads = data.get("result", {}).get("payloads", [])
        texts = [x.get("text", "").strip() for x in payloads if x.get("text")]
        return texts[-1] if texts else "OpenClaw 已返回，但无文本内容"
    except Exception:
        return p.stdout.strip() or "OpenClaw 调用完成"


@dataclass
class UiState:
    running: bool = True
    trail: list[Tuple[float, float]] = field(default_factory=list)
    messages: "queue.Queue[str]" = field(default_factory=queue.Queue)


def world_to_canvas(x: float, y: float) -> Tuple[float, float]:
    scale = CANVAS_SIZE / (WORLD_MAX - WORLD_MIN)
    cx = (x - WORLD_MIN) * scale
    cy = CANVAS_SIZE - (y - WORLD_MIN) * scale
    return cx, cy


def apply_claw_text_as_motion(
    tools: ClawROSTools,
    ros_pub: RosbridgeCmdVelPublisher,
    text: str,
) -> Optional[str]:
    lower = text.lower()
    if "stop" in lower or "停止" in text or "急停" in text:
        ros_pub.publish(0.0, 0.0)
        return tools.emergency_stop()

    m_move = re.search(r"move\s+(\w+)(?:\s+([0-9.]+))?", lower)
    if m_move:
        loc = m_move.group(1)
        speed = float(m_move.group(2)) if m_move.group(2) else 0.4
        ros_pub.publish(speed, 0.0)
        return tools.move_to(loc, speed)

    m_nav = re.search(r"nav\s+(-?[0-9.]+)\s+(-?[0-9.]+)(?:\s+(-?[0-9.]+))?", lower)
    if m_nav:
        x = float(m_nav.group(1))
        y = float(m_nav.group(2))
        theta = float(m_nav.group(3)) if m_nav.group(3) else None
        ros_pub.publish(0.2, 0.0)
        return tools.navigate_to(x, y, theta)

    if "forward" in lower or "前进" in text:
        ros_pub.publish(0.35, 0.0)
        return tools.move_to("forward", 0.35)
    if "back" in lower or "后退" in text:
        ros_pub.publish(-0.25, 0.0)
        return tools.move_to("backward", 0.25)
    if "left" in lower or "左转" in text:
        ros_pub.publish(0.0, 0.4)
        return tools.move_to("left", 0.4)
    if "right" in lower or "右转" in text:
        ros_pub.publish(0.0, -0.4)
        return tools.move_to("right", 0.4)
    return None


def command_loop(
    tools: ClawROSTools,
    ui: UiState,
    cli_path: Optional[str],
    ros_pub: RosbridgeCmdVelPublisher,
) -> None:
    print("可用命令: move <loc> [speed] | nav <x> <y> [theta] | state | stop | quit")
    print("输入自然语言会转给 OpenClaw（若可用）")
    while ui.running:
        try:
            line = input("visual-sim> ").strip()
        except (EOFError, KeyboardInterrupt):
            # 非交互环境（例如后台启动）下保持 GUI 继续运行
            time.sleep(0.5)
            continue
        if not line:
            continue
        if line.lower() in {"quit", "exit"}:
            ui.running = False
            break

        parts = line.split()
        cmd = parts[0].lower()
        try:
            if cmd == "move":
                if len(parts) < 2:
                    ui.messages.put("用法: move <location> [speed]")
                    continue
                speed = float(parts[2]) if len(parts) > 2 else 0.5
                ui.messages.put(tools.move_to(parts[1], speed))
                ros_pub.publish(speed, 0.0)
                continue
            if cmd == "nav":
                if len(parts) < 3:
                    ui.messages.put("用法: nav <x> <y> [theta]")
                    continue
                x = float(parts[1])
                y = float(parts[2])
                theta = float(parts[3]) if len(parts) > 3 else None
                ui.messages.put(tools.navigate_to(x, y, theta))
                ros_pub.publish(0.2, 0.0)
                continue
            if cmd == "state":
                ui.messages.put(tools.get_robot_state())
                continue
            if cmd == "stop":
                ui.messages.put(tools.emergency_stop())
                ros_pub.publish(0.0, 0.0)
                continue

            if cli_path:
                claw_text = call_openclaw(cli_path, line)
                ui.messages.put(f"[OpenClaw] {claw_text}")
                print(f"[OpenClaw] {claw_text}", flush=True)
                acted = apply_claw_text_as_motion(tools, ros_pub, claw_text)
                if acted:
                    ui.messages.put(f"[Exec] {acted}")
                    print(f"[Exec] {acted}", flush=True)
            else:
                ui.messages.put("未检测到 OpenClaw，可用命令: move/nav/state/stop")
        except Exception as exc:
            ui.messages.put(f"命令失败: {exc}")


def autoplay_loop(
    tools: ClawROSTools,
    ui: UiState,
    cli_path: Optional[str],
    ros_pub: RosbridgeCmdVelPublisher,
) -> None:
    """非交互模式下自动演示运动。"""
    try:
        if cli_path:
            prompts = [
                "你是机器人控制器。只回复一行命令：move forward 0.35",
                "你是机器人控制器。只回复一行命令：move left 0.30",
                "你是机器人控制器。只回复一行命令：stop",
            ]
            for p in prompts:
                claw_text = call_openclaw(cli_path, p)
                ui.messages.put(f"[OpenClaw] {claw_text}")
                print(f"[OpenClaw] {claw_text}", flush=True)
                acted = apply_claw_text_as_motion(tools, ros_pub, claw_text)
                if acted:
                    ui.messages.put(f"[Exec] {acted}")
                    print(f"[Exec] {acted}", flush=True)
                time.sleep(2.0)
        else:
            time.sleep(0.8)
            ui.messages.put(tools.move_to("forward", 0.35))
            ros_pub.publish(0.35, 0.0)
            time.sleep(2.5)
            ui.messages.put(tools.navigate_to(1.5, 1.0))
            ros_pub.publish(0.2, 0.0)
            time.sleep(3.5)
            ui.messages.put(tools.navigate_to(-1.2, 0.6))
            ros_pub.publish(0.2, 0.0)
            time.sleep(3.5)
            ui.messages.put(tools.emergency_stop())
            ros_pub.publish(0.0, 0.0)
    except Exception as exc:
        ui.messages.put(f"自动演示失败: {exc}")


def main() -> None:
    bridge = create_simulated_bridge()
    tools = ClawROSTools(bridge=bridge)
    if not tools.initialize():
        print("初始化失败")
        return

    cli = find_openclaw_cli()
    cli = cli if (cli and openclaw_health_ok(cli)) else None

    print("可视化模拟器启动成功")
    if cli:
        print(f"OpenClaw 已连接: {cli}")
    else:
        print("OpenClaw 未连接（仅本地命令控制）")

    ui = UiState()
    ros_pub = RosbridgeCmdVelPublisher()
    if sys.stdin.isatty():
        t = threading.Thread(
            target=command_loop,
            args=(tools, ui, cli, ros_pub),
            daemon=True,
        )
        t.start()
    else:
        print("检测到非交互终端：已仅启动可视化窗口（无命令行输入）")
        t = threading.Thread(
            target=autoplay_loop,
            args=(tools, ui, cli, ros_pub),
            daemon=True,
        )
        t.start()

    root = tk.Tk()
    root.title("ClawROS Visual Simulator")
    root.geometry(f"{CANVAS_SIZE + 20}x{CANVAS_SIZE + 90}")
    canvas = tk.Canvas(root, width=CANVAS_SIZE, height=CANVAS_SIZE, bg="#0f172a")
    canvas.pack(pady=8)
    status = tk.StringVar(value="ready")
    label = tk.Label(root, textvariable=status, anchor="w", justify="left")
    label.pack(fill="x", padx=8)

    def draw_frame() -> None:
        if not ui.running:
            root.destroy()
            return

        while True:
            try:
                status.set(ui.messages.get_nowait())
            except queue.Empty:
                break

        st = bridge.get_robot_state()
        pos = st.get("position", {})
        vel = st.get("velocity", {})
        ori = st.get("orientation", {})
        x = float(pos.get("x", 0.0))
        y = float(pos.get("y", 0.0))
        z = float(ori.get("z", 0.0))
        w = float(ori.get("w", 1.0))
        theta = 2.0 * (0.0 if w == 0.0 else __import__("math").atan2(z, w))
        ui.trail.append((x, y))
        if len(ui.trail) > 800:
            ui.trail = ui.trail[-800:]

        canvas.delete("all")
        # grid
        for i in range(int(WORLD_MIN), int(WORLD_MAX) + 1):
            x1, y1 = world_to_canvas(i, WORLD_MIN)
            x2, y2 = world_to_canvas(i, WORLD_MAX)
            canvas.create_line(x1, y1, x2, y2, fill="#1e293b")
            x1, y1 = world_to_canvas(WORLD_MIN, i)
            x2, y2 = world_to_canvas(WORLD_MAX, i)
            canvas.create_line(x1, y1, x2, y2, fill="#1e293b")

        # obstacles
        for ox, oy in bridge.simulator.obstacles:
            cx, cy = world_to_canvas(ox, oy)
            r = 10
            canvas.create_oval(cx - r, cy - r, cx + r, cy + r, fill="#ef4444", outline="")

        # trail
        if len(ui.trail) > 1:
            pts = []
            for tx, ty in ui.trail:
                cx, cy = world_to_canvas(tx, ty)
                pts.extend([cx, cy])
            canvas.create_line(*pts, fill="#38bdf8", width=2, smooth=True)

        # robot
        cx, cy = world_to_canvas(x, y)
        rr = 12
        canvas.create_oval(cx - rr, cy - rr, cx + rr, cy + rr, fill="#22c55e", outline="")
        hx = cx + 20 * cos(theta)
        hy = cy - 20 * sin(theta)
        canvas.create_line(cx, cy, hx, hy, fill="#eab308", width=3)

        status.set(
            f"pos=({x:.2f}, {y:.2f}) vel=({vel.get('linear',0):.2f}, {vel.get('angular',0):.2f}) "
            f"battery={st.get('battery',0):.1f}% state={st.get('status','idle')}"
        )
        root.after(80, draw_frame)

    def on_close() -> None:
        ui.running = False
        ros_pub.close()
        tools.shutdown()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)
    draw_frame()
    root.mainloop()


if __name__ == "__main__":
    main()
