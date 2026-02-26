"""
ClawROS 单元测试 - Bridge 模块
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
import sys
import os

# 添加 src 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from clawros_bridge import (
    ROSCommand,
    CommandType,
    ROSResponse,
    SecurityLayer,
    StateMonitor,
    ROSAdapter,
    ROSVersion,
)


class TestCommandType:
    """测试命令类型枚举"""
    
    def test_command_types_exist(self):
        """测试所有命令类型存在"""
        assert CommandType.MOVE.value == "move"
        assert CommandType.NAVIGATE.value == "navigate"
        assert CommandType.MANIPULATE.value == "manipulate"
        assert CommandType.SENSOR.value == "sensor"
        assert CommandType.CUSTOM.value == "custom"
        assert CommandType.EMERGENCY_STOP.value == "emergency_stop"


class TestROSCommand:
    """测试 ROS 命令类"""
    
    def test_command_creation_basic(self):
        """测试基本命令创建"""
        cmd = ROSCommand(
            type=CommandType.MOVE,
            target="forward"
        )
        
        assert cmd.type == CommandType.MOVE
        assert cmd.target == "forward"
        assert cmd.parameters == {}
        assert cmd.priority == 0
        assert cmd.timeout == 30.0
    
    def test_command_creation_full(self):
        """测试完整命令创建"""
        cmd = ROSCommand(
            type=CommandType.NAVIGATE,
            target="kitchen",
            parameters={"x": 1.0, "y": 2.0, "theta": 0.5},
            priority=5,
            timeout=60.0
        )
        
        assert cmd.type == CommandType.NAVIGATE
        assert cmd.target == "kitchen"
        assert cmd.parameters["x"] == 1.0
        assert cmd.priority == 5
        assert cmd.timeout == 60.0
    
    def test_command_to_dict(self):
        """测试命令转换为字典"""
        cmd = ROSCommand(
            type=CommandType.MANIPULATE,
            target="pick_object",
            parameters={"object": "cup"}
        )
        
        cmd_dict = cmd.to_dict()
        
        assert isinstance(cmd_dict, dict)
        assert cmd_dict["type"] == "manipulate"
        assert cmd_dict["target"] == "pick_object"
        assert cmd_dict["parameters"]["object"] == "cup"
    
    def test_command_serialization(self):
        """测试命令序列化"""
        import json
        
        cmd = ROSCommand(
            type=CommandType.SENSOR,
            target="lidar",
            parameters={"resolution": "high"}
        )
        
        cmd_dict = cmd.to_dict()
        json_str = json.dumps(cmd_dict)
        assert json_str is not None


class TestROSResponse:
    """测试 ROS 响应类"""
    
    def test_success_response_creation(self):
        """测试成功响应创建"""
        response = ROSResponse.success_response(
            "Command executed successfully",
            {"data": "test"}
        )
        
        assert response.success is True
        assert response.message == "Command executed successfully"
        assert response.data["data"] == "test"
    
    def test_success_response_no_data(self):
        """测试无数据的成功响应"""
        response = ROSResponse.success_response("OK")
        
        assert response.success is True
        assert response.message == "OK"
        assert response.data == {}
    
    def test_error_response_creation(self):
        """测试错误响应创建"""
        response = ROSResponse.error_response("Something went wrong")
        
        assert response.success is False
        assert response.message == "Something went wrong"
        assert response.data == {}
    
    def test_response_is_serializable(self):
        """测试响应可序列化"""
        import json
        from dataclasses import asdict
        
        response = ROSResponse.success_response("Test", {"key": "value"})
        response_dict = asdict(response)
        
        json_str = json.dumps(response_dict)
        assert json_str is not None


class TestSecurityLayer:
    """测试安全层"""
    
    def test_security_layer_creation(self):
        """测试安全层创建"""
        security = SecurityLayer()
        assert security.enabled is True
        assert security.max_linear_velocity == 0.5
        assert security.max_angular_velocity == 1.0
    
    def test_security_layer_custom_config(self):
        """测试自定义配置"""
        config = {
            "enabled": False,
            "max_linear_velocity": 1.0,
            "max_angular_velocity": 2.0,
        }
        security = SecurityLayer(config)
        
        assert security.enabled is False
        assert security.max_linear_velocity == 1.0
    
    def test_validate_command_disabled_security(self):
        """测试禁用安全时的验证"""
        config = {"enabled": False}
        security = SecurityLayer(config)
        
        cmd = ROSCommand(
            type=CommandType.MOVE,
            target="forward",
            parameters={"linear": 100.0}  # 明显超限
        )
        
        is_valid, error_msg = security.validate_command(cmd)
        assert is_valid is True
        assert error_msg == ""
    
    def test_validate_move_command_within_limits(self):
        """测试移动命令在限制内"""
        security = SecurityLayer({"enabled": True})
        
        cmd = ROSCommand(
            type=CommandType.MOVE,
            target="forward",
            parameters={"linear": 0.3, "angular": 0.5}
        )
        
        is_valid, error_msg = security.validate_command(cmd)
        assert is_valid is True
    
    def test_validate_move_command_exceeds_linear(self):
        """测试移动命令超过线速度限制"""
        security = SecurityLayer({"enabled": True})
        
        cmd = ROSCommand(
            type=CommandType.MOVE,
            target="forward",
            parameters={"linear": 1.0}  # 超过 0.5 的限制
        )
        
        is_valid, error_msg = security.validate_command(cmd)
        assert is_valid is False
        assert "exceeds max" in error_msg
    
    def test_validate_move_command_exceeds_angular(self):
        """测试移动命令超过角速度限制"""
        security = SecurityLayer({"enabled": True})
        
        cmd = ROSCommand(
            type=CommandType.MOVE,
            target="turn",
            parameters={"angular": 2.0}  # 超过 1.0 的限制
        )
        
        is_valid, error_msg = security.validate_command(cmd)
        assert is_valid is False
        assert "exceeds max" in error_msg
    
    def test_validate_navigate_command_within_bounds(self):
        """测试导航命令在工作空间内"""
        config = {
            "enabled": True,
            "workspace_bounds": {
                "x": [-2.0, 2.0],
                "y": [-2.0, 2.0],
                "z": [0.0, 1.5]
            }
        }
        security = SecurityLayer(config)
        
        cmd = ROSCommand(
            type=CommandType.NAVIGATE,
            target="navigate",
            parameters={"x": 1.0, "y": 1.0, "z": 0.5}
        )
        
        is_valid, error_msg = security.validate_command(cmd)
        assert is_valid is True
    
    def test_validate_navigate_command_outside_bounds(self):
        """测试导航命令超出工作空间"""
        config = {
            "enabled": True,
            "workspace_bounds": {
                "x": [-1.0, 1.0],
                "y": [-1.0, 1.0],
            }
        }
        security = SecurityLayer(config)
        
        cmd = ROSCommand(
            type=CommandType.NAVIGATE,
            target="navigate",
            parameters={"x": 2.0, "y": 2.0}
        )
        
        is_valid, error_msg = security.validate_command(cmd)
        assert is_valid is False
        assert "outside bounds" in error_msg
    
    def test_rate_limiting(self):
        """测试速率限制"""
        import asyncio
        
        config = {
            "enabled": True,
            "rate_limit": {
                "commands_per_minute": 3
            }
        }
        security = SecurityLayer(config)
        
        # 发送命令直到达到限制
        for i in range(3):
            cmd = ROSCommand(
                type=CommandType.MOVE,
                target=f"move_{i}",
                parameters={"linear": 0.1}
            )
            is_valid, _ = security.validate_command(cmd)
            assert is_valid is True
        
        # 下一个命令应该被限制
        cmd = ROSCommand(
            type=CommandType.MOVE,
            target="move_4",
            parameters={"linear": 0.1}
        )
        is_valid, error_msg = security.validate_command(cmd)
        assert is_valid is False
        assert "Rate limit" in error_msg


class TestStateMonitor:
    """测试状态监控器"""
    
    def test_state_monitor_creation(self):
        """测试状态监控器创建"""
        adapter = Mock(spec=ROSAdapter)
        monitor = StateMonitor(adapter)
        
        state = monitor.get_state()
        assert "position" in state
        assert "battery" in state
        assert "status" in state
    
    def test_get_state_returns_copy(self):
        """测试获取状态返回副本"""
        adapter = Mock(spec=ROSAdapter)
        monitor = StateMonitor(adapter)
        
        state1 = monitor.get_state()
        state1["battery"] = 0.0  # 修改返回值
        
        state2 = monitor.get_state()
        assert state2["battery"] == 100.0  # 原始值不变
    
    def test_state_callback(self):
        """测试状态回调"""
        adapter = Mock(spec=ROSAdapter)
        monitor = StateMonitor(adapter)
        
        callback_called = []
        
        def callback(state):
            callback_called.append(state.copy())
        
        monitor.add_state_callback(callback)
        
        # 模拟状态更新
        new_state = {"battery": 50.0}
        monitor._update_state(new_state)
        
        assert len(callback_called) == 1
        assert callback_called[0]["battery"] == 50.0
    
    def test_multiple_callbacks(self):
        """测试多个回调"""
        adapter = Mock(spec=ROSAdapter)
        monitor = StateMonitor(adapter)
        
        callback1_called = []
        callback2_called = []
        
        monitor.add_state_callback(lambda s: callback1_called.append(True))
        monitor.add_state_callback(lambda s: callback2_called.append(True))
        
        monitor._update_state({"status": "active"})
        
        assert len(callback1_called) == 1
        assert len(callback2_called) == 1


class TestROSAdapter:
    """测试 ROS 适配器"""
    
    def test_adapter_creation_ros2(self):
        """测试 ROS2 适配器创建"""
        adapter = ROSAdapter(ROSVersion.ROS2)
        assert adapter.version == ROSVersion.ROS2
        assert adapter.node is None
    
    def test_adapter_creation_default(self):
        """测试默认适配器创建"""
        adapter = ROSAdapter()
        assert adapter.version == ROSVersion.ROS2
    
    def test_adapter_initialize_simulation(self):
        """测试适配器初始化（模拟模式）"""
        adapter = ROSAdapter(ROSVersion.ROS2)
        
        # 由于 rclpy 未安装，应该进入模拟模式
        result = adapter.initialize()
        
        # 在模拟模式下应该返回 True
        assert result is True
    
    def test_adapter_shutdown(self):
        """测试适配器关闭"""
        adapter = ROSAdapter()
        adapter.shutdown()  # 不应该抛出异常
    
    def test_adapter_create_publisher_without_node(self):
        """测试在没有节点时创建发布者"""
        adapter = ROSAdapter()
        
        publisher = adapter.create_publisher("/test_topic", Mock())
        
        assert publisher is None


# 集成测试样例（需要 ROS 环境）
class TestIntegration:
    """集成测试（需要实际 ROS 环境）"""
    
    @pytest.mark.skip(reason="需要 ROS 环境")
    def test_bridge_initialization_real(self):
        """测试真实桥接初始化"""
        from clawros_bridge import ClawROSBridge, create_bridge
        
        bridge = create_bridge()
        result = bridge.initialize()
        
        assert result is True
        
        bridge.shutdown()
    
    @pytest.mark.skip(reason="需要 ROS 环境")
    def test_command_execution_real(self):
        """测试真实命令执行"""
        from clawros_bridge import ClawROSBridge, ROSCommand, CommandType
        
        bridge = ClawROSBridge()
        bridge.initialize()
        
        cmd = ROSCommand(
            type=CommandType.MOVE,
            target="forward",
            parameters={"linear": 0.3}
        )
        
        response = bridge.execute_command(cmd)
        
        assert hasattr(response, 'success')
        assert hasattr(response, 'message')
        
        bridge.shutdown()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
