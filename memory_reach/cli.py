from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
from shutil import copy2

APP_DIRS = [
    "projects",
    "daily",
    "sessions/active",
    "sessions/archive",
    "rules",
]

SENSITIVE_PATTERNS = [
    r"sk-[A-Za-z0-9]{10,}",
    r"ghp_[A-Za-z0-9]{10,}",
    r"xoxb-[A-Za-z0-9-]{10,}",
    r"BEGIN PRIVATE KEY",
]


def package_root() -> Path:
    return Path(__file__).resolve().parent.parent


def init_memory(base: Path) -> int:
    base.mkdir(parents=True, exist_ok=True)
    for d in APP_DIRS:
        (base / d).mkdir(parents=True, exist_ok=True)

    template_map = {
        "MEMORY.md": package_root() / "templates" / "MEMORY.md",
        "projects/example-project.md": package_root() / "templates" / "projects" / "example-project.md",
        "daily/2026-01-01.md": package_root() / "templates" / "daily" / "example-day.md",
        "rules/memory-rules.md": package_root() / "templates" / "rules" / "memory-rules.md",
        "rules/privacy-rules.md": package_root() / "templates" / "rules" / "privacy-rules.md",
        "rules/retention.md": package_root() / "templates" / "rules" / "retention.md",
    }

    for rel, src in template_map.items():
        dst = base / rel
        if not dst.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            copy2(src, dst)

    state = base / ".memory-reach.json"
    if not state.exists():
        state.write_text(json.dumps({"version": "0.1.0"}, indent=2), encoding="utf-8")

    print(f"Initialized Memory Reach at: {base}")
    return 0


def doctor(base: Path) -> int:
    checks: list[tuple[str, bool, str]] = []

    required = [
        base / "MEMORY.md",
        base / "projects",
        base / "daily",
        base / "sessions" / "archive",
        base / "rules" / "memory-rules.md",
    ]

    for p in required:
        checks.append((str(p.relative_to(base)), p.exists(), "exists" if p.exists() else "missing"))

    writable = os.access(base, os.W_OK) if base.exists() else False
    checks.append(("base_dir", writable, "writable" if writable else "not writable"))

    sensitive_hits = []
    if base.exists():
        for path in base.rglob("*.md"):
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            for pattern in SENSITIVE_PATTERNS:
                if re.search(pattern, text):
                    sensitive_hits.append(path)
                    break
    checks.append(("sensitive_scan", len(sensitive_hits) == 0, "clean" if not sensitive_hits else f"found in {len(sensitive_hits)} file(s)"))

    ok = True
    print("Memory Reach Doctor\n")
    for name, passed, detail in checks:
        icon = "✅" if passed else "❌"
        print(f"{icon} {name}: {detail}")
        ok = ok and passed
    if sensitive_hits:
        print("\nPotential sensitive files:")
        for p in sensitive_hits:
            print(f" - {p}")
    return 0 if ok else 1


def main() -> int:
    parser = argparse.ArgumentParser(prog="memory-reach")
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", help="Initialize Memory Reach structure")
    p_init.add_argument("path", nargs="?", default=".")

    p_doctor = sub.add_parser("doctor", help="Run health checks")
    p_doctor.add_argument("path", nargs="?", default=".")

    args = parser.parse_args()
    base = Path(args.path).expanduser().resolve()

    if args.command == "init":
        return init_memory(base)
    if args.command == "doctor":
        return doctor(base)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
