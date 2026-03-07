"""
ClawROS 模拟器端到端测试

覆盖场景:
1) 完整模拟演示脚本可运行并正常退出
2) OpenClaw 模拟运行器可执行基本命令并正常退出
3) ros_gazebo 启动器（骨架）可初始化并执行命令路径
4) 独立模拟器启动器可启动并响应中断关闭
"""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _run(
    args: list[str],
    input_text: str | None = None,
    timeout: int = 90,
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src")
    return subprocess.run(
        args,
        cwd=ROOT,
        env=env,
        input=input_text,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )


def test_demo_simulation_full_flow() -> None:
    """完整模拟演示应成功执行并输出收尾信息。"""
    proc = _run([sys.executable, "examples/demo_simulation.py"], timeout=120)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    assert "ClawROS 模拟环境演示" in proc.stdout
    assert "演示完成" in proc.stdout
    assert "已关闭" in proc.stdout


def test_openclaw_sim_runner_commands() -> None:
    """OpenClaw 运行器应可执行本地命令。"""
    script_input = "state\nmove forward 0.2\nsensor battery\nstop\nexit\n"
    proc = _run(
        [sys.executable, "examples/openclaw_sim_runner.py"],
        input_text=script_input,
        timeout=60,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    assert "OpenClaw + ClawROS 模拟运行器" in proc.stdout
    assert "Robot State:" in proc.stdout
    assert "Successfully moved to forward" in proc.stdout
    assert "Emergency stop executed" in proc.stdout


def test_ros_gazebo_launcher_skeleton_flow() -> None:
    """ros_gazebo 启动器骨架应可初始化并处理命令。"""
    script_input = "state\nmove 0.2 0.0\nnav 1.0 0.5\nstop\nquit\n"
    proc = _run(
        [
            sys.executable,
            "examples/ros_gazebo_launcher.py",
            "--config",
            "config/clawros_config.yaml",
            "--print-commands",
        ],
        input_text=script_input,
        timeout=60,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    assert "ros_gazebo 启动命令" in proc.stdout
    assert "ros_gazebo 桥接已初始化" in proc.stdout
    assert "velocity command sent" in proc.stdout
    assert "navigation request accepted" in proc.stdout
    assert "桥接已关闭" in proc.stdout


def test_simulator_launcher_start_and_interrupt() -> None:
    """独立模拟器应可启动，并能在中断后正常关闭。"""
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src")
    proc = subprocess.Popen(
        [sys.executable, "examples/simulator_launcher.py"],
        cwd=ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        time.sleep(3)
        proc.send_signal(signal.SIGINT)
        out, _ = proc.communicate(timeout=15)
    finally:
        if proc.poll() is None:
            proc.kill()
            out, _ = proc.communicate(timeout=5)

    assert proc.returncode == 0, out
    assert "ClawROS 模拟环境" in out
    assert "模拟环境已启动" in out
    assert "模拟环境已关闭" in out
