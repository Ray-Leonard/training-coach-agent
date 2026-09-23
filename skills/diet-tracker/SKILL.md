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
| Xunji/Synfit diet query, search, or write-back | `references/synfit-food-api.md` | `scripts/sync_diet_data.py` |

## Data sandbox

- Write only `data/diet/YYYY-MM-DD.json` and its Xunji source mirror under
  `data/diet/xunji/`.
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

## Xunji source-of-truth mode

When the user asks to use Xunji diet data, Xunji is the source of truth for food
records. `scripts/sync_diet_data.py` preserves each official day and food record in
`data/diet/xunji/`; the existing daily tracker remains a derived coach projection,
not a second independent food database. Do not delete or overwrite a remote record
because it is absent from a partial response.

The diet-record key is `SYNFIT_DIET_DATA_API_KEY`. Official-food search uses the
separate `SYNFIT_FOOD_SEARCH_API_KEY`; do not retry search with the diet key.

## Workflow

1. Read profile timezone and targets. If onboarding is incomplete, route to Module 2.
2. In Xunji mode, query the explicit bounded date range and cache the lossless official
   response before deriving a local daily projection.
3. For a remote write, show date, meal, food, amount, unit, and nutrition summary;
   write only after explicit user confirmation.
4. Use `diet_log.py` for local projection validation and target/deficit calculations.
5. Ask the daily training/rest question if it has not been explicitly answered.
6. Use `calculate_daily_nutrition.py` for target-versus-actual output.
7. Present a concise formatted result; do not expose raw personal JSON.

All totals, percentages, target fallback, and energy balance are calculated in
Python. The model must not redo the arithmetic.

## Files

```text
skills/diet-tracker/
├── SKILL.md
├── modules/daily-diet-tracking.md
├── references/
│   ├── assumptions.md
│   ├── daily-diet.template.json
│   └── synfit-food-api.md
└── scripts/
    ├── calculate_daily_nutrition.py
    ├── common.py
    ├── diet_log.py
    └── sync_diet_data.py
```
