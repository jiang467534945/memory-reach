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


def detect_project(base: Path, text: str) -> str | None:
    projects_dir = base / "projects"
    if not projects_dir.exists():
        return None

    haystack = text.lower()
    haystack_normalized = haystack.replace("-", " ").replace("_", " ")
    candidates: list[tuple[int, str]] = []
    for path in projects_dir.glob("*.md"):
        slug = path.stem.lower()
        slug_spaced = slug.replace("-", " ").replace("_", " ")
        score = 0
        if slug and slug in haystack:
            score += 3
        if slug_spaced and slug_spaced in haystack_normalized:
            score += 3
        try:
            body = path.read_text(encoding="utf-8", errors="ignore").lower()
        except Exception:
            body = ""
        title_match = re.search(r"^#\s+(.+)$", body, flags=re.M)
        if title_match:
            title = title_match.group(1).strip().lower()
            title_spaced = title.replace("-", " ").replace("_", " ")
            if title and title in haystack:
                score += 4
            if title_spaced and title_spaced in haystack_normalized:
                score += 4
        if score > 0:
            candidates.append((score, slug))

    if not candidates:
        return None
    candidates.sort(key=lambda x: (-x[0], x[1]))
    return candidates[0][1]


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


def append_section(path: Path, heading: str, lines: list[str]) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""
    if heading in existing:
        return False

    deduped_lines: list[str] = []
    for line in lines:
        if line not in existing and line not in deduped_lines:
            deduped_lines.append(line)
    if not deduped_lines:
        return False

    block = heading + "\n" + "\n".join(deduped_lines).rstrip() + "\n"
    if existing and not existing.endswith("\n"):
        existing += "\n"
    path.write_text(existing + ("\n" if existing else "") + block, encoding="utf-8")
    return True


def conflict_candidates(existing_text: str, new_lines: list[str]) -> list[str]:
    existing_low = existing_text.lower()
    results: list[str] = []
    for line in new_lines:
        low = line.lower()
        if low in existing_low:
            continue
        if (" should " in low or " must " in low or " decision:" in low or low.startswith("- decision")) and (
            " should " in existing_low or " must " in existing_low or "decision:" in existing_low
        ):
            results.append(f"- Conflict candidate: {line[2:] if line.startswith('- ') else line}")
    return results[:3]


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


def build_daily_summary(text: str) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {
        "Progress": [],
        "Decisions": [],
        "Risks": [],
        "Next": [],
    }

    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        cleaned = re.sub(r"^[-*•\d.\)\s]+", "", line).strip()
        low = cleaned.lower()
        if len(cleaned) < 12:
            continue
        if low.startswith(("system:", "conversation info", "sender", "chat history")):
            continue

        if any(k in low for k in ["decision", "decided", "prefer", "must", "should", "direction"]):
            sections["Decisions"].append(f"- {cleaned[:220]}")
        elif any(k in low for k in ["risk", "issue", "bug", "fail", "error", "blocked"]):
            sections["Risks"].append(f"- {cleaned[:220]}")
        elif any(k in low for k in ["next", "todo", "follow up", "continue", "plan"]):
            sections["Next"].append(f"- {cleaned[:220]}")
        else:
            sections["Progress"].append(f"- {cleaned[:220]}")

    for key in sections:
        deduped = []
        seen = set()
        for item in sections[key]:
            if item not in seen:
                seen.add(item)
                deduped.append(item)
        sections[key] = deduped[:4]
    return sections


def suggest_items(text: str, limit: int = 5) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {
        "Preferences": [],
        "Durable Decisions": [],
        "Long-term Constraints": [],
        "Do Not Store": [],
    }

    for raw in text.splitlines():
        line = raw.strip()
        if not line or len(line) < 18:
            continue
        low = line.lower()
        item = f"- {line[:220]}"

        if any(k in low for k in ["prefer", "likes", "usually wants", "short updates", "style"]):
            sections["Preferences"].append(item)
        if any(k in low for k in ["decision", "decided", "we will", "ship", "use ", "must integrate"]):
            sections["Durable Decisions"].append(item)
        if any(k in low for k in ["must", "cannot", "should not", "constraint", "boundary", "requirement"]):
            sections["Long-term Constraints"].append(item)
        if any(k in low for k in ["secret", "cookie", "token", "api key", "do not store", "password"]):
            sections["Do Not Store"].append(item)

    if not any(sections.values()):
        counts: dict[str, int] = {}
        for token in re.findall(r"[A-Za-z][A-Za-z0-9_-]{3,}", text.lower()):
            if token in STOPWORDS:
                continue
            counts[token] = counts.get(token, 0) + 1
        top = [w for w, c in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:limit] if c > 1]
        sections["Durable Decisions"] = [f"- Candidate recurring topic: {w}" for w in top]

    for key in sections:
        deduped = []
        seen = set()
        for item in sections[key]:
            if item not in seen:
                seen.add(item)
                deduped.append(item)
        sections[key] = deduped[:limit]
    return sections


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
    daily_written = False
    if bullets:
        daily_written = append_section(daily_path, f"## Captured Session {sid}", bullets) or daily_written

    structured = build_daily_summary(text)
    for section_name in ["Progress", "Decisions", "Risks", "Next"]:
        lines = structured.get(section_name, [])
        if lines:
            daily_written = append_section(daily_path, f"## {section_name} Update {sid}", lines) or daily_written

    project_match = detect_project(base, text)
    project_written = False
    project_path = None
    if project_match:
        project_path = base / "projects" / f"{project_match}.md"
        project_lines: list[str] = []
        for section_name in ["Progress", "Decisions", "Risks", "Next"]:
            project_lines.extend(structured.get(section_name, []))
        if project_lines:
            existing_project = project_path.read_text(encoding="utf-8", errors="ignore") if project_path.exists() else ""
            project_written = append_section(project_path, f"## Session Update {sid}", project_lines)
            conflicts = conflict_candidates(existing_project, project_lines)
            if conflicts:
                append_section(project_path, f"## Conflict Candidates {sid}", conflicts)

    print(f"Captured session: {archive}")
    if daily_written:
        print(f"Updated daily note: {daily_path}")
    if project_written and project_path is not None:
        print(f"Updated project memory: {project_path}")
    return 0


def capture_openclaw(base: Path, source: str | None) -> int:
    ensure_base(base)
    payload = read_json_input(source)
    session_id, rendered = render_openclaw_transcript(payload)
    return capture_session(base, rendered, session_id=session_id)


def automate_openclaw(base: Path, source: str | None) -> int:
    ensure_base(base)
    payload = read_json_input(source)
    session_id, rendered = render_openclaw_transcript(payload)

    capture_rc = capture_session(base, rendered, session_id=session_id)
    stamp = utc_today()
    sync_rc = sync_day(base, stamp)

    suggestions = suggest_items(rendered)
    lines: list[str] = []
    for section in ["Preferences", "Durable Decisions", "Long-term Constraints", "Do Not Store"]:
        items = suggestions.get(section, [])
        if items:
            lines.append(f"### {section}")
            lines.extend(items)
            lines.append("")
    suggest_path = base / "sessions" / "active" / f"{session_id}.suggestions.md"
    suggest_path.parent.mkdir(parents=True, exist_ok=True)
    suggest_path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")

    print(f"Automated OpenClaw flow complete: {session_id}")
    print(f"Suggestions written: {suggest_path}")
    return 0 if capture_rc == 0 and sync_rc == 0 else 1


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
    for section in ["Preferences", "Durable Decisions", "Long-term Constraints", "Do Not Store"]:
        print(f"## {section}")
        items = suggestions.get(section, [])
        if items:
            for item in items:
                print(item)
        else:
            print("- None")
        print()
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

    p_auto_oc = sub.add_parser("automate-openclaw", help="Run capture + sync + suggestion generation for an OpenClaw payload")
    p_auto_oc.add_argument("source", nargs="?", default="-")
    p_auto_oc.add_argument("--path", default=".")

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
    if args.command == "automate-openclaw":
        return automate_openclaw(Path(args.path).expanduser().resolve(), args.source)
    if args.command == "sync-day":
        return sync_day(Path(args.path).expanduser().resolve(), args.date)
    if args.command == "suggest-memory":
        return suggest_memory(Path(args.path).expanduser().resolve(), args.source)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
