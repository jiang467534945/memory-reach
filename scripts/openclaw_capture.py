#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Bridge an OpenClaw session payload into Memory Reach")
    parser.add_argument("payload", help="Path to an OpenClaw-style JSON payload")
    parser.add_argument("--workspace", default=".", help="Memory Reach workspace path")
    parser.add_argument("--memory-reach-bin", default="memory-reach", help="memory-reach executable name/path")
    args = parser.parse_args()

    payload = Path(args.payload).expanduser().resolve()
    workspace = Path(args.workspace).expanduser().resolve()

    if not payload.exists():
        print(f"Payload not found: {payload}", file=sys.stderr)
        return 1

    cmd = [
        args.memory_reach_bin,
        "capture-openclaw",
        str(payload),
        "--path",
        str(workspace),
    ]
    return subprocess.run(cmd, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
