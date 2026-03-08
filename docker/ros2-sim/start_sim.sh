#!/usr/bin/env bash
set -eo pipefail

source "/opt/ros/$ROS_DISTRO/setup.bash"

export TURTLEBOT3_MODEL="${TURTLEBOT3_MODEL:-waffle}"

echo "[ros2-sim] starting minimal ROS2 simulation runtime..."
echo "[ros2-sim] (no Gazebo in this profile; rosbridge + mock FollowWaypoints)"

echo "[ros2-sim] starting rosbridge websocket on :9090 ..."
ros2 launch rosbridge_server rosbridge_websocket_launch.xml port:=9090 &
BRIDGE_PID=$!

echo "[ros2-sim] starting mock Nav2 FollowWaypoints action server ..."
python3 /workspace/docker/ros2-sim/mock_follow_waypoints_server.py &
NAV2_MOCK_PID=$!

cleanup() {
  echo "[ros2-sim] shutting down..."
  kill "$BRIDGE_PID" "$NAV2_MOCK_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

wait "$BRIDGE_PID"
