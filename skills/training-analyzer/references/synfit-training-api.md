# Optional Xunji/Synfit Training Import

Manual reviewed JSON is the supported fallback and requires no network access:

```bash
python3 skills/training-analyzer/scripts/workout_log.py create \
  --input /path/to/reviewed-session.json --confirmed
```

This repository does not ship a live sync client because it does not pin a public,
versioned endpoint and response schema. A future reviewed client may use only the
environment variable `XUNJI_TRAINING_API_KEY`; it must never print, serialize, or
include that value in an exception.

Any future `sync_training_data.py` must:

1. accept an explicit date range and use bounded pagination;
2. parse unknown fields conservatively and reject partial exercises/sets;
3. normalize pounds to kilograms before validation;
4. mark accepted remote records with source and confirmation source `xunji_api`;
5. show a local diff and require explicit confirmation before writes;
6. merge atomically only into `data/training/`; and
7. replace the HTTP boundary in tests so no test makes a live call.
