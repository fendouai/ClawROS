#!/usr/bin/env python3
"""
LeRobot Unitree G1 MuJoCo sim backend adapter.

This adapter maps a minimal humanoid command vocabulary onto the official
LeRobot v0.5.0 UnitreeG1 simulation backend:

- walk(linear, angular, seconds) -> remote axes for locomotion controller
- pose(posture, seconds) -> upper-body joint targets
- stop(seconds) -> zero remote axes
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import sys
import time
from math import cos, sin
from dataclasses import dataclass
from typing import Any

import yaml


def _append_configured_lerobot_path(config_path: str) -> None:
    try:
        with open(config_path, "r") as f:
            cfg = yaml.safe_load(f) or {}
    except Exception:
        return

    repo = (
        cfg.get("runtime", {})
        .get("lerobot_unitree_g1", {})
        .get("lerobot_repo", "")
    )
    if not repo:
        return

    repo = os.path.expanduser(str(repo))
    src_path = os.path.join(repo, "src")
    for path in (repo, src_path):
        if os.path.isdir(path) and path not in sys.path:
            sys.path.insert(0, path)


@dataclass
class BackendConfig:
    config_path: str
    controller: str = "HolosomaLocomotionController"
    is_simulation: bool = True
    headless: bool = False
    publish_visual: bool = False
    rosbridge_host: str = "127.0.0.1"
    rosbridge_port: int = 9090


class RosbridgeVisualPublisher:
    def __init__(self, host: str, port: int):
        import roslibpy

        self.roslibpy = roslibpy
        self.ros = roslibpy.Ros(host=host, port=port)
        self.ros.run(timeout=5)
        if not self.ros.is_connected:
            raise RuntimeError(f"rosbridge not connected on {host}:{port}")

        self.joint_topic = roslibpy.Topic(
            self.ros, "/joint_states", "sensor_msgs/msg/JointState"
        )
        self.odom_topic = roslibpy.Topic(
            self.ros, "/odom", "nav_msgs/msg/Odometry"
        )

        self.x = 0.0
        self.y = 0.0
        self.yaw = 0.0
        self.last_t = time.time()

    def _integrate_pose(self, linear: float, angular: float) -> None:
        now = time.time()
        dt = max(0.0, min(0.1, now - self.last_t))
        self.last_t = now
        self.yaw += angular * dt
        self.x += linear * dt * cos(self.yaw)
        self.y += linear * dt * sin(self.yaw)

    def publish(self, obs: dict[str, Any], linear: float, angular: float) -> None:
        self._integrate_pose(linear, angular)

        joint_map = {
            "left_hip_pitch": float(obs.get("kLeftHipPitch.q", 0.0)),
            "right_hip_pitch": float(obs.get("kRightHipPitch.q", 0.0)),
            "left_knee": float(obs.get("kLeftKnee.q", 0.0)),
            "right_knee": float(obs.get("kRightKnee.q", 0.0)),
            "waist_yaw": float(obs.get("kWaistYaw.q", 0.0)),
            "left_shoulder_pitch": float(obs.get("kLeftShoulderPitch.q", 0.0)),
            "right_shoulder_pitch": float(obs.get("kRightShoulderPitch.q", 0.0)),
        }

        self.joint_topic.publish(
            self.roslibpy.Message(
                {"name": list(joint_map.keys()), "position": list(joint_map.values())}
            )
        )

        odom = {
            "pose": {
                "pose": {
                    "position": {"x": self.x, "y": self.y, "z": 0.0},
                    "orientation": {
                        "x": 0.0,
                        "y": 0.0,
                        "z": sin(self.yaw / 2.0),
                        "w": cos(self.yaw / 2.0),
                    },
                }
            },
            "twist": {
                "twist": {
                    "linear": {"x": linear, "y": 0.0, "z": 0.0},
                    "angular": {"x": 0.0, "y": 0.0, "z": angular},
                }
            },
        }
        self.odom_topic.publish(self.roslibpy.Message(odom))

    def close(self) -> None:
        try:
            self.ros.terminate()
        except Exception:
            pass


class LeRobotG1SimBackend:
    def __init__(self, backend_cfg: BackendConfig):
        _append_configured_lerobot_path(backend_cfg.config_path)

        try:
            from lerobot.robots.unitree_g1.config_unitree_g1 import UnitreeG1Config
            from lerobot.robots.unitree_g1.unitree_g1 import UnitreeG1
            from huggingface_hub import snapshot_download
        except Exception as exc:
            raise RuntimeError(
                "LeRobot Unitree G1 backend unavailable. "
                "Expected lerobot v0.5.0 with unitree_g1 extras in the active Python environment."
            ) from exc

        self._UnitreeG1Config = UnitreeG1Config
        self._UnitreeG1 = UnitreeG1
        self._snapshot_download = snapshot_download
        self.backend_cfg = backend_cfg
        self.robot = None
        self.visual = None

    def _enable_headless_mode(self) -> None:
        repo_dir = self._snapshot_download("lerobot/unitree-g1-mujoco")
        config_file = os.path.join(repo_dir, "config.yaml")
        try:
            with open(config_file, "r") as f:
                config = yaml.safe_load(f) or {}
            config["ENABLE_ONSCREEN"] = False
            config["ENABLE_OFFSCREEN"] = False
            with open(config_file, "w") as f:
                yaml.safe_dump(config, f, sort_keys=False)
        except Exception:
            pass

        unitree_module = sys.modules.get(self._UnitreeG1.__module__)
        if unitree_module is not None and hasattr(unitree_module, "make_env"):
            original_make_env = unitree_module.make_env

            def _headless_make_env(*args: Any, **kwargs: Any) -> Any:
                return original_make_env(*args, **kwargs)

            unitree_module.make_env = _headless_make_env

    def connect(self) -> None:
        if self.robot is not None:
            return

        if self.backend_cfg.headless:
            self._enable_headless_mode()

        robot_cfg = self._UnitreeG1Config(
            is_simulation=self.backend_cfg.is_simulation,
            controller=self.backend_cfg.controller,
            cameras={},
            gravity_compensation=False,
        )
        self.robot = self._UnitreeG1(robot_cfg)

        if self.backend_cfg.is_simulation and platform.system() == "Darwin":
            original_factory = self.robot._ChannelFactoryInitialize

            def _macos_loopback_factory(domain_id: int, interface: str = "lo") -> Any:
                actual_interface = "lo0" if interface == "lo" else interface
                return original_factory(domain_id, actual_interface)

            self.robot._ChannelFactoryInitialize = _macos_loopback_factory

        self.robot.connect()
        if self.backend_cfg.publish_visual:
            self.visual = RosbridgeVisualPublisher(
                host=self.backend_cfg.rosbridge_host,
                port=self.backend_cfg.rosbridge_port,
            )

        # Give the controller thread time to receive initial lowstate.
        time.sleep(1.0)

    def disconnect(self) -> None:
        if self.robot is None:
            return
        if self.visual is not None:
            self.visual.close()
            self.visual = None
        self.robot.disconnect()
        self.robot = None

    def _ensure_robot(self) -> Any:
        if self.robot is None:
            raise RuntimeError("LeRobot G1 backend not connected")
        return self.robot

    def _send_action_for(self, action: dict[str, float], seconds: float) -> None:
        robot = self._ensure_robot()
        end_at = time.time() + max(0.05, seconds)
        while time.time() < end_at:
            robot.send_action(action)
            if self.visual is not None:
                obs = robot.get_observation()
                linear = float(action.get("remote.lx", 0.0))
                angular = float(action.get("remote.rx", 0.0))
                self.visual.publish(obs, linear=linear, angular=angular)
            time.sleep(0.05)

    def walk(self, linear: float, angular: float, seconds: float) -> None:
        # Holosoma/GROOT consume remote joystick-like axes.
        action = {
            "remote.lx": float(max(-0.3, min(0.3, linear))),
            "remote.ly": 0.0,
            "remote.rx": float(max(-0.3, min(0.3, angular))),
            "remote.ry": 0.0,
        }
        self._send_action_for(action, seconds)

    def stop(self, seconds: float = 1.0) -> None:
        self._send_action_for(
            {"remote.lx": 0.0, "remote.ly": 0.0, "remote.rx": 0.0, "remote.ry": 0.0},
            seconds,
        )

    def pose(self, posture: str, seconds: float) -> None:
        posture = posture.lower()
        if posture == "tpose":
            action = {
                "kLeftShoulderPitch.q": 0.0,
                "kLeftShoulderRoll.q": 1.25,
                "kLeftShoulderYaw.q": 0.0,
                "kLeftElbow.q": 0.0,
                "kRightShoulderPitch.q": 0.0,
                "kRightShoulderRoll.q": -1.25,
                "kRightShoulderYaw.q": 0.0,
                "kRightElbow.q": 0.0,
            }
        elif posture == "crouch":
            # Keep locomotion axes at zero and fold the arms slightly while knees remain controller-owned.
            action = {
                "kLeftShoulderPitch.q": 0.45,
                "kLeftShoulderRoll.q": 0.15,
                "kLeftElbow.q": 0.9,
                "kRightShoulderPitch.q": 0.45,
                "kRightShoulderRoll.q": -0.15,
                "kRightElbow.q": 0.9,
                "remote.lx": 0.0,
                "remote.ly": 0.0,
                "remote.rx": 0.0,
                "remote.ry": 0.0,
            }
        else:
            action = {
                "kLeftShoulderPitch.q": 0.2,
                "kLeftShoulderRoll.q": 0.2,
                "kLeftShoulderYaw.q": 0.0,
                "kLeftElbow.q": 0.6,
                "kRightShoulderPitch.q": 0.2,
                "kRightShoulderRoll.q": -0.2,
                "kRightShoulderYaw.q": 0.0,
                "kRightElbow.q": 0.6,
                "remote.lx": 0.0,
                "remote.ly": 0.0,
                "remote.rx": 0.0,
                "remote.ry": 0.0,
            }
        self._send_action_for(action, seconds)

    def execute_plan(self, plan: list[dict[str, Any]]) -> None:
        for step in plan:
            if not isinstance(step, dict):
                continue
            typ = str(step.get("type", "")).lower()
            seconds = float(step.get("seconds", 1.0))
            if typ == "walk":
                self.walk(
                    linear=float(step.get("linear", 0.15)),
                    angular=float(step.get("angular", 0.0)),
                    seconds=seconds,
                )
            elif typ == "pose":
                self.pose(str(step.get("posture", "stand")), seconds)
            elif typ == "stop":
                self.stop(seconds)

    def get_state_summary(self) -> dict[str, Any]:
        robot = self._ensure_robot()
        obs = robot.get_observation()
        keys = (
            "kLeftHipPitch.q",
            "kRightHipPitch.q",
            "kWaistYaw.q",
            "kLeftShoulderPitch.q",
            "kRightShoulderPitch.q",
            "imu.rpy.yaw",
        )
        return {k: obs.get(k) for k in keys if k in obs}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/clawros_config.yaml")
    parser.add_argument("--plan-json", required=True)
    parser.add_argument("--controller", default="HolosomaLocomotionController")
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--publish-visual", action="store_true")
    parser.add_argument("--rosbridge-host", default="127.0.0.1")
    parser.add_argument("--rosbridge-port", type=int, default=9090)
    args = parser.parse_args()

    plan = json.loads(args.plan_json)
    backend = LeRobotG1SimBackend(
        BackendConfig(
            config_path=args.config,
            controller=args.controller,
            headless=bool(args.headless),
            publish_visual=bool(args.publish_visual),
            rosbridge_host=args.rosbridge_host,
            rosbridge_port=args.rosbridge_port,
        )
    )
    backend.connect()
    try:
        backend.execute_plan(plan)
        print(json.dumps(backend.get_state_summary(), ensure_ascii=False))
    finally:
        backend.stop(0.2)
        backend.disconnect()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
