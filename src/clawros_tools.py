#!/usr/bin/env python3
"""
ClawROS OpenClaw Tools - OpenClaw 可调用的 ROS 工具集

This module provides OpenClaw tools for controlling ROS robots
through natural language commands.
"""

import logging
from typing import Any, Dict, List, Optional

try:
    from .clawros_bridge import (
        ClawROSBridge, 
        ROSCommand, 
        CommandType,
        ROSResponse,
        create_bridge
    )
except ImportError:
    from clawros_bridge import (
        ClawROSBridge, 
        ROSCommand, 
        CommandType,
        ROSResponse,
        create_bridge
    )

logger = logging.getLogger(__name__)


class ClawROSTools:
    """
    OpenClaw Tools for ROS Control
    
    These tools can be registered with OpenClaw/ZeroClaw
    to enable natural language robot control.
    """
    
    def __init__(self, bridge: Optional[ClawROSBridge] = None, config: Optional[Dict] = None):
        """
        初始化工具集
        
        Args:
            bridge: ClawROS 桥接实例，如果为 None 则创建新的
            config: 配置字典
        """
        self.bridge = bridge or create_bridge(config)
        self.initialized = False
    
    def initialize(self) -> bool:
        """初始化工具"""
        if not self.initialized:
            self.initialized = self.bridge.initialize()
        return self.initialized
    
    def shutdown(self) -> None:
        """关闭工具"""
        self.bridge.shutdown()
        self.initialized = False
    
    def get_tools(self) -> List[Dict[str, Any]]:
        """
        获取工具列表（用于 OpenClaw 注册）
        
        Returns:
            工具定义列表
        """
        return [
            {
                "name": "move_to",
                "description": "Move the robot to a specified location or position",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "Target location name (e.g., 'kitchen', 'charging_station') or coordinates"
                        },
                        "speed": {
                            "type": "number",
                            "description": "Movement speed (0.0 to 1.0), default 0.5"
                        }
                    },
                    "required": ["location"]
                }
            },
            {
                "name": "navigate_to",
                "description": "Navigate to a specific coordinate with path planning",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "x": {"type": "number", "description": "X coordinate in meters"},
                        "y": {"type": "number", "description": "Y coordinate in meters"},
                        "theta": {"type": "number", "description": "Orientation in radians"}
                    },
                    "required": ["x", "y"]
                }
            },
            {
                "name": "pick_object",
                "description": "Pick up an object using the robot manipulator",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "object_name": {
                            "type": "string",
                            "description": "Name or description of the object to pick"
                        },
                        "grasp_force": {
                            "type": "number",
                            "description": "Grasping force (0.0 to 1.0), default 0.7"
                        }
                    },
                    "required": ["object_name"]
                }
            },
            {
                "name": "place_object",
                "description": "Place an object at a specified location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "Target location for placing the object"
                        },
                        "orientation": {
                            "type": "string",
                            "description": "Desired orientation of the placed object"
                        }
                    },
                    "required": ["location"]
                }
            },
            {
                "name": "get_sensor_data",
                "description": "Get data from robot sensors",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "sensor_type": {
                            "type": "string",
                            "description": "Type of sensor (camera, lidar, imu, battery, etc.)"
                        }
                    },
                    "required": ["sensor_type"]
                }
            },
            {
                "name": "execute_custom_command",
                "description": "Execute a custom ROS command (advanced users)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "command": {
                            "type": "string",
                            "description": "Custom command string"
                        },
                        "parameters": {
                            "type": "object",
                            "description": "Command parameters"
                        }
                    },
                    "required": ["command"]
                }
            },
            {
                "name": "emergency_stop",
                "description": "Emergency stop - immediately halt all robot motion",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "get_robot_state",
                "description": "Get current robot state including position, battery, and status",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "move_arm",
                "description": "Move robot arm to a specific pose",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "x": {"type": "number", "description": "X position in meters"},
                        "y": {"type": "number", "description": "Y position in meters"},
                        "z": {"type": "number", "description": "Z position in meters"},
                        "roll": {"type": "number", "description": "Roll angle in radians"},
                        "pitch": {"type": "number", "description": "Pitch angle in radians"},
                        "yaw": {"type": "number", "description": "Yaw angle in radians"}
                    },
                    "required": ["x", "y", "z"]
                }
            },
            {
                "name": "scan_environment",
                "description": "Scan the environment using LiDAR or depth camera",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "resolution": {
                            "type": "string",
                            "description": "Scan resolution (low, medium, high)",
                            "enum": ["low", "medium", "high"]
                        }
                    }
                }
            }
        ]
    
    # ========== 工具实现方法 ==========
    
    def move_to(self, location: str, speed: float = 0.5) -> str:
        """
        移动到指定位置
        
        Args:
            location: 目标位置名称或坐标
            speed: 移动速度 (0.0-1.0)
            
        Returns:
            执行结果描述
        """
        logger.info(f"Moving to location: {location} at speed {speed}")
        
        command = ROSCommand(
            type=CommandType.MOVE,
            target=location,
            parameters={"speed": speed}
        )
        
        response = self.bridge.execute_command(command)
        
        if response.success:
            return f"Successfully moved to {location}"
        else:
            return f"Failed to move to {location}: {response.message}"
    
    def navigate_to(self, x: float, y: float, theta: Optional[float] = None) -> str:
        """
        导航到指定坐标
        
        Args:
            x: X 坐标（米）
            y: Y 坐标（米）
            theta: 目标角度（弧度），可选
            
        Returns:
            执行结果描述
        """
        logger.info(f"Navigating to coordinates: ({x}, {y}, {theta})")
        
        params = {"x": x, "y": y}
        if theta is not None:
            params["theta"] = theta
        
        command = ROSCommand(
            type=CommandType.NAVIGATE,
            target="navigation_goal",
            parameters=params
        )
        
        response = self.bridge.execute_command(command)
        
        if response.success:
            return f"Successfully navigating to ({x}, {y})"
        else:
            return f"Navigation failed: {response.message}"
    
    def pick_object(self, object_name: str, grasp_force: float = 0.7) -> str:
        """
        抓取物体
        
        Args:
            object_name: 物体名称
            grasp_force: 抓取力度 (0.0-1.0)
            
        Returns:
            执行结果描述
        """
        logger.info(f"Picking object: {object_name} with force {grasp_force}")
        
        command = ROSCommand(
            type=CommandType.MANIPULATE,
            target=f"pick_{object_name}",
            parameters={"grasp_force": grasp_force}
        )
        
        response = self.bridge.execute_command(command)
        
        if response.success:
            return f"Successfully picked up {object_name}"
        else:
            return f"Failed to pick {object_name}: {response.message}"
    
    def place_object(self, location: str, orientation: Optional[str] = None) -> str:
        """
        放置物体
        
        Args:
            location: 放置位置
            orientation: 放置方向，可选
            
        Returns:
            执行结果描述
        """
        logger.info(f"Placing object at {location} with orientation {orientation}")
        
        params = {"location": location}
        if orientation:
            params["orientation"] = orientation
        
        command = ROSCommand(
            type=CommandType.MANIPULATE,
            target="place_object",
            parameters=params
        )
        
        response = self.bridge.execute_command(command)
        
        if response.success:
            return f"Successfully placed object at {location}"
        else:
            return f"Failed to place object: {response.message}"
    
    def get_sensor_data(self, sensor_type: str) -> str:
        """
        获取传感器数据
        
        Args:
            sensor_type: 传感器类型 (camera, lidar, imu, battery, etc.)
            
        Returns:
            传感器数据描述
        """
        logger.info(f"Getting sensor data for: {sensor_type}")
        
        command = ROSCommand(
            type=CommandType.SENSOR,
            target=sensor_type
        )
        
        response = self.bridge.execute_command(command)
        
        if response.success:
            data = response.data.get("data", {})
            return f"Sensor {sensor_type} data: {data}"
        else:
            return f"Failed to get sensor data: {response.message}"
    
    def execute_custom_command(self, command: str, parameters: Optional[Dict] = None) -> str:
        """
        执行自定义命令
        
        Args:
            command: 命令字符串
            parameters: 命令参数
            
        Returns:
            执行结果描述
        """
        logger.info(f"Executing custom command: {command} with params {parameters}")
        
        ros_command = ROSCommand(
            type=CommandType.CUSTOM,
            target=command,
            parameters=parameters or {}
        )
        
        response = self.bridge.execute_command(ros_command)
        
        if response.success:
            return f"Command executed successfully: {response.message}"
        else:
            return f"Command failed: {response.message}"
    
    def emergency_stop(self) -> str:
        """
        紧急停止
        
        Returns:
            执行结果描述
        """
        logger.warning("EMERGENCY STOP TRIGGERED")
        
        command = ROSCommand(
            type=CommandType.EMERGENCY_STOP,
            target="all"
        )
        
        response = self.bridge.execute_command(command)
        
        if response.success:
            return "Emergency stop executed - all motion halted"
        else:
            return f"Emergency stop failed: {response.message}"
    
    def get_robot_state(self) -> str:
        """
        获取机器人状态
        
        Returns:
            状态描述
        """
        state = self.bridge.get_robot_state()
        
        position = state.get("position", {})
        battery = state.get("battery", 0)
        status = state.get("status", "unknown")
        
        return (
            f"Robot State:\n"
            f"  Position: ({position.get('x', 0):.2f}, {position.get('y', 0):.2f}, {position.get('z', 0):.2f})\n"
            f"  Battery: {battery:.1f}%\n"
            f"  Status: {status}"
        )
    
    def move_arm(self, x: float, y: float, z: float, 
                 roll: Optional[float] = None, 
                 pitch: Optional[float] = None, 
                 yaw: Optional[float] = None) -> str:
        """
        移动机械臂到指定姿态
        
        Args:
            x, y, z: 目标位置
            roll, pitch, yaw: 目标姿态（弧度）
            
        Returns:
            执行结果描述
        """
        logger.info(f"Moving arm to position: ({x}, {y}, {z})")
        
        params = {"x": x, "y": y, "z": z}
        if roll is not None:
            params["roll"] = roll
        if pitch is not None:
            params["pitch"] = pitch
        if yaw is not None:
            params["yaw"] = yaw
        
        command = ROSCommand(
            type=CommandType.MANIPULATE,
            target="arm_pose",
            parameters=params
        )
        
        response = self.bridge.execute_command(command)
        
        if response.success:
            return f"Arm moved to position ({x}, {y}, {z})"
        else:
            return f"Failed to move arm: {response.message}"
    
    def scan_environment(self, resolution: str = "medium") -> str:
        """
        扫描环境
        
        Args:
            resolution: 扫描分辨率 (low, medium, high)
            
        Returns:
            扫描结果描述
        """
        logger.info(f"Scanning environment with resolution: {resolution}")
        
        command = ROSCommand(
            type=CommandType.SENSOR,
            target="scan",
            parameters={"resolution": resolution}
        )
        
        response = self.bridge.execute_command(command)
        
        if response.success:
            return f"Environment scan completed with {resolution} resolution"
        else:
            return f"Scan failed: {response.message}"


def register_with_openclaw(tools: ClawROSTools, openclaw_instance: Any) -> None:
    """
    将 ClawROS 工具注册到 OpenClaw 实例
    
    Args:
        tools: ClawROSTools 实例
        openclaw_instance: OpenClaw/ZeroClaw 实例
    """
    logger.info("Registering ClawROS tools with OpenClaw")
    
    for tool_def in tools.get_tools():
        tool_name = tool_def["name"]
        tool_func = getattr(tools, tool_name, None)
        
        if tool_func:
            # 注册工具到 OpenClaw
            if hasattr(openclaw_instance, 'register_tool'):
                openclaw_instance.register_tool(tool_name, tool_func)
            logger.info(f"Registered tool: {tool_name}")


def create_openclaw_tools(config_path: Optional[str] = None) -> ClawROSTools:
    """
    创建 ClawROS 工具实例的工厂函数
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        ClawROSTools: 工具实例
    """
    from .clawros_bridge import create_bridge
    
    bridge = create_bridge(config_path)
    return ClawROSTools(bridge)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    tools = create_openclaw_tools()
    
    if tools.initialize():
        print("ClawROS Tools initialized!")
        print("\nAvailable tools:")
        for tool in tools.get_tools():
            print(f"  - {tool['name']}: {tool['description']}")
        
        print("\nTesting get_robot_state tool...")
        result = tools.get_robot_state()
        print(result)
        
        tools.shutdown()
    else:
        print("Failed to initialize ClawROS Tools")
