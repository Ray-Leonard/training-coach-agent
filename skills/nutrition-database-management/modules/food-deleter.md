# Food Deleter

Removes an existing food entry from the database.

## Trigger

- User asks to "delete food", "remove from database", "delete this entry", "remove this food"
- User asks to "list all foods" or "what's in the database"

## Database Paths

```
DB_ROOT = data/nutrition/
├── source_images/           # Raw nutrition label photos
├── individual_food_data/    # Individual food .md files
└── all_food_names.md         # Master index
```

## Naming Convention

Files use **timestamp prefix** format `YYYYMMDD_HHMMSS`:

```
data/nutrition/individual_food_data/20260405_143022_peanut_butter_smooth.md
data/nutrition/source_images/20260405_143022_peanut_butter_smooth.jpg
data/nutrition/all_food_names.md entry: 20260405_143022: peanut_butter_smooth
```

## Workflow

### Case A: List All Foods (Read-only)

If user asks to list/view foods:

1. Read `data/nutrition/all_food_names.md`
2. Return a clean list of all foods with timestamps
3. Do NOT modify anything

---

### Case B: Delete a Specific Food

If user specifies which food to delete:

#### Step 1: Locate the Food

1. Read `data/nutrition/all_food_names.md`
2. Search for the food name (fuzzy match)
3. If multiple matches → show list and ask user to confirm which one
4. If not found → report "Food not found" with suggestions

#### Step 2: Get Exact Timestamps

For the identified food, extract:
- Timestamp from `data/nutrition/all_food_names.md` entry
- Expected filenames:
  - `data/nutrition/individual_food_data/{timestamp}_{food_name}.md`
  - `data/nutrition/source_images/{timestamp}_{food_name}.jpg` (if image exists)

#### Step 3: Confirm with User

Show the user what will be deleted and ask for explicit confirmation:

```
I found this entry:
  - Food: [food_name]
  - Timestamp: [YYYYMMDD_HHMMSS]
  - Data file: data/nutrition/individual_food_data/[timestamp]_[food_name].md
  - Image: data/nutrition/source_images/[timestamp]_[food_name].jpg (if exists)

Delete this? Reply "yes" to confirm.
```

**Safety rule**: Without explicit "yes" confirmation, do NOT delete anything.

#### Step 4: Delete Files

If user confirms:
1. Delete `data/nutrition/individual_food_data/{timestamp}_{food_name}.md`
2. Delete `data/nutrition/source_images/{timestamp}_{food_name}.jpg` (if exists)
3. Remove entry from `data/nutrition/all_food_names.md`

#### Step 5: Verification

After deletion:
1. Confirm the data file no longer exists
2. Confirm the image file no longer exists (if applicable)
3. Confirm `data/nutrition/all_food_names.md` no longer contains the entry or points to the deleted data file

#### Step 6: Report to User

After successful deletion:
- ✅ **Deleted**: `[food_name]`
- ✅ **Data file**: removed (`data/nutrition/individual_food_data/{timestamp}_{food_name}.md`)
- ✅ **Image**: removed (`data/nutrition/source_images/{timestamp}_{food_name}.{ext}`) if existed
- ✅ **Index**: entry removed from `data/nutrition/all_food_names.md`
- **Confirmation**: [What user confirmed in Step 3]
- **Status**: [Succeeded / Failed with reason]

#### Step 7: Git Commit

After successful deletion and before user pushes:

```bash
git add data/nutrition/individual_food_data/ data/nutrition/source_images/ data/nutrition/all_food_names.md
git commit -m "chore: delete food {food_name} ({timestamp})

- Remove data/nutrition/individual_food_data/{timestamp}_{food_name}.md
- Remove data/nutrition/source_images/{timestamp}_{food_name}.{ext}
- Remove from data/nutrition/all_food_names.md"
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

## Safety Rules

- **Always confirm**: Never delete without explicit user confirmation
- **List before delete**: Always show the user what will be deleted
- **Read-only for list**: "list foods" never modifies anything
- **One at a time**: Delete one food per confirmation (no bulk delete)
