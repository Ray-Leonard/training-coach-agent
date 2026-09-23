# Diet Calculation and Source Assumptions

## Primary input path

Manual conversation is the primary usable path. Text or image-agent extraction may
prepare a candidate meal, but the user must confirm uncertain foods, portions, and
nutrition values before a write. Module 1 records may be used as known sources.

## Calculation boundaries

- `diet_log.py` validates records and calculates totals, targets, progress, and
  energy balance.
- A profile TDEE is an estimate and is labelled as such.
- A manually supplied expenditure keeps its explicit source label.
- No meal entries means missing intake, not zero intake.
- An unanswered training/rest question keeps the daily result pending.

## Xunji/Synfit integration boundary

The official Xunji diet API is the preferred source of truth when the user enables
Xunji mode. The live client is `scripts/sync_diet_data.py`, and its contract is in
`references/synfit-food-api.md`.

- `SYNFIT_DIET_DATA_API_KEY` authenticates diet-record query, write-back, custom-food,
  and template endpoints.
- `SYNFIT_FOOD_SEARCH_API_KEY` authenticates the separate official-food search
  endpoint. A diet key must not be reused for search.
- Query responses are cached losslessly under `data/diet/xunji/`; the existing
  `data/diet/YYYY-MM-DD.json` shape is a derived local projection used by the coach
  calculations.
- Remote writes show a diff-like summary and require explicit user confirmation.
- The client preserves `uniquekey`, `ntr`, unit metadata, IDs, and unknown raw fields;
  it rejects partial food records rather than guessing missing nutrition.
- Tests replace the HTTP boundary and do not make live calls. Manual local logging
  remains an offline fallback, but it is not merged into Xunji silently.
