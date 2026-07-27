---
name: user-profile-management
description: "User profile and body data management. Sub-modules: body-data-management, profile-management."
version: 1.0.0
---

# User Profile Management

## When to Use

Use this skill when the user wants to manage body measurements, weight or body-fat
history, goals, macros, metabolic estimates, training settings, or initial profile
setup.

## Architecture

```text
user-profile-management/
├── SKILL.md                          ← This file (router)
├── modules/
│   ├── body-data-management.md       ← Body data: query, log, sync
│   └── profile-management.md         ← Profile: setup, view, recalculate
├── scripts/
│   ├── calculate_tdee.py             ← BMR + TDEE calculator
│   └── sync_body_data.py             ← Xunji API client
└── references/
    ├── synfit-body-api.md             ← Xunji Body API documentation
    ├── profile.template.json          ← profile.json schema template
    └── body-log.template.json         ← Body-log entry schema template
```

## Routing Table

| User says | Sub-module |
|-----------|-----------|
| "update my weight", "log body data", "我今天 X kg", "my bodyfat is" | `modules/body-data-management.md` (log) |
| "what's my weight trend", "体脂变化", "show body log" | `modules/body-data-management.md` (query) |
| "sync body data", "拉训记数据", "sync from Xunji" | `modules/body-data-management.md` (sync) |
| "set my goals", "我想增肌/减脂到 X kg", "new goal" | `modules/profile-management.md` (setup) |
| "update macros", "calculate TDEE", "算一下每日消耗" | `modules/profile-management.md` (recalculate) |
| "what's my plan", "我的训练 split", "show profile" | `modules/profile-management.md` (view) |
| "onboarding", "get started", "setup profile" | `modules/profile-management.md` (onboarding) |

## Critical: First-Run Detection & Onboarding

Before **every** profile operation:

1. Check whether `data/user/profile.json` exists and contains more than `{}`.
2. Check whether `data/user/body-log/` exists and contains any non-empty monthly log.

If the profile is missing or empty, stop the requested workflow and begin onboarding:

Route to the onboarding workflow in `modules/profile-management.md`. A missing
body log alone does not block profile operations; it means body-dependent
calculations may require the user's current weight. If a non-empty profile
exists, proceed directly to the routed operation.

## Xunji (训记)

[Xunji](https://www.xunjiapp.com) is a Chinese fitness-tracking app available on
iOS and Android. Its API integration is a VIP feature and requires a Xunji
membership. When connected, it can automatically sync body weight, body-fat
percentage, and body measurements. Users without VIP or who prefer not to
connect can use manual entry with no loss of core profile-management features.

## Shared Conventions

- Database root: `data/user/`
- Body log: `data/user/body-log/YYYY-MM.json` (monthly files)
- Profile: `data/user/profile.json` (single file, overwrite on update)
- All dates: ISO `YYYY-MM-DD`
- All timestamps: ISO 8601 `YYYY-MM-DDTHH:MM:SSZ`
- **Timezone**: All date calculations and daily cutoffs use the user's IANA timezone
  from `profile.timezone`. Scripts that call `date.today()` must use the profile's
  timezone, not the system clock.
- Xunji API key: `.env` variable `SYNFIT_BODY_DATA_API_KEY`
- Use the scripts in `scripts/` for calculations and API/data merging; do not do
  arithmetic in the model.
- Treat `references/profile.template.json` and
  `references/body-log.template.json` as JSON-with-comments reference files.
  Persisted monthly body logs are strict JSON.
- **Data sandbox**: Only this skill writes to `data/user/`. No other module
  reads or writes `data/user/profile.json` or `data/user/body-log/`. Other
  modules may only *read* these files.
