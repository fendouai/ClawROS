#!/usr/bin/env python3
"""
ClawROS 模拟环境演示

这是一个完整的演示，展示如何在模拟环境中使用 ClawROS 控制机器人。
无需真实的 ROS 环境即可运行！

运行方式:
    python examples/demo_simulation.py
"""

import sys
import os
import time
import math

# 添加 src 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from clawros_tools import ClawROSTools
from simple_simulator import create_simulated_bridge


def print_header(text: str) -> None:
    """打印标题"""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)


def print_state(state: dict) -> None:
    """打印机器人状态"""
    pos = state.get('position', {})
    print(f"  位置：({pos.get('x', 0):.2f}, {pos.get('y', 0):.2f})")
    print(f"  电量：{state.get('battery', 0):.1f}%")
    print(f"  状态：{state.get('status', 'unknown')}")


def demo_basic_movement(tools: ClawROSTools) -> None:
    """演示 1: 基本移动"""
    print_header("演示 1: 基本移动控制")
    
    print("\n1.1 前进 3 秒")
    result = tools.move_to("forward", speed=0.3)
    print(f"   {result}")
    time.sleep(3)
    
    print("\n1.2 获取机器人状态")
    state_result = tools.get_robot_state()
    print(state_result)
    
    print("\n1.3 右转 2 秒")
    # 使用自定义命令实现转向
    from clawros_bridge import ROSCommand, CommandType
    cmd = ROSCommand(
        type=CommandType.MOVE,
        target="turn_right",
        parameters={"angular": 0.5}
    )
    response = tools.bridge.execute_command(cmd)
    print(f"   {response.message}")
    time.sleep(2)
    
    print("\n1.4 停止")
    tools.emergency_stop()
    time.sleep(1)


def demo_navigation(tools: ClawROSTools) -> None:
    """演示 2: 自主导航"""
    print_header("演示 2: 自主导航")
    
    waypoints = [
        (2.0, 1.0, "检查点 A"),
        (1.0, 2.0, "检查点 B"),
        (-1.0, 1.0, "检查点 C"),
        (0.0, 0.0, "返回起点"),
    ]
    
    for i, (x, y, name) in enumerate(waypoints, 1):
        print(f"\n{i}. 导航到 {name} ({x}, {y})")
        result = tools.navigate_to(x, y)
        print(f"   {result}")
        
        # 等待导航完成（简单等待，实际应该检查状态）
        time.sleep(4)
        
        # 在检查点获取状态
        state = tools.bridge.get_robot_state()
        print_state(state)


def demo_sensor_scanning(tools: ClawROSTools) -> None:
    """演示 3: 传感器扫描"""
    print_header("演示 3: 传感器扫描")
    
    print("\n3.1 获取激光雷达数据")
    result = tools.get_sensor_data("lidar")
    print(f"   {result}")
    
    print("\n3.2 获取电池状态")
    result = tools.get_sensor_data("battery")
    print(f"   {result}")
    
    print("\n3.3 扫描环境")
    result = tools.scan_environment(resolution="medium")
    print(f"   {result}")


def demo_emergency_stop(tools: ClawROSTools) -> None:
    """演示 4: 紧急停止"""
    print_header("演示 4: 紧急停止功能")
    
    print("\n4.1 先让机器人移动")
    from clawros_bridge import ROSCommand, CommandType
    cmd = ROSCommand(
        type=CommandType.MOVE,
        target="forward",
        parameters={"linear": 0.5}
    )
    response = tools.bridge.execute_command(cmd)
    print(f"   {response.message}")
    time.sleep(1)
    
    print("\n4.2 触发紧急停止!")
    result = tools.emergency_stop()
    print(f"   {result}")
    
    print("\n4.3 验证已停止")
    state = tools.bridge.get_robot_state()
    vel = state.get('velocity', {})
    print(f"   线速度：{vel.get('linear', 0):.2f}")
    print(f"   角速度：{vel.get('angular', 0):.2f}")


def demo_complete_task(tools: ClawROSTools) -> None:
    """演示 5: 完整任务执行"""
    print_header("演示 5: 完整任务 - 仓库巡检")
    
    task_sequence = [
        ("移动到仓库入口", lambda: tools.move_to("warehouse_entrance", 0.3)),
        ("导航到货架 A", lambda: tools.navigate_to(2.0, 2.0)),
        ("扫描环境", lambda: tools.scan_environment()),
        ("导航到货架 B", lambda: tools.navigate_to(-2.0, 2.0)),
        ("再次扫描", lambda: tools.scan_environment()),
        ("返回充电站", lambda: tools.navigate_to(0.0, 0.0)),
    ]
    
    print("\n开始执行仓库巡检任务...\n")
    
    for i, (task_name, task_func) in enumerate(task_sequence, 1):
        print(f"{i}. {task_name}")
        result = task_func()
        print(f"   ✓ {result}")
        time.sleep(2)
    
    print("\n✓ 所有任务执行完成!")
    
    # 最终状态
    print("\n最终状态:")
    state = tools.bridge.get_robot_state()
    print_state(state)


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("  ClawROS 模拟环境演示")
    print("  无需真实 ROS 环境!")
    print("=" * 60)
    
    # 创建工具（使用模拟桥接）
    print("\n初始化模拟环境...")
    simulator_bridge = create_simulated_bridge()
    tools = ClawROSTools(bridge=simulator_bridge)
    
    if not tools.initialize():
        print("初始化失败!")
        return
    
    print("✓ 模拟环境初始化成功\n")
    
    try:
        # 运行所有演示
        demo_basic_movement(tools)
        demo_navigation(tools)
        demo_sensor_scanning(tools)
        demo_emergency_stop(tools)
        demo_complete_task(tools)
        
        print_header("演示完成")
        print("\n所有演示已成功完成！")
        print("\n提示:")
        print("  - 这个演示使用了模拟环境，无需真实 ROS")
        print("  - 真实环境中，只需配置真实的 ROS 桥接")
        print("  - 查看 docs/TESTING.md 了解更多测试信息")
        
    except KeyboardInterrupt:
        print("\n\n演示被用户中断")
    except Exception as e:
        print(f"\n演示出错：{e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n关闭模拟环境...")
        tools.shutdown()
        print("✓ 已关闭\n")


if __name__ == "__main__":
    main()
