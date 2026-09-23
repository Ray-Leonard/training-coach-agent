---
name: training-analyzer
description: "Use to store explicitly confirmed actual workouts and deterministically analyze volume, estimated 1RM, RPE, frequency, and PRs."
version: 1.0.0
---

# Training Analyzer

## When to use

Use this skill when the user wants to record an actual workout, list/load prior
sessions, analyze a confirmed session, compare historical performance, or check PRs.

## Router

| Intent | Reference | Script |
|---|---|---|
| Record, list, or load actual training | `references/training-session.template.json` | `scripts/workout_log.py` |
| Volume, Epley 1RM, RPE, recent frequency, or PR analysis | this file | `scripts/analyze_training.py` |
| Xunji/Synfit training import | `references/synfit-training-api.md` | Follow the manual fallback unless a reviewed client exists |

## Data sandbox

- Write only `data/training/`.
- Read Module 2's profile/body logs and Module 5 plan proposals when context helps.
- Never write `data/user/`, `data/diet/`, `data/nutrition/`, or
  `data/training-plans/`.
- Store normalized sessions as `data/training/YYYY-MM-DD.json` and calculated reports
  as `data/training/YYYY-MM-DD-analyze.md`.

## Actual-workout confirmation

Never assume a workout occurred. A manual/text/image-agent session requires an
explicit user confirmation and the `--confirmed` flag. The logger ignores supplied
confirmation metadata and creates its own. A normalized record whose source is
`xunji_api` may be confirmed by that source.

A plan is never an actual session. If confirmation is absent, discuss the candidate
record without writing it.

## Workflow

1. Read the profile timezone; all session timestamps must use that timezone.
2. Normalize one reviewed session using the reference shape. Each set uses exactly
   one of `weight_kg` or `weight_lbs`; pounds are stored as kilograms.
3. For manual input, ask the user to confirm that the workout happened and that the
   parsed exercises/sets are correct.
4. Run `workout_log.py create --input ... --confirmed`.
5. Run `analyze_training.py --date YYYY-MM-DD`.
6. Read and concisely present the generated Markdown report.

All training arithmetic is performed by Python. The model must not calculate volume,
estimated 1RM, average RPE, frequency, or PR status.

## Analysis definitions

- Exercise/session volume: sum of `weight_kg * reps`.
- Estimated 1RM: Epley formula for weighted sets of 1–12 reps.
- Average RPE: mean of recorded RPE values only.
- Recent frequency: confirmed sessions in a 28-day inclusive window, normalized per
  week.
- PR: current best estimated 1RM strictly exceeds the best earlier confirmed record
  for the same case-insensitive exercise name. A first observation is a baseline.

## Commands

```bash
python3 skills/training-analyzer/scripts/workout_log.py create \
  --input /path/to/reviewed-session.json --confirmed
python3 skills/training-analyzer/scripts/workout_log.py list
python3 skills/training-analyzer/scripts/workout_log.py load --date 2026-09-23
python3 skills/training-analyzer/scripts/analyze_training.py --date 2026-09-23
```
