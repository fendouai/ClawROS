#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

TASK_TEXT="${1:-先前进两步，然后右转，再做 tpose，最后停止。}"
CONDA_ENV="${CONDA_ENV:-lerobot-g1}"
CONTROLLER="${LEROBOT_G1_CONTROLLER:-HolosomaLocomotionController}"
PYTHON_BIN="${LEROBOT_G1_PYTHON:-mjpython}"
HEADLESS_FLAG="${LEROBOT_G1_HEADLESS:-0}"

echo "[lerobot-g1-demo] task: $TASK_TEXT"
echo "[lerobot-g1-demo] generating humanoid plan via OpenClaw..."
PLAN_JSON="$(python3 examples/claw_text_to_humanoid_plan.py --text "$TASK_TEXT")"
echo "[lerobot-g1-demo] plan=$PLAN_JSON"

echo "[lerobot-g1-demo] executing plan on LeRobot Unitree G1 MuJoCo sim..."
CMD=(
  conda run -n "$CONDA_ENV" "$PYTHON_BIN" examples/lerobot_g1_sim_backend.py
  --config config/clawros_config.yaml
  --controller "$CONTROLLER"
  --plan-json "$PLAN_JSON"
)

if [ "$HEADLESS_FLAG" = "1" ]; then
  CMD+=(--headless)
fi

CYCLONEDDS_HOME=/opt/anaconda3/envs/$CONDA_ENV \
CMAKE_PREFIX_PATH=/opt/anaconda3/envs/$CONDA_ENV \
"${CMD[@]}"

echo "[lerobot-g1-demo] done."
