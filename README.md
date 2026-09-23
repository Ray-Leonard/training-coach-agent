# Training Coach Agent: 老铁 Old-Iron

An open-source, modular AI fitness coach. Point an AI agent at this repository and
it can maintain nutrition data, manage a profile, track daily diet, record and
analyze confirmed workouts, and manage training-plan proposals while preserving
strict module sandboxes.

> **Work in progress:** Modules 3–5 are usable for daily workflows, but the complete
> project is not production-ready or a substitute for medical care.

> **AI agent onboarding:** Read [SETUP.md](SETUP.md), then [AGENTS.md](AGENTS.md).

[中文版](README.zh-CN.md)

## Modules

| # | Module | Status | What it does |
|---|---|---|---|
| 1 | **Nutrition Database Management** | ✅ Complete | Maintains personal food and meal-template data. |
| 2 | **User Profile Management** | ✅ Complete | Manages body data, goals, macros, TDEE, and weekly training/cardio metadata. |
| 3 | **Diet Tracker** | ✅ Usable | Logs meal CRUD, reports target-versus-actual macros, and labels estimated/manual energy deficit. |
| 4 | **Training Analyzer** | ✅ Usable | Stores confirmed actual sessions and calculates volume, Epley 1RM, RPE, frequency, and PR flags. |
| 5 | **Training Planning** | ✅ Usable | Generates, validates, confirms, and creates reduced-volume deload plan proposals without changing the profile. |
| 6 | **Monthly Summary** | 📋 Planned | Aggregates training, diet, body, and goal trends. |
| 7 | **Proactive Reminder** | 📋 Planned | Provides timezone-aware, non-intrusive check-ins. |

Plans and actual training are deliberately separate. Every daily check-in asks the
user whether today is `training` or `rest`; no calendar or proposal can answer for
them.

## Quick start with a Hermes profile

```bash
hermes profile create trainingcoach --description "Private modular fitness coach"
hermes profile use trainingcoach
hermes profile show trainingcoach
hermes config edit
hermes --in /absolute/path/to/training-coach-agent
```

During `hermes config edit`, merge the settings from
[`coach-agent-profile/config.reference.yaml`](coach-agent-profile/config.reference.yaml)
and replace its absolute path placeholder. Then tell the agent: `Read SETUP.md and
get started`. To leave this profile later, run `hermes profile use default`.

Runtime user data lives under `data/` and is Git-ignored. Credentials belong in the
active Hermes profile or environment, never in this repository.

## Coach persona

The coach is **老铁 Old-Iron** — strict, caring, and Chinese-speaking. Persona and
safety boundaries live in
[`coach-agent-profile/SOUL.md`](coach-agent-profile/SOUL.md).
