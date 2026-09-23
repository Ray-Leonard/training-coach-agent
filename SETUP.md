# SETUP.md — Agent Onboarding Guide

> ⚠️ **WORK IN PROGRESS — NOT READY FOR DEPLOYMENT**
>
> The Training Coach Agent is under active development. Modules 1 and 2 are the
> established profile/nutrition foundation; Modules 3 and 5 now have a usable MVP,
> but the complete system is not production-ready. Continue to watch this repo for
> changes before deploying it for unattended use.

---

## What This Repo Is

A modular AI fitness coach. The agent loads only the skill needed for the current
request, reads the owning module's data sandbox, performs calculations through that
skill's scripts, and presents a concise result.

Read these in order:

1. `coach-agent-profile/SOUL.md` — persona and safety boundaries.
2. `AGENTS.md` — intent routing, ownership, and data contracts.
3. The selected `skills/<name>/SKILL.md` — the module workflow.

## Current Status

| Module | Status |
|---|---|
| Nutrition Database Management | ✅ Complete |
| User Profile Management | ✅ Complete |
| Diet Tracker | 🧪 MVP usable — daily meals and configurable deficit camps |
| Training Analyzer | 📋 Planned |
| Training Planning | 🧪 MVP usable — proposed plans only |
| Monthly Summary | 📋 Planned |
| Proactive Reminder | 📋 Planned |

## MVP examples

Generate a proposed 10-day plan. This reads the profile and writes only to
`data/training-plans/`:

```bash
python3 skills/training-planning/scripts/generate_plan.py generate \
  --start 2026-09-23 --days 10 --split upper-lower
```

Start a configurable deficit camp. The Task #449 example is 10 days at 700 kcal/day;
the target is an explicit parameter, not a code-level assumption:

```bash
python3 skills/diet-tracker/scripts/cut_camp.py init \
  --start 2026-09-23 --days 10 --target-deficit 700 \
  --slug 2026-09-23-10-day-cut
```

## Safety and privacy rules

- `data/` contains personal data and is ignored by Git. Do not stage it.
- Never put API keys, passwords, tokens, or `.env` contents in chat, files, or task
  comments.
- Never infer that the user trained. Daily tracking asks for explicit `training` or
  `rest`; unknown remains pending.
- A generated training schedule is a proposal, not an actual workout record.
- Every module owns its own sandbox and must not write another module's data.
- This MVP is not medical advice and must not be used to manage injury or disease.
