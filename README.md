<h1 align="center">🧠 Memory Reach</h1>

<p align="center">
  <strong>Turn agent conversations into durable memory files — with structure, summaries, and runtime capture.</strong>
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge" alt="MIT License"></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.10+-green.svg?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.10+"></a>
</p>

<p align="center">
  <a href="#why-memory-reach">Why</a> ·
  <a href="#what-it-does">What it does</a> ·
  <a href="#quickstart">Quickstart</a> ·
  <a href="#openclaw-integration">OpenClaw</a> ·
  <a href="#roadmap">Roadmap</a>
</p>

---

## Why Memory Reach?

Most AI agents can talk, search, and code.
Very few can **remember the right things in the right place**.

That creates the same failure pattern everywhere:

- a useful preference gets lost in the next session
- a project decision gets buried inside random chat logs
- daily progress is mixed with long-term memory
- sensitive content risks being written into durable notes
- nobody can explain **why** a memory exists or where it came from

**Memory Reach** is a lightweight memory infrastructure layer for agents.
It does not try to be a giant memory platform.
It gives you a clean, inspectable workflow for turning runtime conversations into structured files.

> The goal is not “more memory.”
> The goal is **better memory hygiene**.

---

## What it does

### 1) Create a standard memory workspace

```text
MEMORY.md
projects/
daily/
sessions/archive/
rules/
.memory-reach.json
```

### 2) Capture conversations into durable files

- archive sessions into `sessions/archive/*.md`
- summarize sessions into `daily/YYYY-MM-DD.md`
- accept runtime-shaped payloads from OpenClaw

### 3) Organize memory instead of dumping text

- structured daily summaries:
  - Progress
  - Decisions
  - Risks
  - Next
- structured long-term memory suggestions:
  - Preferences
  - Durable Decisions
  - Long-term Constraints
  - Do Not Store

### 4) Keep memory inspectable

- plain Markdown files
- simple CLI
- explicit rules
- health checks with `doctor`

---

## Current capabilities

### Workspace / scaffold
- `memory-reach init`
- `memory-reach doctor`
- `memory-reach new-project <name>`
- `memory-reach new-daily`

### Session / runtime capture
- `memory-reach capture-session`
- `memory-reach capture-openclaw`
- `memory-reach automate-openclaw`
- `memory-reach sync-day`

### Memory governance
- structured daily summaries
- structured long-term memory suggestions
- basic sensitive-content scanning

---

## Quickstart

### Install

```bash
pip install -e .
```

### Initialize a workspace

```bash
memory-reach init .
```

### Check health

```bash
memory-reach doctor .
```

### Create a project memory file

```bash
memory-reach new-project memory-reach .
```

### Create today's daily note

```bash
memory-reach new-daily 2026-03-09 .
```

### Capture a session transcript

```bash
memory-reach capture-session sample-session.txt --session-id demo-001 --path .
```

### Suggest long-term memory candidates

```bash
memory-reach suggest-memory sample-session.txt --path .
```

---

## OpenClaw integration

Memory Reach already includes a runtime-facing entrypoint for OpenClaw-style payloads:

```bash
memory-reach capture-openclaw payload.json --path /your/workspace
```

There is also a bridge example script:

```bash
python scripts/openclaw_capture.py /tmp/openclaw-session.json --workspace /your/workspace
```

Docs:

- `docs/openclaw-hook.md`
- `docs/openclaw-hook-example.md`

### Expected payload shape

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

---

## Example output shape

After capture, your workspace can evolve like this:

```text
MEMORY.md
projects/
  example-project.md
  memory-reach.md
daily/
  2026-03-09.md
sessions/archive/
  telegram-group-20260309-001.md
rules/
  memory-rules.md
  privacy-rules.md
  retention.md
```

And a daily note can contain structured updates like:

```md
## Progress Update demo-v52
- We shipped v0.5.2 daily summary improvements.

## Decisions Update demo-v52
- Decision: daily summaries should group content into Progress, Decisions, Risks, and Next.

## Risks Update demo-v52
- Risk: raw transcript snippets can become noisy in daily notes.

## Next Update demo-v52
- Next: connect this structured summary flow to a real OpenClaw hook.
```

---

## Why this project matters

There are many tools for storing more text.
There are far fewer tools for helping agents:

- decide what belongs in daily vs long-term memory
- preserve project continuity across sessions
- keep memory files human-readable
- connect runtime transcripts to durable notes
- avoid storing secrets by accident

Memory Reach is designed as a **memory infrastructure layer** — not a black-box memory product.

---

## Roadmap

### Done
- [x] scaffolded memory workspace
- [x] health checks (`doctor`)
- [x] project and daily templates
- [x] session archive flow
- [x] OpenClaw-style runtime payload capture
- [x] OpenClaw bridge example
- [x] structured daily summaries
- [x] structured long-term memory suggestions

### v0.6 target
- [x] **project-level auto classification** (v0.6.2 minimal version)
- [x] **more realistic hook automation** (v0.6.4 minimal version)
- [x] **memory deduplication / conflict handling** (v0.6.3 minimal version)

### Later
- [ ] Claude / Codex payload adapters
- [ ] stronger retrieval integration
- [ ] higher-quality summarization and memory ranking

---

## Design principle

**Memory Reach is not a giant agent framework.**

It is a small, composable layer that helps agents:

- capture
- summarize
- classify
- retain
- audit

If your agent already thinks well, Memory Reach helps it **remember more cleanly**.

---

## License

MIT
