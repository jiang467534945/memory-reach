from __future__ import annotations

import argparse
import json
import os
import re
from datetime import datetime, timezone
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

STOPWORDS = {
    "the",
    "and",
    "for",
    "that",
    "with",
    "this",
    "from",
    "have",
    "were",
    "your",
    "about",
    "into",
    "when",
    "what",
    "will",
    "would",
    "there",
    "they",
    "them",
    "then",
    "than",
    "just",
    "been",
    "also",
    "their",
    "should",
    "could",
    "project",
    "memory",
    "agent",
    "session",
}


def package_root() -> Path:
    return Path(__file__).resolve().parent.parent


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def utc_today() -> str:
    return utc_now().strftime("%Y-%m-%d")


def project_slug(name: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9._-]+", "-", name.strip()).strip("-").lower()
    return slug or "project"


def ensure_file(dst: Path, src: Path) -> None:
    if not dst.exists():
        dst.parent.mkdir(parents=True, exist_ok=True)
        copy2(src, dst)


def read_text_input(value: str | None) -> str:
    if not value or value == "-":
        import sys

        return sys.stdin.read()
    if "\n" in value or "\r" in value:
        return value
    try:
        path = Path(value)
        if path.exists():
            return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return value
    return value


def read_json_input(value: str | None) -> dict:
    text = read_text_input(value)
    return json.loads(text)


def append_section(path: Path, heading: str, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""
    block = heading + "\n" + "\n".join(lines).rstrip() + "\n"
    if existing and not existing.endswith("\n"):
        existing += "\n"
    path.write_text(existing + ("\n" if existing else "") + block, encoding="utf-8")


def extract_bullets(text: str, limit: int = 5) -> list[str]:
    bullets: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        line = re.sub(r"^[-*•\d.\)\s]+", "", line).strip()
        if len(line) < 12:
            continue
        if line.lower().startswith(("system:", "conversation info", "sender", "chat history")):
            continue
        bullets.append(f"- {line[:220]}")
        if len(bullets) >= limit:
            break
    return bullets


def suggest_items(text: str, limit: int = 5) -> list[str]:
    candidates = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or len(line) < 18:
            continue
        if any(token in line.lower() for token in ["decided", "decision", "prefer", "remember", "important", "always", "never"]):
            candidates.append(f"- {line[:220]}")
        if len(candidates) >= limit:
            break
    if candidates:
        return candidates

    counts: dict[str, int] = {}
    for token in re.findall(r"[A-Za-z][A-Za-z0-9_-]{3,}", text.lower()):
        if token in STOPWORDS:
            continue
        counts[token] = counts.get(token, 0) + 1
    top = [w for w, c in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:limit] if c > 1]
    return [f"- Candidate recurring topic: {w}" for w in top]


def ensure_base(base: Path) -> None:
    if not (base / ".memory-reach.json").exists():
        init_memory(base)


def render_openclaw_transcript(payload: dict) -> tuple[str, str]:
    meta = payload.get("meta", {}) if isinstance(payload, dict) else {}
    session_id = str(payload.get("session_id") or payload.get("sessionId") or meta.get("session_id") or utc_now().strftime("openclaw-%Y%m%d-%H%M%S"))
    lines = [f"# OpenClaw Session {session_id}"]

    if meta:
        lines.append("")
        lines.append("## Metadata")
        for key in ["channel", "chat_id", "chat_type", "surface", "user", "started_at"]:
            if key in meta and meta[key] not in (None, ""):
                lines.append(f"- {key}: {meta[key]}")

    msgs = payload.get("messages", []) if isinstance(payload, dict) else []
    if msgs:
        lines.append("")
        lines.append("## Transcript")
        for item in msgs:
            role = item.get("role", "unknown")
            text = (item.get("content") or item.get("text") or "").strip()
            if not text:
                continue
            lines.append(f"### {role}")
            lines.append(text)
            lines.append("")

    summary = payload.get("summary")
    if summary:
        lines.append("## Summary")
        lines.append(str(summary).strip())

    return session_id, "\n".join(lines).strip() + "\n"


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
        ensure_file(base / rel, src)

    state = base / ".memory-reach.json"
    if not state.exists():
        state.write_text(json.dumps({"version": "0.4.0"}, indent=2), encoding="utf-8")

    print(f"Initialized Memory Reach at: {base}")
    return 0


def new_project(base: Path, name: str) -> int:
    base.mkdir(parents=True, exist_ok=True)
    (base / "projects").mkdir(parents=True, exist_ok=True)
    slug = project_slug(name)
    dst = base / "projects" / f"{slug}.md"
    if dst.exists():
        print(f"Project already exists: {dst}")
        return 1

    template = (package_root() / "templates" / "projects" / "example-project.md").read_text(encoding="utf-8")
    title = name.strip() or slug
    content = template.replace("# Example Project", f"# {title}")
    dst.write_text(content, encoding="utf-8")
    print(f"Created project memory: {dst}")
    return 0


def new_daily(base: Path, date_str: str | None = None) -> int:
    base.mkdir(parents=True, exist_ok=True)
    (base / "daily").mkdir(parents=True, exist_ok=True)
    day = date_str or utc_today()
    dst = base / "daily" / f"{day}.md"
    if dst.exists():
        print(f"Daily note already exists: {dst}")
        return 0
    dst.write_text(
        f"# {day}\n\n## Today\n- \n\n## Progress\n- \n\n## Decisions\n- \n\n## Issues\n- \n\n## Next\n- \n",
        encoding="utf-8",
    )
    print(f"Created daily note: {dst}")
    return 0


def capture_session(base: Path, source: str | None, session_id: str | None = None) -> int:
    ensure_base(base)
    text = read_text_input(source)
    if not text.strip():
        print("No session content provided")
        return 1

    stamp = utc_now()
    sid = session_id or stamp.strftime("session-%Y%m%d-%H%M%S")
    archive = base / "sessions" / "archive" / f"{sid}.md"
    archive.parent.mkdir(parents=True, exist_ok=True)
    archive.write_text(text.rstrip() + "\n", encoding="utf-8")

    daily_path = base / "daily" / f"{stamp.strftime('%Y-%m-%d')}.md"
    if not daily_path.exists():
        new_daily(base, stamp.strftime('%Y-%m-%d'))

    bullets = extract_bullets(text)
    if bullets:
        append_section(daily_path, f"## Captured Session {sid}", bullets)

    print(f"Captured session: {archive}")
    if bullets:
        print(f"Updated daily note: {daily_path}")
    return 0


def capture_openclaw(base: Path, source: str | None) -> int:
    ensure_base(base)
    payload = read_json_input(source)
    session_id, rendered = render_openclaw_transcript(payload)
    return capture_session(base, rendered, session_id=session_id)


def sync_day(base: Path, date_str: str | None = None) -> int:
    ensure_base(base)
    day = date_str or utc_today()
    daily_path = base / "daily" / f"{day}.md"
    if not daily_path.exists():
        new_daily(base, day)

    archives = sorted((base / "sessions" / "archive").glob("*.md")) if (base / "sessions" / "archive").exists() else []
    day_prefix = day.replace("-", "")
    matched = [p for p in archives if day_prefix in p.stem or day in p.stem]
    if not matched:
        print(f"No archived sessions matched {day}")
        return 0

    summary_lines = [f"- {p.stem}" for p in matched]
    append_section(daily_path, f"## Session Sync {day}", summary_lines)
    print(f"Synced {len(matched)} session(s) into: {daily_path}")
    return 0


def suggest_memory(base: Path, source: str | None) -> int:
    ensure_base(base)
    text = read_text_input(source)
    if not text.strip():
        print("No content provided")
        return 1

    suggestions = suggest_items(text)
    print("Memory Suggestions\n")
    if not suggestions:
        print("- No strong long-term memory candidates found")
        return 0
    for item in suggestions:
        print(item)
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

    memory_exists = (base / "MEMORY.md").exists()
    memory_has_heading = False
    if memory_exists:
        text = (base / "MEMORY.md").read_text(encoding="utf-8", errors="ignore").strip()
        memory_has_heading = text.startswith("#") and len(text) > 5
    checks.append(("memory_content", memory_has_heading, "basic content present" if memory_has_heading else "empty or malformed"))

    recent_daily_count = 0
    daily_dir = base / "daily"
    if daily_dir.exists():
        recent_daily_count = len(list(daily_dir.glob("*.md")))
    checks.append(("daily_notes", recent_daily_count > 0, f"{recent_daily_count} file(s)"))

    project_files = list((base / "projects").glob("*.md")) if (base / "projects").exists() else []
    checks.append(("project_templates", len(project_files) > 0, f"{len(project_files)} file(s)"))

    archive_files = list((base / "sessions" / "archive").glob("*.md")) if (base / "sessions" / "archive").exists() else []
    checks.append(("session_archives", len(archive_files) > 0, f"{len(archive_files)} file(s)"))

    runtime_capture = False
    for p in archive_files[:10]:
        try:
            archive_text = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        if "## Metadata" in archive_text and "## Transcript" in archive_text:
            runtime_capture = True
            break

    checks.append(("runtime_capture", True, "openclaw-like archive detected" if runtime_capture else "no runtime-shaped archive yet"))

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

    p_project = sub.add_parser("new-project", help="Create a new project memory file")
    p_project.add_argument("name")
    p_project.add_argument("path", nargs="?", default=".")

    p_daily = sub.add_parser("new-daily", help="Create today's daily note or a specific date")
    p_daily.add_argument("date", nargs="?", default=None)
    p_daily.add_argument("path", nargs="?", default=".")

    p_capture = sub.add_parser("capture-session", help="Archive a session and append a daily summary")
    p_capture.add_argument("source", nargs="?", default="-")
    p_capture.add_argument("--session-id", default=None)
    p_capture.add_argument("--path", default=".")

    p_capture_oc = sub.add_parser("capture-openclaw", help="Archive an OpenClaw-style session JSON payload")
    p_capture_oc.add_argument("source", nargs="?", default="-")
    p_capture_oc.add_argument("--path", default=".")

    p_sync = sub.add_parser("sync-day", help="Sync archived sessions into a daily note")
    p_sync.add_argument("date", nargs="?", default=None)
    p_sync.add_argument("path", nargs="?", default=".")

    p_suggest = sub.add_parser("suggest-memory", help="Suggest long-term memory candidates from text or a file")
    p_suggest.add_argument("source", nargs="?", default="-")
    p_suggest.add_argument("--path", default=".")

    args = parser.parse_args()

    if args.command == "init":
        return init_memory(Path(args.path).expanduser().resolve())
    if args.command == "doctor":
        return doctor(Path(args.path).expanduser().resolve())
    if args.command == "new-project":
        return new_project(Path(args.path).expanduser().resolve(), args.name)
    if args.command == "new-daily":
        return new_daily(Path(args.path).expanduser().resolve(), args.date)
    if args.command == "capture-session":
        return capture_session(Path(args.path).expanduser().resolve(), args.source, args.session_id)
    if args.command == "capture-openclaw":
        return capture_openclaw(Path(args.path).expanduser().resolve(), args.source)
    if args.command == "sync-day":
        return sync_day(Path(args.path).expanduser().resolve(), args.date)
    if args.command == "suggest-memory":
        return suggest_memory(Path(args.path).expanduser().resolve(), args.source)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
