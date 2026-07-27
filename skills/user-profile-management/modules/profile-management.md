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
6. Ask flexibly about the user's goal, accepting weight, body-fat percentage,
   measurements, or a plain-language outcome. Confirm whether it maps to
   `bulk`, `cut`, or `maintain`; if the user has no goal, use `maintain`. Never
   leave goal or macro fields empty.
7. Continue to Goal Setup and always create a valid profile.

## Goal Setup

The agent should be able to translate various goal formats (weight, body-fat
percentage, measurements, or another concrete outcome) into the standard goal
fields in `profile.json`. Adapt the questions to information the user has
already provided instead of forcing a fixed questionnaire.

1. Confirm goal type (`bulk`, `cut`, or `maintain`), then ask: “Is your goal
   based on weight, body fat percentage, or something else?”
2. Ask for the current weight if it was not already provided. Store it as
   `initial_weight_kg` and set `target_set_date` to today.
3. Translate the user's goal into `target_weight_kg`:
   - Weight goal: use the requested target weight.
   - Body-fat goal: ask “What's your current body-fat percentage?” (or read the
     latest body-fat entry from the body log), then ask “What's your target
     body-fat percentage?” Use a Python script to calculate target weight,
     assuming lean mass stays constant:
     `current_weight * (1 - current_bf / 100) / (1 - target_bf / 100)`.
     For example, 85 kg at 20% body fat targeting 15% gives
     `85 * 0.80 / 0.85 = 80.0 kg`. Present the calculated target weight and
     confirm it with the user.
   - Measurement or other goal: ask only for the missing measurable details,
     explain how they map to the standard goal fields, and confirm the derived
     target weight. If no defensible weight can be derived, ask the user to
     choose a working target weight rather than inventing one.
   - For `maintain`, default the target weight to current weight when needed.
4. Confirm the goal and target weight. Ask: “Do you have a target date in mind?”
   If the user supplies one, use its ISO date. If the user says no or does not
   know, skip timeline collection for now and set `timeline` to `null` until
   estimation is complete.
5. Offer a calorie tier and record the selection as `calorie_delta_kcal`:
   - cut: low deficit (`-200`), medium deficit (`-300`), or high deficit
     (`-500`);
   - bulk: low surplus (`+200`), medium surplus (`+300`), or high surplus
     (`+500`);
   - maintain: `0`, with no tier choice needed.
6. Run `calculate_tdee.py`:
   - derive age from birth date;
   - calculate Mifflin–St Jeor BMR using the sex-specific formula;
   - multiply BMR by `activity_level.multiplier` (fall back to the named
     activity mapping only for a legacy string profile);
   - calculate macros using the chosen `calorie_delta_kcal`:
     - cut: target weight × 2.2 g protein/kg;
     - bulk: target weight × 2.0 g protein/kg;
     - maintain: target weight × 1.8 g protein/kg;
     - fat is 25% of calories divided by 9; carbs receive remaining calories.
7. After calorie tier selection and macro calculation, always run timeline
   estimation with a Python script before writing the profile:
   - expected weekly change =
     `abs(calorie_delta_kcal) * 7 / 3500 * 0.45` kg;
   - realistic weeks =
     `abs(target_weight_kg - initial_weight_kg) / expected_weekly_change`, then
     derive the suggested target date;
   - always present: “Based on your chosen deficit of -500 kcal/day, you can
     expect to reach 75.0 kg in approximately X weeks, around [date]. I'll use
     this as your target timeline.” Use “surplus” for a bulk goal;
   - if the user did not provide a timeline, store this estimated date as
     `timeline`;
   - if the user provided a timeline, also calculate required weekly change =
     `abs(target_weight_kg - initial_weight_kg) / weeks_until_timeline`. If it
     exceeds 1 kg/week, flag it as unrealistic, present both requested and
     suggested timelines, and ask which timeline to use as before;
   - for maintain (`calorie_delta_kcal = 0`), skip division by zero and confirm
     the requested maintain date, or leave `timeline` as `null` when no
     completion date applies.
8. Present a summary table with goal, target/timeline, calorie tier and delta,
   BMR, TDEE, calories,
   protein, carbs, and fat.
9. Ask for training days/week, cardio days/week, and cardio minutes/session. If the user doesn't know, explicitly tell them:
   "If you're not sure, just say so — I'll suggest a setup based on your goal."
   Then suggest defaults (e.g., 3-4 days/week for cut, 4-5 for bulk) and work it
   out together. Never leave these fields empty or guess the answer.
10. Write every applicable field from `../references/profile.template.json` to
   `data/user/profile.json`, updating `updated_at`.
11. Report: “✅ Profile updated — goal: cut to 75.0 kg by 2026-10-01. Daily:
   2200 kcal, P180/C220/F49”.

## View Profile

1. Read `data/user/profile.json`.
2. Calculate current age with the script and present:
   - Bio: “Female, 31 years old, 165 cm, moderate activity”
   - Goal: “Cutting from 82.0 kg → 75.0 kg by 2026-10-01”
   - Macros: “2200 kcal/day — P:180g C:220g F:49g”
   - Training: “5 days/week, 2 cardio days × 30min”
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
| Cannot determine macro targets | Ask the user to verify goal and weight |
| Invalid activity level | Show `sedentary`, `light`, `moderate`, `intense` |
| Birth date in future | Reject it and ask for the correct date |
