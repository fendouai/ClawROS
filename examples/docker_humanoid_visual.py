#!/usr/bin/env python3
import queue
import tkinter as tk
from dataclasses import dataclass, field
from math import cos, sin
from typing import Dict, Tuple

import roslibpy


@dataclass
class UiState:
    messages: "queue.Queue[str]" = field(default_factory=queue.Queue)
    trail: list[Tuple[float, float]] = field(default_factory=list)
    joints: Dict[str, float] = field(default_factory=dict)
    x: float = 0.0
    y: float = 0.0
    yaw_hint: float = 0.0
    linear: float = 0.0
    angular: float = 0.0


def world_to_canvas(x: float, y: float, size: int = 360) -> Tuple[float, float]:
    world_min, world_max = -5.0, 5.0
    scale = size / (world_max - world_min)
    cx = (x - world_min) * scale
    cy = size - (y - world_min) * scale
    return cx, cy


def main() -> None:
    ui = UiState()
    ros = roslibpy.Ros(host="127.0.0.1", port=9090)
    ros.run(timeout=5)
    if not ros.is_connected:
        raise RuntimeError("rosbridge not connected on 127.0.0.1:9090")

    odom_topic = roslibpy.Topic(ros, "/odom", "nav_msgs/msg/Odometry")
    joint_topic = roslibpy.Topic(ros, "/joint_states", "sensor_msgs/msg/JointState")

    def on_odom(msg):
        p = msg.get("pose", {}).get("pose", {}).get("position", {})
        t = msg.get("twist", {}).get("twist", {})
        ui.x = float(p.get("x", 0.0))
        ui.y = float(p.get("y", 0.0))
        ui.linear = float(t.get("linear", {}).get("x", 0.0))
        ui.angular = float(t.get("angular", {}).get("z", 0.0))
        ui.yaw_hint += ui.angular * 0.08

    def on_joint(msg):
        names = msg.get("name", []) or []
        pos = msg.get("position", []) or []
        for i, n in enumerate(names):
            if i < len(pos):
                ui.joints[str(n)] = float(pos[i])

    odom_topic.subscribe(on_odom)
    joint_topic.subscribe(on_joint)

    root = tk.Tk()
    root.title("Docker Humanoid Visual (from /joint_states + /odom)")
    root.geometry("1040x760")
    left = tk.Canvas(root, width=620, height=680, bg="#0b1220")
    left.pack(side="left", padx=10, pady=10)
    right = tk.Canvas(root, width=360, height=360, bg="#111827")
    right.pack(side="top", padx=10, pady=10)
    status = tk.StringVar(value="connected")
    tk.Label(root, textvariable=status, anchor="w").pack(fill="x", padx=10)

    def j(name: str) -> float:
        return float(ui.joints.get(name, 0.0))

    def draw_humanoid() -> None:
        left.delete("all")
        cx, cy = 310, 340
        hip_l = j("left_hip_pitch")
        hip_r = j("right_hip_pitch")
        knee_l = j("left_knee")
        knee_r = j("right_knee")
        sh_l = j("left_shoulder_pitch")
        sh_r = j("right_shoulder_pitch")
        waist = j("waist_yaw")

        torso_top = (cx + 35 * sin(waist), cy - 180)
        pelvis = (cx, cy)
        left.create_line(pelvis[0], pelvis[1], torso_top[0], torso_top[1], fill="#f8fafc", width=8)
        left.create_oval(torso_top[0] - 16, torso_top[1] - 28, torso_top[0] + 16, torso_top[1] + 4, fill="#22d3ee", outline="")

        sh_y = torso_top[1] + 24
        ls = (torso_top[0] - 58, sh_y)
        rs = (torso_top[0] + 58, sh_y)
        l_hand = (ls[0] - 120 * cos(sh_l), ls[1] + 120 * sin(sh_l))
        r_hand = (rs[0] + 120 * cos(sh_r), rs[1] + 120 * sin(sh_r))
        left.create_line(ls[0], ls[1], l_hand[0], l_hand[1], fill="#94a3b8", width=6)
        left.create_line(rs[0], rs[1], r_hand[0], r_hand[1], fill="#94a3b8", width=6)

        lk = (pelvis[0] - 38 + 55 * sin(hip_l), pelvis[1] + 100)
        rk = (pelvis[0] + 38 + 55 * sin(hip_r), pelvis[1] + 100)
        la = (lk[0] + 45 * sin(knee_l), lk[1] + 110)
        ra = (rk[0] + 45 * sin(knee_r), rk[1] + 110)
        left.create_line(pelvis[0] - 36, pelvis[1], lk[0], lk[1], fill="#e2e8f0", width=7)
        left.create_line(lk[0], lk[1], la[0], la[1], fill="#e2e8f0", width=7)
        left.create_line(pelvis[0] + 36, pelvis[1], rk[0], rk[1], fill="#e2e8f0", width=7)
        left.create_line(rk[0], rk[1], ra[0], ra[1], fill="#e2e8f0", width=7)
        left.create_text(16, 16, text="Humanoid Skeleton", anchor="nw", fill="#cbd5e1", font=("Menlo", 16, "bold"))

    def draw_traj() -> None:
        right.delete("all")
        ui.trail.append((ui.x, ui.y))
        if len(ui.trail) > 600:
            ui.trail = ui.trail[-600:]

        for i in range(-5, 6):
            x1, y1 = world_to_canvas(i, -5)
            x2, y2 = world_to_canvas(i, 5)
            right.create_line(x1, y1, x2, y2, fill="#1f2937")
            x1, y1 = world_to_canvas(-5, i)
            x2, y2 = world_to_canvas(5, i)
            right.create_line(x1, y1, x2, y2, fill="#1f2937")

        if len(ui.trail) > 1:
            pts = []
            for x, y in ui.trail:
                cx, cy = world_to_canvas(x, y)
                pts.extend([cx, cy])
            right.create_line(*pts, fill="#38bdf8", width=2, smooth=True)

        cx, cy = world_to_canvas(ui.x, ui.y)
        right.create_oval(cx - 8, cy - 8, cx + 8, cy + 8, fill="#22c55e", outline="")
        hx = cx + 16 * cos(ui.yaw_hint)
        hy = cy - 16 * sin(ui.yaw_hint)
        right.create_line(cx, cy, hx, hy, fill="#eab308", width=3)

    def tick() -> None:
        draw_humanoid()
        draw_traj()
        status.set(
            f"/odom=({ui.x:.2f},{ui.y:.2f}) v=({ui.linear:.2f},{ui.angular:.2f}) "
            f"hips=({j('left_hip_pitch'):.2f},{j('right_hip_pitch'):.2f})"
        )
        root.after(80, tick)

    def on_close() -> None:
        try:
            odom_topic.unsubscribe()
            joint_topic.unsubscribe()
        except Exception:
            pass
        ros.terminate()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)
    tick()
    root.mainloop()


if __name__ == "__main__":
    main()
