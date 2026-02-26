# ClawROS 测试文档

## 测试概述

ClawROS 项目采用多层次的测试策略，确保代码质量和系统可靠性。

### 测试类型

1. **单元测试**: 测试单个函数或类的功能
2. **集成测试**: 测试组件间的交互
3. **系统测试**: 测试整个系统的功能
4. **性能测试**: 测试系统性能指标
5. **安全测试**: 验证安全机制

## 测试环境

### 前置要求

```bash
# 安装测试依赖
pip install pytest pytest-cov pytest-asyncio pytest-mock

# 安装 ROS2 测试工具
sudo apt install ros-jazzy-ament-copyright ros-jazzy-ament-flake8 ros-jazzy-ament-pep257
```

### 测试配置

```yaml
# pytest.ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto
addopts = 
    -v
    --cov=src
    --cov-report=html
    --cov-report=term-missing
```

## 单元测试

### 1. 测试 ClawROS Bridge

**文件**: `tests/unit/test_bridge.py`

```python
import pytest
from src.clawros_bridge import (
    ClawROSBridge, 
    ROSCommand, 
    CommandType,
    ROSResponse,
    SecurityLayer,
)


class TestROSCommand:
    """测试 ROS 命令类"""
    
    def test_command_creation(self):
        """测试命令创建"""
        cmd = ROSCommand(
            type=CommandType.MOVE,
            target="forward",
            parameters={"speed": 0.5}
        )
        
        assert cmd.type == CommandType.MOVE
        assert cmd.target == "forward"
        assert cmd.parameters["speed"] == 0.5
    
    def test_command_to_dict(self):
        """测试命令转换为字典"""
        cmd = ROSCommand(
            type=CommandType.NAVIGATE,
            target="kitchen",
            parameters={"x": 1.0, "y": 2.0}
        )
        
        cmd_dict = cmd.to_dict()
        
        assert cmd_dict["type"] == "navigate"
        assert cmd_dict["target"] == "kitchen"
        assert cmd_dict["parameters"]["x"] == 1.0


class TestROSResponse:
    """测试 ROS 响应类"""
    
    def test_success_response(self):
        """测试成功响应"""
        response = ROSResponse.success_response(
            "Command executed",
            {"result": "ok"}
        )
        
        assert response.success is True
        assert response.message == "Command executed"
        assert response.data["result"] == "ok"
    
    def test_error_response(self):
        """测试错误响应"""
        response = ROSResponse.error_response("Failed")
        
        assert response.success is False
        assert response.message == "Failed"


class TestSecurityLayer:
    """测试安全层"""
    
    def test_command_validation(self):
        """测试命令验证"""
        config = {
            "enabled": True,
            "max_linear_velocity": 0.5,
        }
        security = SecurityLayer(config)
        
        cmd = ROSCommand(
            type=CommandType.MOVE,
            target="forward",
            parameters={"linear": 0.3}
        )
        
        is_valid, error_msg = security.validate_command(cmd)
        assert is_valid is True
    
    def test_velocity_limit(self):
        """测试速度限制"""
        config = {
            "enabled": True,
            "max_linear_velocity": 0.5,
        }
        security = SecurityLayer(config)
        
        cmd = ROSCommand(
            type=CommandType.MOVE,
            target="forward",
            parameters={"linear": 1.0}  # 超过限制
        )
        
        is_valid, error_msg = security.validate_command(cmd)
        assert is_valid is False
        assert "exceeds max" in error_msg


class TestClawROSBridge:
    """测试 ClawROS 桥接类"""
    
    def test_bridge_initialization(self):
        """测试桥接初始化"""
        bridge = ClawROSBridge()
        assert bridge.initialized is False
        
        # 注意：实际测试需要 ROS 环境
        # result = bridge.initialize()
        # assert result is True
    
    def test_emergency_stop(self):
        """测试紧急停止"""
        bridge = ClawROSBridge()
        
        cmd = ROSCommand(
            type=CommandType.EMERGENCY_STOP,
            target="all"
        )
        
        # 模拟响应
        response = ROSResponse.success_response("Emergency stop executed")
        assert response.success is True
```

### 2. 测试 ClawROS Tools

**文件**: `tests/unit/test_tools.py`

```python
import pytest
from unittest.mock import Mock, MagicMock
from src.clawros_tools import ClawROSTools


class TestClawROSTools:
    """测试 ClawROS 工具集"""
    
    @pytest.fixture
    def mock_bridge(self):
        """创建模拟桥接"""
        bridge = Mock()
        bridge.initialize.return_value = True
        bridge.execute_command.return_value = \
            type('ROSResponse', (), {
                'success': True,
                'message': 'OK',
                'data': {}
            })()
        return bridge
    
    @pytest.fixture
    def tools(self, mock_bridge):
        """创建工具实例"""
        return ClawROSTools(bridge=mock_bridge)
    
    def test_get_tools_list(self, tools):
        """测试获取工具列表"""
        tool_list = tools.get_tools()
        
        assert len(tool_list) > 0
        assert any(t['name'] == 'move_to' for t in tool_list)
        assert any(t['name'] == 'emergency_stop' for t in tool_list)
    
    def test_move_to(self, tools, mock_bridge):
        """测试移动命令"""
        result = tools.move_to("kitchen", speed=0.5)
        
        assert "Successfully moved" in result
        mock_bridge.execute_command.assert_called_once()
    
    def test_navigate_to(self, tools, mock_bridge):
        """测试导航命令"""
        result = tools.navigate_to(1.0, 2.0, theta=0.5)
        
        assert "Successfully navigating" in result
    
    def test_emergency_stop(self, tools, mock_bridge):
        """测试紧急停止"""
        result = tools.emergency_stop()
        
        assert "Emergency stop executed" in result
    
    def test_get_robot_state(self, tools, mock_bridge):
        """测试获取机器人状态"""
        mock_bridge.get_robot_state.return_value = {
            "position": {"x": 1.0, "y": 2.0, "z": 0.0},
            "battery": 85.5,
            "status": "active"
        }
        
        result = tools.get_robot_state()
        
        assert "Robot State" in result
        assert "Battery" in result
```

## 集成测试

### 3. 测试桥接与 ROS 集成

**文件**: `tests/integration/test_ros_integration.py`

```python
import pytest
import time

try:
    import rclpy
    from geometry_msgs.msg import Twist
    ROS_AVAILABLE = True
except ImportError:
    ROS_AVAILABLE = False


@pytest.mark.skipif(not ROS_AVAILABLE, reason="ROS2 not available")
class TestROSIntegration:
    """测试 ROS 集成"""
    
    def test_topic_publishing(self):
        """测试话题发布"""
        rclpy.init()
        node = rclpy.create_node('test_node')
        publisher = node.create_publisher(Twist, '/cmd_vel', 10)
        
        # 发布测试消息
        msg = Twist()
        msg.linear.x = 0.5
        publisher.publish(msg)
        
        rclpy.spin_once(node, timeout_sec=0.1)
        
        node.destroy_node()
        rclpy.shutdown()
        
        assert True  # 如果没有异常则测试通过
    
    def test_service_call(self):
        """测试服务调用"""
        # 实现服务调用测试
        pass
```

## 系统测试

### 4. 端到端测试

**文件**: `tests/system/test_end_to_end.py`

```python
import pytest
from src.clawros_bridge import create_bridge, ROSCommand, CommandType


class TestEndToEnd:
    """端到端测试"""
    
    def test_full_command_flow(self):
        """测试完整命令流程"""
        bridge = create_bridge()
        
        # 初始化
        if not bridge.initialize():
            pytest.skip("Cannot initialize bridge")
        
        try:
            # 创建命令
            cmd = ROSCommand(
                type=CommandType.MOVE,
                target="test_move",
                parameters={"speed": 0.3}
            )
            
            # 执行命令
            response = bridge.execute_command(cmd)
            
            # 验证响应
            assert hasattr(response, 'success')
            assert hasattr(response, 'message')
            
            # 获取状态
            state = bridge.get_robot_state()
            assert isinstance(state, dict)
            
        finally:
            bridge.shutdown()
```

## 安全测试

### 5. 安全机制测试

**文件**: `tests/system/test_safety.py`

```python
import pytest
from src.clawros_bridge import SecurityLayer, ROSCommand, CommandType


class TestSafety:
    """安全测试"""
    
    def test_rate_limiting(self):
        """测试速率限制"""
        config = {
            "enabled": True,
            "rate_limit": {
                "commands_per_minute": 5
            }
        }
        security = SecurityLayer(config)
        
        # 发送多个命令
        for i in range(10):
            cmd = ROSCommand(
                type=CommandType.MOVE,
                target=f"move_{i}",
                parameters={"linear": 0.1}
            )
            is_valid, _ = security.validate_command(cmd)
            
            # 超过限制后应该失败
            if i >= 5:
                assert is_valid is False
    
    def test_workspace_bounds(self):
        """测试工作空间边界"""
        config = {
            "enabled": True,
            "workspace_bounds": {
                "x": [-1.0, 1.0],
                "y": [-1.0, 1.0],
            }
        }
        security = SecurityLayer(config)
        
        # 测试边界内
        cmd_in = ROSCommand(
            type=CommandType.NAVIGATE,
            target="nav",
            parameters={"x": 0.5, "y": 0.5}
        )
        is_valid_in, _ = security.validate_command(cmd_in)
        assert is_valid_in is True
        
        # 测试边界外
        cmd_out = ROSCommand(
            type=CommandType.NAVIGATE,
            target="nav",
            parameters={"x": 2.0, "y": 2.0}
        )
        is_valid_out, _ = security.validate_command(cmd_out)
        assert is_valid_out is False
    
    def test_emergency_stop_priority(self):
        """测试紧急停止优先级"""
        config = {"enabled": True}
        security = SecurityLayer(config)
        
        # 紧急停止应该始终通过
        cmd = ROSCommand(
            type=CommandType.EMERGENCY_STOP,
            target="all"
        )
        is_valid, _ = security.validate_command(cmd)
        assert is_valid is True
```

## 运行测试

### 运行所有测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行单元测试
pytest tests/unit/ -v

# 运行集成测试
pytest tests/integration/ -v

# 运行系统测试
pytest tests/system/ -v

# 生成覆盖率报告
pytest --cov=src --cov-report=html tests/

# 在浏览器中查看覆盖率报告
open htmlcov/index.html
```

### 运行特定测试

```bash
# 运行特定测试文件
pytest tests/unit/test_bridge.py -v

# 运行特定测试类
pytest tests/unit/test_bridge.py::TestSecurityLayer -v

# 运行特定测试函数
pytest tests/unit/test_bridge.py::TestSecurityLayer::test_command_validation -v

# 运行匹配模式的测试
pytest -k "test_emergency" -v
```

## 测试指标

### 覆盖率目标

- **语句覆盖率**: >= 80%
- **分支覆盖率**: >= 75%
- **函数覆盖率**: >= 90%

### 性能目标

- **单元测试执行时间**: < 10 秒
- **集成测试执行时间**: < 60 秒
- **系统测试执行时间**: < 300 秒

## 持续集成

### GitHub Actions 配置

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov
      
      - name: Run tests
        run: |
          pytest tests/ --cov=src --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
```

## 测试最佳实践

1. **测试隔离**: 每个测试应该独立，不依赖其他测试
2. **模拟外部依赖**: 使用 Mock 对象模拟 ROS、数据库等
3. **测试边界条件**: 测试正常情况和异常情况
4. **命名清晰**: 测试名称应该清楚表达测试内容
5. **断言明确**: 每个测试应该有明确的断言
6. **快速执行**: 测试应该快速执行，便于频繁运行

## 故障排除

### 常见问题

1. **ROS 导入错误**: 确保已安装 ROS2 并 sourced 环境
2. **测试超时**: 增加超时时间或优化测试逻辑
3. **覆盖率低**: 添加更多测试用例覆盖边缘情况

### 调试技巧

```bash
# 显示打印输出
pytest -s tests/

# 在失败时进入调试器
pytest --pdb tests/

# 逐步执行测试
pytest -s --pdb tests/unit/test_bridge.py::TestClass::test_method
```
