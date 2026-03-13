#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

CONFIG_PATH="${1:-config/clawros_config.yaml}"

echo "[lerobot-g1] config: $CONFIG_PATH"
python3 examples/lerobot_unitree_g1_launcher.py --config "$CONFIG_PATH"
