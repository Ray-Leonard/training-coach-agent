# Training Coach Agent: 老铁 Old-Iron

An open-source, modular AI fitness coach. Give this repository to an Agent and it can
maintain nutrition data, manage a Fitness User Profile, track daily diet, record and
analyze confirmed workouts, and manage training-plan proposals while preserving strict
module sandboxes.

> **Work in progress:** Modules 3–5 are usable for daily workflows, but the complete
> project is not production-ready or a substitute for medical care.

> **AI Agent onboarding:** The installation protocol is in [SETUP.md](SETUP.md). The
> installed Training Coach runtime follows [AGENTS.md](AGENTS.md).

[中文版](README.zh-CN.md)

## What this project provides

Training Coach separates the Agent's runtime identity from the user's fitness data:

- **Agent Profile:** the host profile containing the runtime Soul, workspace, skills,
  provider configuration, and gateway integration;
- **Fitness User Profile:** the user's body data, goals, TDEE, macros, and weekly
  settings stored under `data/user/`.

The runtime is language-agnostic. During installation, the user chooses the language
for normal communication. The finalized Soul is installed into the active Agent
Profile; the repository's Soul files are read-only examples only.

## Modules

| # | Module | Status | What it does |
|---|---|---|---|
| 1 | **Nutrition Database Management** | ✅ Complete | Maintains personal food and meal-template data. |
| 2 | **User Profile Management** | ✅ Complete | Runs User Onboarding & Fitness Profile Creation, then manages body data, goals, macros, TDEE, and weekly training/cardio metadata. |
| 3 | **Diet Tracker** | ✅ Usable | Logs meal CRUD, reports target-versus-actual macros, and labels estimated/manual energy deficit. |
| 4 | **Training Analyzer** | ✅ Usable | Stores confirmed actual sessions and calculates volume, Epley 1RM, RPE, frequency, and PR flags. |
| 5 | **Training Planning** | ✅ Usable | Generates, validates, confirms, and creates reduced-volume deload plan proposals without changing the Fitness User Profile. |
| 6 | **Monthly Summary** | 📋 Planned | Aggregates training, diet, body, and goal trends. |
| 7 | **Proactive Reminder** | 📋 Planned | Provides timezone-aware, non-intrusive check-ins. |

Plans and actual training are deliberately separate. Every daily check-in asks the
user whether today is `training` or `rest`; no calendar or proposal can answer for
them.

## How installation works

Give this repository URL to an existing Agent that can clone repositories and configure
an Agent Profile. The installation is split into explicit phases:

```text
Phase 0 — Agent Profile Installation
  Existing Agent clones the repo, creates/configures trainingcoach,
  asks for the communication language, and installs the runtime SOUL.md.

Phase 0.5 — Profile Handoff & Gateway Setup
  Existing Agent invites the user to switch to trainingcoach and set up its gateway.

Phase 1 — User Onboarding & Fitness Profile Creation
  After switching, Training Coach follows AGENTS.md and creates
  data/user/profile.json when the user starts fitness onboarding.
```

The existing Agent reads `SETUP.md` only during Phase 0 and Phase 0.5. After the
handoff, the Training Coach runtime does **not** read `SETUP.md`; it follows
`AGENTS.md`, the active profile's `SOUL.md`, and the skill required for the request.

After the installation and profile handoff, switch to the new Training Coach profile,
complete gateway setup, start a new conversation, and say:

```text
Start my fitness onboarding.
```

Do not expect `data/user/profile.json` to exist before Phase 1. Installation creates
the Agent Profile; User Onboarding later creates the Fitness User Profile.

## Data and privacy

Runtime user data lives under `data/` and is Git-ignored. Credentials belong in the
active Agent Profile or environment, never in this repository. Each module owns its
own data sandbox and may not modify another module's output.

## Coach persona

The coach is **老铁 Old-Iron** — strict, caring, and language-agnostic at runtime.
Persona and safety boundaries are documented in the read-only example
[`coach-agent-profile/SOUL.example.md`](coach-agent-profile/SOUL.example.md). During
Phase 0, the existing Agent generates the selected-language runtime Soul and writes it
directly to the active profile's `SOUL.md`.
