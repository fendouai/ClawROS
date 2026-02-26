#!/usr/bin/env python3
"""
ClawROS Launch File

启动 ClawROS 桥接节点和相关组件
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, LogInfo
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    """生成启动描述"""
    
    # 声明启动参数
    config_file_arg = DeclareLaunchArgument(
        'config_file',
        default_value='',
        description='Path to ClawROS configuration file'
    )
    
    ros_version_arg = DeclareLaunchArgument(
        'ros_version',
        default_value='ros2',
        description='ROS version (ros1 or ros2)'
    )
    
    enable_safety_arg = DeclareLaunchArgument(
        'enable_safety',
        default_value='true',
        description='Enable safety layer'
    )
    
    config_file = LaunchConfiguration('config_file')
    ros_version = LaunchConfiguration('ros_version')
    enable_safety = LaunchConfiguration('enable_safety')
    
    # 创建 ClawROS 节点
    clawros_node = Node(
        package='clawros',
        executable='clawros_bridge_node',
        name='clawros_bridge',
        output='screen',
        parameters=[{
            'config_file': config_file,
            'ros_version': ros_version,
            'enable_safety': enable_safety,
        }],
        remappings=[
            ('/cmd_vel', '/clawros/cmd_vel'),
            ('/clawros/status', '/clawros/status'),
            ('/clawros/command', '/clawros/command'),
        ]
    )
    
    # 创建状态监控节点（可选）
    monitor_node = Node(
        package='clawros',
        executable='clawros_monitor_node',
        name='clawros_monitor',
        output='screen',
        parameters=[{
            'publish_rate': 10.0,
        }]
    )
    
    # 创建日志信息
    log_info = LogInfo(
        msg=[
            'Starting ClawROS Bridge...\n',
            'Config file: ', config_file, '\n',
            'ROS version: ', ros_version, '\n',
            'Safety enabled: ', enable_safety,
        ]
    )
    
    return LaunchDescription([
        config_file_arg,
        ros_version_arg,
        enable_safety_arg,
        log_info,
        clawros_node,
        monitor_node,
    ])
