# ClawROS 使用示例

## 示例 1: 基本移动控制

### Python 脚本

```python
#!/usr/bin/env python3
"""
示例 1: 使用 ClawROS 控制机器人移动
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from clawros_bridge import create_bridge, ROSCommand, CommandType

def main():
    # 创建桥接
    bridge = create_bridge()
    
    # 初始化
    if not bridge.initialize():
        print("初始化失败!")
        return
    
    print("ClawROS 初始化成功!")
    
    try:
        # 示例 1: 前进
        print("\n1. 前进 1 米")
        cmd = ROSCommand(
            type=CommandType.MOVE,
            target="forward",
            parameters={"distance": 1.0, "speed": 0.3}
        )
        response = bridge.execute_command(cmd)
        print(f"结果：{response.message}")
        
        # 示例 2: 转向
        print("\n2. 向右转 90 度")
        cmd = ROSCommand(
            type=CommandType.MOVE,
            target="turn_right",
            parameters={"angle": 1.57}  # 弧度
        )
        response = bridge.execute_command(cmd)
        print(f"结果：{response.message}")
        
        # 示例 3: 导航到指定位置
        print("\n3. 导航到坐标 (2.0, 1.5)")
        cmd = ROSCommand(
            type=CommandType.NAVIGATE,
            target="navigation_goal",
            parameters={"x": 2.0, "y": 1.5, "theta": 0.0}
        )
        response = bridge.execute_command(cmd)
        print(f"结果：{response.message}")
        
        # 示例 4: 获取机器人状态
        print("\n4. 获取机器人状态")
        state = bridge.get_robot_state()
        print(f"位置：{state.get('position', {})}")
        print(f"电量：{state.get('battery', 0):.1f}%")
        print(f"状态：{state.get('status', 'unknown')}")
        
    finally:
        # 关闭桥接
        bridge.shutdown()
        print("\nClawROS 已关闭")

if __name__ == "__main__":
    main()
```

## 示例 2: 与 OpenClaw 集成

```python
#!/usr/bin/env python3
"""
示例 2: 将 ClawROS 工具注册到 OpenClaw
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from clawros_tools import ClawROSTools, register_with_openclaw

def main():
    # 创建 ClawROS 工具
    tools = ClawROSTools()
    
    # 初始化工具
    if not tools.initialize():
        print("ClawROS 工具初始化失败!")
        return
    
    print("ClawROS 工具初始化成功!")
    
    # 显示所有可用工具
    print("\n可用工具列表:")
    for i, tool in enumerate(tools.get_tools(), 1):
        print(f"  {i}. {tool['name']}: {tool['description']}")
    
    # 如果已有 OpenClaw 实例，可以这样注册
    # try:
    #     from openclaw import OpenClaw
    #     openclaw = OpenClaw()
    #     register_with_openclaw(tools, openclaw)
    #     print("\n工具已注册到 OpenClaw!")
    # except ImportError:
    #     print("\nOpenClaw 未安装，跳过注册")
    
    # 测试几个工具
    print("\n测试工具调用:")
    
    print("\n1. 获取机器人状态:")
    result = tools.get_robot_state()
    print(result)
    
    print("\n2. 测试移动:")
    result = tools.move_to("test_location", speed=0.3)
    print(result)
    
    print("\n3. 测试紧急停止:")
    result = tools.emergency_stop()
    print(result)
    
    # 关闭工具
    tools.shutdown()
    print("\nClawROS 工具已关闭")

if __name__ == "__main__":
    main()
```

## 示例 3: 命令行控制

```python
#!/usr/bin/env python3
"""
示例 3: 命令行交互式控制机器人
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from clawros_tools import ClawROSTools

def print_help():
    """打印帮助信息"""
    print("""
ClawROS 命令行控制

可用命令:
  move <location> [speed]    - 移动到指定位置
  navigate <x> <y> [theta]   - 导航到坐标
  pick <object>              - 抓取物体
  place <location>           - 放置物体
  sensor <type>              - 获取传感器数据
  state                      - 获取机器人状态
  stop                       - 紧急停止
  help                       - 显示帮助
  quit                       - 退出程序

示例:
  move kitchen 0.5
  navigate 2.0 1.5 0.785
  pick cup
  sensor battery
""")

def main():
    print("欢迎使用 ClawROS 命令行控制!")
    print("输入 'help' 查看可用命令\n")
    
    # 初始化工具
    tools = ClawROSTools()
    if not tools.initialize():
        print("初始化失败!")
        return
    
    try:
        while True:
            try:
                cmd_input = input("clawros> ").strip()
            except (KeyboardInterrupt, EOFError):
                print("\n再见!")
                break
            
            if not cmd_input:
                continue
            
            parts = cmd_input.split()
            command = parts[0].lower()
            args = parts[1:]
            
            try:
                if command == "quit" or command == "exit":
                    print("再见!")
                    break
                
                elif command == "help":
                    print_help()
                
                elif command == "move":
                    if len(args) < 1:
                        print("用法：move <location> [speed]")
                        continue
                    location = args[0]
                    speed = float(args[1]) if len(args) > 1 else 0.5
                    result = tools.move_to(location, speed)
                    print(result)
                
                elif command == "navigate":
                    if len(args) < 2:
                        print("用法：navigate <x> <y> [theta]")
                        continue
                    x = float(args[0])
                    y = float(args[1])
                    theta = float(args[2]) if len(args) > 2 else None
                    result = tools.navigate_to(x, y, theta)
                    print(result)
                
                elif command == "pick":
                    if len(args) < 1:
                        print("用法：pick <object>")
                        continue
                    obj = args[0]
                    result = tools.pick_object(obj)
                    print(result)
                
                elif command == "place":
                    if len(args) < 1:
                        print("用法：place <location>")
                        continue
                    loc = args[0]
                    result = tools.place_object(loc)
                    print(result)
                
                elif command == "sensor":
                    if len(args) < 1:
                        print("用法：sensor <type>")
                        continue
                    sensor_type = args[0]
                    result = tools.get_sensor_data(sensor_type)
                    print(result)
                
                elif command == "state":
                    result = tools.get_robot_state()
                    print(result)
                
                elif command == "stop":
                    result = tools.emergency_stop()
                    print(result)
                
                else:
                    print(f"未知命令：{command}")
                    print("输入 'help' 查看可用命令")
            
            except Exception as e:
                print(f"执行错误：{e}")
    
    finally:
        tools.shutdown()

if __name__ == "__main__":
    main()
```

## 示例 4: 自定义 ROS 命令

```python
#!/usr/bin/env python3
"""
示例 4: 执行自定义 ROS 命令
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from clawros_bridge import create_bridge, ROSCommand, CommandType

def custom_velocity_control():
    """自定义速度控制示例"""
    bridge = create_bridge()
    
    if not bridge.initialize():
        return
    
    try:
        # 发送自定义速度命令
        cmd = ROSCommand(
            type=CommandType.CUSTOM,
            target="cmd_vel",
            parameters={
                "linear": {"x": 0.3, "y": 0.0, "z": 0.0},
                "angular": {"x": 0.0, "y": 0.0, "z": 0.5}
            }
        )
        
        response = bridge.execute_command(cmd)
        print(f"速度命令执行：{response.message}")
        
    finally:
        bridge.shutdown()

def custom_arm_control():
    """自定义机械臂控制示例"""
    bridge = create_bridge()
    
    if not bridge.initialize():
        return
    
    try:
        # 发送机械臂关节命令
        cmd = ROSCommand(
            type=CommandType.CUSTOM,
            target="arm_joint_command",
            parameters={
                "joints": [0.5, -0.3, 0.8, 0.2, -0.1, 0.4],
                "velocities": [0.1] * 6,
                "effort": [10.0] * 6
            }
        )
        
        response = bridge.execute_command(cmd)
        print(f"机械臂命令执行：{response.message}")
        
    finally:
        bridge.shutdown()

if __name__ == "__main__":
    print("=== 自定义速度控制 ===")
    custom_velocity_control()
    
    print("\n=== 自定义机械臂控制 ===")
    custom_arm_control()
```

## 示例 5: 批处理任务

```python
#!/usr/bin/env python3
"""
示例 5: 执行批处理任务
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from clawros_tools import ClawROSTools
import time

def warehouse_task():
    """仓库搬运任务示例"""
    tools = ClawROSTools()
    
    if not tools.initialize():
        return
    
    try:
        tasks = [
            ("移动到仓库 A", lambda: tools.move_to("warehouse_a")),
            ("抓取货物", lambda: tools.pick_object("package_1")),
            ("移动到分拣区", lambda: tools.move_to("sorting_area")),
            ("放置货物", lambda: tools.place_object("conveyor_belt")),
            ("返回充电站", lambda: tools.move_to("charging_station")),
        ]
        
        print("开始执行仓库任务序列...\n")
        
        for i, (task_name, task_func) in enumerate(tasks, 1):
            print(f"步骤 {i}/{len(tasks)}: {task_name}")
            result = task_func()
            print(f"  结果：{result}\n")
            time.sleep(1)  # 任务间延迟
        
        print("所有任务执行完成!")
        
    finally:
        tools.shutdown()

def inspection_task():
    """巡检任务示例"""
    tools = ClawROSTools()
    
    if not tools.initialize():
        return
    
    try:
        checkpoints = [
            ("检查点 1", 1.0, 1.0),
            ("检查点 2", 3.0, 1.0),
            ("检查点 3", 3.0, 3.0),
            ("检查点 4", 1.0, 3.0),
        ]
        
        print("开始执行巡检任务...\n")
        
        for name, x, y in checkpoints:
            print(f"前往 {name}: ({x}, {y})")
            result = tools.navigate_to(x, y)
            print(f"  {result}")
            
            # 在检查点扫描环境
            print(f"  扫描环境...")
            scan_result = tools.scan_environment(resolution="medium")
            print(f"  {scan_result}\n")
            
            time.sleep(2)  # 每个检查点停留 2 秒
        
        print("巡检任务完成!")
        
    finally:
        tools.shutdown()

if __name__ == "__main__":
    print("=== 仓库搬运任务 ===")
    warehouse_task()
    
    print("\n=== 巡检任务 ===")
    inspection_task()
```

## 运行示例

```bash
# 运行示例 1
python examples/example_1_basic_move.py

# 运行示例 2
python examples/example_2_openclaw_integration.py

# 运行示例 3 (交互式)
python examples/example_3_cli_control.py

# 运行示例 4
python examples/example_4_custom_commands.py

# 运行示例 5
python examples/example_5_batch_tasks.py
```

## 注意事项

1. **ROS 环境**: 确保已正确安装 ROS2 并 sourced 环境
2. **模拟器**: 可以使用 Gazebo 等模拟器进行测试
3. **安全**: 在真实机器人上运行前，先在模拟环境中测试
4. **配置**: 根据实际机器人修改配置文件

## 故障排除

1. **连接失败**: 检查 ROS_MASTER_URI 和 ROS_HOSTNAME
2. **命令超时**: 增加命令超时时间或检查网络
3. **传感器数据为空**: 确认传感器节点正常运行
