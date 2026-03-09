# Install Memory Reach

You are helping the user install **Memory Reach**, a lightweight scaffolding that gives an AI agent structured long-term and project memory.

## Goal

Set up a standard memory directory with:
- long-term memory
- project memory
- daily logs
- session archive
- memory rules
- doctor checks

## Install steps

1. Clone the repository if needed.
2. Install it in editable mode:

```bash
pip install -e .
```

3. Initialize the memory structure in the target workspace:

```bash
memory-reach init .
```

4. Run doctor:

```bash
memory-reach doctor .
```

## Success criteria

The workspace should contain:
- `MEMORY.md`
- `projects/`
- `daily/`
- `sessions/archive/`
- `rules/memory-rules.md`

And `memory-reach doctor .` should print mostly green checks.
