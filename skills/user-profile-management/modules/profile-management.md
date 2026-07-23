# Profile Management

Use `../scripts/calculate_tdee.py` for every age, BMR, TDEE, and macro
calculation. Do not calculate these values in the model.

## Onboarding (first-run setup)

Called when the router detects a missing or empty `data/user/profile.json`.

1. Ask: “What's your sex? (male/female)”
2. Ask: “What's your birth date? (YYYY-MM-DD)”
3. Ask: “What's your height in cm?”
4. Ask: “What's your activity level?” Explain the choices:
   - `sedentary`: under 2 hours of exercise per week (desk job, no intentional
     exercise);
   - `light`: 2–4 hours per week (walking, light jogging, 1–2 gym sessions);
   - `moderate`: 4–7 hours per week (3–5 gym sessions, active lifestyle);
   - `intense`: 7+ hours per week (6–7 gym sessions, physical job, athlete).
   Store both the selected `name` and its multiplier in the `activity_level`
   object shown in `../references/profile.template.json`.
5. Ask: “Do you want to connect Xunji API?” Be ready to explain that
   [Xunji](https://www.xunjiapp.com) is a Chinese iOS/Android fitness-tracking
   app; API access requires Xunji VIP and automatically syncs body weight,
   body-fat percentage, and body measurements. Manual entry works as a fallback.
   If yes, explain how to add
   `SYNFIT_BODY_DATA_API_KEY=<key>` to `.env`; never request that the key be
   posted in chat.
6. Ask: “Do you have a specific goal? (bulk/cut/maintain)” If the user has no
   goal, use `maintain`; never leave goal or macro fields empty.
7. Continue to Goal Setup and always create a valid profile.

## Goal Setup

1. Confirm goal (`bulk`, `cut`, or `maintain`), target weight, and ISO timeline.
   For `maintain`, default the target weight to the current weight when needed.
2. Ask: “What's your current weight?” Store it as `initial_weight_kg` and set
   `target_set_date` to today.
3. Offer a calorie tier and record the selection as `calorie_delta_kcal`:
   - cut: low deficit (`-200`), medium deficit (`-300`), or high deficit
     (`-500`);
   - bulk: low surplus (`+200`), medium surplus (`+300`), or high surplus
     (`+500`);
   - maintain: `0`, with no tier choice needed.
4. Run `calculate_tdee.py`:
   - derive age from birth date;
   - calculate Mifflin–St Jeor BMR using the sex-specific formula;
   - multiply BMR by `activity_level.multiplier` (fall back to the named
     activity mapping only for a legacy string profile);
   - calculate macros using the chosen `calorie_delta_kcal`:
     - cut: target weight × 2.2 g protein/kg;
     - bulk: target weight × 2.0 g protein/kg;
     - maintain: target weight × 1.8 g protein/kg;
     - fat is 25% of calories divided by 9; carbs receive remaining calories.
5. Run a goal reality check with a Python script before writing the profile:
   - expected weekly change =
     `abs(calorie_delta_kcal) * 7 / 3500 * 0.45` kg;
   - required weekly change =
     `abs(target_weight_kg - initial_weight_kg) / weeks_until_timeline`;
   - if required change is greater than 1 kg/week, flag the timeline as
     unrealistic;
   - realistic weeks =
     `abs(target_weight_kg - initial_weight_kg) / expected_weekly_change`, then
     derive the suggested target date;
   - present both the requested and suggested timelines and ask: “Your goal
     requires losing X kg per week, which is aggressive. A more realistic pace
     would be Y kg/week, reaching your target by [date]. Which timeline would
     you prefer?” Use “gaining” for a bulk goal. For maintain
     (`calorie_delta_kcal = 0`), skip the division and confirm the maintain
     timeline directly.
6. Present a summary table with goal, target/timeline, calorie tier and delta,
   BMR, TDEE, calories,
   protein, carbs, and fat.
7. Ask for training split description, training days/week, cardio days/week, and
   cardio minutes/session.
8. Write every applicable field from `../references/profile.template.json` to
   `data/user/profile.json`, updating `updated_at`.
9. Report: “✅ Profile updated — goal: cut to 75.0 kg by 2026-10-01. Daily:
   2200 kcal, P180/C220/F49”.

## View Profile

1. Read `data/user/profile.json`.
2. Calculate current age with the script and present:
   - Bio: “Female, 31 years old, 165 cm, moderate activity”
   - Goal: “Cutting from 82.0 kg → 75.0 kg by 2026-10-01”
   - Macros: “2200 kcal/day — P:180g C:220g F:49g”
   - Training: “PPL 三分化, 5 days/week, 2 cardio days × 30min”
   - Metabolic: “TDEE 2600 kcal, BMR 1780 kcal”

## Recalculate

1. Read the current profile.
2. Obtain current weight from the latest weight body-log entry; if none exists,
   ask the user.
3. Run the script to recalculate age, BMR, TDEE, and macros using the current
   profile goal, target weight, `activity_level.multiplier`, and
   `calorie_delta_kcal`.
4. Show a before/after comparison.
5. Ask: “Update profile with new values?”
6. Only on confirmation, update `bmr_kcal`, `tdee_kcal`, `daily_macros`, and
   `updated_at`.

## Error Handling

| Error | Action |
|-------|--------|
| Profile not found | Trigger onboarding |
| Cannot determine macro targets | Ask the user to verify goal, weight, and timeline |
| Invalid activity level | Show `sedentary`, `light`, `moderate`, `intense` |
| Birth date in future | Reject it and ask for the correct date |
