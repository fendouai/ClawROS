#!/usr/bin/env python3
import argparse
import json
from typing import List

import rclpy
from geometry_msgs.msg import PoseStamped
from nav2_msgs.action import FollowWaypoints
from rclpy.action import ActionClient
from rclpy.node import Node


class WaypointClient(Node):
    def __init__(self) -> None:
        super().__init__("clawros_follow_waypoints_client")
        self.client = ActionClient(self, FollowWaypoints, "/follow_waypoints")

    def send(self, points: List[List[float]], timeout_sec: float = 120.0) -> int:
        if not self.client.wait_for_server(timeout_sec=8.0):
            self.get_logger().error("Action server /follow_waypoints not ready")
            return 2

        goal = FollowWaypoints.Goal()
        for p in points:
            ps = PoseStamped()
            ps.header.frame_id = "map"
            ps.pose.position.x = float(p[0])
            ps.pose.position.y = float(p[1])
            ps.pose.orientation.w = 1.0
            goal.poses.append(ps)

        future = self.client.send_goal_async(goal)
        rclpy.spin_until_future_complete(self, future, timeout_sec=8.0)
        goal_handle = future.result()
        if goal_handle is None or not goal_handle.accepted:
            self.get_logger().error("Goal rejected")
            return 3

        result_future = goal_handle.get_result_async()
        rclpy.spin_until_future_complete(self, result_future, timeout_sec=timeout_sec)
        result_wrap = result_future.result()
        if result_wrap is None:
            self.get_logger().error("Timed out waiting for result")
            return 4

        missed = list(result_wrap.result.missed_waypoints)
        if missed:
            self.get_logger().warning(f"missed_waypoints={missed}")
        else:
            self.get_logger().info("FollowWaypoints completed with no missed waypoints")
        return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--waypoints-json",
        required=True,
        help='JSON, e.g. [[1.0,1.0],[2.0,0.5],[-1.0,0.0]]',
    )
    args = parser.parse_args()

    points = json.loads(args.waypoints_json)
    if not isinstance(points, list) or not points:
        print("Invalid waypoints-json")
        return 1

    rclpy.init()
    node = WaypointClient()
    try:
        return node.send(points)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    raise SystemExit(main())
