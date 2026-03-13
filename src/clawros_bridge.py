#!/usr/bin/env python3
"""
ClawROS Bridge - 连接 OpenClaw 和 ROS 的核心桥接模块

This module provides the main bridge between OpenClaw AI assistant
and ROS (Robot Operating System) for natural language robot control.
"""

from __future__ import annotations

import asyncio
import logging
import math
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Type, Union

try:
    import rclpy
    from rclpy.node import Node
    from rclpy.publisher import Publisher
    from rclpy.subscription import Subscription
    from rclpy.client import Client
    from rclpy.action_client import ActionClient
    ROS2_AVAILABLE = True
except ImportError:
    ROS2_AVAILABLE = False
    rclpy = None
    Node = object

logger = logging.getLogger(__name__)


class ROSVersion(Enum):
    """ROS 版本枚举"""
    ROS1 = "ros1"
    ROS2 = "ros2"


class RuntimeMode(Enum):
    """运行模式枚举"""
    ROS_DIRECT = "ros_direct"
    ROS_GAZEBO = "ros_gazebo"
    SIMPLE_SIM = "simple_sim"
    HUMANOID_SIM = "humanoid_sim"
    LEROBOT_UNITREE_G1 = "lerobot_unitree_g1"


class CommandType(Enum):
    """命令类型枚举"""
    MOVE = "move"
    NAVIGATE = "navigate"
    MANIPULATE = "manipulate"
    SENSOR = "sensor"
    CUSTOM = "custom"
    EMERGENCY_STOP = "emergency_stop"


@dataclass
class ROSCommand:
    """ROS 命令数据类"""
    type: CommandType
    target: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    priority: int = 0
    timeout: float = 30.0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "type": self.type.value,
            "target": self.target,
            "parameters": self.parameters,
            "priority": self.priority,
            "timeout": self.timeout,
        }


@dataclass
class ROSResponse:
    """ROS 响应数据类"""
    success: bool
    message: str
    data: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def success_response(cls, message: str, data: Optional[Dict] = None) -> "ROSResponse":
        """创建成功响应"""
        return cls(success=True, message=message, data=data or {})
    
    @classmethod
    def error_response(cls, message: str) -> "ROSResponse":
        """创建错误响应"""
        return cls(success=False, message=message)


class ROSAdapter:
    """
    ROS 适配器 - 抽象 ROS1 和 ROS2 的差异
    
    当前仅支持 ROS2，预留 ROS1 支持接口
    """
    
    def __init__(self, version: ROSVersion = ROSVersion.ROS2):
        self.version = version
        self.node = None
        self.publishers: Dict[str, Publisher] = {}
        self.subscriptions: Dict[str, Subscription] = {}
        self.clients: Dict[str, Client] = {}
        self.action_clients: Dict[str, ActionClient] = {}
        
        if version == ROSVersion.ROS2 and ROS2_AVAILABLE:
            logger.info("Initializing ROS2 adapter")
        elif version == ROSVersion.ROS1:
            logger.warning("ROS1 support is planned but not yet implemented")
        else:
            logger.warning("ROS2 not available, running in simulation mode")
    
    def initialize(self, node_name: str = "clawros_node") -> bool:
        """初始化 ROS 节点"""
        if self.version == ROSVersion.ROS2 and ROS2_AVAILABLE:
            try:
                rclpy.init()
                self.node = rclpy.create_node(node_name)
                logger.info(f"ROS2 node '{node_name}' initialized")
                return True
            except Exception as e:
                logger.error(f"Failed to initialize ROS2 node: {e}")
                return False
        else:
            logger.warning("Running in simulation mode - no real ROS connection")
            return True
    
    def shutdown(self) -> None:
        """关闭 ROS 连接"""
        if self.node and ROS2_AVAILABLE:
            self.node.destroy_node()
            rclpy.shutdown()
            logger.info("ROS2 node shutdown")
    
    def create_publisher(self, topic: str, msg_type: Type) -> Optional[Publisher]:
        """创建发布者"""
        if not self.node:
            logger.error("ROS node not initialized")
            return None
        
        if topic not in self.publishers:
            try:
                publisher = self.node.create_publisher(msg_type, topic, 10)
                self.publishers[topic] = publisher
                logger.info(f"Publisher created for topic: {topic}")
                return publisher
            except Exception as e:
                logger.error(f"Failed to create publisher for {topic}: {e}")
                return None
        return self.publishers[topic]
    
    def create_subscriber(
        self, 
        topic: str, 
        msg_type: Type, 
        callback: Callable
    ) -> Optional[Subscription]:
        """创建订阅者"""
        if not self.node:
            logger.error("ROS node not initialized")
            return None
        
        if topic not in self.subscriptions:
            try:
                subscription = self.node.create_subscription(
                    msg_type, topic, callback, 10
                )
                self.subscriptions[topic] = subscription
                logger.info(f"Subscription created for topic: {topic}")
                return subscription
            except Exception as e:
                logger.error(f"Failed to create subscription for {topic}: {e}")
                return None
        return self.subscriptions[topic]
    
    def create_service_client(
        self, 
        service: str, 
        srv_type: Type
    ) -> Optional[Client]:
        """创建服务客户端"""
        if not self.node:
            logger.error("ROS node not initialized")
            return None
        
        if service not in self.clients:
            try:
                client = self.node.create_client(srv_type, service)
                self.clients[service] = client
                logger.info(f"Service client created for: {service}")
                return client
            except Exception as e:
                logger.error(f"Failed to create service client for {service}: {e}")
                return None
        return self.clients[service]
    
    def spin_once(self) -> None:
        """执行一次 ROS 回调处理"""
        if self.node and ROS2_AVAILABLE:
            rclpy.spin_once(self.node, timeout_sec=0.01)


class SecurityLayer:
    """
    安全层 - 验证所有 ROS 命令的安全性
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.enabled = self.config.get("enabled", True)
        self.max_linear_velocity = self.config.get("max_linear_velocity", 0.5)
        self.max_angular_velocity = self.config.get("max_angular_velocity", 1.0)
        self.workspace_bounds = self.config.get("workspace_bounds", {})
        self.rate_limit = self.config.get("rate_limit", {})
        
        self.command_count = 0
        self.last_reset_time = asyncio.get_event_loop().time()
    
    def validate_command(self, command: ROSCommand) -> tuple[bool, str]:
        """
        验证命令的安全性
        
        Returns:
            (is_valid, error_message)
        """
        if not self.enabled:
            return True, ""
        
        # 检查速率限制
        if not self._check_rate_limit():
            return False, "Rate limit exceeded"
        
        # 根据命令类型进行特定验证
        if command.type == CommandType.MOVE:
            return self._validate_move_command(command)
        elif command.type == CommandType.NAVIGATE:
            return self._validate_navigate_command(command)
        elif command.type == CommandType.MANIPULATE:
            return self._validate_manipulate_command(command)
        
        return True, ""
    
    def _check_rate_limit(self) -> bool:
        """检查速率限制"""
        current_time = asyncio.get_event_loop().time()
        max_commands = self.rate_limit.get("commands_per_minute", 60)
        
        # 每分钟重置计数器
        if current_time - self.last_reset_time > 60:
            self.command_count = 0
            self.last_reset_time = current_time
        
        if self.command_count >= max_commands:
            return False
        
        self.command_count += 1
        return True
    
    def _validate_move_command(self, command: ROSCommand) -> tuple[bool, str]:
        """验证移动命令"""
        params = command.parameters
        
        # 检查速度限制
        linear = params.get("linear", 0.0)
        angular = params.get("angular", 0.0)
        
        if abs(linear) > self.max_linear_velocity:
            return False, f"Linear velocity {linear} exceeds max {self.max_linear_velocity}"
        
        if abs(angular) > self.max_angular_velocity:
            return False, f"Angular velocity {angular} exceeds max {self.max_angular_velocity}"
        
        return True, ""
    
    def _validate_navigate_command(self, command: ROSCommand) -> tuple[bool, str]:
        """验证导航命令"""
        params = command.parameters
        
        # 检查工作空间边界
        if self.workspace_bounds:
            x = params.get("x", 0.0)
            y = params.get("y", 0.0)
            z = params.get("z", 0.0)
            
            x_bounds = self.workspace_bounds.get("x", [-float('inf'), float('inf')])
            y_bounds = self.workspace_bounds.get("y", [-float('inf'), float('inf')])
            z_bounds = self.workspace_bounds.get("z", [-float('inf'), float('inf')])
            
            if not (x_bounds[0] <= x <= x_bounds[1]):
                return False, f"X coordinate {x} outside bounds {x_bounds}"
            
            if not (y_bounds[0] <= y <= y_bounds[1]):
                return False, f"Y coordinate {y} outside bounds {y_bounds}"
            
            if not (z_bounds[0] <= z <= z_bounds[1]):
                return False, f"Z coordinate {z} outside bounds {z_bounds}"
        
        return True, ""
    
    def _validate_manipulate_command(self, command: ROSCommand) -> tuple[bool, str]:
        """验证操作命令"""
        # 添加机械臂特定的安全验证
        return True, ""


class StateMonitor:
    """
    状态监控器 - 监控 ROS 系统状态
    """
    
    def __init__(self, adapter: ROSAdapter):
        self.adapter = adapter
        self.state: Dict[str, Any] = {
            "position": {"x": 0.0, "y": 0.0, "z": 0.0},
            "orientation": {"x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0},
            "velocity": {"linear": 0.0, "angular": 0.0},
            "battery": 100.0,
            "status": "idle",
            "sensors": {},
        }
        self.callbacks: List[Callable] = []
    
    def start_monitoring(self) -> None:
        """开始监控"""
        logger.info("State monitoring started")
        # 实际实现会订阅 ROS 话题
    
    def stop_monitoring(self) -> None:
        """停止监控"""
        logger.info("State monitoring stopped")
    
    def get_state(self) -> Dict[str, Any]:
        """获取当前状态"""
        return self.state.copy()
    
    def add_state_callback(self, callback: Callable) -> None:
        """添加状态变更回调"""
        self.callbacks.append(callback)
    
    def _update_state(self, new_state: Dict[str, Any]) -> None:
        """更新状态并通知回调"""
        self.state.update(new_state)
        for callback in self.callbacks:
            try:
                callback(self.state)
            except Exception as e:
                logger.error(f"Error in state callback: {e}")


class ClawROSBridge:
    """
    ClawROS 核心桥接类
    
    这是 OpenClaw 和 ROS 之间的主要接口
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.ros_version = ROSVersion(
            self.config.get("ros_version", "ros2")
        )
        self.adapter = ROSAdapter(self.ros_version)
        self.security = SecurityLayer(self.config.get("safety", {}))
        self.state_monitor = StateMonitor(self.adapter)
        self.initialized = False
    
    def initialize(self) -> bool:
        """初始化桥接"""
        logger.info("Initializing ClawROS Bridge")
        
        if not self.adapter.initialize():
            logger.error("Failed to initialize ROS adapter")
            return False
        
        self.state_monitor.start_monitoring()
        self.initialized = True
        logger.info("ClawROS Bridge initialized successfully")
        return True
    
    def shutdown(self) -> None:
        """关闭桥接"""
        logger.info("Shutting down ClawROS Bridge")
        self.state_monitor.stop_monitoring()
        self.adapter.shutdown()
        self.initialized = False
    
    def execute_command(self, command: ROSCommand) -> ROSResponse:
        """
        执行 ROS 命令
        
        Args:
            command: ROS 命令对象
            
        Returns:
            ROSResponse: 执行结果
        """
        if not self.initialized:
            return ROSResponse.error_response("Bridge not initialized")
        
        # 安全验证
        is_valid, error_msg = self.security.validate_command(command)
        if not is_valid:
            logger.warning(f"Command failed security validation: {error_msg}")
            return ROSResponse.error_response(f"Security violation: {error_msg}")
        
        logger.info(f"Executing command: {command.type.value} -> {command.target}")
        
        try:
            # 根据命令类型执行不同操作
            if command.type == CommandType.EMERGENCY_STOP:
                return self._emergency_stop()
            elif command.type == CommandType.MOVE:
                return self._move(command)
            elif command.type == CommandType.NAVIGATE:
                return self._navigate(command)
            elif command.type == CommandType.MANIPULATE:
                return self._manipulate(command)
            elif command.type == CommandType.SENSOR:
                return self._get_sensor_data(command)
            else:
                return ROSResponse.error_response(f"Unknown command type: {command.type}")
        
        except Exception as e:
            logger.error(f"Command execution error: {e}")
            return ROSResponse.error_response(f"Execution error: {str(e)}")
    
    def _emergency_stop(self) -> ROSResponse:
        """紧急停止"""
        logger.warning("EMERGENCY STOP TRIGGERED")
        # 发布零速度命令
        if self.adapter.node:
            from geometry_msgs.msg import Twist, Vector3
            cmd_vel_topic = self.config.get("topics", {}).get("cmd_vel", "/cmd_vel")
            pub = self.adapter.create_publisher(cmd_vel_topic, Twist)
            if pub:
                pub.publish(Twist(linear=Vector3(), angular=Vector3()))
        return ROSResponse.success_response("Emergency stop executed")
    
    def _move(self, command: ROSCommand) -> ROSResponse:
        """移动命令"""
        # 实现移动逻辑
        return ROSResponse.success_response(
            f"Move command executed: {command.target}",
            command.to_dict()
        )
    
    def _navigate(self, command: ROSCommand) -> ROSResponse:
        """导航命令"""
        # 实现导航逻辑
        return ROSResponse.success_response(
            f"Navigate command executed: {command.target}",
            command.to_dict()
        )
    
    def _manipulate(self, command: ROSCommand) -> ROSResponse:
        """操作命令"""
        # 实现机械臂操作逻辑
        return ROSResponse.success_response(
            f"Manipulate command executed: {command.target}",
            command.to_dict()
        )
    
    def _get_sensor_data(self, command: ROSCommand) -> ROSResponse:
        """获取传感器数据"""
        sensor_type = command.target
        # 实现传感器数据读取逻辑
        return ROSResponse.success_response(
            f"Sensor data retrieved: {sensor_type}",
            {"sensor_type": sensor_type, "data": {}}
        )
    
    def get_robot_state(self) -> Dict[str, Any]:
        """获取机器人状态"""
        return self.state_monitor.get_state()
    
    def register_tool(self, name: str, func: Callable) -> None:
        """注册自定义工具"""
        logger.info(f"Registering custom tool: {name}")
        # 实现工具注册逻辑


class ROSGazeboBridge(ClawROSBridge):
    """
    ROS + Gazebo 模式桥接骨架

    说明:
    - 该类提供 ros_gazebo 运行模式的统一入口
    - 目前为骨架实现，真实导航/传感器回调可在此基础上补齐
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config=config)
        runtime_cfg = self.config.get("runtime", {})
        self.gazebo_cfg = runtime_cfg.get("ros_gazebo", {})
        self.topics = self.config.get("topics", {})
        self.services = self.config.get("services", {})
        self.actions = self.config.get("actions", {})

    def initialize(self) -> bool:
        logger.info("Initializing ClawROS Bridge in ros_gazebo mode")
        ok = super().initialize()
        if not ok:
            return False

        world = self.gazebo_cfg.get("world", "empty.sdf")
        robot_model = self.gazebo_cfg.get("robot_model", "turtlebot3_waffle")
        use_sim_time = self.gazebo_cfg.get("use_sim_time", True)
        logger.info(
            "ROS Gazebo context: world=%s robot_model=%s use_sim_time=%s",
            world,
            robot_model,
            use_sim_time,
        )
        return True

    def _move(self, command: ROSCommand) -> ROSResponse:
        params = command.parameters
        linear = float(params.get("linear", params.get("speed", 0.3)))
        angular = float(params.get("angular", 0.0))
        cmd_vel_topic = self.topics.get("cmd_vel", "/cmd_vel")

        if self.adapter.node and ROS2_AVAILABLE:
            try:
                from geometry_msgs.msg import Twist

                pub = self.adapter.create_publisher(cmd_vel_topic, Twist)
                if not pub:
                    return ROSResponse.error_response(
                        f"Failed to create publisher for {cmd_vel_topic}"
                    )

                msg = Twist()
                msg.linear.x = linear
                msg.angular.z = angular
                pub.publish(msg)
            except Exception as e:
                return ROSResponse.error_response(
                    f"ros_gazebo move publish failed: {e}"
                )

        return ROSResponse.success_response(
            f"[ros_gazebo] velocity command sent to {cmd_vel_topic}",
            {"linear": linear, "angular": angular},
        )

    def _navigate(self, command: ROSCommand) -> ROSResponse:
        nav_action = self.actions.get("navigation", "/navigate")
        nav_service = self.services.get("navigation", "/navigate_to_pose")
        params = command.parameters
        return ROSResponse.success_response(
            f"[ros_gazebo] navigation request accepted via action={nav_action} service={nav_service}",
            {"target": command.target, "parameters": params},
        )

    def _get_sensor_data(self, command: ROSCommand) -> ROSResponse:
        sensor_type = command.target
        topic_map = {
            "lidar": self.topics.get("scan", "/scan"),
            "camera": self.topics.get("camera", "/camera/image_raw"),
            "battery": self.topics.get("battery", "/battery_state"),
            "odom": self.topics.get("odom", "/odom"),
        }
        sensor_topic = topic_map.get(sensor_type, f"/{sensor_type}")
        return ROSResponse.success_response(
            f"[ros_gazebo] sensor endpoint ready: {sensor_type}",
            {"sensor_type": sensor_type, "topic": sensor_topic},
        )

    def get_robot_state(self) -> Dict[str, Any]:
        state = super().get_robot_state()
        state["runtime_mode"] = RuntimeMode.ROS_GAZEBO.value
        state["sim_time"] = bool(self.gazebo_cfg.get("use_sim_time", True))
        return state


class HumanoidSimBridge(ClawROSBridge):
    """
    人形机器人仿真模式桥接骨架

    目标:
    - 统一承载步态/足步/双臂/全身姿态等高层控制语义
    - 为后续接入 ros2_control / MoveIt2 / Isaac / MuJoCo 提供接口层
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config=config)
        runtime_cfg = self.config.get("runtime", {})
        self.humanoid_cfg = runtime_cfg.get("humanoid_sim", {})
        self.topics = self.config.get("topics", {})
        self.services = self.config.get("services", {})
        self.actions = self.config.get("actions", {})
        self.joint_names: List[str] = list(
            self.humanoid_cfg.get(
                "joint_names",
                [
                    "left_hip_yaw",
                    "left_hip_roll",
                    "left_hip_pitch",
                    "left_knee",
                    "right_hip_yaw",
                    "right_hip_roll",
                    "right_hip_pitch",
                    "right_knee",
                    "waist_yaw",
                    "left_shoulder_pitch",
                    "right_shoulder_pitch",
                    "head_yaw",
                ],
            )
        )
        self.joint_positions: Dict[str, float] = {name: 0.0 for name in self.joint_names}
        self.current_pose = "stand"
        self.gait_mode = "idle"
        self.last_linear = 0.0
        self.last_angular = 0.0
        self.gait_phase = 0.0
        self.last_update_ts = time.time()

    def initialize(self) -> bool:
        logger.info("Initializing ClawROS Bridge in humanoid_sim mode")
        ok = super().initialize()
        if not ok:
            return False

        model = self.humanoid_cfg.get("robot_model", "generic_humanoid")
        stack = self.humanoid_cfg.get("controller_stack", "ros2_control")
        planners = self.humanoid_cfg.get("planners", ["footstep", "whole_body", "arm"])
        logger.info(
            "Humanoid sim context: model=%s stack=%s planners=%s",
            model,
            stack,
            planners,
        )
        return True

    def _move(self, command: ROSCommand) -> ROSResponse:
        params = command.parameters
        linear = float(params.get("linear", params.get("speed", 0.2)))
        angular = float(params.get("angular", 0.0))
        gait = str(params.get("gait", self.humanoid_cfg.get("default_gait", "walk")))
        self.gait_mode = gait
        self.last_linear = linear
        self.last_angular = angular

        gait_topic = self.topics.get("gait_cmd", "/humanoid/gait_cmd")
        whole_body_topic = self.topics.get("whole_body_cmd", "/humanoid/whole_body_cmd")

        # 骨架模拟：根据速度更新关键关节的示意值（非真实动力学）
        amp = max(0.0, min(0.6, abs(linear) + abs(angular) * 0.4))
        self.joint_positions["left_hip_pitch"] = amp
        self.joint_positions["right_hip_pitch"] = -amp
        self.joint_positions["left_knee"] = -amp * 0.7
        self.joint_positions["right_knee"] = amp * 0.7
        self.joint_positions["waist_yaw"] = max(-0.4, min(0.4, angular))

        return ROSResponse.success_response(
            f"[humanoid_sim] gait command accepted ({gait})",
            {
                "linear": linear,
                "angular": angular,
                "gait": gait,
                "topics": {
                    "gait_cmd": gait_topic,
                    "whole_body_cmd": whole_body_topic,
                },
            },
        )

    def _navigate(self, command: ROSCommand) -> ROSResponse:
        params = command.parameters
        footstep_action = self.actions.get("footstep_navigation", "/humanoid/follow_footsteps")
        nav_action = self.actions.get("navigation", "/navigate")
        footstep_service = self.services.get("footstep_plan", "/humanoid/plan_footsteps")
        return ROSResponse.success_response(
            "[humanoid_sim] footstep navigation request accepted",
            {
                "target": command.target,
                "parameters": params,
                "action": footstep_action,
                "fallback_navigation_action": nav_action,
                "planning_service": footstep_service,
            },
        )

    def _manipulate(self, command: ROSCommand) -> ROSResponse:
        params = command.parameters
        arm = str(params.get("arm", "both"))
        posture = str(params.get("posture", "stand"))
        self.current_pose = posture

        left_arm_action = self.actions.get("left_arm_trajectory", "/humanoid/left_arm/follow_joint_trajectory")
        right_arm_action = self.actions.get("right_arm_trajectory", "/humanoid/right_arm/follow_joint_trajectory")
        whole_body_action = self.actions.get("whole_body", "/humanoid/whole_body_control")

        if posture == "stand":
            self.joint_positions["waist_yaw"] = 0.0
            self.joint_positions["left_shoulder_pitch"] = 0.0
            self.joint_positions["right_shoulder_pitch"] = 0.0
        elif posture == "tpose":
            self.joint_positions["left_shoulder_pitch"] = -1.2
            self.joint_positions["right_shoulder_pitch"] = 1.2
        elif posture == "crouch":
            self.joint_positions["left_knee"] = -0.9
            self.joint_positions["right_knee"] = 0.9

        return ROSResponse.success_response(
            "[humanoid_sim] manipulation request accepted",
            {
                "arm": arm,
                "posture": posture,
                "target": command.target,
                "parameters": params,
                "actions": {
                    "left_arm": left_arm_action,
                    "right_arm": right_arm_action,
                    "whole_body": whole_body_action,
                },
            },
        )

    def _get_sensor_data(self, command: ROSCommand) -> ROSResponse:
        sensor_type = command.target
        topic_map = {
            "imu": self.topics.get("imu", "/imu/data"),
            "force_torque": self.topics.get("foot_force", "/humanoid/foot_force"),
            "camera": self.topics.get("camera", "/camera/image_raw"),
            "lidar": self.topics.get("scan", "/scan"),
            "joint_states": self.topics.get("joint_states", "/joint_states"),
            "odom": self.topics.get("odom", "/odom"),
        }
        sensor_topic = topic_map.get(sensor_type, f"/{sensor_type}")
        return ROSResponse.success_response(
            f"[humanoid_sim] sensor endpoint ready: {sensor_type}",
            {"sensor_type": sensor_type, "topic": sensor_topic},
        )

    def _emergency_stop(self) -> ROSResponse:
        self.gait_mode = "idle"
        self.last_linear = 0.0
        self.last_angular = 0.0
        for name in self.joint_positions:
            self.joint_positions[name] = 0.0
        return ROSResponse.success_response("[humanoid_sim] emergency stop executed")

    def get_robot_state(self) -> Dict[str, Any]:
        now = time.time()
        dt = max(0.0, now - self.last_update_ts)
        self.last_update_ts = now

        if self.gait_mode != "idle":
            speed_scale = max(0.2, min(1.5, abs(self.last_linear) * 3.0 + abs(self.last_angular)))
            self.gait_phase += dt * speed_scale * 3.2
            swing = math.sin(self.gait_phase) * 0.45
            self.joint_positions["left_hip_pitch"] = swing
            self.joint_positions["right_hip_pitch"] = -swing
            self.joint_positions["left_knee"] = -swing * 0.8
            self.joint_positions["right_knee"] = swing * 0.8
            self.joint_positions["left_shoulder_pitch"] = -swing * 0.5
            self.joint_positions["right_shoulder_pitch"] = swing * 0.5

        state = super().get_robot_state()
        state["runtime_mode"] = RuntimeMode.HUMANOID_SIM.value
        state["humanoid"] = {
            "robot_model": self.humanoid_cfg.get("robot_model", "generic_humanoid"),
            "gait_mode": self.gait_mode,
            "pose": self.current_pose,
            "joint_positions": self.joint_positions.copy(),
            "controller_stack": self.humanoid_cfg.get("controller_stack", "ros2_control"),
        }
        return state


class LeRobotUnitreeG1Bridge(HumanoidSimBridge):
    """
    LeRobot Unitree G1 集成桥接骨架

    目标:
    - 复用 humanoid 高层语义接口
    - 映射到 LeRobot 的 Unitree G1 sim / remote / real-robot 工作流
    - 为后续接入 run_g1_server、MuJoCo sim、policy inference 预留配置入口
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config=config)
        runtime_cfg = self.config.get("runtime", {})
        self.lerobot_cfg = runtime_cfg.get("lerobot_unitree_g1", {})

    def initialize(self) -> bool:
        logger.info("Initializing ClawROS Bridge in lerobot_unitree_g1 mode")
        ok = super().initialize()
        if not ok:
            return False

        logger.info(
            "LeRobot Unitree G1 context: simulation=%s profile=%s teleop=%s policy=%s",
            self.lerobot_cfg.get("is_simulation", True),
            self.lerobot_cfg.get("robot_profile", "g1_29dof"),
            self.lerobot_cfg.get("teleop_id", "wbc_unitree"),
            self.lerobot_cfg.get("policy", "none"),
        )
        return True

    def get_robot_state(self) -> Dict[str, Any]:
        state = super().get_robot_state()
        state["runtime_mode"] = RuntimeMode.LEROBOT_UNITREE_G1.value
        state["lerobot"] = {
            "robot_type": "unitree_g1",
            "is_simulation": bool(self.lerobot_cfg.get("is_simulation", True)),
            "robot_profile": self.lerobot_cfg.get("robot_profile", "g1_29dof"),
            "teleop_id": self.lerobot_cfg.get("teleop_id", "wbc_unitree"),
            "policy": self.lerobot_cfg.get("policy", "none"),
            "server": {
                "host": self.lerobot_cfg.get("server_host", "127.0.0.1"),
                "lowcmd_port": int(self.lerobot_cfg.get("lowcmd_port", 6000)),
                "lowstate_port": int(self.lerobot_cfg.get("lowstate_port", 6001)),
                "video_port": int(self.lerobot_cfg.get("video_port", 5555)),
            },
        }
        state["humanoid"]["robot_model"] = "unitree_g1"
        state["humanoid"]["controller_stack"] = "lerobot"
        return state


def _load_config(config_source: Optional[Union[str, Dict[str, Any]]]) -> Dict[str, Any]:
    """加载配置，支持配置路径或配置字典。"""
    if not config_source:
        return {}

    if isinstance(config_source, dict):
        return config_source

    if isinstance(config_source, str):
        import yaml

        try:
            with open(config_source, "r") as f:
                config = yaml.safe_load(f) or {}
                logger.info(f"Loaded configuration from {config_source}")
                return config
        except Exception as e:
            logger.warning(f"Failed to load config: {e}, using defaults")
            return {}

    logger.warning("Unsupported config source type: %s", type(config_source))
    return {}


def _resolve_runtime_mode(config: Dict[str, Any], mode: Optional[str]) -> RuntimeMode:
    """解析运行模式。"""
    mode_value = mode or config.get("runtime", {}).get("mode") or RuntimeMode.ROS_DIRECT.value
    try:
        return RuntimeMode(mode_value)
    except Exception:
        logger.warning("Unknown runtime mode '%s', fallback to ros_direct", mode_value)
        return RuntimeMode.ROS_DIRECT


def create_bridge(
    config_path: Optional[Union[str, Dict[str, Any]]] = None,
    mode: Optional[str] = None,
) -> Any:
    """
    创建 ClawROS 桥接实例的工厂函数
    
    Args:
        config_path: 配置文件路径或配置字典
        mode: 显式运行模式（ros_direct/ros_gazebo/simple_sim/humanoid_sim/lerobot_unitree_g1），优先级高于配置文件
        
    Returns:
        桥接实例（根据运行模式返回不同实现）
    """
    config = _load_config(config_path)
    runtime_mode = _resolve_runtime_mode(config, mode)

    if runtime_mode == RuntimeMode.SIMPLE_SIM:
        try:
            from simple_simulator import create_simulated_bridge
        except ImportError:
            from .simple_simulator import create_simulated_bridge
        return create_simulated_bridge()

    if runtime_mode == RuntimeMode.ROS_GAZEBO:
        return ROSGazeboBridge(config)

    if runtime_mode == RuntimeMode.HUMANOID_SIM:
        return HumanoidSimBridge(config)

    if runtime_mode == RuntimeMode.LEROBOT_UNITREE_G1:
        return LeRobotUnitreeG1Bridge(config)

    return ClawROSBridge(config)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    bridge = create_bridge()
    if bridge.initialize():
        print("ClawROS Bridge initialized successfully!")
        
        test_command = ROSCommand(
            type=CommandType.MOVE,
            target="forward",
            parameters={"linear": 0.3, "angular": 0.0}
        )
        
        response = bridge.execute_command(test_command)
        print(f"Command response: {response.success} - {response.message}")
        
        bridge.shutdown()
    else:
        print("Failed to initialize ClawROS Bridge")
