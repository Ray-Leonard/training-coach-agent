---
name: nutrition-database-management
description: "Central hub for nutrition database operations. Routes to sub-modules: food-ingestion, food-deleter, food-renamer, menu-manager."
version: 1.0.0
author: Cagoo 加拿大鹅 (Hermes Agent)
license: MIT
metadata:
  hermes:
    tags: [nutrition, database, food, menu, health]
    category: health
---


# Nutrition Database Management

## When to Use

This skill is the **active entry point** for all nutrition database operations. It is triggered **directly by the user** when they ask to:
- Add a new food item (from an image or manual entry)
- Remove an existing food item from the database
- View or list the current food database
- Manage or update the user's meal templates (`data/nutrition/menu/`)

> **Note (2026-06-25)**: The Training Coach Meta-Agent was scrapped. Routing is handled by the unified repo's `AGENTS.md`. This skill continues to work both standalone and as part of the broader training-coach-agent system.

## Architecture

**Location** (relative to repo root): `skills/nutrition-database-management/`

**Purpose**: Central routing hub for all nutrition database operations. Routes user requests to the appropriate sub-module.

```
nutrition-database-management/
├── SKILL.md                          ← This file (router)
├── modules/
│   ├── food-ingestion.md             ← Add new food from image or web data ✅ done
│   ├── food-deleter.md               ← Remove or list entries   ✅ done
│   ├── food-renamer.md               ← Rename food entry        ✅ done
│   └── menu-manager.md               ← Manage meal files        ✅ done
└── references/                        # Static references (future)
```

## Current Status

**Production-ready**: 70+ foods under `data/nutrition/individual-food-data/whole-foods/` and `data/nutrition/individual-food-data/processed-foods/`. Actively used for daily nutrition management.

**⚠️ Deprecated (2026-06-25)**: The legacy consolidated-database workflow and separate food-name index are deprecated. They were workarounds for Perplexity WebUI's single-file-upload limitation. With a local agent, **run `find data/nutrition/individual-food-data/whole-foods/ data/nutrition/individual-food-data/processed-foods/ -type f -name '*.md'` to list all foods, then `read_file` only the specific food(s) needed**. This avoids loading 70+ entries when only 1–3 are needed.

**Planned future modules** (these are now separate top-level skills in the unified training-coach-agent repo, NOT sub-modules here):
- `diet-tracker` — daily food intake logging against user goals
- `training-analyzer` — training session analysis and progression tracking
- `user-profile-management` — body weight, goals, training split, TDEE calculation
- `training-planning` — training plan design and adjustment
- `monthly-summary` — monthly report generation
- `proactive-reminder` — cron-based reminders

## Routing Rules

Read the user's request and route to the appropriate sub-module:

| User says | Sub-module |
|-----------|-----------|
| "process this image", "add food", "add chicken breast 200g", "add an egg", "new food", "save this to database" | `modules/food-ingestion.md` |
| "delete food", "remove from database", "delete this entry" | `modules/food-deleter.md` |
| "list foods", "what's in the database", "show all foods" | `modules/food-deleter.md` (read-only mode) |
| "rename food", "rename this entry", "change the name of this food", "update food name" | `modules/food-renamer.md` |
| "update menu", "add to menu", "change my meals", "manage menu", "add a new meal" | `modules/menu-manager.md` |

## Shared Conventions

All sub-modules share these:

- **Database root**: `data/nutrition/`
- **`data/nutrition/individual-food-data/`**: Single source of truth. Foods are classified below `whole-foods/` (`fruits/`, `meats/`, `dairy/`, `grains/`) or `processed-foods/` (`breads/`, `snacks/`, `instant/`, `frozen-prepared/`, `canned/`, `condiments/`, `dairy-processed/`, `meats-processed/`, `beverages/`). **To find a food**: search both trees with `find data/nutrition/individual-food-data/whole-foods/ data/nutrition/individual-food-data/processed-foods/ -type f -name '*.md'`, then `read_file` only the specific food(s) needed.
- **`data/nutrition/menu/`**: Each meal template has its own `.md` file.
- **⚠️ Deprecated**: The legacy consolidated-database workflow and separate food-name index must not be used or referenced. They were Perplexity WebUI workarounds.
- **Data sandbox**: Only this skill writes to `data/nutrition/`. No other module
  creates, modifies, or deletes files in `data/nutrition/individual-food-data/`,
  `data/nutrition/menu/`, or `data/nutrition/source-images/`. Other modules may
  only *read* these files.
- **Data presentation**: When showing data to the user, read files with `read_file`
  and present formatted inline. Do NOT use Python scripts or raw JSON/Markdown
  dumps for user-facing output. Scripts are for calculations and writes only.

> ⚠️ **Path Resolution**: All paths are relative to the `training-coach-agent` repo root. Nutrition data lives under `data/nutrition/`, while this skill and its sub-modules live under `skills/nutrition-database-management/`. Work from the repo root; if that root cannot be identified, **do not guess** — ask the user to confirm it.

## Error Handling (shared)

| Error | Action |
|-------|--------|
| Food not found in database | Report alternatives, ask for clarification |
| File operation fails | Report error, suggest manual intervention |
| Ingredient missing from database (while using menu-manager) | Ask user whether Add it first before proceeding |
