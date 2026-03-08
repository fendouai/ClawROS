#!/usr/bin/env python3
import math
import threading
import time
from typing import Optional

import rclpy
from geometry_msgs.msg import Twist
from nav2_msgs.action import FollowWaypoints
from nav_msgs.msg import Odometry
from rclpy.action import ActionServer
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node


class MockFollowWaypointsServer(Node):
    def __init__(self) -> None:
        super().__init__("clawros_mock_follow_waypoints")
        self.action_server = ActionServer(
            self,
            FollowWaypoints,
            "/follow_waypoints",
            execute_callback=self.execute_callback,
        )
        self.odom_pub = self.create_publisher(Odometry, "/odom", 10)
        self.cmd_sub = self.create_subscription(Twist, "/cmd_vel", self.on_cmd_vel, 10)
        self.timer = self.create_timer(0.05, self.on_tick)
        self.x = 0.0
        self.y = 0.0
        self.yaw = 0.0
        self.v = 0.0
        self.w = 0.0
        self.last_t = time.time()
        self.lock = threading.Lock()
        self.override_until = 0.0

    def on_cmd_vel(self, msg: Twist) -> None:
        with self.lock:
            self.v = float(msg.linear.x)
            self.w = float(msg.angular.z)
            self.override_until = time.time() + 0.4

    def on_tick(self) -> None:
        now = time.time()
        dt = max(0.0, now - self.last_t)
        self.last_t = now

        with self.lock:
            self.yaw += self.w * dt
            self.x += self.v * math.cos(self.yaw) * dt
            self.y += self.v * math.sin(self.yaw) * dt

        odom = Odometry()
        odom.header.stamp = self.get_clock().now().to_msg()
        odom.header.frame_id = "odom"
        odom.child_frame_id = "base_link"
        odom.pose.pose.position.x = self.x
        odom.pose.pose.position.y = self.y
        odom.pose.pose.orientation.z = math.sin(self.yaw / 2.0)
        odom.pose.pose.orientation.w = math.cos(self.yaw / 2.0)
        odom.twist.twist.linear.x = self.v
        odom.twist.twist.angular.z = self.w
        self.odom_pub.publish(odom)

    def _drive_towards(self, tx: float, ty: float) -> None:
        dx = tx - self.x
        dy = ty - self.y
        dist = math.hypot(dx, dy)
        target_yaw = math.atan2(dy, dx)
        yaw_err = math.atan2(math.sin(target_yaw - self.yaw), math.cos(target_yaw - self.yaw))
        linear = min(0.5, max(0.0, dist))
        angular = max(-1.0, min(1.0, yaw_err))
        self.v = linear
        self.w = angular

    def _stop(self) -> None:
        self.v = 0.0
        self.w = 0.0

    def execute_callback(self, goal_handle):
        poses = list(goal_handle.request.poses)
        feedback = FollowWaypoints.Feedback()
        result = FollowWaypoints.Result()
        result.missed_waypoints = []

        for idx, pose in enumerate(poses):
            tx = float(pose.pose.position.x)
            ty = float(pose.pose.position.y)
            reached = False
            for _ in range(800):
                if goal_handle.is_cancel_requested:
                    with self.lock:
                        self._stop()
                    goal_handle.canceled()
                    return result

                with self.lock:
                    # external /cmd_vel has short priority window
                    if time.time() > self.override_until:
                        self._drive_towards(tx, ty)
                    dist = math.hypot(tx - self.x, ty - self.y)
                if dist < 0.12:
                    reached = True
                    break
                time.sleep(0.05)

            if not reached:
                result.missed_waypoints.append(idx)

            feedback.current_waypoint = idx
            goal_handle.publish_feedback(feedback)

        with self.lock:
            self._stop()
        goal_handle.succeed()
        return result


def main() -> None:
    rclpy.init()
    node = MockFollowWaypointsServer()
    executor = MultiThreadedExecutor(num_threads=2)
    executor.add_node(node)
    try:
        executor.spin()
    finally:
        executor.shutdown()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
