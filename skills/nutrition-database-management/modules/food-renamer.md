# Food Renamer

Renames an existing food entry in the database (both the data file and the index entry).

## Trigger

- User asks to "rename food", "rename this entry", "change the name of this food", "update food name"

## Database Paths

```
DB_ROOT = data/nutrition/
├── source_images/           # Raw nutrition label photos
├── individual_food_data/    # Individual food .md files
└── all_food_names.md         # Master index
```

## Naming Conventions

All files use **timestamp prefix** in format `YYYYMMDD_HHMMSS`:

```
data/nutrition/individual_food_data/20260405_143022_peanut_butter_smooth.md
data/nutrition/source_images/20260405_143022_peanut_butter_smooth.jpg
data/nutrition/all_food_names.md entry: 20260405_143022: peanut_butter_smooth
```

### Food Name

- snake_case: `peanut_butter_smooth_500g`, `clif_bar_white_chocolate_macadamia_nut_68g`
- Include weight/size if relevant: `oat_chocolate_bar_26g`

## Workflow

### Step 1: Locate the Food

1. Read `data/nutrition/all_food_names.md`
2. Search for the food name (fuzzy match)
3. If multiple matches → show list and ask user to confirm which one
4. If not found → report "Food not found" with suggestions

### Step 2: Confirm Current Name

Show the user the current entry:
- Current food name (from `data/nutrition/all_food_names.md`)
- Current data file: `data/nutrition/individual_food_data/{timestamp}_{old_name}.md`
- Current image (if exists): `data/nutrition/source_images/{timestamp}_{old_name}.{ext}`

Ask user to confirm this is the correct entry before proceeding.

### Step 3: Confirm New Name

1. Ask user for the new name if not already provided. 
2. convert the user input name to snake_case naming convention if it did not follow the convension. 
3. Ask user to confirm the new name before proceeding

### Step 4: Rename Files

1. Rename `data/nutrition/individual_food_data/{timestamp}_{old_name}.md` → `data/nutrition/individual_food_data/{timestamp}_{new_name}.md`
2. Rename `data/nutrition/source_images/{timestamp}_{old_name}.{ext}` → `data/nutrition/source_images/{timestamp}_{new_name}.{ext}` (if image exists)

### Step 5: Update data/nutrition/all_food_names.md

Replace the old entry with the new name:
- Old: `20260405_143022: peanut_butter_smooth_500g`
- New: `20260405_143022: peanut_butter_creamy_500g`

### Step 6: Verification

1. Confirm the renamed data file exists with correct content
2. Confirm the renamed image exists (if applicable)
3. Confirm `data/nutrition/all_food_names.md` has the updated entry and points to the renamed data file

### Step 7: Report to User

After successful rename:
- ✅ **Renamed**: `{old_name}` → `{new_name}`
- ✅ **Data file**: `{timestamp}_{new_name}.md`
- ✅ **Image**: `{timestamp}_{new_name}.{ext}` (if existed)
- ✅ **Index**: entry updated in `data/nutrition/all_food_names.md`
- **Confirmation**: [What the user confirmed at each step]
- **Status**: [Succeeded / Failed with reason]

### Step 8: Git Commit

After successful processing and before user pushes:

```bash
git add data/nutrition/individual_food_data/ data/nutrition/source_images/ data/nutrition/all_food_names.md
git commit -m "refactor: rename food {old_name} → {new_name} ({timestamp})

- Rename data/nutrition/individual_food_data/{timestamp}_{old_name}.md → {new_name}.md
- Rename data/nutrition/source_images/{timestamp}_{old_name}.{ext} → {new_name}.{ext}
- Update data/nutrition/all_food_names.md"
```

Report to user:
- ✅ **Committed**: `[commit hash]` — `refactor: rename food {old_name} → {new_name}`
- 📤 **Ready to push** — user should run `git push` when ready

## Error Handling

| Error | Action |
|-------|--------|
| Food not found | Report "not found" and suggest alternatives |
| No explicit confirmation at any step | Do NOT proceed, ask again |
| Old data file not found | Report error, data may be inconsistent |
| Image file not found | Skip image rename, continue with data file only |
| New name already exists | Ask user to choose a different name |

## Safety Rules

- **Confirm at each step**: Never rename without explicit user confirmation at both current and new name steps
- **One rename at a time**: Rename one food per confirmation cycle
- **Preserve timestamp**: The timestamp prefix must NOT change — only the food name portion changes
- **Verify after**: Always verify all files and index are updated correctly
