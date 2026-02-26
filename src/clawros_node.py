#!/usr/bin/env python3
"""
ClawROS Bridge Node - ROS2 节点实现

This node provides the main ROS2 interface for ClawROS,
allowing OpenClaw to control robots through ROS topics,
services, and actions.
"""

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy
from geometry_msgs.msg import Twist, PoseStamped
from sensor_msgs.msg import JointState, BatteryState
from nav_msgs.msg import Odometry
from std_msgs.msg import String, Float32
from clawros_bridge import ClawROSBridge, ROSCommand, CommandType, create_bridge


class ClawROSNode(Node):
    """ClawROS ROS2 节点"""
    
    def __init__(self):
        super().__init__('clawros_bridge_node')
        
        # 声明参数
        self.declare_parameter('config_file', '')
        self.declare_parameter('ros_version', 'ros2')
        self.declare_parameter('enable_safety', True)
        
        # 获取参数
        config_file = self.get_parameter('config_file').get_parameter_value().string_value
        ros_version = self.get_parameter('ros_version').get_parameter_value().string_value
        enable_safety = self.get_parameter('enable_safety').get_parameter_value().bool_value
        
        self.get_logger().info(f'Initializing ClawROS Node')
        self.get_logger().info(f'Config file: {config_file}')
        self.get_logger().info(f'ROS version: {ros_version}')
        self.get_logger().info(f'Safety enabled: {enable_safety}')
        
        # 创建桥接实例
        config = {
            'ros_version': ros_version,
            'safety': {
                'enabled': enable_safety
            }
        }
        
        self.bridge = create_bridge(config)
        
        # 初始化桥接
        if not self.bridge.initialize():
            self.get_logger().error('Failed to initialize ClawROS bridge')
            raise RuntimeError('Bridge initialization failed')
        
        self.get_logger().info('ClawROS bridge initialized')
        
        # 创建发布者
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.status_pub = self.create_publisher(String, '/clawros/status', 10)
        self.get_logger().info('Publishers created')
        
        # 创建订阅者
        self.create_subscription(
            String,
            '/clawros/command',
            self.command_callback,
            10
        )
        self.get_logger().info('Subscribers created')
        
        # 创建服务
        from clawros_interfaces.srv import ExecuteCommand, GetRobotState
        self.cmd_srv = self.create_service(
            ExecuteCommand,
            '/clawros/execute_command',
            self.execute_command_callback
        )
        self.state_srv = self.create_service(
            GetRobotState,
            '/clawros/get_state',
            self.get_state_callback
        )
        self.get_logger().info('Services created')
        
        # 创建定时器（状态发布）
        self.timer = self.create_timer(1.0, self.publish_status)
        
        self.get_logger().info('ClawROS Node fully initialized')
    
    def command_callback(self, msg: String) -> None:
        """处理命令消息"""
        try:
            import json
            command_data = json.loads(msg.data)
            
            command_type = CommandType(command_data.get('type', 'custom'))
            target = command_data.get('target', '')
            parameters = command_data.get('parameters', {})
            
            ros_command = ROSCommand(
                type=command_type,
                target=target,
                parameters=parameters
            )
            
            response = self.bridge.execute_command(ros_command)
            
            # 发布响应
            response_msg = String()
            response_msg.data = json.dumps({
                'success': response.success,
                'message': response.message
            })
            self.status_pub.publish(response_msg)
            
            self.get_logger().info(f'Command executed: {response.success}')
            
        except Exception as e:
            self.get_logger().error(f'Error executing command: {e}')
    
    def execute_command_callback(self, request, response):
        """执行命令服务回调"""
        try:
            command_type = CommandType(request.command_type)
            
            ros_command = ROSCommand(
                type=command_type,
                request.target,
                dict(request.parameters) if request.parameters else {}
            )
            
            result = self.bridge.execute_command(ros_command)
            
            response.success = result.success
            response.message = result.message
            
            return response
            
        except Exception as e:
            self.get_logger().error(f'Error in execute_command service: {e}')
            response.success = False
            response.message = str(e)
            return response
    
    def get_state_callback(self, request, response):
        """获取机器人状态服务回调"""
        try:
            state = self.bridge.get_robot_state()
            
            response.state.position.x = state.get('position', {}).get('x', 0.0)
            response.state.position.y = state.get('position', {}).get('y', 0.0)
            response.state.position.z = state.get('position', {}).get('z', 0.0)
            response.battery_level = state.get('battery', 0.0)
            response.status_message = state.get('status', 'unknown')
            
            return response
            
        except Exception as e:
            self.get_logger().error(f'Error in get_state service: {e}')
            response.status_message = str(e)
            return response
    
    def publish_status(self) -> None:
        """定期发布状态"""
        try:
            state = self.bridge.get_robot_state()
            
            import json
            status_msg = String()
            status_msg.data = json.dumps(state)
            self.status_pub.publish(status_msg)
            
        except Exception as e:
            self.get_logger().error(f'Error publishing status: {e}')
    
    def destroy_node(self) -> None:
        """销毁节点"""
        self.get_logger().info('Destroying ClawROS Node')
        self.bridge.shutdown()
        super().destroy_node()


def main(args=None):
    """主函数"""
    rclpy.init(args=args)
    
    try:
        node = ClawROSNode()
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        rclpy.get_logger('clawros').error(f'Node error: {e}')
    finally:
        rclpy.shutdown()


if __name__ == '__main__':
    main()
