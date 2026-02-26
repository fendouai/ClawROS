#!/usr/bin/env python3
"""
ClawROS 模拟环境启动文件

启动模拟环境和 ClawROS 桥接
"""

import sys
import os
import time

# 添加 src 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from simple_simulator import create_simulated_bridge, SimpleRobotSimulator
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("  ClawROS 模拟环境")
    print("  按 Ctrl+C 退出")
    print("=" * 60 + "\n")
    
    # 创建模拟器
    simulator = create_simulated_bridge()
    
    # 初始化
    logger.info("初始化模拟环境...")
    if not simulator.initialize():
        logger.error("初始化失败")
        return
    
    logger.info("✓ 模拟环境已启动")
    logger.info("机器人初始位置：(0.0, 0.0)")
    
    # 添加状态回调
    def state_callback(state):
        # 可以在此添加状态显示逻辑
        pass
    
    simulator.simulator.add_state_callback(state_callback)
    
    try:
        # 保持运行
        while True:
            time.sleep(1)
            
            # 显示状态
            state = simulator.get_robot_state()
            pos = state['position']
            battery = state['battery']
            status = state['status']
            
            # 清屏并显示状态（简单实现）
            print(f"\r位置：({pos['x']:6.2f}, {pos['y']:6.2f}) | "
                  f"电量：{battery:5.1f}% | "
                  f"状态：{status:8s}", end='', flush=True)
    
    except KeyboardInterrupt:
        print("\n\n收到退出信号...")
    finally:
        logger.info("关闭模拟环境...")
        simulator.shutdown()
        logger.info("✓ 模拟环境已关闭")


if __name__ == "__main__":
    main()
