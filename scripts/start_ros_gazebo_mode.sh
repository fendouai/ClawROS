#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

CONFIG_PATH="${1:-config/clawros_config.yaml}"

echo "[ClawROS] using config: $CONFIG_PATH"
python examples/ros_gazebo_launcher.py --config "$CONFIG_PATH" --run-commands
