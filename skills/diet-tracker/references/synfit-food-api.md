# Xunji (训记) Food Open API

## Credentials

- Diet records, custom foods, and templates read `SYNFIT_DIET_DATA_API_KEY` from
  `.env`.
- Official-food search reads the separate `SYNFIT_FOOD_SEARCH_API_KEY`.
- Send credentials only in `Authorization: Bearer ***`; never put them in the
  JSON body, query string, logs, exceptions, or user-facing output.

## Endpoints

| Capability | Base URL | Endpoint |
|---|---|---|
| Query diet records | `https://eatings.xunjiapp.cn` | `POST /open/food/query_gzip` |
| Write diet records | `https://eatings.xunjiapp.cn` | `POST /open/food/upsert_gzip` |
| Custom food upsert | `https://eatings.xunjiapp.cn` | `POST /open/food/custom/upsert_gzip` |
| List templates | `https://eatings.xunjiapp.cn` | `POST /open/food/templates/list_gzip` |
| Apply template | `https://eatings.xunjiapp.cn` | `POST /open/food/templates/apply_gzip` |
| Official-food search | `https://api.xunjiapp.cn` | `POST /open_agent/food/search_gzip` |

The gzip endpoints may return a compressed JSON body. `sync_diet_data.py` decodes
gzip and accepts the official `success`/`res` envelope.

## Query

```json
{
  "start_date": "YYYY-MM-DD",
  "end_date": "YYYY-MM-DD",
  "include_detail": true
}
```

Query only the date range the user requested. The service limits history to the
past year and future three months; explain and split a request outside that window.
The official response stores daily records in `res.days`. The local mirror keeps the
complete `raw_day` alongside conservative normalized food records.

## Official-food search

```json
{"keyword": "鸡蛋", "limit": 8}
```

Prefer `res.foods`. A result's `ntr` is per 100g, `units` contains unit conversions,
and `uniquekey` must be preserved for later write-back. The compact `res.d` form is
accepted by the service but must not be treated as the primary parser when
`res.foods` is present.

## Write-back safety

Before writing, display date, meal type, food name, amount, unit, `uniquekey`, and
nutrition values. `build_food_upsert_payload(..., confirmed=True)` is the only path
that creates a write payload; without explicit confirmation it raises
`UserConfirmationRequired`. Do not infer confirmation from a plan or a previous
message.

The official food record shape is:

```json
{
  "date": "YYYY-MM-DD",
  "meal_type": "lunch",
  "name": "用户确认的食物名",
  "amount": 150,
  "unit": "g",
  "uniquekey": "official result key",
  "ntr": {"cal": 165, "protein": 31, "fat": 3.6, "carb": 0}
}
```

Do not create a custom food when an official match is available. A custom food must
have user-confirmed nutrition per 100g and matching `units`/`ntr.foodUnit` metadata.

## Caching and local compatibility

- Cache one lossless normalized day at `data/diet/xunji/YYYY-MM-DD.json`.
- Treat the cache as the remote-source mirror, not a second manually editable food
  database.
- Derive the existing `data/diet/YYYY-MM-DD.json` daily tracker record from the
  cached official foods. Keep coach-owned training status, expenditure, and notes in
  that projection.
- Never delete local records because an incomplete API response omitted them.
- Preserve IDs, `uniquekey`, `ntr`, `units`, and the complete raw record so future
  projection logic can improve without another remote fetch.

## Limits and errors

- Allow at least 15 seconds between calls to the same endpoint.
- On `too frequent`, honor `retry_after_ms` and retry once.
- A missing or invalid key is a configuration error; do not ask the user to paste a
  credential into chat.
- Unknown or partial nutrition records are rejected rather than estimated.