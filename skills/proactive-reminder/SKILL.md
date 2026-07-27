# Proactive Reminder

> Status: PENDING — stub created during repo scaffolding
> Skill path: skills/proactive-reminder/

## Goal

TODO: Fill in module goal and responsibilities.

## Structure

TODO: Fill in module structure (SKILL.md, modules/, scripts/, references/).

## ⚠️ Cross-Module Rules — MUST IMPLEMENT

When developing this module, you must follow these rules:

1. **Data sandbox**: May read `data/user/profile.json` (Module 2) for timezone and training schedule. Does NOT write to any `data/` directory. Operates via cron or scheduled triggers.
2. **Timezone**: Read `timezone` from `data/user/profile.json`. All reminder timing (morning check-in, pre-workout nudge) uses this timezone.
3. **No guessing**: Reminders ask questions, they don't make statements. "Did you eat today?" not "You haven't eaten today."
4. **Non-intrusive**: Respect user's quiet hours. Don't spam.
5. **Data presentation**: When showing data to the user, read files with `read_file` and present formatted inline. Never use Python scripts or raw dumps for user-facing output. Scripts are for calculations and writes only.
