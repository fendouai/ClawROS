#!/usr/bin/env python3
import json
import math
import time
from typing import Dict, List

import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node
from sensor_msgs.msg import JointState
from std_msgs.msg import String


class MockHumanoidController(Node):
    def __init__(self) -> None:
        super().__init__("clawros_mock_humanoid_controller")
        self.joint_pub = self.create_publisher(JointState, "/joint_states", 10)
        self.gait_sub = self.create_subscription(String, "/humanoid/gait_cmd", self.on_gait_cmd, 10)
        self.pose_sub = self.create_subscription(String, "/humanoid/whole_body_cmd", self.on_pose_cmd, 10)
        self.cmd_sub = self.create_subscription(Twist, "/cmd_vel", self.on_cmd_vel, 10)
        self.timer = self.create_timer(0.05, self.on_tick)  # 20Hz

        self.joint_names: List[str] = [
            "left_hip_yaw",
            "left_hip_roll",
            "left_hip_pitch",
            "left_knee",
            "right_hip_yaw",
            "right_hip_roll",
            "right_hip_pitch",
            "right_knee",
            "waist_yaw",
            "left_shoulder_pitch",
            "right_shoulder_pitch",
            "head_yaw",
        ]
        self.joints: Dict[str, float] = {name: 0.0 for name in self.joint_names}

        self.linear = 0.0
        self.angular = 0.0
        self.gait = "idle"
        self.pose = "stand"
        self.phase = 0.0
        self.last_t = time.time()

    def _apply_pose(self, posture: str) -> None:
        self.pose = posture
        if posture == "stand":
            for k in self.joints:
                self.joints[k] = 0.0
        elif posture == "crouch":
            self.joints["left_knee"] = -0.9
            self.joints["right_knee"] = 0.9
            self.joints["left_hip_pitch"] = -0.45
            self.joints["right_hip_pitch"] = 0.45
        elif posture == "tpose":
            self.joints["left_shoulder_pitch"] = -1.2
            self.joints["right_shoulder_pitch"] = 1.2
            self.joints["waist_yaw"] = 0.0

    def on_gait_cmd(self, msg: String) -> None:
        try:
            data = json.loads(msg.data)
            self.linear = float(data.get("linear", 0.0))
            self.angular = float(data.get("angular", 0.0))
            self.gait = str(data.get("gait", "walk"))
        except Exception:
            self.get_logger().warning("invalid /humanoid/gait_cmd json")

    def on_pose_cmd(self, msg: String) -> None:
        try:
            data = json.loads(msg.data)
            posture = str(data.get("posture", "stand"))
            self._apply_pose(posture)
        except Exception:
            self.get_logger().warning("invalid /humanoid/whole_body_cmd json")

    def on_cmd_vel(self, msg: Twist) -> None:
        # 与底盘速度指令联动，兼容现有流程
        self.linear = float(msg.linear.x)
        self.angular = float(msg.angular.z)
        if abs(self.linear) > 1e-3 or abs(self.angular) > 1e-3:
            self.gait = "walk"
        else:
            self.gait = "idle"

    def on_tick(self) -> None:
        now = time.time()
        dt = max(0.0, now - self.last_t)
        self.last_t = now

        speed_scale = max(0.2, min(2.0, abs(self.linear) * 4.0 + abs(self.angular) * 1.5))
        self.phase += dt * speed_scale * 4.0

        if self.gait != "idle" and self.pose in {"stand", "walk"}:
            swing = math.sin(self.phase) * 0.45
            self.joints["left_hip_pitch"] = swing
            self.joints["right_hip_pitch"] = -swing
            self.joints["left_knee"] = -swing * 0.8
            self.joints["right_knee"] = swing * 0.8
            self.joints["left_shoulder_pitch"] = -swing * 0.5
            self.joints["right_shoulder_pitch"] = swing * 0.5
            self.joints["waist_yaw"] = max(-0.4, min(0.4, self.angular))

        js = JointState()
        js.header.stamp = self.get_clock().now().to_msg()
        js.name = self.joint_names
        js.position = [self.joints[n] for n in self.joint_names]
        self.joint_pub.publish(js)


def main() -> None:
    rclpy.init()
    node = MockHumanoidController()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
