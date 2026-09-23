---
name: training-planning
description: "Use for proposing and storing detailed training plans without modifying Module 2 profile data."
version: 1.0.0
---

# Training Planning

## When to Use

Use this skill when the user asks for a training plan, a detailed split, a new
program, or an adjustment to a proposed schedule.

## Architecture

```text
skills/training-planning/
├── SKILL.md
├── modules/training-plan-management.md
├── scripts/generate_plan.py
└── references/training-plan.template.json
```

## Data ownership

- Read `data/user/profile.json` for goal, target weight, timezone, strength-day and
  cardio metadata.
- Write only `data/training-plans/`.
- Never modify `data/user/profile.json`, `data/user/body-log/`, `data/diet/`, or
  `data/training/`.
- A generated plan is a proposal. It never proves that a workout occurred and never
  replaces the daily training confirmation required by Diet Tracker/Training Analyzer.

## Routing

| User intent | Read |
|---|---|
| “create a training plan”, “new program” | `modules/training-plan-management.md` |
| “change my split”, “PPL or upper/lower” | `modules/training-plan-management.md` |

## Generic behavior

The generator accepts a requested split. If none is provided, it recommends a split
from the profile's weekly strength frequency and clearly marks that recommendation.
If the user does not know the split, explain the options and work it out with them;
do not write the profile to remember the split.

Use `scripts/generate_plan.py` for scheduling and file writes. Use `read_file` to
present a formatted plan rather than dumping raw JSON.
