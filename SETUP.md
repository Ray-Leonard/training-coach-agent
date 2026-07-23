# SETUP.md — Agent Onboarding Guide

> ⚠️ **WORK IN PROGRESS — NOT READY FOR DEPLOYMENT**
>
> The Training Coach Agent is under active development. Only **Module 1 (Nutrition Database Management)** is complete. Modules 2–7 are stubs. Setup instructions will be finalized as more modules become functional.
>
> **Watch this repo** to get notified when setup goes live. PRs and contributions welcome.

---

## What This Repo Will Be

A modular AI fitness coach system. When complete, any AI agent pointed at this repo will be able to:

- Maintain a personal food nutrition database
- Track daily diet and compare against macro goals
- Record and analyze workouts across exercises
- Generate and adjust training programs
- Produce monthly progress reports
- Send proactive reminders

You load skills from `skills/`, read/write user data from `data/`, and pull reference knowledge from `knowledge/`.

---

## Current Status

| Module | Status |
|--------|--------|
| Nutrition Database Management | ✅ Complete — ready to use |
| User Profile Management | 📋 Planned — stub only |
| Diet Tracker | 📋 Planned — stub only |
| Training Analyzer | 📋 Planned — stub only |
| Training Planning | 📋 Planned — stub only |
| Monthly Summary | 📋 Planned — stub only |
| Proactive Reminder | 📋 Planned — stub only |

---

## Planned Setup (Preview)

Once ready, setup will support two modes:

### Hermes Mode
```bash
hermes profile create coach --clone
cp coach-agent-profile/SOUL.md ~/.hermes/profiles/coach/
# Configure external_dirs + cwd in ~/.hermes/profiles/coach/config.yaml
```

### Generic Mode (any AI agent)
```bash
# 1. Set working directory to this repo root
# 2. Read AGENTS.md for routing instructions
# 3. Load skills from skills/ as needed
```

---

## Data Directory

The `data/` directory is **git-ignored**. Only the directory skeleton is tracked (via `.gitkeep` files). Each user populates their own data.

---

## Stay Updated

- ⭐ Star the repo
- 👀 Watch for releases
- 🤝 Contributions welcome — see open issues
