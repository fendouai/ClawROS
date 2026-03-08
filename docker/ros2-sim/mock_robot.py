#!/usr/bin/env python3
import math
import time

import rclpy
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from rclpy.node import Node


class MockRobot(Node):
    def __init__(self) -> None:
        super().__init__("clawros_mock_robot")
        self.pub = self.create_publisher(Odometry, "/odom", 10)
        self.sub = self.create_subscription(Twist, "/cmd_vel", self.on_cmd, 10)
        self.timer = self.create_timer(0.05, self.on_tick)  # 20Hz
        self.x = 0.0
        self.y = 0.0
        self.yaw = 0.0
        self.v = 0.0
        self.w = 0.0
        self.last_t = time.time()

    def on_cmd(self, msg: Twist) -> None:
        self.v = float(msg.linear.x)
        self.w = float(msg.angular.z)

    def on_tick(self) -> None:
        now = time.time()
        dt = max(0.0, now - self.last_t)
        self.last_t = now
        self.yaw += self.w * dt
        self.x += self.v * math.cos(self.yaw) * dt
        self.y += self.v * math.sin(self.yaw) * dt

        o = Odometry()
        o.header.stamp = self.get_clock().now().to_msg()
        o.header.frame_id = "odom"
        o.child_frame_id = "base_link"
        o.pose.pose.position.x = self.x
        o.pose.pose.position.y = self.y
        o.pose.pose.orientation.z = math.sin(self.yaw / 2.0)
        o.pose.pose.orientation.w = math.cos(self.yaw / 2.0)
        o.twist.twist.linear.x = self.v
        o.twist.twist.angular.z = self.w
        self.pub.publish(o)


def main() -> None:
    rclpy.init()
    node = MockRobot()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
