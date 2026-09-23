# Daily Diet Tracking

## Workflow

1. Read `data/user/profile.json` for the user's timezone and targets.
2. For a daily check-in, ask **“今天练不练？”** and wait for an explicit `training`
   or `rest` answer. Do not use the training plan as evidence that training occurred.
3. Parse the meal and nutrition values. If a value is unknown, ask for it or use a
   confirmed nutrition database entry; never invent nutrition numbers.
4. Show the proposed meal entry and ask for confirmation before writing if the user
   is correcting an existing record. New user-reported meals may be logged after the
   normal conversational confirmation.
5. Run `scripts/diet_log.py add-meal ...` for the write.
6. Run `scripts/diet_log.py summary --date YYYY-MM-DD` for totals.
7. Explain whether the result is complete or pending. A pending result must name the
   missing confirmation/data instead of presenting a guessed deficit.

## Storage

One strict JSON file per local calendar date:

`data/diet/YYYY-MM-DD.json`

The schema is defined in `../references/daily-diet.template.json`. The script keeps
writes atomic and refuses to replace a corrupted file with an empty record.

## Commands

```bash
python3 skills/diet-tracker/scripts/diet_log.py set-training-status training \
  --date 2026-09-23 --confirmed
python3 skills/diet-tracker/scripts/diet_log.py add-meal --date 2026-09-23 \
  --meal-name breakfast --food-name "food from Module 1" \
  --calories 500 --protein 35 --carbs 55 --fat 15
python3 skills/diet-tracker/scripts/diet_log.py summary --date 2026-09-23
```

`--confirmed` is intentionally required by the status command. The agent must only
supply it after the user has explicitly answered the daily question.

## Deficit semantics

The script reports intake calories/macros and, when possible, an estimated or manual
expenditure source. It calculates:

`actual_deficit_kcal = expenditure_kcal - intake_kcal`

It does not silently treat an absent meal log as zero calories or an absent training
answer as rest.
