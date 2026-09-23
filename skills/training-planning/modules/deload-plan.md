# Deload Plan

A deload is a separate training-plan variant. It is never an actual workout and does
not modify its source proposal, the profile, diet records, or Module 4 data.

## Generate

```bash
python3 skills/training-planning/scripts/generate_deload.py \
  --source-plan 2026-09-23-10-day-plan.json
```

The script retains every scheduled movement and reduces aggregate planned strength
sets by about 40–50% using a deterministic allocation. Planned cardio minutes are
reduced by the same target proportion. It records the measured set reduction in the
output and saves to a different filename under `data/training-plans/`.

The result starts as `status: proposed` with no confirmation. Discuss recovery,
fatigue, pain, performance trend, and timing with the user before confirming it via
`plan_manager.py`. The deterministic reduction is a plan transformation, not an
automatic claim that a deload is clinically necessary.
