# Diet Tracker

> Status: PENDING — stub created during repo scaffolding
> Skill path: skills/diet-tracker/

## Goal

TODO: Fill in module goal and responsibilities.

## Structure

TODO: Fill in module structure (SKILL.md, modules/, scripts/, references/).

## ⚠️ Cross-Module Rules — MUST IMPLEMENT

When developing this module, you must follow these rules:

1. **Data sandbox**: Write only to `data/diet/`. Read from `data/nutrition/` (Module 1) and `data/user/profile.json` (Module 2). Never write to other modules' data directories.
2. **Timezone**: Read `timezone` from `data/user/profile.json`. All meal timestamps use this timezone.
3. **Python scripts**: All nutrition calculations (macro totals, calorie sums) use Python scripts in `scripts/`, not LLM arithmetic.
4. **No guessing**: Every interaction, ask "Are you training today?" Never assume. Training day vs rest day affects calorie recommendations.
5. **Data presentation**: When showing data to the user, read files with `read_file` and present formatted inline. Never use Python scripts or raw dumps for user-facing output. Scripts are for calculations and writes only.
