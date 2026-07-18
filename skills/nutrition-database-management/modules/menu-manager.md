# Menu Manager

Manages `MENU.md` — the user's meal templates. Ensures all ingredients exist in the food database before adding them to the menu.

## Trigger

- User asks to "update menu", "add to menu", "change my meals", "manage menu", "add a new meal"

## Database Paths

```
DB_ROOT = ./my-nutritional-database/
├── MENU.md                    # User's meal templates (this is what we manage)
├── NUTRITION_MASTER.md        # Consolidated food database
├── all_food_names.md          # Master food index
├── individual_food_data/      # Individual food data files
└── nutrition-database-management/
    └── modules/
        └── food-image-processor.md  # Used when ingredient is missing
```

## Menu Format

Each meal in `MENU.md` follows this format:

```markdown
## Meal Name

- Ingredient Name: Xg
- Another Ingredient: Yg
```

Example:
```markdown
## Greek Yogurt Bowl

- 0% fat and Sugar Free Greek Yogurt: 180g
- Mixed Berries: 100g
- Generic Cereal: 30g
```

## Workflow

### Step 1: Read Existing Menu

1. Read `MENU.md` to understand current structure
2. Note the format conventions (ingredient names, gram amounts, sections)
3. If `MENU.md` doesn't exist → create it with a header

### Step 2: Parse User's Request

Understand what the user wants:
- **Add new meal**: New meal name + ingredients list
- **Update existing meal**: Modify ingredients in an existing meal
- **Delete meal**: Remove a meal from the menu
- **Replace ingredient**: Swap one ingredient for another ⚠️ [PENDING: confirm behavior]

Extract:
- Meal name
- List of ingredients with gram amounts

### Step 3: Validate Each Ingredient

For each ingredient in the user's request:

1. Search `all_food_names.md` for a match (fuzzy name matching)
2. If found → note the timestamp and exact name
3. If NOT found → this ingredient needs to be added to the database first

#### If Ingredient Is Missing:

**Option A**: Ask user to provide a nutrition label image
- → Use `food-image-processor.md` to add the new food first
- → Then re-check `all_food_names.md`

**Option B**: Ask user to provide nutrition facts directly
- → You create the food entry manually following `food-image-processor.md` logic
- → Add to `individual_food_data/` with timestamp
- → Update `all_food_names.md`
- → Run consolidation

#### Only after ALL ingredients are confirmed to exist → proceed to Step 4

### Step 4: Update MENU.md

Add or update the meal entry:

```markdown
## [Meal Name]

- [Validated Ingredient 1]: [Amount]g
- [Validated Ingredient 2]: [Amount]g
```

- Use ingredient names that **exactly match** `all_food_names.md` entries (for reliable lookup later)
- Maintain consistent formatting
- Keep meals organized (alphabetically or by category)

### Step 5: Verification

After updating `MENU.md`:
1. Confirm the meal entry exists in `MENU.md` with correct format
2. Confirm all ingredient names match `all_food_names.md` exactly
3. Confirm gram amounts are correct

> **Note**: MENU.md is independent of NUTRITION_MASTER.md — no consolidation script is needed. ⚠️ [PENDING: confirm this behavior]

### Step 6: Report to User

Summarize changes:
- ✅ **Action**: [Added / Updated / Deleted] meal `[Meal Name]`
- ✅ **Ingredients**: `[N]` ingredients validated and added
- ✅ **MENU.md**: updated successfully
- ⚠️ **New foods added to database**: `[list]` (if any ingredients were missing and added)
- ⚠️ **Foods not found** (needed user input): `[list]` (if any remained unfound)
- **Confirmation**: [What the user confirmed at each step]
- **Status**: [Succeeded / Failed with reason]

### Step 7: Git Commit

After successful processing and before user pushes:

```bash
cd ./my-nutritional-database
git add -A
git commit -m "feat(menu): {action} meal {meal_name}

- {Add/Update/Delete} meal in MENU.md
- Validated {N} ingredients against all_food_names.md
- {New foods added: [list] if any}"
```

Report to user:
- ✅ **Committed**: `[commit hash]` — `feat(menu): {action} meal {meal_name}`
- 📤 **Ready to push** — user should run `git push` when ready

## Ingredient Name Matching Rules

When matching user ingredient names to `all_food_names.md`:

| User says | Database has | Action |
|-----------|-------------|--------|
| "Greek Yogurt" | "0% fat and Sugar Free Greek Yogurt" | ✅ Use database name |
| "milk" | "2% milk" | ✅ Use database name |
| "chicken breast" | not found | ⚠️ Needs to be added first |

**Rule**: Always prefer exact or very close matches. When in doubt, ask the user to confirm.

## Validation Checklist

Before updating `MENU.md`, confirm:
- [ ] All ingredients found in `all_food_names.md`
- [ ] Ingredient names use exact matches from database
- [ ] Gram amounts are specified for each ingredient
- [ ] Meal name is unique (or user wants to update existing)

## Error Handling

| Situation | Action |
|-----------|--------|
| Ingredient not in database | Add it first (see Step 3) |
| Ambiguous ingredient name | Show matches, ask user to pick |
| Meal name already exists | Ask: update existing or create new? |
| No gram amount specified | Ask user to specify grams |
| User cancels | Do not modify MENU.md |

## Pending (Waiting for User Confirmation)

| # | Item | Question |
|---|------|----------|
| 1 | Replace ingredient behavior | When replacing an ingredient, should gram amount be preserved from the old ingredient, from the user's request, or explicitly asked again? |
| 2 | Consolidation needed? | Should menu changes trigger `generate_nutrition_master_from_individual.py`, or is MENU.md truly independent of NUTRITION_MASTER.md? |

## Example Conversation

**User**: "Add a new meal: Egg Sandwich with 2 eggs, 2 slices bread, 10g butter"

**Agent**:
1. [Reads MENU.md and all_food_names.md]
2. "Eggs" → found as "cooked_white_shrimp" (no eggs!); "2 eggs" → need to clarify or add
3. "Bread" → found as "multigrain_european_style_sliced_bread"
4. "Butter" → found as "butter_salted"
5. "Eggs" not in database → "Do you have a nutrition label for eggs? Or should I search online?"
6. User provides image → `food-image-processor.md` adds eggs
7. All ingredients validated ✅
8. Updates MENU.md
9. "✅ Added 'Egg Sandwich' to menu with: multigrain_european_style_sliced_bread (2 slices), butter_salted (10g), eggs (2)"
