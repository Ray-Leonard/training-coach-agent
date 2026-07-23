# Food Deleter

Removes an existing food entry from the database.

## Trigger

- User asks to "delete food", "remove from database", "delete this entry", "remove this food"
- User asks to "list all foods" or "what's in the database"

## Database Paths

```
DB_ROOT = data/nutrition/
├── source-images/           # Raw nutrition label photos
└── individual-food-data/
    ├── whole-foods/
    │   ├── fruits/
    │   ├── meats/
    │   ├── dairy/
    │   └── grains/
    └── processed-foods/
        ├── breads/
        ├── snacks/
        ├── instant/
        ├── frozen-prepared/
        ├── canned/
        ├── condiments/
        ├── dairy-processed/
        ├── meats-processed/
        └── beverages/
```

## Naming Convention

Files use **timestamp prefix** format `YYYYMMDD_HHMMSS`:

```
data/nutrition/individual-food-data/processed-foods/condiments/20260405_143022-peanut-butter-smooth.md
data/nutrition/source-images/20260405_143022-peanut-butter-smooth.jpg
```

## Workflow

### Case A: List All Foods (Read-only)

If user asks to list/view foods:

1. Run `find data/nutrition/individual-food-data/whole-foods/ data/nutrition/individual-food-data/processed-foods/ -type f -name '*.md'` to list all foods
2. Return a clean list of all foods with timestamps
3. Do NOT modify anything

---

### Case B: Delete a Specific Food

If user specifies which food to delete:

#### Step 1: Locate the Food

1. Search both category trees with `find data/nutrition/individual-food-data/whole-foods/ data/nutrition/individual-food-data/processed-foods/ -type f -name '*.md'`
2. Fuzzy match the food name against the `ls` output
3. If multiple matches → show list and ask user to confirm which one
4. If not found → report "Food not found" with suggestions

#### Step 2: Get Exact Timestamps

For the identified food, extract:
- Timestamp from the matched filename
- Expected filenames:
  - `data/nutrition/individual-food-data/{food-type}/{category}/{timestamp}-{food-name}.md`
  - `data/nutrition/source-images/{timestamp}-{food-name}.jpg` (if image exists)

#### Step 3: Confirm with User

Show the user what will be deleted and ask for explicit confirmation:

```
I found this entry:
  - Food: [food-name]
  - Timestamp: [YYYYMMDD_HHMMSS]
  - Data file: data/nutrition/individual-food-data/[food-type]/[category]/[timestamp]-[food-name].md
  - Image: data/nutrition/source-images/[timestamp]-[food-name].jpg (if exists)

Delete this? Reply "yes" to confirm.
```

**Safety rule**: Without explicit "yes" confirmation, do NOT delete anything.

#### Step 4: Delete Files

If user confirms:
1. Delete the exact matched `data/nutrition/individual-food-data/{food-type}/{category}/{timestamp}-{food-name}.md`
2. Delete `data/nutrition/source-images/{timestamp}-{food-name}.jpg` (if exists)

#### Step 5: Verification

After deletion:
1. Confirm the data file no longer exists
2. Confirm the image file no longer exists (if applicable)
3. Confirm the data file no longer appears when searching both `whole-foods/` and `processed-foods/`

#### Step 6: Report to User

After successful deletion:
- ✅ **Deleted**: `[food-name]`
- ✅ **Data file**: removed (`data/nutrition/individual-food-data/{food-type}/{category}/{timestamp}-{food-name}.md`)
- ✅ **Image**: removed (`data/nutrition/source-images/{timestamp}-{food-name}.{ext}`) if existed
- **Confirmation**: [What user confirmed in Step 3]
- **Status**: [Succeeded / Failed with reason]

## Error Handling

| Error | Action |
|-------|--------|
| Food not found | Report "not found" and suggest alternatives |
| No explicit confirmation | Do NOT delete, ask again |
| File deletion fails | Report error, note which file failed |

## Safety Rules

- **Always confirm**: Never delete without explicit user confirmation
- **List before delete**: Always show the user what will be deleted
- **Read-only for list**: "list foods" never modifies anything
- **One at a time**: Delete one food per confirmation (no bulk delete)
