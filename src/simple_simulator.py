#!/usr/bin/env python3
"""
ClawROS 简单模拟器 - 模拟机器人环境

This module provides a simple robot simulator for testing
ClawROS without requiring real ROS hardware.
"""

import math
import threading
import time
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


@dataclass
class RobotState:
    """机器人状态"""
    x: float = 0.0
    y: float = 0.0
    theta: float = 0.0  # 弧度
    battery: float = 100.0
    status: str = "idle"
    velocity_linear: float = 0.0
    velocity_angular: float = 0.0


@dataclass
class SensorData:
    """传感器数据"""
    lidar_distances: Dict[str, float] = field(default_factory=dict)
    battery_level: float = 100.0
    obstacles: List[Tuple[float, float]] = field(default_factory=list)


class SimpleRobotSimulator:
    """
    简单机器人模拟器
    
    模拟一个差速驱动机器人，支持：
    - 平面移动
    - 速度控制
    - 传感器数据
    - 碰撞检测
    """
    
    def __init__(self, 
                 initial_x: float = 0.0,
                 initial_y: float = 0.0,
                 max_speed: float = 1.0,
                 update_rate: float = 100.0):
        """
        初始化模拟器
        
        Args:
            initial_x: 初始 X 位置
            initial_y: 初始 Y 位置
            max_speed: 最大速度 (m/s)
            update_rate: 更新频率 (Hz)
        """
        self.state = RobotState(
            x=initial_x,
            y=initial_y,
            theta=0.0,
            battery=100.0
        )
        
        self.max_speed = max_speed
        self.update_rate = update_rate
        self.dt = 1.0 / update_rate
        
        self.cmd_linear = 0.0
        self.cmd_angular = 0.0
        
        self.running = False
        self.thread: Optional[threading.Thread] = None
        # 使用可重入锁，避免在同线程内嵌套调用时死锁
        self.lock = threading.RLock()
        
        # 环境障碍物
        self.obstacles: List[Tuple[float, float]] = [
            (2.0, 2.0),
            (3.0, 1.0),
            (-1.0, 2.0),
        ]
        
        # 回调函数
        self.state_callbacks: List[Callable] = []
        self.collision_callbacks: List[Callable] = []
        
        logger.info(f"Robot simulator initialized at ({initial_x}, {initial_y})")
    
    def start(self) -> None:
        """启动模拟器"""
        if self.running:
            logger.warning("Simulator already running")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._update_loop, daemon=True)
        self.thread.start()
        logger.info("Robot simulator started")
    
    def stop(self) -> None:
        """停止模拟器"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
        logger.info("Robot simulator stopped")
    
    def set_velocity(self, linear: float, angular: float) -> None:
        """
        设置机器人速度
        
        Args:
            linear: 线速度 (m/s)
            angular: 角速度 (rad/s)
        """
        with self.lock:
            # 限制速度
            self.cmd_linear = max(-self.max_speed, min(linear, self.max_speed))
            self.cmd_angular = max(-self.max_speed, min(angular, self.max_speed))
            
            self.state.velocity_linear = self.cmd_linear
            self.state.velocity_angular = self.cmd_angular
            self.state.status = "moving" if abs(self.cmd_linear) > 0.01 else "idle"
    
    def stop_robot(self) -> None:
        """停止机器人"""
        self.set_velocity(0.0, 0.0)
    
    def get_state(self) -> RobotState:
        """获取机器人状态"""
        with self.lock:
            return RobotState(
                x=self.state.x,
                y=self.state.y,
                theta=self.state.theta,
                battery=self.state.battery,
                status=self.state.status,
                velocity_linear=self.state.velocity_linear,
                velocity_angular=self.state.velocity_angular
            )
    
    def get_sensor_data(self) -> SensorData:
        """获取传感器数据"""
        with self.lock:
            # 模拟激光雷达数据（8 个方向）
            lidar = {}
            for angle in range(0, 360, 45):
                lidar[f"{angle}°"] = self._measure_distance(math.radians(angle))
            
            return SensorData(
                lidar_distances=lidar,
                battery_level=self.state.battery,
                obstacles=self.obstacles.copy()
            )
    
    def navigate_to(self, target_x: float, target_y: float, 
                    tolerance: float = 0.1) -> bool:
        """
        导航到目标位置
        
        Args:
            target_x: 目标 X 坐标
            target_y: 目标 Y 坐标
            tolerance: 到达容差（米）
            
        Returns:
            是否成功到达
        """
        logger.info(f"Navigating to ({target_x}, {target_y})")
        
        while True:
            with self.lock:
                dx = target_x - self.state.x
                dy = target_y - self.state.y
                distance = math.sqrt(dx**2 + dy**2)
                
                # 检查是否到达
                if distance < tolerance:
                    self.stop_robot()
                    logger.info(f"Reached target at ({target_x}, {target_y})")
                    return True
                
                # 计算目标角度
                target_theta = math.atan2(dy, dx)
                theta_error = self._normalize_angle(target_theta - self.state.theta)
                
                # 如果角度偏差大，先旋转
                if abs(theta_error) > 0.1:
                    angular_speed = max(-1.0, min(theta_error, 1.0))
                    self.set_velocity(0.0, angular_speed)
                else:
                    # 否则向前移动
                    linear_speed = max(-0.5, min(distance * 0.5, 0.5))
                    self.set_velocity(linear_speed, 0.0)
            
            time.sleep(0.1)
    
    def add_state_callback(self, callback: Callable[[RobotState], None]) -> None:
        """添加状态更新回调"""
        self.state_callbacks.append(callback)
    
    def add_collision_callback(self, callback: Callable) -> None:
        """添加碰撞检测回调"""
        self.collision_callbacks.append(callback)
    
    def _update_loop(self) -> None:
        """主更新循环"""
        last_time = time.time()
        
        while self.running:
            current_time = time.time()
            elapsed = current_time - last_time
            
            if elapsed >= self.dt:
                self._update_physics()
                last_time = current_time
            
            time.sleep(0.001)
    
    def _update_physics(self) -> None:
        """更新物理状态"""
        with self.lock:
            # 更新位置
            self.state.x += self.cmd_linear * math.cos(self.state.theta) * self.dt
            self.state.y += self.cmd_linear * math.sin(self.state.theta) * self.dt
            self.state.theta += self.cmd_angular * self.dt
            
            # 归一化角度到 [-π, π]
            self.state.theta = self._normalize_angle(self.state.theta)
            
            # 消耗电池
            power_consumption = (abs(self.cmd_linear) + abs(self.cmd_angular)) * 0.01
            self.state.battery = max(0.0, self.state.battery - power_consumption)
            
            # 检查碰撞
            if self._check_collision():
                logger.warning("Collision detected!")
                self.stop_robot()
                for callback in self.collision_callbacks:
                    callback(self.state)
            
            # 调用状态回调
            for callback in self.state_callbacks:
                callback(self.state)
    
    def _measure_distance(self, angle: float) -> float:
        """测量指定方向的距离"""
        with self.lock:
            robot_angle = self.state.theta + angle
            max_range = 5.0
            
            min_distance = max_range
            for obs_x, obs_y in self.obstacles:
                dx = obs_x - self.state.x
                dy = obs_y - self.state.y
                obs_angle = math.atan2(dy, dx)
                obs_distance = math.sqrt(dx**2 + dy**2)
                
                angle_diff = abs(self._normalize_angle(robot_angle - obs_angle))
                if angle_diff < 0.2:  # 在激光束范围内
                    min_distance = min(min_distance, obs_distance)
            
            return min_distance
    
    def _check_collision(self) -> bool:
        """检查是否碰撞"""
        with self.lock:
            for obs_x, obs_y in self.obstacles:
                dx = obs_x - self.state.x
                dy = obs_y - self.state.y
                distance = math.sqrt(dx**2 + dy**2)
                
                if distance < 0.3:  # 机器人半径
                    return True
            return False
    
    @staticmethod
    def _normalize_angle(angle: float) -> float:
        """归一化角度到 [-π, π]"""
        while angle > math.pi:
            angle -= 2 * math.pi
        while angle < -math.pi:
            angle += 2 * math.pi
        return angle
    
    def reset(self, x: float = 0.0, y: float = 0.0) -> None:
        """重置机器人位置"""
        with self.lock:
            self.state.x = x
            self.state.y = y
            self.state.theta = 0.0
            self.state.battery = 100.0
            self.state.status = "idle"
            self.cmd_linear = 0.0
            self.cmd_angular = 0.0
        logger.info(f"Robot reset to ({x}, {y})")


class SimulatedROSBridge:
    """
    模拟的 ROS 桥接（无需真实 ROS）
    
    用于在没有 ROS 环境下测试 ClawROS
    """
    
    def __init__(self):
        self.simulator = SimpleRobotSimulator()
        self.initialized = False
    
    def initialize(self) -> bool:
        """初始化桥接"""
        if not self.initialized:
            self.simulator.start()
            self.initialized = True
            logger.info("Simulated ROS bridge initialized")
        return True
    
    def shutdown(self) -> None:
        """关闭桥接"""
        if self.initialized:
            self.simulator.stop()
            self.initialized = False
            logger.info("Simulated ROS bridge shutdown")
    
    def execute_command(self, command) -> 'SimulatedResponse':
        """执行命令"""
        from clawros_bridge import CommandType
        
        if command.type == CommandType.MOVE:
            return self._move(command)
        elif command.type == CommandType.NAVIGATE:
            return self._navigate(command)
        elif command.type == CommandType.SENSOR:
            return self._get_sensor(command)
        elif command.type == CommandType.EMERGENCY_STOP:
            return self._emergency_stop()
        else:
            return SimulatedResponse.error_response(f"Unknown command: {command.type}")
    
    def _move(self, command) -> 'SimulatedResponse':
        """移动命令"""
        params = command.parameters
        linear = params.get("linear", 0.3)
        angular = params.get("angular", 0.0)
        
        self.simulator.set_velocity(linear, angular)
        
        return SimulatedResponse.success_response(
            f"Move command executed: linear={linear}, angular={angular}"
        )
    
    def _navigate(self, command) -> 'SimulatedResponse':
        """导航命令"""
        params = command.parameters
        x = params.get("x", 0.0)
        y = params.get("y", 0.0)
        
        # 启动导航线程
        thread = threading.Thread(
            target=self.simulator.navigate_to,
            args=(x, y),
            daemon=True
        )
        thread.start()
        
        return SimulatedResponse.success_response(
            f"Navigating to ({x}, {y})"
        )
    
    def _get_sensor(self, command) -> 'SimulatedResponse':
        """获取传感器数据"""
        sensor_data = self.simulator.get_sensor_data()
        
        return SimulatedResponse.success_response(
            "Sensor data retrieved",
            {
                "lidar": sensor_data.lidar_distances,
                "battery": sensor_data.battery_level,
                "obstacles": len(sensor_data.obstacles)
            }
        )
    
    def _emergency_stop(self) -> 'SimulatedResponse':
        """紧急停止"""
        self.simulator.stop_robot()
        return SimulatedResponse.success_response("Emergency stop executed")
    
    def get_robot_state(self) -> Dict:
        """获取机器人状态"""
        state = self.simulator.get_state()
        return {
            "position": {"x": state.x, "y": state.y, "z": 0.0},
            "orientation": {"x": 0.0, "y": 0.0, "z": math.sin(state.theta/2), "w": math.cos(state.theta/2)},
            "battery": state.battery,
            "status": state.status,
            "velocity": {
                "linear": state.velocity_linear,
                "angular": state.velocity_angular
            }
        }


@dataclass
class SimulatedResponse:
    """模拟响应"""
    success: bool
    message: str
    data: Dict = field(default_factory=dict)
    
    @classmethod
    def success_response(cls, message: str, data: Optional[Dict] = None) -> 'SimulatedResponse':
        return cls(success=True, message=message, data=data or {})
    
    @classmethod
    def error_response(cls, message: str) -> 'SimulatedResponse':
        return cls(success=False, message=message)


def create_simulated_bridge() -> SimulatedROSBridge:
    """创建模拟桥接的工厂函数"""
    return SimulatedROSBridge()


if __name__ == "__main__":
    # 测试模拟器
    logging.basicConfig(level=logging.INFO)
    
    print("=== ClawROS 简单模拟器测试 ===\n")
    
    bridge = create_simulated_bridge()
    bridge.initialize()
    
    try:
        # 测试 1: 前进
        print("1. 前进 2 秒")
        from clawros_bridge import ROSCommand, CommandType
        cmd = ROSCommand(
            type=CommandType.MOVE,
            target="forward",
            parameters={"linear": 0.3}
        )
        response = bridge.execute_command(cmd)
        print(f"   结果：{response.message}")
        time.sleep(2)
        
        # 测试 2: 获取状态
        print("\n2. 获取机器人状态")
        state = bridge.get_robot_state()
        print(f"   位置：({state['position']['x']:.2f}, {state['position']['y']:.2f})")
        print(f"   电量：{state['battery']:.1f}%")
        
        # 测试 3: 导航
        print("\n3. 导航到 (2.0, 1.5)")
        cmd = ROSCommand(
            type=CommandType.NAVIGATE,
            target="goal",
            parameters={"x": 2.0, "y": 1.5}
        )
        response = bridge.execute_command(cmd)
        print(f"   结果：{response.message}")
        time.sleep(3)  # 等待导航
        
        # 测试 4: 获取传感器数据
        print("\n4. 获取传感器数据")
        cmd = ROSCommand(
            type=CommandType.SENSOR,
            target="lidar"
        )
        response = bridge.execute_command(cmd)
        print(f"   结果：{response.message}")
        print(f"   数据：{response.data}")
        
        # 测试 5: 紧急停止
        print("\n5. 紧急停止")
        cmd = ROSCommand(
            type=CommandType.EMERGENCY_STOP,
            target="all"
        )
        response = bridge.execute_command(cmd)
        print(f"   结果：{response.message}")
        
        print("\n=== 测试完成 ===")
        
    finally:
        bridge.shutdown()
