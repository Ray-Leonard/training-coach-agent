# Xunji (训记) Body API

## Authentication and Base URL

- Base URL: `https://api.xunjiapp.cn`
- Send `Authorization: Bearer <token>`.
- Read the token from `.env` variable `SYNFIT_BODY_DATA_API_KEY`. Never print or
  commit it.
- Requests and responses use JSON. The `_gzip` endpoints may return a
  gzip-compressed response.

## Query body data

`POST /open/body/query_gzip`

Request parameters:

| Parameter | Type | Required | Meaning |
|-----------|------|----------|---------|
| `start_date` | string | yes | Inclusive `YYYY-MM-DD` |
| `end_date` | string | yes | Inclusive `YYYY-MM-DD` |
| `types` | array of strings | no | Restrict results to body-data types |
| `include_latest` | boolean | no | Include the latest entry for each type |
| `include_records` | boolean | no | Include the date-descending `records` array |
| `limit` | integer | no | Maximum records returned |
| `offset` | integer | no | Pagination offset |

Every record contains `id`, `datestr`, `type`, `value`, `weight` (an alias of
`value`), `unit`, `label`, and `label_en`. The response also exposes
`type_metadata`, `latest`, and `records`.

## Upsert body data

`POST /open/body/upsert_gzip`

Request parameters:

- `schema_version`
- `client_request_id`
- `dry_run`
- `records` (array)
- `confirmed` (required for the confirmed write)

Upsert is always a two-stage operation:

1. Call with `dry_run=true`.
2. Show the returned summary to the user and obtain explicit confirmation.
3. Only after confirmation call with `dry_run=false` and `confirmed=true`.

Never bypass the dry run or infer confirmation.

## Body-data types

There are 15 supported types. Historical API spellings (`weist`, `bot`, `cav`)
must be preserved exactly.

| Type | Unit | `label_en` |
|------|------|------------|
| `weight` | kg | Weight |
| `bodyfat` | % | Body Fat |
| `neck` | cm | Neck |
| `chest` | cm | Chest |
| `weist` | cm | Waist |
| `shoulder` | cm | Shoulder |
| `bot` | cm | Hips |
| `arm_left` | cm | Left Arm |
| `arm_right` | cm | Right Arm |
| `forearm_left` | cm | Left Forearm |
| `forearm_right` | cm | Right Forearm |
| `leg_left` | cm | Left Leg |
| `leg_right` | cm | Right Leg |
| `cav_left` | cm | Left Calf |
| `cav_right` | cm | Right Calf |

Use `type_metadata` from the live response as the authoritative labels and units
when displaying API data.

## Rate limiting

Allow at least 15 seconds between calls to the same endpoint. On a “too
frequent” response, read `retry_after_ms`, wait that duration, and retry only
once.

## Errors

| Error | Handling |
|-------|----------|
| Too frequent / rate limited | Wait `retry_after_ms`, retry once |
| API key missing | Offer manual entry or explain how to configure `.env` |
| API key invalid | Ask the user to re-copy the key from the Xunji App |
| User confirmation required | Run dry-run, show summary, obtain confirmation, then write with `confirmed=true` |
| VIP only | Explain that this endpoint requires Xunji VIP access; offer manual entry |
