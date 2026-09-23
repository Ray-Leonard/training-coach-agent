# SETUP.md — Agent Onboarding Guide

> ⚠️ **WORK IN PROGRESS — NOT READY FOR UNATTENDED DEPLOYMENT**
>
> Modules 3, 4, and 5 support daily use, but the full system is still under active
> development. Keep a human in the loop and do not use it as medical advice.

## Agent onboarding examples

Hermes Agent is shown below only as an example host for this repository. Onboarding
for other agents is being developed as needed; contributions and pull requests are
welcome.

If you use Hermes, first create/select a dedicated profile:

```bash
hermes profile create trainingcoach --description "Private modular fitness coach"
hermes profile use trainingcoach
hermes profile show trainingcoach
```

Next, locate the directory where you cloned this repository. Do not copy the example
path from this document literally:

```bash
cd /path/to/your/cloned/training-coach-agent
REPO_DIR="$(pwd)"
printf '%s\n' "$REPO_DIR"
```

Use the absolute path printed by `pwd` in the profile configuration. In
`hermes config edit`, merge the relevant settings from
`coach-agent-profile/config.reference.yaml`, replacing every path placeholder with
that actual clone path:

```yaml
terminal:
  cwd: /your/actual/clone/path/training-coach-agent

skills:
  external_dirs:
    - /your/actual/clone/path/training-coach-agent/skills
```

Then start the agent in that same repository:

```bash
hermes --in "$REPO_DIR"
```

For a one-shot onboarding check:

```bash
hermes --in "$REPO_DIR" \
  -z "Read SETUP.md, AGENTS.md, and the repository's read-only coach-agent-profile/SOUL.example.md; report the available modules without reading personal data."
```

`hermes profile use trainingcoach` makes the selection sticky. Use
`hermes profile use default` to return to the default profile. Keep provider
credentials in Hermes; do not copy them into this repository.

## Read order

1. The active agent/profile's primary `SOUL.md` — persona, selected language, and
   safety boundaries. The repository's `coach-agent-profile/SOUL.example.md` is a
   **read-only canonical English example**, not the runtime Soul. The localized
   `coach-agent-profile/SOUL.zh-CN.example.md` is also a read-only example.
2. `AGENTS.md` — intent routing, ownership, confirmation, and data contracts.
3. The one `skills/<name>/SKILL.md` selected for the current request.

## Choose Old-Iron's communication language

As part of user-profile onboarding, ask the user which language Old-Iron should use
for normal communication. English and Simplified Chinese have read-only repository
examples (`SOUL.example.md` and `SOUL.zh-CN.example.md`); other languages may be
selected and translated from the complete canonical English example.

After the user confirms the choice, finalize the complete Soul and **write it directly
to the active profile's primary `SOUL.md`**. For a Hermes named profile, use:

```text
~/.hermes/profiles/<profile-name>/SOUL.md
```

This profile file is the runtime Soul and is the file onboarding must modify. Do not
modify, overwrite, or install into the repository's `*.example.md` files, and do not
commit the user's language choice. The active Soul must explicitly say that Old-Iron
continues using the selected language unless the user asks to switch. Other agent
hosts need their own adapter for the active Soul location; onboarding support for more
hosts is being developed as needed, and pull requests are welcome.

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
