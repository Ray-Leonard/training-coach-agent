# Training Plan Management

## Generate a proposal

1. Read Module 2's profile. Confirm that the weekly training/cardio settings are
   present; if they are missing, route back to Module 2 rather than guessing.
2. Ask whether the user has a preferred split. If not, explain the generated
   recommendation and let the user say “I don't know”.
3. Generate a plan without writing `profile.json`:

```bash
python3 skills/training-planning/scripts/generate_plan.py generate \
  --start 2026-09-23 --days 10 --split upper-lower
```

4. Read the resulting JSON and show the schedule as planned sessions, explicitly
   asking which day's training actually happened when the day arrives.

Supported starter splits are `upper-lower`, `full-body`, and `ppl`. The generator is
configuration-driven and can be extended with more templates without changing the
profile schema.

## Plan semantics

Each day contains `status: planned` and `user_confirmation_required: true`. A rest
entry is a planned recovery suggestion, not a claim that the user rested. Actual
workout records belong to the future Training Analyzer module.

## Safety

The starter plan uses moderate volume, alternatives for common equipment, and a
reserve-based effort note. It is not a diagnosis or a substitute for medical advice;
pain or injury should be handled by a qualified clinician.
