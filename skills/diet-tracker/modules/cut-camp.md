# Cut Camp

## Purpose

A camp is a configurable date range for tracking a daily deficit target. The task
example uses 10 days and 700 kcal/day, but the implementation accepts any positive
target and a date range of 1–31 days.

## Start a camp

Read the profile timezone and TDEE, then run:

```bash
python3 skills/diet-tracker/scripts/cut_camp.py init \
  --start 2026-09-23 --days 10 --target-deficit 700 \
  --slug 2026-09-23-10-day-cut
```

This writes only to `data/diet/camps/`. It captures the profile TDEE as a baseline
and calculates a target intake for reference; it does not modify the profile or
claim that the target is medically appropriate.

## Daily operation

For every day:

1. Ask whether the user is training today and obtain an explicit `training` or
   `rest` answer.
2. Log meals and their confirmed nutrition values.
3. If the user has a better expenditure estimate, record it with
   `diet_log.py set-expenditure`; otherwise the profile TDEE is labelled as an
   estimate.
4. Refresh the camp:

```bash
python3 skills/diet-tracker/scripts/cut_camp.py refresh \
  --camp 2026-09-23-10-day-cut.json
```

A day is complete only when training status is confirmed and intake data exists.
The camp stores `actual_deficit_kcal` and `difference_from_target_kcal` only then.

## Review

```bash
python3 skills/diet-tracker/scripts/cut_camp.py summary \
  --camp 2026-09-23-10-day-cut.json
```

Present the resulting entries as a compact table. Do not report pending days as
successful deficit days and do not fabricate missing actuals.
