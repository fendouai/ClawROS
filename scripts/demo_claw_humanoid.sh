#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

TASK_TEXT="${1:-请先前进两步，然后右转小幅行走，再做一个 T 字姿态，最后站立停止。}"
VISUAL_CMD_RE='^python3 (examples/docker_humanoid_visual.py|.*/examples/docker_humanoid_visual.py)$'

is_visualizer_running() {
  ps -ax -o command= | rg -q "${VISUAL_CMD_RE}"
}

echo "[humanoid-demo] task: $TASK_TEXT"
echo "[humanoid-demo] ensuring ros2-sim is up..."
./scripts/ros2_sim_docker.sh up >/dev/null

echo "[humanoid-demo] waiting for rosbridge(:9090)..."
for _ in $(seq 1 30); do
  if python3 - <<'PY' >/dev/null 2>&1
import roslibpy
ros = roslibpy.Ros(host='127.0.0.1', port=9090)
ros.run(timeout=2)
ok = ros.is_connected
if ok:
    ros.terminate()
raise SystemExit(0 if ok else 1)
PY
  then
    break
  fi
  sleep 1
done

echo "[humanoid-demo] waiting for /joint_states ..."
for _ in $(seq 1 40); do
  if docker exec clawros-ros2-sim bash -lc 'source /opt/ros/humble/setup.bash && ros2 topic list' | rg -q '^/joint_states$'; then
    break
  fi
  sleep 1
done

if ! docker exec clawros-ros2-sim bash -lc 'source /opt/ros/humble/setup.bash && ros2 topic list' | rg -q '^/joint_states$'; then
  echo "[humanoid-demo] error: /joint_states not available"
  exit 2
fi

if ! is_visualizer_running; then
  echo "[humanoid-demo] launching humanoid visualizer..."
  nohup env PYTHONUNBUFFERED=1 python3 examples/docker_humanoid_visual.py >/tmp/docker_humanoid_visual.log 2>&1 &
  sleep 2
  if ! is_visualizer_running; then
    echo "[humanoid-demo] warning: visualizer not running (headless/session limit possible), check /tmp/docker_humanoid_visual.log"
    echo "[humanoid-demo] continuing with humanoid task execution..."
  fi
else
  echo "[humanoid-demo] visualizer already running, reusing window"
fi

echo "[humanoid-demo] asking OpenClaw to create humanoid plan..."
PLAN_JSON="$(python3 examples/claw_text_to_humanoid_plan.py --text "$TASK_TEXT")"
echo "[humanoid-demo] plan=$PLAN_JSON"

echo "[humanoid-demo] executing plan via rosbridge..."
python3 examples/execute_humanoid_plan.py --plan-json "$PLAN_JSON"

echo "[humanoid-demo] done. visualizer shows /joint_states skeleton + /odom trajectory."
