# Body Data Management

Use `../scripts/sync_body_data.py` for API access, merging, and persistence. Valid
types are documented in `../references/synfit-body-api.md`.

## Query Body Data

Triggered by requests such as “what's my weight trend” or “show body log”.

1. Check `.env` for `SYNFIT_BODY_DATA_API_KEY`.
2. If present, query recent Xunji data as the primary source.
3. Read all applicable `data/user/body-log/YYYY-MM.json` files as the secondary
   source.
4. Merge on `(date, type)` with Xunji API entries winning conflicts.
5. Use a Python script to calculate change and trend; show the date range, first
   and latest values, absolute change, and record count.
6. If neither source has data, say: “No body data found. Would you like to sync
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
6. Report: “✅ Logged weight 85.0 kg on 2026-07-23”.

## Sync from Xunji API

Triggered by “sync body data”, “拉训记数据”, or “sync from Xunji”.

1. Read the API key from `.env`. If missing, offer manual entry.
2. Determine the range: use the earliest local entry through today; if there is
   no local data, use the last 30 days.
3. Call `POST /open/body/query_gzip`.
4. Compare API records with local entries by `(date, type)` and count new or
   changed records.
5. Show a summary such as: “Found 5 new records: 3 weight, 2 bodyfat since July
   18. Sync?”
6. Do not write until the user confirms.
7. On confirmation, merge at entry level with API winning, then use
   `save_body_log` for each affected month.
8. Report: “✅ Synced 5 records from Xunji”.

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
