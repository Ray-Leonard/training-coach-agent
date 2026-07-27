# Monthly Summary

> Status: PENDING — stub created during repo scaffolding
> Skill path: skills/monthly-summary/

## Goal

TODO: Fill in module goal and responsibilities.

## Structure

TODO: Fill in module structure (SKILL.md, modules/, scripts/, references/).

## ⚠️ Cross-Module Rules — MUST IMPLEMENT

When developing this module, you must follow these rules:

1. **Data sandbox**: Read-only from all modules: `data/user/profile.json` + `data/user/body-log/` (Module 2), `data/diet/` (Module 3), `data/training/` (Module 4). Write summaries to `data/summaries/` or report inline — never modify source data.
2. **Timezone**: Read `timezone` from `data/user/profile.json`. All month boundaries use this timezone.
3. **Python scripts**: All aggregation (weekly averages, totals, deltas) uses Python scripts.
4. **Privacy**: Summaries must not expose raw data beyond what the user explicitly requests. Aggregate first, then present.
5. **Data presentation**: When showing data to the user, read files with `read_file` and present formatted inline. Never use Python scripts or raw dumps for user-facing output. Scripts are for calculations and writes only.
