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

## Optional Xunji/Synfit fallback

No diet sync client is shipped because this repository does not pin a public,
versioned endpoint and response schema. Manual entry therefore remains available
without credentials or network access.

If a verified client is added later, it must read only `XUNJI_DIET_API_KEY`, never
print or persist that value, use bounded pagination and conservative field parsing,
show a local diff, and require explicit confirmation before an atomic merge into
`data/diet/`. Tests must replace the network boundary and must never make live calls.
