# OpenClaw Hook Example (v0.5.1)

This file shows the thinnest possible integration shape for OpenClaw.

## Goal

At the end of a session (or after compaction/reset), serialize the session into JSON and hand it to Memory Reach.

## 1) Install Memory Reach

```bash
pip install -e .
```

## 2) Example payload

Save a payload like this to `/tmp/openclaw-session.json`:

```json
{
  "session_id": "telegram-group-20260309-001",
  "meta": {
    "channel": "telegram",
    "chat_id": "-1003837441352",
    "chat_type": "group",
    "surface": "telegram",
    "user": "Lao yu",
    "started_at": "2026-03-09T10:40:00Z"
  },
  "messages": [
    {"role": "user", "content": "Please make Memory Reach integrate runtime conversations."},
    {"role": "assistant", "content": "Understood. v0.4 adds capture-openclaw for runtime-shaped payloads."}
  ],
  "summary": "Direction confirmed: Memory Reach must connect runtime conversation capture to durable files."
}
```

## 3) Call the bridge script

```bash
python scripts/openclaw_capture.py /tmp/openclaw-session.json --workspace /path/to/memory-workspace
```

This script simply forwards the payload into:

```bash
memory-reach capture-openclaw /tmp/openclaw-session.json --path /path/to/memory-workspace
```

## 4) Expected outputs

After one successful call, the workspace should contain:

- `sessions/archive/<session-id>.md`
- `daily/YYYY-MM-DD.md` updated with a captured-session summary

## 5) Production wiring idea

A real OpenClaw hook can do this at the end of a run:

1. collect transcript + metadata
2. write JSON payload to a temp file
3. call `scripts/openclaw_capture.py`
4. optionally call `memory-reach doctor`

This keeps runtime collection outside Memory Reach, and memory persistence inside Memory Reach.
