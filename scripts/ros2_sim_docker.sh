#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

COMPOSE_FILE="docker-compose.ros2-sim.yml"
SERVICE="ros2-sim"

usage() {
  cat <<'EOF'
Usage:
  scripts/ros2_sim_docker.sh build
  scripts/ros2_sim_docker.sh up
  scripts/ros2_sim_docker.sh down
  scripts/ros2_sim_docker.sh logs
  scripts/ros2_sim_docker.sh shell

Notes:
  - up: 启动 rosbridge(:9090) + mock Nav2 FollowWaypoints + /odom
  - shell: 进入容器后可执行 ros2 topic list / ros2 node list
EOF
}

cmd="${1:-}"
case "$cmd" in
  build)
    docker compose -f "$COMPOSE_FILE" build "$SERVICE"
    ;;
  up)
    docker compose -f "$COMPOSE_FILE" up -d "$SERVICE"
    ;;
  down)
    docker compose -f "$COMPOSE_FILE" down
    ;;
  logs)
    docker compose -f "$COMPOSE_FILE" logs -f "$SERVICE"
    ;;
  shell)
    docker compose -f "$COMPOSE_FILE" exec "$SERVICE" bash
    ;;
  *)
    usage
    exit 1
    ;;
esac
