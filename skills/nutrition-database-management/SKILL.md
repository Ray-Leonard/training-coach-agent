---
name: nutrition-database-management
description: "Central hub for nutrition database operations. Routes to sub-modules: food-image-processor, food-deleter, food-renamer, menu-manager."
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
- Manage or update the user's meal menu (`MENU.md`)

> **Note (2026-06-25)**: The Training Coach Meta-Agent was scrapped. Routing is handled by the unified repo's `AGENTS.md`. This skill continues to work both standalone and as part of the broader training-coach-agent system.

## Architecture

**Location** (absolute path): `~/workspace/training-coach/my-nutritional-database/nutrition-database-management/`

**Purpose**: Central routing hub for all nutrition database operations. Routes user requests to the appropriate sub-module.

```
nutrition-database-management/
├── SKILL.md                          ← This file (router)
├── modules/
│   ├── food-image-processor.md       ← Add new food from image  ✅ done
│   ├── food-deleter.md               ← Remove or list entries   ✅ done
│   ├── food-renamer.md               ← Rename food entry        ✅ done
│   └── menu-manager.md               ← Manage MENU.md           ✅ done
└── references/                        # Static references (future)
```

## Current Status

**Production-ready**: 70+ foods in `individual_food_data/`. Actively used for daily nutrition management.

**⚠️ Deprecated (2026-06-25)**: `NUTRITION_MASTER.md` and `generate_nutrition_master.py` are deprecated. They were a workaround for Perplexity WebUI's single-file-upload limitation. With a local agent, **use `ls individual_food_data/` to list foods, then `read_file` only the specific food(s) needed**. Do NOT read NUTRITION_MASTER.md directly — it wastes tokens loading 70+ entries when you only need 1–3.

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
| "process this image", "add food", "new food", "save this to database" | `modules/food-image-processor.md` |
| "delete food", "remove from database", "delete this entry" | `modules/food-deleter.md` |
| "list foods", "what's in the database", "show all foods" | `modules/food-deleter.md` (read-only mode) |
| "rename food", "rename this entry", "change the name of this food", "update food name" | `modules/food-renamer.md` |
| "update menu", "add to menu", "change my meals", "manage menu", "add a new meal" | `modules/menu-manager.md` |

## Shared Conventions

All sub-modules share these:

- **Database root**: `~/workspace/training-coach/my-nutritional-database/`
- **`individual_food_data/`**: Single source of truth — each food has its own `.md` file. **To find a food**: `ls individual_food_data/` to list all, then `read_file` only the specific food(s) needed. Do NOT read the entire directory at once.
- **`all_food_names.md`**: Food name → file mapping for quick lookup
- **⚠️ Deprecated**: `NUTRITION_MASTER.md` and `generate_nutrition_master.py` — do not use or reference them. They were a Perplexity WebUI workaround.

> ⚠️ **Path Resolution**: Sub-modules use relative paths (`./my-nutritional-database/`) relative to the skill location (`~/workspace/training-coach/my-nutritional-database/`). If this absolute path does not exist on the system, **do not guess** — ask the user to confirm or provide the correct path, and update this skill's documentation accordingly.

## Error Handling (shared)

| Error | Action |
|-------|--------|
| Food not found in database | Report alternatives, ask for clarification |
| File operation fails | Report error, suggest manual intervention |
| Ingredient missing from database (while using menu-manager) | Ask user whether Add it first before proceeding |
