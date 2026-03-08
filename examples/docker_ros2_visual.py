#!/usr/bin/env python3
import json
import os
import queue
import re
import subprocess
import threading
import time
import tkinter as tk
from dataclasses import dataclass, field
from math import atan2, cos, sin
from typing import Optional, Tuple

import roslibpy

WORLD_MIN = -5.0
WORLD_MAX = 5.0
CANVAS_SIZE = 720


def world_to_canvas(x: float, y: float) -> Tuple[float, float]:
    scale = CANVAS_SIZE / (WORLD_MAX - WORLD_MIN)
    cx = (x - WORLD_MIN) * scale
    cy = CANVAS_SIZE - (y - WORLD_MIN) * scale
    return cx, cy


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
    x: float = 0.0
    y: float = 0.0
    yaw: float = 0.0
    v: float = 0.0
    w: float = 0.0


class DockerRos2Bridge:
    def __init__(self, host: str = "127.0.0.1", port: int = 9090):
        self.client = roslibpy.Ros(host=host, port=port)
        self.client.run(timeout=5)
        if not self.client.is_connected:
            raise RuntimeError("rosbridge 未连接")
        self.cmd_topic = roslibpy.Topic(
            self.client, "/cmd_vel", "geometry_msgs/msg/Twist"
        )
        self.odom_topic = roslibpy.Topic(
            self.client, "/odom", "nav_msgs/msg/Odometry"
        )

    def publish_cmd(self, linear: float, angular: float) -> None:
        self.cmd_topic.publish(
            roslibpy.Message(
                {
                    "linear": {"x": linear, "y": 0.0, "z": 0.0},
                    "angular": {"x": 0.0, "y": 0.0, "z": angular},
                }
            )
        )

    def subscribe_odom(self, callback) -> None:
        self.odom_topic.subscribe(callback)

    def close(self) -> None:
        try:
            self.odom_topic.unsubscribe()
        except Exception:
            pass
        self.client.terminate()


def apply_claw_text(bridge: DockerRos2Bridge, text: str) -> str:
    lower = text.lower()
    if "stop" in lower or "停止" in text:
        bridge.publish_cmd(0.0, 0.0)
        return "stop -> /cmd_vel"
    m_move = re.search(r"move\s+(\w+)(?:\s+([0-9.]+))?", lower)
    if m_move:
        loc = m_move.group(1)
        speed = float(m_move.group(2)) if m_move.group(2) else 0.35
        if loc in ("left", "right"):
            bridge.publish_cmd(0.0, speed if loc == "left" else -speed)
        elif loc in ("backward", "back"):
            bridge.publish_cmd(-speed, 0.0)
        else:
            bridge.publish_cmd(speed, 0.0)
        return f"{text} -> /cmd_vel"
    if "forward" in lower or "前进" in text:
        bridge.publish_cmd(0.35, 0.0)
        return "forward -> /cmd_vel"
    if "left" in lower or "左转" in text:
        bridge.publish_cmd(0.0, 0.35)
        return "left -> /cmd_vel"
    if "right" in lower or "右转" in text:
        bridge.publish_cmd(0.0, -0.35)
        return "right -> /cmd_vel"
    return "未识别命令"


def claw_autoplay(ui: UiState, bridge: DockerRos2Bridge, cli: Optional[str]) -> None:
    if not cli:
        ui.messages.put("未检测到 OpenClaw")
        return
    prompts = [
        "你是机器人控制器。只回复一行命令：move forward 0.35",
        "你是机器人控制器。只回复一行命令：move left 0.30",
        "你是机器人控制器。只回复一行命令：stop",
    ]
    for p in prompts:
        t = call_openclaw(cli, p)
        ui.messages.put(f"[OpenClaw] {t}")
        ui.messages.put(f"[Exec] {apply_claw_text(bridge, t)}")
        time.sleep(2.0)


def main() -> None:
    bridge = DockerRos2Bridge()
    ui = UiState()
    cli = find_openclaw_cli()

    def on_odom(msg):
        p = msg.get("pose", {}).get("pose", {}).get("position", {})
        o = msg.get("pose", {}).get("pose", {}).get("orientation", {})
        t = msg.get("twist", {}).get("twist", {})
        z = float(o.get("z", 0.0))
        w = float(o.get("w", 1.0))
        ui.x = float(p.get("x", 0.0))
        ui.y = float(p.get("y", 0.0))
        ui.yaw = 2.0 * atan2(z, w)
        ui.v = float(t.get("linear", {}).get("x", 0.0))
        ui.w = float(t.get("angular", {}).get("z", 0.0))

    bridge.subscribe_odom(on_odom)

    t = threading.Thread(target=claw_autoplay, args=(ui, bridge, cli), daemon=True)
    t.start()

    root = tk.Tk()
    root.title("Docker ROS2 Visual (from /odom)")
    root.geometry(f"{CANVAS_SIZE + 20}x{CANVAS_SIZE + 90}")
    canvas = tk.Canvas(root, width=CANVAS_SIZE, height=CANVAS_SIZE, bg="#0f172a")
    canvas.pack(pady=8)
    status = tk.StringVar(value="connecting...")
    label = tk.Label(root, textvariable=status, anchor="w", justify="left")
    label.pack(fill="x", padx=8)

    def draw_frame() -> None:
        while True:
            try:
                status.set(ui.messages.get_nowait())
            except queue.Empty:
                break
        ui.trail.append((ui.x, ui.y))
        if len(ui.trail) > 800:
            ui.trail = ui.trail[-800:]
        canvas.delete("all")
        for i in range(int(WORLD_MIN), int(WORLD_MAX) + 1):
            x1, y1 = world_to_canvas(i, WORLD_MIN)
            x2, y2 = world_to_canvas(i, WORLD_MAX)
            canvas.create_line(x1, y1, x2, y2, fill="#1e293b")
            x1, y1 = world_to_canvas(WORLD_MIN, i)
            x2, y2 = world_to_canvas(WORLD_MAX, i)
            canvas.create_line(x1, y1, x2, y2, fill="#1e293b")
        if len(ui.trail) > 1:
            pts = []
            for tx, ty in ui.trail:
                cx, cy = world_to_canvas(tx, ty)
                pts.extend([cx, cy])
            canvas.create_line(*pts, fill="#38bdf8", width=2, smooth=True)
        cx, cy = world_to_canvas(ui.x, ui.y)
        rr = 12
        canvas.create_oval(cx - rr, cy - rr, cx + rr, cy + rr, fill="#22c55e", outline="")
        hx = cx + 20 * cos(ui.yaw)
        hy = cy - 20 * sin(ui.yaw)
        canvas.create_line(cx, cy, hx, hy, fill="#eab308", width=3)
        if not ui.messages.qsize():
            status.set(f"/odom pos=({ui.x:.2f},{ui.y:.2f}) vel=({ui.v:.2f},{ui.w:.2f})")
        root.after(80, draw_frame)

    def on_close() -> None:
        ui.running = False
        bridge.close()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)
    draw_frame()
    root.mainloop()


if __name__ == "__main__":
    main()
