# Food Renamer

Renames an existing food entry in the database.

## Trigger

- User asks to "rename food", "rename this entry", "change the name of this food", "update food name"

## Database Paths

```
DB_ROOT = data/nutrition/
├── source_images/           # Raw nutrition label photos
└── individual-food-data/    # Individual food .md files
```

## Naming Conventions

All files use **timestamp prefix** in format `YYYYMMDD_HHMMSS`:

```
data/nutrition/individual-food-data/20260405_143022_peanut_butter_smooth.md
data/nutrition/source_images/20260405_143022_peanut_butter_smooth.jpg
```

### Food Name

- snake_case: `peanut_butter_smooth_500g`, `clif_bar_white_chocolate_macadamia_nut_68g`
- Include weight/size if relevant: `oat_chocolate_bar_26g`

## Workflow

### Step 1: Locate the Food

1. Run `ls data/nutrition/individual-food-data/` to list all foods
2. Fuzzy match the food name against the `ls` output
3. If multiple matches → show list and ask user to confirm which one
4. If not found → report "Food not found" with suggestions

### Step 2: Confirm Current Name

Show the user the current entry:
- Current food name (from the matched filename)
- Current data file: `data/nutrition/individual-food-data/{timestamp}_{old_name}.md`
- Current image (if exists): `data/nutrition/source_images/{timestamp}_{old_name}.{ext}`

Ask user to confirm this is the correct entry before proceeding.

### Step 3: Confirm New Name

1. Ask user for the new name if not already provided. 
2. convert the user input name to snake_case naming convention if it did not follow the convension. 
3. Ask user to confirm the new name before proceeding

### Step 4: Rename Files

1. Rename `data/nutrition/individual-food-data/{timestamp}_{old_name}.md` → `data/nutrition/individual-food-data/{timestamp}_{new_name}.md`
2. Rename `data/nutrition/source_images/{timestamp}_{old_name}.{ext}` → `data/nutrition/source_images/{timestamp}_{new_name}.{ext}` (if image exists)

### Step 5: Verification

1. Confirm the renamed data file exists with correct content
2. Confirm the renamed image exists (if applicable)
3. Confirm the old data file no longer exists

### Step 6: Report to User

After successful rename:
- ✅ **Renamed**: `{old_name}` → `{new_name}`
- ✅ **Data file**: `{timestamp}_{new_name}.md`
- ✅ **Image**: `{timestamp}_{new_name}.{ext}` (if existed)
- **Confirmation**: [What the user confirmed at each step]
- **Status**: [Succeeded / Failed with reason]

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
- **Verify after**: Always verify all renamed files are updated correctly
