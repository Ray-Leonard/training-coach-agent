# Profile Management

Use `../scripts/calculate_tdee.py` for every age, BMR, TDEE, and macro
calculation. Do not calculate these values in the model.

## Onboarding (first-run setup)

Called when the router detects a missing or empty `data/user/profile.json`.

1. Collect and validate `gender`, `birth_date`, `height_cm`, and
   `activity_level`, using the questions in `../SKILL.md`.
2. Ask: “Do you have a specific goal? (bulk/cut/maintain)”
3. If yes, continue to Goal Setup.
4. If no, create `profile.json` with the bio fields and `updated_at`; leave goal,
   macros, and training settings empty. Say: “Profile saved. You can set goals
   anytime by saying 'set my goals'.”
5. Ask: “Would you like to connect Xunji API? Your body data can sync
   automatically.” If yes, explain how to add
   `SYNFIT_BODY_DATA_API_KEY=<key>` to `.env`; never request that the key be
   posted in chat.

## Goal Setup

1. Confirm goal (`bulk`, `cut`, or `maintain`), target weight, and ISO timeline.
2. Ask: “What's your current weight?” Store it as `initial_weight_kg` and set
   `target_set_date` to today.
3. Run `calculate_tdee.py`:
   - derive age from birth date;
   - calculate Mifflin–St Jeor BMR using the gender-specific formula;
   - multiply BMR by `sedentary=1.2`, `light=1.375`, `moderate=1.55`, or
     `intense=1.725`;
   - calculate macros:
     - cut: TDEE − 500 kcal, target weight × 2.2 g protein/kg;
     - bulk: TDEE + 300 kcal, target weight × 2.0 g protein/kg;
     - maintain: TDEE, target weight × 1.8 g protein/kg;
     - fat is 25% of calories divided by 9; carbs receive remaining calories.
4. Present a summary table with goal, target/timeline, BMR, TDEE, calories,
   protein, carbs, and fat.
5. Ask for training split description, training days/week, cardio days/week, and
   cardio minutes/session.
6. Write every applicable field from `../references/profile.template.json` to
   `data/user/profile.json`, updating `updated_at`.
7. Report: “✅ Profile updated — goal: cut to 75.0 kg by 2026-10-01. Daily:
   2200 kcal, P180/C220/F49”.

## View Profile

1. Read `data/user/profile.json`.
2. Calculate current age with the script and present:
   - Bio: “Male, 31 years old, 178 cm, moderate activity”
   - Goal: “Cutting from 82.0 kg → 75.0 kg by 2026-10-01”
   - Macros: “2200 kcal/day — P:180g C:220g F:49g”
   - Training: “PPL 三分化, 5 days/week, 2 cardio days × 30min”
   - Metabolic: “TDEE 2600 kcal, BMR 1780 kcal”

## Recalculate

1. Read the current profile.
2. Obtain current weight from the latest weight body-log entry; if none exists,
   ask the user.
3. Run the script to recalculate age, BMR, TDEE, and macros using the current
   profile goal and target weight.
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
