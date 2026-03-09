# OpenClaw Hook Integration (v0.4)

Memory Reach v0.4 adds a first runtime-facing entrypoint:

```bash
memory-reach capture-openclaw payload.json --path /your/workspace
```

It accepts an OpenClaw-style JSON payload and converts it into:

- `sessions/archive/<session-id>.md`
- a daily summary appended to `daily/YYYY-MM-DD.md`

## Expected payload shape

```json
{
  "session_id": "telegram-group-20260309-001",
  "meta": {
    "channel": "telegram",
    "chat_id": "-1001234567890",
    "chat_type": "group",
    "surface": "telegram",
    "user": "Lao yu",
    "started_at": "2026-03-09T10:00:00Z"
  },
  "messages": [
    {"role": "user", "content": "Remember that I prefer short updates."},
    {"role": "assistant", "content": "Got it. I will keep updates concise."}
  ],
  "summary": "Preference captured: short, direct updates."
}
```

## Example

```bash
memory-reach capture-openclaw payload.json --path .
memory-reach doctor .
```

## What this solves

Before v0.4, Memory Reach could scaffold memory files and archive arbitrary text.
With `capture-openclaw`, it can now accept a runtime-shaped payload from an agent framework and persist it in a predictable format.

## Next step

A production hook can collect transcript/summary data at session end, serialize it to JSON, and call:

```bash
memory-reach capture-openclaw /tmp/openclaw-session.json --path /your/workspace
```

This keeps the runtime integration thin and leaves the memory logic inside Memory Reach.
