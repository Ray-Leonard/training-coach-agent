---
name: training-planning
description: "Use for generating, validating, confirming, and deriving deload variants of detailed training-plan proposals."
version: 2.0.0
---

# Training Planning

## When to use

Use this skill for a new training program, detailed split, proposal confirmation,
plan listing/loading, or a reduced-volume deload proposal.

## Router

| Intent | Read | Run |
|---|---|---|
| Generate or choose a split | `modules/training-plan-management.md` | `scripts/generate_plan.py` |
| List, load, or explicitly confirm a proposal | `modules/training-plan-management.md` | `scripts/plan_manager.py` |
| Create a reduced-volume variant | `modules/deload-plan.md` | `scripts/generate_deload.py` |

## Data ownership

- Read `data/user/profile.json` for goal, timezone, and high-level weekly
  training/cardio metadata.
- May read Module 4 confirmed records/reports for discussion and future review tools.
- Write only `data/training-plans/`.
- Never modify the profile, body logs, diet data, or actual workout records.
- Do not add `training_split` or detailed-plan fields to Module 2.

## Proposal semantics

Every generated plan has `status: proposed` and unconfirmed metadata. The agent must
discuss it with the user. Only `plan_manager.py confirm ... --confirmed` changes that
plan file to `confirmed`; this still does not claim any workout happened. Every day
continues to carry `user_confirmation_required: true`.

If no split is requested, the generator recommends `full-body`, `ppl`, or
`upper-lower` from weekly strength frequency and labels the recommendation. The user
may choose another supported split without changing the profile schema.

All scheduling and set-reduction arithmetic is performed by Python.

## Files

```text
skills/training-planning/
├── SKILL.md
├── modules/
│   ├── deload-plan.md
│   └── training-plan-management.md
├── references/training-plan.template.json
└── scripts/
    ├── generate_deload.py
    ├── generate_plan.py
    └── plan_manager.py
```
