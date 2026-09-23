# Training Coach Agent: 老铁 Old-Iron

An open-source, modular AI fitness coach system. Point an AI agent at this repo and
it can maintain nutrition data, manage a profile, track daily diet, and generate a
profile-driven training-plan proposal while preserving strict module sandboxes.

> **AI agent onboarding:** Read [SETUP.md](SETUP.md) and then [AGENTS.md](AGENTS.md).

[中文版 (Chinese)](README.zh-CN.md)

---

## Modules

| # | Module | Status | What it does |
|---|---|---|---|
| 1 | **Nutrition Database Management** | ✅ Complete | Maintains personal food and meal-template data from labels or web research. |
| 2 | **User Profile Management** | ✅ Complete | Manages body data, goals, macros, TDEE, and high-level weekly training/cardio metadata. |
| 3 | **Diet Tracker** | 🧪 MVP usable | Logs daily meals, calculates deterministic totals and estimated/manual deficit, and runs configurable multi-day diet camps. |
| 4 | **Training Analyzer** | 📋 Planned | Records actual workouts, detects PRs, and analyzes progression. |
| 5 | **Training Planning** | 🧪 MVP usable | Generates a proposed detailed split and schedule in its own sandbox without modifying the profile. |
| 6 | **Monthly Summary** | 📋 Planned | Aggregates training, diet, body, and goal trends into monthly reports. |
| 7 | **Proactive Reminder** | 📋 Planned | Provides timezone-aware, non-intrusive check-ins and reminders. |

The MVP intentionally distinguishes **planned** training from **confirmed actual**
training. Daily tracking must ask the user whether they trained; it never infers
that from a calendar or a generated plan.

---

## Quick Start

1. Clone this repo.
2. Copy `.env.example` to `.env` and fill optional integration keys yourself.
3. Tell your AI agent: `Read SETUP.md and get started`.
4. For a plan proposal, load `skills/training-planning/SKILL.md`.
5. For meals or a deficit camp, load `skills/diet-tracker/SKILL.md`.

User data lives under `data/` and is git-ignored. Only directory markers are tracked.
Each module writes only to its own data sandbox; see [AGENTS.md](AGENTS.md).

---

## Coach Persona

The coach is **老铁 Old-Iron** — a strict but caring Chinese-speaking gym veteran.
The persona and safety boundaries are defined in
[`coach-agent-profile/SOUL.md`](coach-agent-profile/SOUL.md).

---
