# Daily Diet Tracking

## Required conversation flow

1. Read `data/user/profile.json` for timezone and nutrition targets.
2. Accept a user-confirmed meal from manual text, a reviewed image extraction, or a
   known Module 1 nutrition record. Unknown numbers remain unknown; ask instead of
   guessing.
3. Log the meal. A meal may be saved before daily training status is known.
4. For every daily check-in, explicitly ask whether today is `training` or `rest`.
   Do not infer. If the answer is unknown, leave it unknown and report pending.
5. Run the calculation entry point and present its values without recalculating.

## Storage

One atomic JSON file per local date:

`data/diet/YYYY-MM-DD.json`

The stable shape is in `../references/daily-diet.template.json`. A meal includes an
ID, meal name, food name and item list, calories, protein, carbs, fat, source, and an
offset-aware timestamp. The script validates loaded files and never replaces a
corrupt record with an empty one.

## Commands

```bash
python3 skills/diet-tracker/scripts/diet_log.py add-meal \
  --date 2026-09-23 --meal-name breakfast --food-name "oats and yogurt" \
  --item oats --item yogurt --calories 500 --protein 35 --carbs 60 --fat 12 \
  --source manual

python3 skills/diet-tracker/scripts/diet_log.py update-meal \
  --date 2026-09-23 --meal-id MEAL_ID --calories 520

python3 skills/diet-tracker/scripts/diet_log.py get-meal \
  --date 2026-09-23 --meal-id MEAL_ID

python3 skills/diet-tracker/scripts/diet_log.py remove-meal \
  --date 2026-09-23 --meal-id MEAL_ID

python3 skills/diet-tracker/scripts/diet_log.py set-training-status training \
  --date 2026-09-23 --confirmed

python3 skills/diet-tracker/scripts/calculate_daily_nutrition.py \
  --date 2026-09-23
```

`--confirmed` is an evidence flag, not a convenience default.

## Target and deficit semantics

- Calorie target first uses `profile.daily_macros.calories_kcal`.
- If absent, it uses `profile.tdee_kcal + profile.calorie_delta_kcal`.
- A manually recorded expenditure is labelled with its source; otherwise profile
  TDEE is labelled `profile_tdee_estimate`.
- Missing meals are `null`/pending, never zero intake.
- Energy deficit is reported only when intake, expenditure, and the daily
  training/rest confirmation are present.

See `../references/assumptions.md` for source and integration boundaries.
