#!/usr/bin/env python3
import argparse
import json
import time
from typing import Any, List

import roslibpy


def publish_twist(topic: roslibpy.Topic, linear: float, angular: float) -> None:
    topic.publish(
        roslibpy.Message(
            {
                "linear": {"x": linear, "y": 0.0, "z": 0.0},
                "angular": {"x": 0.0, "y": 0.0, "z": angular},
            }
        )
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan-json", required=True, help="humanoid plan json array")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9090)
    args = parser.parse_args()

    plan: List[Any] = json.loads(args.plan_json)
    if not isinstance(plan, list) or not plan:
        print("invalid plan")
        return 1

    ros = roslibpy.Ros(host=args.host, port=args.port)
    ros.run(timeout=5)
    if not ros.is_connected:
        print("rosbridge not connected")
        return 2

    cmd_vel = roslibpy.Topic(ros, "/cmd_vel", "geometry_msgs/msg/Twist")
    gait_cmd = roslibpy.Topic(ros, "/humanoid/gait_cmd", "std_msgs/msg/String")
    body_cmd = roslibpy.Topic(ros, "/humanoid/whole_body_cmd", "std_msgs/msg/String")

    for step in plan:
        if not isinstance(step, dict):
            continue
        typ = str(step.get("type", "")).lower()
        seconds = float(step.get("seconds", 1.0))
        if typ == "walk":
            linear = float(step.get("linear", 0.2))
            angular = float(step.get("angular", 0.0))
            gait_cmd.publish(
                roslibpy.Message(
                    {
                        "data": json.dumps(
                            {"gait": "walk", "linear": linear, "angular": angular}
                        )
                    }
                )
            )
            publish_twist(cmd_vel, linear, angular)
            print(f"walk linear={linear} angular={angular} for {seconds}s")
            time.sleep(max(0.1, seconds))
            publish_twist(cmd_vel, 0.0, 0.0)
        elif typ == "pose":
            posture = str(step.get("posture", "stand"))
            body_cmd.publish(
                roslibpy.Message({"data": json.dumps({"posture": posture})})
            )
            print(f"pose {posture} for {seconds}s")
            time.sleep(max(0.1, seconds))
        elif typ == "stop":
            gait_cmd.publish(
                roslibpy.Message({"data": json.dumps({"gait": "idle", "linear": 0.0, "angular": 0.0})})
            )
            publish_twist(cmd_vel, 0.0, 0.0)
            print(f"stop for {seconds}s")
            time.sleep(max(0.1, seconds))

    # final safety stop
    gait_cmd.publish(
        roslibpy.Message({"data": json.dumps({"gait": "idle", "linear": 0.0, "angular": 0.0})})
    )
    publish_twist(cmd_vel, 0.0, 0.0)
    ros.terminate()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
