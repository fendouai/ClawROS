#!/usr/bin/env python3
import argparse
import json
import os
import subprocess
from typing import Any, List


def find_openclaw_cli() -> str:
    candidates = [
        os.path.expanduser("~/.openclaw/bin/openclaw"),
        "/usr/local/bin/openclaw",
        "/opt/homebrew/bin/openclaw",
    ]
    for path in candidates:
        if os.path.isfile(path) and os.access(path, os.X_OK):
            return path
    raise FileNotFoundError("OpenClaw CLI not found")


def call_openclaw(cli_path: str, user_text: str, agent_id: str = "main") -> str:
    p = subprocess.run(
        [cli_path, "agent", "--agent", agent_id, "--message", user_text, "--json"],
        text=True,
        capture_output=True,
        timeout=120,
        check=False,
    )
    if p.returncode != 0:
        raise RuntimeError((p.stderr or p.stdout or "unknown error").strip())
    data = json.loads(p.stdout)
    payloads = data.get("result", {}).get("payloads", [])
    texts = [x.get("text", "").strip() for x in payloads if x.get("text")]
    return texts[-1] if texts else "[]"


def _extract_first_json_array(text: str) -> List[Any]:
    first = text.find("[")
    last = text.rfind("]")
    if first == -1 or last == -1 or last <= first:
        return []
    try:
        arr = json.loads(text[first : last + 1])
        return arr if isinstance(arr, list) else []
    except Exception:
        return []


def sanitize_plan(raw_steps: List[Any]) -> List[dict]:
    out: List[dict] = []
    for step in raw_steps:
        if not isinstance(step, dict):
            continue
        typ = str(step.get("type", "")).lower()
        if typ == "walk":
            linear = float(step.get("linear", 0.25))
            angular = float(step.get("angular", 0.0))
            seconds = float(step.get("seconds", 2.0))
            out.append(
                {
                    "type": "walk",
                    "linear": max(-0.6, min(0.6, linear)),
                    "angular": max(-1.2, min(1.2, angular)),
                    "seconds": max(0.5, min(8.0, seconds)),
                }
            )
        elif typ == "pose":
            posture = str(step.get("posture", step.get("name", "stand"))).lower()
            if posture not in {"stand", "crouch", "tpose"}:
                posture = "stand"
            seconds = float(step.get("seconds", 1.5))
            out.append({"type": "pose", "posture": posture, "seconds": max(0.3, min(6.0, seconds))})
        elif typ == "stop":
            out.append({"type": "stop", "seconds": max(0.2, min(4.0, float(step.get("seconds", 1.0))))})
    if not out:
        return [
            {"type": "walk", "linear": 0.35, "angular": 0.0, "seconds": 3.0},
            {"type": "walk", "linear": 0.2, "angular": 0.5, "seconds": 2.5},
            {"type": "pose", "posture": "tpose", "seconds": 2.0},
            {"type": "stop", "seconds": 1.0},
        ]
    return out[:12]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--text", required=True, help="用户自然语言任务文本")
    args = parser.parse_args()

    cli = find_openclaw_cli()
    prompt = (
        "你是 humanoid 任务规划器。"
        "把用户任务转成执行步骤 JSON 数组，只输出 JSON，不要解释。"
        "步骤对象格式只允许:\n"
        "1) {\"type\":\"walk\",\"linear\":0.3,\"angular\":0.0,\"seconds\":2.0}\n"
        "2) {\"type\":\"pose\",\"posture\":\"stand|crouch|tpose\",\"seconds\":1.5}\n"
        "3) {\"type\":\"stop\",\"seconds\":1.0}\n"
        f"用户任务: {args.text}"
    )
    raw = call_openclaw(cli, prompt)
    plan = sanitize_plan(_extract_first_json_array(raw))
    print(json.dumps(plan, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
