# Food Ingestion

Ingests foods into the nutrition database from either a nutrition-label image or standard nutrition data found on the web.

## Trigger

- **Path A — image provided**: User sends a nutrition label or food packaging image, or asks to "process this image"
- **Path B — no image provided**: User describes a food to add, such as "add chicken breast 200g" or "add an egg"
- Either path may also be triggered by "add food", "new food", or "save this to database"

## Database Paths

```
DB_ROOT = data/nutrition/
├── individual-food-data/
│   ├── whole-foods/
│   │   ├── fruits/
│   │   ├── meats/
│   │   ├── dairy/
│   │   └── grains/
│   └── processed-foods/
│       ├── breads/
│       ├── snacks/
│       ├── instant/
│       ├── frozen-prepared/
│       ├── canned/
│       ├── condiments/
│       ├── dairy-processed/
│       ├── meats-processed/
│       └── beverages/
├── menu/                    # One kebab-case .md file per meal template
├── source-images/           # Nutrition label images for Path A
├── all_food_names.md        # Deprecated legacy food-name index; do not update
└── MENU.md                  # Deprecated legacy consolidated menu; do not update
```

## Naming Conventions

### File Prefix

All food data and source-image filenames use the pattern `{timestamp}-{food-name}.{ext}`. The timestamp format is `YYYYMMDD_HHMMSS`; the separator inside the timestamp remains an underscore.

```text
data/nutrition/individual-food-data/processed-foods/condiments/20260405_143022-peanut-butter-smooth.md
data/nutrition/source-images/20260405_143022-peanut-butter-smooth.jpg
```

### Food Name

- Use kebab-case: `peanut-butter-smooth-500g`, `clif-bar-white-chocolate-macadamia-nut-68g`
- Include weight or size when relevant: `oat-chocolate-bar-26g`
- If the user provides a name, convert it to kebab-case
- Otherwise, generate a descriptive name from the label or web-search result

## Workflow Overview

Choose exactly one intake path, then complete the common workflow:

1. **Path A only**: Save and analyze the image
2. **Path B only**: Search the web, present nutrition data, and obtain confirmation
3. **Common steps**: Determine the name, check duplicates, generate a timestamp, create the Markdown file, verify, and report
4. **Path A only**: Rename and verify the saved image

## Path A: Nutrition-Label Image

### A1: Save the Incoming Image

Regardless of how the image is sent (attachment, URL, file path, etc.):

1. Copy or save it to `data/nutrition/source-images/`
2. Keep the original filename temporarily
3. Note the original filename for later renaming

### A2: Analyze the Image

Use the available vision capability to extract:

- **Required**: Serving Size (g), Calories, Protein (g), Carbohydrates (g), Fat (g)
- **Optional but important**: Saturated Fat, Trans Fat, Fiber, Sugar, Sodium (mg), Potassium (mg)
- **Optional**: Vitamins and other micronutrients

If any required value is unclear, present the extracted data and ask the user to correct or confirm it before continuing.

## Path B: Food Without an Image

### B1: Search for Standard Nutrition Data

When the user says "add [food name]" without providing an image:

1. Search the web for reputable standard nutrition data for the food
2. Find per-100g values for Calories, Protein, Carbohydrates, and Fat
3. When available, also collect Saturated Fat, Fiber, Sugar, and Sodium
4. Record the source and do not silently combine conflicting sources

### B2: Present Data and Confirm

Present the result before writing any file:

| Nutrient | Per 100g |
|----------|----------|
| Calories | xxx |
| Protein | xg |
| Carbohydrates | xg |
| Fat | xg |
| Saturated Fat | xg or `-` |
| Fiber | xg or `-` |
| Sugar | xg or `-` |
| Sodium | xmg or `-` |

Include the source, then ask the user to confirm the values. Do not proceed to the common workflow until the user confirms.

## Common Workflow

These steps apply to both paths after the nutrition data has been extracted or confirmed.

### C1: Determine the Food Name

1. Use the user's name when provided, converted to kebab-case
2. Otherwise, generate a descriptive name from the label or web result
3. Include weight or size when relevant
4. Examples: `peanut-butter-smooth-500g`, `clif-bar-white-chocolate-macadamia-nut-68g`

### C2: Duplicate Check

1. Search both trees with `find data/nutrition/individual-food-data/whole-foods/ data/nutrition/individual-food-data/processed-foods/ -type f -name '*.md'`
2. Fuzzy-match the proposed food name against the output
3. If it exists, ask: "This food already exists as `[timestamp]-[food-name]`. Skip, rename, or overwrite?"
4. Proceed only when the entry is new or the user has confirmed the intended action

### C3: Generate Timestamp

```python
from datetime import datetime
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
```

### C4: Classify and Create Individual Food Markdown

Choose the appropriate leaf category, then create `data/nutrition/individual-food-data/{food-type}/{category}/{timestamp}-{food-name}.md`:

```markdown
# Food Name (Title Case)

| Nutrient      | Per Serving | DV% | Component of  |
| ------------- | ----------- | --- | ------------- |
| Serving Size  | xg          | -   | -             |
| Calories      | xxx         | x%  | -             |
| Fat           | 10g         | 15% | -             |
| Saturated Fat | 3g          | -   | Fat           |
| Trans Fat     | 0g          | -   | Fat           |
| Carbohydrates | 25g         | 10% | -             |
| Fiber         | 5g          | -   | Carbohydrates |
| Sugar         | 8g          | -   | Carbohydrates |
| Sodium        | 100mg       | x%  | -             |
```

Rules:

- H1 heading uses Title Case, such as `# Peanut Butter Smooth`
- For Path B, use a 100g serving unless the confirmed source provides another standard serving the user wants
- Saturated Fat and Trans Fat are components of Fat; Fiber and Sugar are components of Carbohydrates
- Do not add sub-component values to parent totals
- Use `-` when DV% is unavailable
- Use `-` in "Component of" for main nutrients

### C5: Path A Image Rename

For Path A only:

1. Rename the image saved in A1 to `{timestamp}-{food-name}.{ext}`
2. Preserve the actual extension
3. Confirm it exists in `data/nutrition/source-images/`

Path B skips this step because no image exists.

### C6: Verification

For both paths:

1. Confirm the Markdown file exists and follows the required format
2. Confirm it appears when searching both `whole-foods/` and `processed-foods/`

For Path A, also confirm the renamed image exists in `data/nutrition/source-images/`.

### C7: Report to User

Report:

- ✅ **Data file**: saved as `{timestamp}-{food-name}.md`
- ✅ **Image**: saved as `{timestamp}-{food-name}.{ext}` (Path A only)
- ✅ **Nutrition source**: label image or confirmed web source
- **Confirmation**: What the user confirmed, including selected data when sources conflicted
- **Status**: Succeeded, or failed with the reason

## Error Handling

| Error | Action |
|-------|--------|
| OCR fails to extract text | Ask the user to type the nutrition data manually |
| Cannot determine food name | Ask the user to provide a name |
| Image is not a nutrition label | Warn the user and ask for confirmation |
| Web search returns no clear results | Ask the user to provide nutrition information manually |
| Web search returns conflicting results | Present the options with their sources and let the user choose |
| File already exists | Ask the user to skip, rename, or overwrite |
