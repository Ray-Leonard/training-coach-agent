# Training Plan Management

## Generate a proposal

1. Read Module 2's profile. If weekly strength/cardio metadata is incomplete, route
   to Module 2 instead of guessing.
2. Ask whether the user prefers a split. If they do not know, explain the generator's
   labelled recommendation.
3. Generate only inside this module's sandbox:

```bash
python3 skills/training-planning/scripts/generate_plan.py generate \
  --start 2026-09-23 --days 10 --split upper-lower
```

Supported starter splits are `upper-lower`, `full-body`, and `ppl`. The output is a
proposal and never changes the profile.

## Inspect and confirm

```bash
python3 skills/training-planning/scripts/plan_manager.py list
python3 skills/training-planning/scripts/plan_manager.py load \
  --plan 2026-09-23-10-day-plan.json
python3 skills/training-planning/scripts/plan_manager.py confirm \
  --plan 2026-09-23-10-day-plan.json --confirmed
```

The final command may run only after explicit user confirmation. A confirmed plan is
still a schedule, not proof of actual training. Actual records belong to Module 4.

## Safety

The starter templates use moderate volume, alternatives for common equipment, and a
reserve-based effort note. Pain or injury requires appropriate professional care.
