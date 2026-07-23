# Body Data Management

Use `../scripts/sync_body_data.py` for API access, merging, and persistence. Valid
types are documented in `../references/synfit-body-api.md`.

## Table of Contents

- [Query Body Data](#query-body-data)
- [Log Body Data (manual)](#log-body-data-manual)
- [Sync from Xunji API](#sync-from-xunji-api)

## Query Body Data

Triggered by requests such as “what's my weight trend” or “show body log”.

1. Ask: “Would you like to see this week, this month, last 3 months, or all
   data?”
2. Read the applicable `data/user/body-log/YYYY-MM.json` files only. Local
   `data/user/body-log/` is the source of truth; never query Xunji during a body
   data query.
3. Use a Python script to calculate change and trend; show the date range, first
   and latest values, absolute change, and record count.
4. If local data has no applicable records, say: “No body data found. Would you like to sync
   from Xunji or log manually?”

## Log Body Data (manual)

Triggered by input such as “我今天 85kg” or “my bodyfat is 18%”.

1. Parse type, numeric value, unit, and date (today if omitted). Validate the type,
   positive value, matching unit, and ISO date.
2. Show: “Logging: weight 85.0 kg on 2026-07-23. Confirm?”
3. Do not write until the user confirms.
4. On confirmation, load or create `data/user/body-log/YYYY-MM.json`, replace an
   existing manual entry with the same `(date, type)` or append:

   ```json
   {"date":"2026-07-23","type":"weight","value":85.0,"unit":"kg","source":"manual"}
   ```

5. Sort entries consistently and save strict JSON.
6. Report: “✅ Logged weight 85.0 kg on 2026-07-23. Logged to
   `data/user/body-log/2026-07.json`”.

## Sync from Xunji API

Triggered by “sync body data”, “拉训记数据”, or “sync from Xunji”.

1. Read the API key from `.env`. If missing, offer manual entry.
2. Always fetch all Xunji data: call `POST /open/body/query_gzip` with a wide
   range from a date far in the past (for example `1900-01-01`) through today.
   Do not infer the cloud range from local records.
3. Read every local `data/user/body-log/YYYY-MM.json` file.
4. Merge all API and local records on `(date, type)`, with Xunji winning every
   conflict.
5. Compare the merged result with local records and count new or changed
   records.
6. Show a summary such as: “Found 5 new records: 3 weight, 2 bodyfat since July
   18. Sync?”
7. Do not write until the user confirms.
8. On confirmation, write all merged records back to their local monthly files,
   including unchanged months, using `save_body_log` for every month represented
   in the merged data. `save_body_log` is a function in
   `../scripts/sync_body_data.py` that atomically writes one month of records to
   `data/user/body-log/YYYY-MM.json`.
9. Report: “✅ Synced 5 records from Xunji. Local
   `data/user/body-log/` is now the only source of truth. Future queries read
   from local files only.”

This full-fetch → read-local → conflict-aware merge → rewrite-all-months pattern
is the reusable sync design for future modules. It ensures local storage never
misses a cloud entry.

This sync workflow only queries and stores Xunji records. Any call to the Xunji
upsert endpoint must separately follow the mandatory dry-run → summary → explicit
confirmation → confirmed write workflow in `../references/synfit-body-api.md`.

## Error Handling

| Error | Action |
|-------|--------|
| API key missing | Offer manual entry |
| API rate limited | Wait `retry_after_ms`, retry once |
| API key invalid | Tell the user to re-copy it from the Xunji App |
| Cannot parse manual input | Ask for clarification, e.g. `weight 85kg` |
| Body-log file corrupted | Report the exact file and suggest a manual fix; do not overwrite it |
