# Food Deleter

Removes an existing food entry from the database.

## Trigger

- User asks to "delete food", "remove from database", "delete this entry", "remove this food"
- User asks to "list all foods" or "what's in the database"

## Database Paths

```
DB_ROOT = ./my-nutritional-database/
├── source_images/           # Raw nutrition label photos
├── individual_food_data/   # Individual food .md files
├── all_food_names.md        # Master index
├── NUTRITION_MASTER.md     # Consolidated database
└── generate_nutrition_master_from_individual.py  # Consolidation script
```

## Naming Convention

Files use **timestamp prefix** format `YYYYMMDD_HHMMSS`:

```
individual_food_data/20260405_143022_peanut_butter_smooth.md
source_images/20260405_143022_peanut_butter_smooth.jpg
all_food_names.md entry: 20260405_143022: peanut_butter_smooth
```

## Workflow

### Case A: List All Foods (Read-only)

If user asks to list/view foods:

1. Read `all_food_names.md`
2. Return a clean list of all foods with timestamps
3. Do NOT modify anything

---

### Case B: Delete a Specific Food

If user specifies which food to delete:

#### Step 1: Locate the Food

1. Read `all_food_names.md`
2. Search for the food name (fuzzy match)
3. If multiple matches → show list and ask user to confirm which one
4. If not found → report "Food not found" with suggestions

#### Step 2: Get Exact Timestamps

For the identified food, extract:
- Timestamp from `all_food_names.md` entry
- Expected filenames:
  - `individual_food_data/{timestamp}_{food_name}.md`
  - `source_images/{timestamp}_{food_name}.jpg` (if image exists)

#### Step 3: Confirm with User

Show the user what will be deleted and ask for explicit confirmation:

```
I found this entry:
  - Food: [food_name]
  - Timestamp: [YYYYMMDD_HHMMSS]
  - Data file: individual_food_data/[timestamp]_[food_name].md
  - Image: source_images/[timestamp]_[food_name].jpg (if exists)

Delete this? Reply "yes" to confirm.
```

**Safety rule**: Without explicit "yes" confirmation, do NOT delete anything.

#### Step 4: Delete Files

If user confirms:
1. Delete `individual_food_data/{timestamp}_{food_name}.md`
2. Delete `source_images/{timestamp}_{food_name}.jpg` (if exists)
3. Remove entry from `all_food_names.md`

#### Step 5: Run Consolidation Script

```bash
cd ./my-nutritional-database
python generate_nutrition_master_from_individual.py
```

#### Step 6: Verification

After deletion:
1. Confirm the data file no longer exists
2. Confirm the image file no longer exists (if applicable)
3. Confirm `all_food_names.md` entry is removed
4. Confirm NUTRITION_MASTER.md no longer contains the entry

#### Step 7: Report to User

After successful deletion:
- ✅ **Deleted**: `[food_name]`
- ✅ **Data file**: removed (`individual_food_data/{timestamp}_{food_name}.md`)
- ✅ **Image**: removed (`source_images/{timestamp}_{food_name}.{ext}`) if existed
- ✅ **Index**: entry removed from `all_food_names.md`
- ✅ **Database**: NUTRITION_MASTER.md updated
- **Confirmation**: [What user confirmed in Step 3]
- **Status**: [Succeeded / Failed with reason]

#### Step 8: Git Commit

After successful deletion and before user pushes:

```bash
cd ./my-nutritional-database
git add -A
git commit -m "chore: delete food {food_name} ({timestamp})

- Remove individual_food_data/{timestamp}_{food_name}.md
- Remove source_images/{timestamp}_{food_name}.{ext}
- Remove from all_food_names.md
- Update NUTRITION_MASTER.md"
```

Report to user:
- ✅ **Committed**: `[commit hash]` — `chore: delete food {food_name}`
- 📤 **Ready to push** — user should run `git push` when ready

## Error Handling

| Error | Action |
|-------|--------|
| Food not found | Report "not found" and suggest alternatives |
| No explicit confirmation | Do NOT delete, ask again |
| File deletion fails | Report error, note which file failed |
| Consolidation script fails | Report error, data may be inconsistent |

## Safety Rules

- **Always confirm**: Never delete without explicit user confirmation
- **List before delete**: Always show the user what will be deleted
- **Read-only for list**: "list foods" never modifies anything
- **One at a time**: Delete one food per confirmation (no bulk delete)
