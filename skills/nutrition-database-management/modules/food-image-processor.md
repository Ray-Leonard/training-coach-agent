# Food Image Processor

Processes nutrition label images and creates new food entries in the database.

## Trigger

- User sends an image (nutrition label / food packaging photo)
- User asks to "process this image", "add food", "new food", "save this to database"

## Database Paths

```
DB_ROOT = data/nutrition/
├── source_images/           # Raw nutrition label photos
└── individual-food-data/    # Individual food .md files
```

## Naming Conventions

### File Prefix

All files use **timestamp prefix** in format `YYYYMMDD_HHMMSS`:

```
data/nutrition/individual-food-data/20260405_143022_peanut_butter_smooth.md
data/nutrition/source_images/20260405_143022_peanut_butter_smooth.jpg
```

### Food Name

- snake_case: `peanut_butter_smooth_500g`, `clif_bar_white_chocolate_macadamia_nut_68g`
- Include weight/size if relevant: `oat_chocolate_bar_26g`
- If user provides a name → use it (convert to snake_case)
- If not → generate descriptive name from OCR content


## Workflow

### Step 0: Save Incoming Image

Regardless of how the image is sent (Discord attachment, URL, file path, etc.):

1. Copy/save the image file to `data/nutrition/source_images/` directory
2. Do NOT rename yet — keep the original filename temporarily
3. Note the original filename for reference

---

### Step 1: Analyze the Image

Use the **auxiliary vision tool** to extract and understand the text from the image.

Extract these fields:
- **Required**: Serving Size (g), Calories, Protein (g), Carbohydrates (g), Fat (g)
- **Optional but important**: Saturated Fat, Trans Fat, Fiber, Sugar, Sodium (mg), Potassium (mg)
- **Optional**: Vitamins, other micronutrients

---

### Step 2: Determine Food Name

**Important**: Follow the naming conventions above.

1. If user provided a name → use it (converted to snake_case)
2. If not → generate descriptive name from OCR content
3. Pattern: `[adjective_]...[product_size]`
   - Examples: `peanut_butter_smooth_500g`, `clif_bar_white_chocolate_macadamia_nut_68g`

---


### Step 3: Duplicate Check

1. Run `ls data/nutrition/individual-food-data/` to list all foods
2. Fuzzy match the proposed food name against the `ls` output
3. If exists → ask user: "This food already exists as `[timestamp]: [name]`. Skip, rename, or overwrite?"
4. If new → proceed

---

### Step 4: Generate Timestamp

```python
from datetime import datetime
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
```

---

### Step 5: Create Individual Food Markdown

Create `data/nutrition/individual-food-data/{timestamp}_{food_name}.md`:

Example content to write:
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

**Rules**:
- H1 heading: Title Case (e.g., `# Peanut Butter Smooth`)
- Sub-components (Saturated Fat, Trans Fat → Fat; Fiber, Sugar → Carbohydrates) must have their parent in "Component of" column
- Do NOT add sub-component values to parent totals (avoid double-counting)
- Mark DV% as `-` if not available
- Mark "Component of" as `-` for main nutrients

---

### Step 6: Rename and Organize Image

1. Rename the image saved in Step 0 to `{timestamp}_{food_name}.{ext}`
   - Use the actual file extension (jpg, png, etc.)
2. Confirm the renamed file exists in `data/nutrition/source_images/`

---

### Step 7: Verification

After processing:
1. Confirm the markdown file exists with correct format
2. Confirm image is renamed correctly in `data/nutrition/source_images/`
3. Confirm the new data file appears in `ls data/nutrition/individual-food-data/`

---

### Step 8: Report to User

After successful processing, report:

- ✅ **Image**: saved as `{timestamp}_{food_name}.{ext}`
- ✅ **Data file**: saved as `{timestamp}_{food_name}.md`
- **Confirmation**: [Describe what the user confirmed — e.g., "User confirmed name: peanut_butter_smooth_500g" or "User chose to skip duplicate: clif_bar_white_chocolate_macadamia_nut"]
- **Status**: [Succeeded / Failed with reason]

## Error Handling

| Error | Action |
|-------|--------|
| OCR fails to extract text | Ask user to type the nutrition data manually |
| Cannot determine food name | Ask user to provide a name |
| Image is not a nutrition label | Warn user and ask for confirmation |
| File already exists | Ask user: skip / rename / overwrite |
