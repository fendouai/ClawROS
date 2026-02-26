"""
ClawROS 单元测试 - Tools 模块
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from clawros_tools import ClawROSTools


class TestClawROSToolsInit:
    """测试 ClawROSTools 初始化"""
    
    def test_tools_creation_without_bridge(self):
        """测试不传入桥接时创建工具"""
        tools = ClawROSTools()
        
        assert tools is not None
        assert tools.initialized is False
    
    def test_tools_creation_with_mock_bridge(self):
        """测试使用模拟桥接创建工具"""
        mock_bridge = Mock()
        tools = ClawROSTools(bridge=mock_bridge)
        
        assert tools.bridge == mock_bridge
        assert tools.initialized is False
    
    def test_tools_initialization(self):
        """测试工具初始化"""
        mock_bridge = Mock()
        mock_bridge.initialize.return_value = True
        
        tools = ClawROSTools(bridge=mock_bridge)
        result = tools.initialize()
        
        assert result is True
        assert tools.initialized is True
        mock_bridge.initialize.assert_called_once()
    
    def test_tools_shutdown(self):
        """测试工具关闭"""
        mock_bridge = Mock()
        tools = ClawROSTools(bridge=mock_bridge)
        
        tools.shutdown()
        
        mock_bridge.shutdown.assert_called_once()
        assert tools.initialized is False


class TestToolsList:
    """测试工具列表"""
    
    @pytest.fixture
    def tools_with_mock_bridge(self):
        """创建带有模拟桥接的工具实例"""
        mock_bridge = Mock()
        return ClawROSTools(bridge=mock_bridge)
    
    def test_get_tools_returns_list(self, tools_with_mock_bridge):
        """测试获取工具列表返回列表"""
        tools = tools_with_mock_bridge
        tool_list = tools.get_tools()
        
        assert isinstance(tool_list, list)
        assert len(tool_list) > 0
    
    def test_get_tools_contains_expected_tools(self, tools_with_mock_bridge):
        """测试工具列表包含预期的工具"""
        tools = tools_with_mock_bridge
        tool_list = tools.get_tools()
        
        tool_names = [t['name'] for t in tool_list]
        
        expected_tools = [
            'move_to',
            'navigate_to',
            'pick_object',
            'place_object',
            'get_sensor_data',
            'execute_custom_command',
            'emergency_stop',
            'get_robot_state',
            'move_arm',
            'scan_environment',
        ]
        
        for tool_name in expected_tools:
            assert tool_name in tool_names
    
    def test_tool_definition_structure(self, tools_with_mock_bridge):
        """测试工具定义结构"""
        tools = tools_with_mock_bridge
        tool_list = tools.get_tools()
        
        for tool in tool_list:
            assert 'name' in tool
            assert 'description' in tool
            assert 'parameters' in tool
            assert isinstance(tool['name'], str)
            assert isinstance(tool['description'], str)
            assert isinstance(tool['parameters'], dict)


class TestMoveToTool:
    """测试移动工具"""
    
    @pytest.fixture
    def tools_with_success_bridge(self):
        """创建返回成功响应的模拟桥接"""
        mock_bridge = Mock()
        mock_response = Mock()
        mock_response.success = True
        mock_response.message = "Success"
        mock_bridge.execute_command.return_value = mock_response
        
        return ClawROSTools(bridge=mock_bridge)
    
    def test_move_to_success(self, tools_with_success_bridge):
        """测试移动成功"""
        tools = tools_with_success_bridge
        result = tools.move_to("kitchen", speed=0.5)
        
        assert "Successfully moved" in result
        tools.bridge.execute_command.assert_called_once()
    
    def test_move_to_default_speed(self, tools_with_success_bridge):
        """测试使用默认速度移动"""
        tools = tools_with_success_bridge
        result = tools.move_to("bedroom")
        
        assert "Successfully moved" in result
    
    def test_move_to_failure(self):
        """测试移动失败"""
        mock_bridge = Mock()
        mock_response = Mock()
        mock_response.success = False
        mock_response.message = "Path blocked"
        mock_bridge.execute_command.return_value = mock_response
        
        tools = ClawROSTools(bridge=mock_bridge)
        result = tools.move_to("kitchen")
        
        assert "Failed to move" in result
        assert "Path blocked" in result


class TestNavigateToTool:
    """测试导航工具"""
    
    @pytest.fixture
    def tools_with_success_bridge(self):
        """创建返回成功响应的模拟桥接"""
        mock_bridge = Mock()
        mock_response = Mock()
        mock_response.success = True
        mock_response.message = "Success"
        mock_bridge.execute_command.return_value = mock_response
        
        return ClawROSTools(bridge=mock_bridge)
    
    def test_navigate_to_with_theta(self, tools_with_success_bridge):
        """测试带角度的导航"""
        tools = tools_with_success_bridge
        result = tools.navigate_to(1.0, 2.0, theta=0.5)
        
        assert "Successfully navigating" in result
    
    def test_navigate_to_without_theta(self, tools_with_success_bridge):
        """测试不带角度的导航"""
        tools = tools_with_success_bridge
        result = tools.navigate_to(1.0, 2.0)
        
        assert "Successfully navigating" in result


class TestManipulationTools:
    """测试操作工具"""
    
    @pytest.fixture
    def tools_with_success_bridge(self):
        """创建返回成功响应的模拟桥接"""
        mock_bridge = Mock()
        mock_response = Mock()
        mock_response.success = True
        mock_response.message = "Success"
        mock_bridge.execute_command.return_value = mock_response
        
        return ClawROSTools(bridge=mock_bridge)
    
    def test_pick_object_success(self, tools_with_success_bridge):
        """测试抓取成功"""
        tools = tools_with_success_bridge
        result = tools.pick_object("cup", grasp_force=0.7)
        
        assert "Successfully picked up" in result
    
    def test_pick_object_default_force(self, tools_with_success_bridge):
        """测试使用默认力度抓取"""
        tools = tools_with_success_bridge
        result = tools.pick_object("ball")
        
        assert "Successfully picked up" in result
    
    def test_place_object_success(self, tools_with_success_bridge):
        """测试放置成功"""
        tools = tools_with_success_bridge
        result = tools.place_object("table", orientation="upright")
        
        assert "Successfully placed" in result
    
    def test_place_object_no_orientation(self, tools_with_success_bridge):
        """测试不指定方向放置"""
        tools = tools_with_success_bridge
        result = tools.place_object("table")
        
        assert "Successfully placed" in result


class TestSensorTools:
    """测试传感器工具"""
    
    @pytest.fixture
    def tools_with_success_bridge(self):
        """创建返回成功响应的模拟桥接"""
        mock_bridge = Mock()
        mock_response = Mock()
        mock_response.success = True
        mock_response.message = "Success"
        mock_response.data = {"data": {"value": 42}}
        mock_bridge.execute_command.return_value = mock_response
        
        return ClawROSTools(bridge=mock_bridge)
    
    def test_get_sensor_data_success(self, tools_with_success_bridge):
        """测试获取传感器数据成功"""
        tools = tools_with_success_bridge
        result = tools.get_sensor_data("battery")
        
        assert "Sensor battery data" in result
    
    def test_scan_environment_success(self, tools_with_success_bridge):
        """测试环境扫描成功"""
        tools = tools_with_success_bridge
        result = tools.scan_environment(resolution="high")
        
        assert "scan completed" in result.lower()
    
    def test_scan_environment_default_resolution(self, tools_with_success_bridge):
        """测试使用默认分辨率扫描"""
        tools = tools_with_success_bridge
        result = tools.scan_environment()
        
        assert "scan completed" in result.lower()


class TestEmergencyStopTool:
    """测试紧急停止工具"""
    
    def test_emergency_stop_success(self):
        """测试紧急停止成功"""
        mock_bridge = Mock()
        mock_response = Mock()
        mock_response.success = True
        mock_response.message = "Stopped"
        mock_bridge.execute_command.return_value = mock_response
        
        tools = ClawROSTools(bridge=mock_bridge)
        result = tools.emergency_stop()
        
        assert "Emergency stop executed" in result
    
    def test_emergency_stop_failure(self):
        """测试紧急停止失败"""
        mock_bridge = Mock()
        mock_response = Mock()
        mock_response.success = False
        mock_response.message = "Failed"
        mock_bridge.execute_command.return_value = mock_response
        
        tools = ClawROSTools(bridge=mock_bridge)
        result = tools.emergency_stop()
        
        assert "Emergency stop failed" in result


class TestRobotStateTool:
    """测试机器人状态工具"""
    
    def test_get_robot_state(self):
        """测试获取机器人状态"""
        mock_bridge = Mock()
        mock_bridge.get_robot_state.return_value = {
            "position": {"x": 1.0, "y": 2.0, "z": 0.0},
            "battery": 85.5,
            "status": "active"
        }
        
        tools = ClawROSTools(bridge=mock_bridge)
        result = tools.get_robot_state()
        
        assert "Robot State" in result
        assert "Position" in result
        assert "Battery" in result
        assert "85.5" in result
        assert "active" in result
    
    def test_get_robot_state_default_values(self):
        """测试获取默认状态"""
        mock_bridge = Mock()
        mock_bridge.get_robot_state.return_value = {}
        
        tools = ClawROSTools(bridge=mock_bridge)
        result = tools.get_robot_state()
        
        assert "Robot State" in result


class TestArmMovementTool:
    """测试机械臂移动工具"""
    
    @pytest.fixture
    def tools_with_success_bridge(self):
        """创建返回成功响应的模拟桥接"""
        mock_bridge = Mock()
        mock_response = Mock()
        mock_response.success = True
        mock_response.message = "Success"
        mock_bridge.execute_command.return_value = mock_response
        
        return ClawROSTools(bridge=mock_bridge)
    
    def test_move_arm_basic(self, tools_with_success_bridge):
        """测试基本机械臂移动"""
        tools = tools_with_success_bridge
        result = tools.move_arm(0.5, 0.3, 0.2)
        
        assert "Arm moved" in result
    
    def test_move_arm_with_orientation(self, tools_with_success_bridge):
        """测试带方向的机械臂移动"""
        tools = tools_with_success_bridge
        result = tools.move_arm(
            0.5, 0.3, 0.2,
            roll=0.1, pitch=0.2, yaw=0.3
        )
        
        assert "Arm moved" in result


class TestCustomCommandTool:
    """测试自定义命令工具"""
    
    @pytest.fixture
    def tools_with_success_bridge(self):
        """创建返回成功响应的模拟桥接"""
        mock_bridge = Mock()
        mock_response = Mock()
        mock_response.success = True
        mock_response.message = "Command executed"
        mock_bridge.execute_command.return_value = mock_response
        
        return ClawROSTools(bridge=mock_bridge)
    
    def test_execute_custom_command_basic(self, tools_with_success_bridge):
        """测试基本自定义命令"""
        tools = tools_with_success_bridge
        result = tools.execute_custom_command("move_base")
        
        assert "Command executed successfully" in result
    
    def test_execute_custom_command_with_params(self, tools_with_success_bridge):
        """测试带参数的自定义命令"""
        tools = tools_with_success_bridge
        result = tools.execute_custom_command(
            "move_base",
            parameters={"x": 1.0, "y": 2.0}
        )
        
        assert "Command executed successfully" in result
    
    def test_execute_custom_command_failure(self):
        """测试自定义命令失败"""
        mock_bridge = Mock()
        mock_response = Mock()
        mock_response.success = False
        mock_response.message = "Invalid command"
        mock_bridge.execute_command.return_value = mock_response
        
        tools = ClawROSTools(bridge=mock_bridge)
        result = tools.execute_custom_command("invalid_command")
        
        assert "Command failed" in result
        assert "Invalid command" in result


class TestRegisterWithOpenClaw:
    """测试 OpenClaw 注册"""
    
    def test_register_tools(self):
        """测试工具注册"""
        from clawros_tools import register_with_openclaw
        
        mock_bridge = Mock()
        tools = ClawROSTools(bridge=mock_bridge)
        
        mock_openclaw = Mock()
        mock_openclaw.register_tool = Mock()
        
        register_with_openclaw(tools, mock_openclaw)
        
        # 应该注册多个工具
        assert mock_openclaw.register_tool.call_count > 0


class TestFactoryFunction:
    """测试工厂函数"""
    
    def test_create_openclaw_tools(self):
        """测试创建 OpenClaw 工具"""
        from clawros_tools import create_openclaw_tools
        
        tools = create_openclaw_tools()
        
        assert isinstance(tools, ClawROSTools)
        assert tools.initialized is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
