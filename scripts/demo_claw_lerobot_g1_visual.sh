#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

TASK_TEXT="${1:-前进两步，右转，再做 tpose，最后停止。}"
CONDA_ENV="${CONDA_ENV:-lerobot-g1}"
CONTROLLER="${LEROBOT_G1_CONTROLLER:-HolosomaLocomotionController}"
PYTHON_BIN="${LEROBOT_G1_PYTHON:-python}"
HEADLESS_FLAG="${LEROBOT_G1_HEADLESS:-1}"

echo "[lerobot-g1-visual] task: $TASK_TEXT"
echo "[lerobot-g1-visual] ensuring ros2-sim is up..."
./scripts/ros2_sim_docker.sh up >/dev/null

echo "[lerobot-g1-visual] waiting for rosbridge(:9090)..."
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

if ! pgrep -f "examples/docker_humanoid_visual.py" >/dev/null 2>&1; then
  echo "[lerobot-g1-visual] launching humanoid visualizer..."
  nohup env PYTHONUNBUFFERED=1 python3 examples/docker_humanoid_visual.py >/tmp/docker_humanoid_visual.log 2>&1 &
  sleep 2
else
  echo "[lerobot-g1-visual] visualizer already running, reusing window"
fi

echo "[lerobot-g1-visual] generating humanoid plan via OpenClaw..."
PLAN_JSON="$(python3 examples/claw_text_to_humanoid_plan.py --text "$TASK_TEXT")"
echo "[lerobot-g1-visual] plan=$PLAN_JSON"

CMD=(
  conda run -n "$CONDA_ENV" "$PYTHON_BIN" examples/lerobot_g1_sim_backend.py
  --config config/clawros_config.yaml
  --controller "$CONTROLLER"
  --publish-visual
  --rosbridge-host 127.0.0.1
  --rosbridge-port 9090
  --plan-json "$PLAN_JSON"
)

if [ "$HEADLESS_FLAG" = "1" ]; then
  CMD+=(--headless)
fi

echo "[lerobot-g1-visual] executing LeRobot G1 sim and streaming state to /joint_states + /odom..."
CYCLONEDDS_HOME=/opt/anaconda3/envs/$CONDA_ENV \
CMAKE_PREFIX_PATH=/opt/anaconda3/envs/$CONDA_ENV \
"${CMD[@]}"

echo "[lerobot-g1-visual] done."
