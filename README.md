# Training Coach Agent: 老铁 Old-Iron

An open-source AI fitness coach system. Give your AI agent this repo and it becomes your personal trainer — tracking your diet, analyzing workouts, planning training cycles, and keeping you accountable.

> **If you're an AI agent reading this:** Go read [SETUP.md](SETUP.md) first. That's your onboarding guide.

[中文版 (Chinese)](README.zh-CN.md)

---

## Modules

| # | Module | Status | What it does |
|---|--------|--------|-------------|
| 1 | **Nutrition Database Management** | ✅ Done | Maintain your personal food database. Add foods from nutrition labels (OCR) or web search. Organize by whole foods vs. processed foods. Manage meal templates. |
| 2 | **User Profile Management** | 📋 Planned | Track body weight, body fat, measurements. Set training goals and macro targets. Calculate TDEE. |
| 3 | **Diet Tracker** | 📋 Planned | Log daily meals, calculate macros and micronutrients, compare against your goals. Supports manual entry and 训记 (Xunji) app sync. |
| 4 | **Training Analyzer** | 📋 Planned | Record workouts and track progress across exercises. Detect PRs, analyze volume trends, generate per-session reports. 训记 sync supported. |
| 5 | **Training Planning** | 📋 Planned | Design and adjust training programs (5×5, PPL, Ivysaur, etc.) based on your history and goals. Includes deload week planning. |
| 6 | **Monthly Summary** | 📋 Planned | Auto-generate monthly reports: training frequency, volume changes, diet compliance, weight trends. |
| 7 | **Proactive Reminder** | 📋 Planned | Cron-based check-ins: "Did you eat today?", "It's leg day — here's your plan." |

---

## Quick Start

1. Clone this repo
2. Copy `.env.example` to `.env` and fill in your keys (optional — 训记/Xunji integration)
3. Tell your AI agent: "Read SETUP.md and get started"

Your personal data lives in `data/` — it's git-ignored. Only directory structure is tracked.

---

## Coach Persona

The coach is **老铁 Old-Iron** — a strict but caring Chinese-speaking gym veteran. Persona defined in [`coach-agent-profile/SOUL.md`](coach-agent-profile/SOUL.md).

---
