---
name: diet-tracker
description: "Use for meal CRUD, daily calorie and macro progress, and estimated or manual energy deficit in the user's normal goal context."
version: 2.0.0
---

# Diet Tracker

## When to use

Use this skill when the user reports food or drinks, corrects/removes a meal, asks
for daily calories/macros, or asks how intake compares with their profile target.

## Router

| Intent | Read | Run |
|---|---|---|
| Log, correct, inspect, or delete food | `modules/daily-diet-tracking.md` | `scripts/diet_log.py` |
| Daily target, macro progress, expenditure, or deficit | `modules/daily-diet-tracking.md` and `references/assumptions.md` | `scripts/calculate_daily_nutrition.py` |
| Optional Xunji/Synfit import question | `references/assumptions.md` | Use the documented manual fallback; no live client is shipped |

## Data sandbox

- Write only `data/diet/YYYY-MM-DD.json`.
- Read Module 2's `data/user/profile.json` and Module 1 nutrition records.
- Never write `data/user/`, `data/nutrition/`, `data/training/`, or
  `data/training-plans/`.
- Store only confirmed daily training/rest context, never a detailed workout or plan.

## Non-negotiable daily rule

For **every daily check-in**, ask: **“今天是 training 还是 rest？如果还不知道，就先
保持 unknown。”** Never infer the answer from a plan, calendar, previous behavior,
or a missing workout.

Meals may be recorded before the answer. Until the user explicitly answers, the
daily result remains pending and no energy deficit is presented as complete. Pass
`--confirmed` to the status command only after that explicit answer.

## Workflow

1. Read profile timezone and targets. If onboarding is incomplete, route to Module 2.
2. Prefer user-confirmed manual/text/image-agent meal input. Never invent nutrition.
3. Use `diet_log.py` for every write and all CRUD validation.
4. Ask the daily training/rest question if it has not been explicitly answered.
5. Use `calculate_daily_nutrition.py` for target-versus-actual output.
6. Present a concise formatted result; do not expose raw personal JSON.

All totals, percentages, target fallback, and energy balance are calculated in
Python. The model must not redo the arithmetic.

## Files

```text
skills/diet-tracker/
├── SKILL.md
├── modules/daily-diet-tracking.md
├── references/
│   ├── assumptions.md
│   └── daily-diet.template.json
└── scripts/
    ├── calculate_daily_nutrition.py
    ├── common.py
    └── diet_log.py
```
