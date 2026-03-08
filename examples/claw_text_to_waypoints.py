#!/usr/bin/env python3
import argparse
import json
import os
import re
import subprocess
from typing import List


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


def parse_waypoints(text: str) -> List[List[float]]:
    # 优先抽取第一个 JSON 数组片段
    first = text.find("[")
    last = text.rfind("]")
    if first != -1 and last != -1 and last > first:
        candidate = text[first : last + 1]
        try:
            obj = json.loads(candidate)
            if isinstance(obj, list):
                out = []
                for p in obj:
                    if isinstance(p, (list, tuple)) and len(p) >= 2:
                        out.append([float(p[0]), float(p[1])])
                    elif isinstance(p, dict) and "x" in p and "y" in p:
                        out.append([float(p["x"]), float(p["y"])])
                if out:
                    return _sanitize(out)
        except Exception:
            pass

    # 先尝试直接 JSON
    try:
        obj = json.loads(text)
        if isinstance(obj, list):
            out = []
            for p in obj:
                if isinstance(p, (list, tuple)) and len(p) >= 2:
                    out.append([float(p[0]), float(p[1])])
                elif isinstance(p, dict) and "x" in p and "y" in p:
                    out.append([float(p["x"]), float(p["y"])])
            if out:
                return _sanitize(out)
    except Exception:
        pass

    # 兜底：提取文本中的数字对
    nums = [float(x) for x in re.findall(r"-?\d+(?:\.\d+)?", text)]
    out = []
    for i in range(0, len(nums) - 1, 2):
        out.append([nums[i], nums[i + 1]])
    return _sanitize(out)


def _sanitize(points: List[List[float]]) -> List[List[float]]:
    clean = []
    for x, y in points:
        if -10.0 <= x <= 10.0 and -10.0 <= y <= 10.0:
            clean.append([round(float(x), 3), round(float(y), 3)])
    if not clean:
        return []
    # 去重保持顺序
    uniq = []
    seen = set()
    for p in clean:
        key = (p[0], p[1])
        if key not in seen:
            uniq.append(p)
            seen.add(key)
    return uniq[:8]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--text", required=True, help="用户自然语言任务文本")
    args = parser.parse_args()

    cli = find_openclaw_cli()
    direct = _extract_pairs_from_text(args.text)
    prompt = (
        "把用户任务转成 2D waypoint 列表。"
        "只输出 JSON 数组，不要解释。格式必须是 [[x,y],[x,y],...]. "
        f"用户任务: {args.text}"
    )
    raw = call_openclaw(cli, prompt)
    points = parse_waypoints(raw)
    if direct:
        points = direct
    if not points:
        print("[]")
        return 1
    print(json.dumps(points, ensure_ascii=False))
    return 0


def _extract_pairs_from_text(text: str) -> List[List[float]]:
    pairs = []
    for m in re.finditer(r"\(\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*\)", text):
        pairs.append([float(m.group(1)), float(m.group(2))])
    return _sanitize(pairs)


if __name__ == "__main__":
    raise SystemExit(main())
