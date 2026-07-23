# Menu Manager

Manages individual meal template files in `data/nutrition/menu/`. Ensures all ingredients exist in the food database before adding them to a meal.

## Trigger

- User asks to "update menu", "add to menu", "change my meals", "manage menu", "add a new meal"

## Database Paths

```
DB_ROOT = data/nutrition/
├── menu/                     # One .md file per meal template
└── individual-food-data/     # Individual food data files
```

## Menu Format

Each meal is stored in `data/nutrition/menu/{meal_name}.md` and follows this format:

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

### Step 1: List Existing Meals

1. Run `ls data/nutrition/menu/` to list all meals
2. For an update or deletion, read only `data/nutrition/menu/{meal_name}.md`
3. If `data/nutrition/menu/` doesn't exist → create the directory

### Step 2: Parse User's Request

Understand what the user wants:
- **Add new meal**: New meal name + ingredients list
- **Update existing meal**: Modify ingredients in an existing meal
- **Delete meal**: Remove a meal from the menu
- **Replace ingredient**: Swap one ingredient for another

Extract:
- Meal name
- List of ingredients with gram amounts

### Step 3: Validate Each Ingredient

For each ingredient in the user's request:

1. Run `ls data/nutrition/individual-food-data/` to list all foods
2. Fuzzy match the ingredient against the `ls` output; if found, note the exact food name from the filename
3. If NOT found → this ingredient needs to be added to the database first

#### If Ingredient Is Missing:

**Option A**: Ask user to provide a nutrition label image
- → Use `skills/nutrition-database-management/modules/food-image-processor.md` to add the new food first
- → Then re-check the `ls data/nutrition/individual-food-data/` output

**Option B**: Ask user to provide nutrition facts directly
- → You create the food entry manually following `skills/nutrition-database-management/modules/food-image-processor.md` logic
- → Add to `data/nutrition/individual-food-data/` with timestamp

#### Only after ALL ingredients are confirmed to exist → proceed to Step 4

### Step 4: Create, Edit, or Delete the Meal File

For an add, create `data/nutrition/menu/{meal_name}.md`. For an update, edit that file. For a deletion, delete that file after explicit user confirmation.

Use this content for an add or update:

```markdown
## [Meal Name]

- [Validated Ingredient 1]: [Amount]g
- [Validated Ingredient 2]: [Amount]g
```

- Use ingredient names that **exactly match** names derived from the `ls data/nutrition/individual-food-data/` output (for reliable lookup later)
- Maintain consistent formatting
- Use snake_case for `{meal_name}` filenames

### Step 5: Verification

After changing a meal:
1. Confirm `data/nutrition/menu/{meal_name}.md` was created, edited, or deleted as requested
2. Confirm all ingredient names match the food filenames exactly
3. Confirm gram amounts are correct

> **Note**: Each meal file is maintained directly and requires no additional generated artifact.

### Step 6: Report to User

Summarize changes:
- ✅ **Action**: [Added / Updated / Deleted] meal `[Meal Name]`
- ✅ **Ingredients**: `[N]` ingredients validated and added
- ✅ **Meal file**: `data/nutrition/menu/{meal_name}.md` updated successfully
- ⚠️ **New foods added to database**: `[list]` (if any ingredients were missing and added)
- ⚠️ **Foods not found** (needed user input): `[list]` (if any remained unfound)
- **Confirmation**: [What the user confirmed at each step]
- **Status**: [Succeeded / Failed with reason]

## Ingredient Name Matching Rules

When matching user ingredient names to the `ls data/nutrition/individual-food-data/` output:

| User says | Database has | Action |
|-----------|-------------|--------|
| "Greek Yogurt" | "0% fat and Sugar Free Greek Yogurt" | ✅ Use database name |
| "milk" | "2% milk" | ✅ Use database name |
| "chicken breast" | not found | ⚠️ Needs to be added first |

**Rule**: Always prefer exact or very close matches. When in doubt, ask the user to confirm.

## Validation Checklist

Before creating or editing `data/nutrition/menu/{meal_name}.md`, confirm:
- [ ] All ingredients found in the `ls data/nutrition/individual-food-data/` output
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
| User cancels | Do not modify the meal file |

## Example Conversation

**User**: "Add a new meal: Egg Sandwich with 2 eggs, 2 slices bread, 10g butter"

**Agent**:
1. [Lists `data/nutrition/menu/` and `data/nutrition/individual-food-data/`]
2. "Eggs" → found as "cooked_white_shrimp" (no eggs!); "2 eggs" → need to clarify or add
3. "Bread" → found as "multigrain_european_style_sliced_bread"
4. "Butter" → found as "butter_salted"
5. "Eggs" not in database → "Do you have a nutrition label for eggs? Or should I search online?"
6. User provides image → `skills/nutrition-database-management/modules/food-image-processor.md` adds eggs
7. All ingredients validated ✅
8. Creates `data/nutrition/menu/egg_sandwich.md`
9. "✅ Added 'Egg Sandwich' to menu with: multigrain_european_style_sliced_bread (2 slices), butter_salted (10g), eggs (2)"
