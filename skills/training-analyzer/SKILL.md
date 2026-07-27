# Training Analyzer

> Status: PENDING — stub created during repo scaffolding
> Skill path: skills/training-analyzer/

## Goal

TODO: Fill in module goal and responsibilities.

## Structure

TODO: Fill in module structure (SKILL.md, modules/, scripts/, references/).

## ⚠️ Cross-Module Rules — MUST IMPLEMENT

When developing this module, you must follow these rules:

1. **Data sandbox**: Write to `data/training/`. Read from `data/user/body-log/` (Module 2) for weight/bodyfat trends. Never write to other modules' data.
2. **Timezone**: Read `timezone` from `data/user/profile.json`. All workout timestamps use this timezone.
3. **Python scripts**: All progression calculations (volume, 1RM estimates, PR detection) use Python scripts, not LLM arithmetic.
4. **No guessing**: Never assume a workout happened. Always confirm with user.
5. **Data presentation**: When showing data to the user, read files with `read_file` and present formatted inline. Never use Python scripts or raw dumps for user-facing output. Scripts are for calculations and writes only.
