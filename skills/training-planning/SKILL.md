# Training Planning

> Status: PENDING — stub created during repo scaffolding
> Skill path: skills/training-planning/

## Goal

TODO: Fill in module goal and responsibilities.

## Structure

TODO: Fill in module structure (SKILL.md, modules/, scripts/, references/).

## ⚠️ Cross-Module Rules — MUST IMPLEMENT

When developing this module, you must follow these rules:

1. **Data sandbox**: Read `data/user/profile.json` (Module 2) for goals, training_days, cardio settings — but NEVER write to it. Training plans go to `data/training/` or a dedicated `data/training-plans/` directory.
2. **Timezone**: Read `timezone` from `data/user/profile.json`. All plan date references use this timezone.
3. **Python scripts**: All programming logic (periodization, volume calculations, deload scheduling) uses Python scripts.
4. **Training split**: Detailed split design (3-day PPL, 5-day bro split, 5×5, etc.) lives here. Module 2 only stores meta info (training_days_per_week, cardio_*).
5. **Beginner-friendly**: If the user doesn't know what split they want, suggest options based on their goal and training_days_per_week. Never force them to choose.
5. **Data presentation**: When showing data to the user, read files with `read_file` and present formatted inline. Never use Python scripts or raw dumps for user-facing output. Scripts are for calculations and writes only.
