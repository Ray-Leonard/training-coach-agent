# SETUP.md — Agent Onboarding Guide

> **You (the AI agent) should read this file first.** It tells you how to bootstrap yourself into a working fitness coach.

## What This Repo Is

A modular AI fitness coach system. You load skills from `skills/`, read/write user data from `data/`, and use reference knowledge from `knowledge/`.

Your coach persona is **老铁 Old-Iron** — a strict but supportive Chinese-speaking gym bro. Persona lives in `coach-agent-profile/SOUL.md`.

## Setup: Hermes Mode

If you're running inside [Hermes Agent](https://hermes-agent.nousresearch.com):

1. Create a dedicated coach profile:
   ```
   hermes profile create coach --clone
   ```
2. Copy the persona:
   ```
   cp coach-agent-profile/SOUL.md ~/.hermes/profiles/coach/
   ```
3. In `~/.hermes/profiles/coach/config.yaml`, add:
   ```yaml
   skills:
     external_dirs:
       - /absolute/path/to/training-coach-agent-old-iron/skills
   terminal:
     cwd: /absolute/path/to/training-coach-agent-old-iron
   ```
4. Start Hermes with the coach profile.

## Setup: Generic Mode

If you're any other AI agent (Claude Code, Codex, Cursor, etc.):

1. Set your working directory to this repo root
2. Read `AGENTS.md` for routing instructions
3. Load skills from `skills/` as needed
4. Read/write user data from `data/`

## Data Directory

The `data/` directory is **git-ignored**. Each user maintains their own:

- `data/nutrition/` — Food database (70+ foods)
- `data/user/profile.json` — Goals, macros, training split
- `data/user/body-log.json` — Weight/bodyfat history
- `data/training/` — Workout records (JSON)
- `data/diet/` — Daily food logs (JSON)

## Optional: 训记 (Xunji) Integration

If the user has a 训记 membership, they can put API keys in `.env`:

```
XUNJI_BODY_API_KEY=...
XUNJI_DIET_API_KEY=...
XUNJI_TRAINING_API_KEY=...
```

Skills will auto-detect these and pull data from 训记 APIs. Without them, all skills fall back to manual input (text/photos).
