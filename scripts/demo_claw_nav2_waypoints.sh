#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

TASK_TEXT="${1:-请从原点出发，先到(1.5, 0.8)，再到(2.2, -0.6)，最后到(0.0, 0.0)}"

echo "[demo] task: $TASK_TEXT"
echo "[demo] ensuring ros2-sim is up..."
./scripts/ros2_sim_docker.sh up >/dev/null

echo "[demo] waiting for /follow_waypoints action..."
for _ in $(seq 1 30); do
  if docker exec clawros-ros2-sim bash -lc 'source /opt/ros/humble/setup.bash && ros2 action list' | rg -q "/follow_waypoints"; then
    break
  fi
  sleep 1
done

if ! docker exec clawros-ros2-sim bash -lc 'source /opt/ros/humble/setup.bash && ros2 action list' | rg -q "/follow_waypoints"; then
  echo "[demo] error: /follow_waypoints not available"
  exit 2
fi

if ! pgrep -f "examples/docker_ros2_visual.py" >/dev/null 2>&1; then
  echo "[demo] launching visualizer..."
  nohup env PYTHONUNBUFFERED=1 python3 examples/docker_ros2_visual.py >/tmp/docker_ros2_visual.log 2>&1 &
  sleep 2
fi

echo "[demo] asking OpenClaw to plan waypoints..."
WAYPOINTS_JSON="$(python3 examples/claw_text_to_waypoints.py --text "$TASK_TEXT")"
echo "[demo] waypoints=$WAYPOINTS_JSON"

echo "[demo] sending FollowWaypoints goal..."
docker exec clawros-ros2-sim bash -lc \
  "source /opt/ros/humble/setup.bash && /usr/bin/python3 /workspace/docker/ros2-sim/send_waypoints_goal.py --waypoints-json '$WAYPOINTS_JSON'"

echo "[demo] done. visualizer should show trajectory from Docker /odom."
