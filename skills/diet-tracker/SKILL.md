---
name: diet-tracker
description: "Use for logging meals, daily nutrition totals, deficit tracking, and configurable multi-day diet camps."
version: 1.0.0
---

# Diet Tracker

## When to Use

Use this skill when the user reports food or drinks, asks for daily calories/macros,
starts or checks a diet camp, or wants actual deficit versus a target.

## Architecture

```text
skills/diet-tracker/
├── SKILL.md
├── modules/
│   ├── daily-diet-tracking.md
│   └── cut-camp.md
├── scripts/
│   ├── common.py
│   ├── diet_log.py
│   └── cut_camp.py
└── references/
    ├── daily-diet.template.json
    └── cut-camp.template.json
```

## Routing

| User intent | Read |
|---|---|
| “I ate…”, “log this meal”, “今天吃了什么” | `modules/daily-diet-tracking.md` |
| “how many calories today”, “daily macros”, “actual deficit” | `modules/daily-diet-tracking.md` |
| “start a 10-day cut”, “check camp progress” | `modules/cut-camp.md` |

## Data Sandbox

- This skill exclusively writes `data/diet/`.
- It may read `data/user/profile.json` and Module 1 nutrition files.
- It must never write `data/user/`, `data/nutrition/`, `data/training/`, or
  `data/training-plans/`.
- Detailed training plans belong to Module 5. A diet record may store only the
  user's explicitly confirmed daily training status as context for the calculation.

## Non-negotiable daily confirmation

Before completing any daily check-in or calculating a day's camp result, ask:
**“今天练不练？请明确告诉我 training 或 rest；如果还不确定，就先说不知道。”**
Never infer training from the calendar, the plan, previous weeks, or an absent log.
An unconfirmed day remains pending and has no actual deficit value.

## Calculation rules

- Intake totals and deficit arithmetic are performed by `scripts/diet_log.py` and
  `scripts/cut_camp.py`, never by the model.
- `actual_deficit_kcal = expenditure_kcal - intake_kcal`.
- The profile TDEE may be used only as an explicitly labelled estimate when no
  manual expenditure is recorded. Missing intake or training confirmation stays
  pending; it is not converted into zero.
- Read JSON with `read_file` and format user-facing summaries inline. Do not dump
  raw script JSON to the user.

## First use

1. Read `data/user/profile.json` for timezone and baseline TDEE.
2. If profile onboarding is incomplete, route to Module 2 first.
3. Create the daily record only after the user's training status is confirmed for a
   daily check-in. Meal logging may happen before that, but the result stays pending.
4. Use the scripts for all writes and calculations.
