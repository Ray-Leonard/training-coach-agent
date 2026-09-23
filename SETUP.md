# SETUP.md — Agent Onboarding Guide

> ⚠️ **WORK IN PROGRESS — NOT READY FOR UNATTENDED DEPLOYMENT**
>
> Modules 3, 4, and 5 support daily use, but the full system is still under active
> development. Keep a human in the loop and do not use it as medical advice.

## Create and use a Hermes profile

Run these commands with Hermes Agent installed:

```bash
hermes profile create trainingcoach --description "Private modular fitness coach"
hermes profile use trainingcoach
hermes profile show trainingcoach
hermes config edit
```

In the editor, merge `coach-agent-profile/config.reference.yaml` into the active
profile config and replace `/absolute/path/to/training-coach-agent` with this
repository's absolute path. Start the profile in the repository:

```bash
hermes --in /absolute/path/to/training-coach-agent
```

For a one-shot onboarding check:

```bash
hermes --in /absolute/path/to/training-coach-agent \
  -z "Read SETUP.md, AGENTS.md, and coach-agent-profile/SOUL.md; report the available modules without reading personal data."
```

`hermes profile use trainingcoach` makes the selection sticky. Use
`hermes profile use default` to return to the default profile. Keep provider
credentials in Hermes; do not copy them into this repository.

## Read order

1. `coach-agent-profile/SOUL.md` — persona and safety boundaries.
2. `AGENTS.md` — intent routing, ownership, confirmation, and data contracts.
3. The one `skills/<name>/SKILL.md` selected for the current request.

## Daily workflow examples

Log food first; the daily result remains pending until the user answers whether the
day is `training` or `rest`:

```bash
python3 skills/diet-tracker/scripts/diet_log.py add-meal \
  --date 2026-09-23 --meal-name breakfast --food-name oats \
  --calories 500 --protein 30 --carbs 70 --fat 12
python3 skills/diet-tracker/scripts/diet_log.py set-training-status rest \
  --date 2026-09-23 --confirmed
python3 skills/diet-tracker/scripts/calculate_daily_nutrition.py --date 2026-09-23
```

Create and analyze a confirmed actual workout from a reviewed JSON input:

```bash
python3 skills/training-analyzer/scripts/workout_log.py create \
  --input /path/to/reviewed-session.json --confirmed
python3 skills/training-analyzer/scripts/analyze_training.py --date 2026-09-23
```

Generate and explicitly confirm a proposed plan, or derive a separate deload:

```bash
python3 skills/training-planning/scripts/generate_plan.py generate \
  --start 2026-09-23 --days 10 --split upper-lower
python3 skills/training-planning/scripts/plan_manager.py confirm \
  --plan 2026-09-23-10-day-plan.json --confirmed
python3 skills/training-planning/scripts/generate_deload.py \
  --source-plan 2026-09-23-10-day-plan.json
```

## Safety and privacy

- Runtime files under `data/` are Git-ignored; only `.gitkeep` markers belong in
  version control.
- Never print or commit API keys, passwords, tokens, `.env`, or raw personal data.
- Never infer daily training status or turn a proposed plan into an actual record.
- Every module writes only its own sandbox.
- All arithmetic comes from the owning module's Python scripts.
- Tests never call external APIs.
