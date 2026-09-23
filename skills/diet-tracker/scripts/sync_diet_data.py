#!/usr/bin/env python3
"""Xunji/Synfit Open Food API client and lossless local diet mirror."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
import os
import tempfile
import time
import uuid
from datetime import date
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

try:  # Support package imports and direct CLI execution.
    from .common import iso_timestamp, load_profile
except ImportError:  # pragma: no cover - exercised by direct CLI use
    from common import iso_timestamp, load_profile  # type: ignore


DIET_BASE_URL = "https://eatings.xunjiapp.cn"
FOOD_SEARCH_BASE_URL = "https://api.xunjiapp.cn"
QUERY_ENDPOINT = "/open/food/query_gzip"
UPSERT_ENDPOINT = "/open/food/upsert_gzip"
CUSTOM_FOOD_ENDPOINT = "/open/food/custom/upsert_gzip"
TEMPLATES_LIST_ENDPOINT = "/open/food/templates/list_gzip"
TEMPLATES_APPLY_ENDPOINT = "/open/food/templates/apply_gzip"
FOOD_SEARCH_ENDPOINT = "/open_agent/food/search_gzip"
MIN_ENDPOINT_INTERVAL_SECONDS = 15.0
REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_ENV_PATH = REPO_ROOT / ".env"
DIET_CACHE_DIR = REPO_ROOT / "data" / "diet" / "xunji"
QUERY_INDEX_NAME = ".query-index.json"
_LAST_CALL_AT: Dict[str, float] = {}


class XunjiDietAPIError(RuntimeError):
    """A safe, user-actionable Xunji diet API error."""

    def __init__(
        self,
        message: str,
        *,
        code: Optional[str] = None,
        retry_after_ms: int = 0,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.retry_after_ms = retry_after_ms


class UserConfirmationRequired(ValueError):
    """Raised when a remote food write lacks explicit user confirmation."""


def _read_dotenv_value(path: Path, key: str) -> Optional[str]:
    if not path.is_file():
        return None
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return None
    for raw_line in lines:
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        if name.strip() != key:
            continue
        clean_value = value.strip()
        if len(clean_value) >= 2 and clean_value[0] == clean_value[-1]:
            if clean_value[0] in {"'", '"'}:
                clean_value = clean_value[1:-1]
        return clean_value or None
    return None


def get_diet_api_key() -> Optional[str]:
    """Return the diet record key without exposing its value."""
    return os.environ.get("SYNFIT_DIET_DATA_API_KEY") or _read_dotenv_value(
        DEFAULT_ENV_PATH, "SYNFIT_DIET_DATA_API_KEY"
    )


def get_food_search_api_key() -> Optional[str]:
    """Return the separate official-food-search key without exposing its value."""
    return os.environ.get("SYNFIT_FOOD_SEARCH_API_KEY") or _read_dotenv_value(
        DEFAULT_ENV_PATH, "SYNFIT_FOOD_SEARCH_API_KEY"
    )


def _validate_iso_date(value: str, field: str) -> str:
    try:
        return date.fromisoformat(value).isoformat()
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must use YYYY-MM-DD format") from exc


def _validate_query_window(start_date: str, end_date: str) -> tuple[str, str]:
    start = _validate_iso_date(start_date, "start_date")
    end = _validate_iso_date(end_date, "end_date")
    if start > end:
        raise ValueError("start_date cannot be after end_date")
    return start, end


def _decode_response(raw: bytes, content_encoding: str = "") -> Any:
    if content_encoding.lower() == "gzip" or raw.startswith(b"\x1f\x8b"):
        raw = gzip.decompress(raw)
    if not raw:
        return {}
    return json.loads(raw.decode("utf-8"))


def decode_json_response(raw: bytes, content_encoding: str = "") -> Any:
    """Public testable wrapper for JSON/gzip response decoding."""
    return _decode_response(raw, content_encoding)


def _error_from_payload(payload: Any, status: Optional[int] = None) -> XunjiDietAPIError:
    body = payload if isinstance(payload, dict) else {}
    code = str(body.get("code") or body.get("error_code") or status or "api_error")
    message = str(body.get("message") or body.get("msg") or "Xunji diet API request failed")
    try:
        retry_after_ms = int(body.get("retry_after_ms") or 0)
    except (TypeError, ValueError):
        retry_after_ms = 0
    return XunjiDietAPIError(message, code=code, retry_after_ms=retry_after_ms)


def _is_rate_limit(error: XunjiDietAPIError) -> bool:
    combined = f"{error.code or ''} {error}".lower()
    return (
        error.retry_after_ms > 0
        or "too frequent" in combined
        or "rate" in combined
        or error.code == "429"
    )


def _respect_endpoint_interval(endpoint: str) -> None:
    elapsed = time.monotonic() - _LAST_CALL_AT.get(endpoint, 0.0)
    remaining = MIN_ENDPOINT_INTERVAL_SECONDS - elapsed
    if remaining > 0:
        time.sleep(remaining)


def _post_json(
    base_url: str,
    endpoint: str,
    payload: Dict[str, Any],
    api_key: Optional[str],
    *,
    retry_rate_limit: bool = True,
) -> Any:
    if not api_key:
        raise XunjiDietAPIError(
            "required Xunji API key is not configured", code="apikey_missing"
        )
    attempts = 2 if retry_rate_limit else 1
    for attempt in range(attempts):
        _respect_endpoint_interval(endpoint)
        request = Request(
            f"{base_url}{endpoint}",
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Accept-Encoding": "gzip",
            },
            method="POST",
        )
        _LAST_CALL_AT[endpoint] = time.monotonic()
        try:
            with urlopen(request, timeout=30) as response:
                result = _decode_response(
                    response.read(), response.headers.get("Content-Encoding", "")
                )
        except HTTPError as exc:
            raw = exc.read()
            try:
                result = _decode_response(
                    raw,
                    exc.headers.get("Content-Encoding", "") if exc.headers else "",
                )
            except (OSError, UnicodeDecodeError, json.JSONDecodeError):
                result = {"message": f"Xunji diet API HTTP {exc.code}"}
            error = _error_from_payload(result, exc.code)
            if attempt == 0 and _is_rate_limit(error):
                time.sleep(max(error.retry_after_ms / 1000, 15.0))
                continue
            raise error from exc
        except (URLError, TimeoutError) as exc:
            raise XunjiDietAPIError(f"Unable to reach Xunji diet API: {exc}") from exc
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise XunjiDietAPIError("Xunji diet API returned an unreadable response") from exc

        if isinstance(result, dict) and (
            result.get("success") is False or result.get("error")
        ):
            error = _error_from_payload(result)
            if attempt == 0 and _is_rate_limit(error):
                time.sleep(max(error.retry_after_ms / 1000, 15.0))
                continue
            raise error
        return result
    raise XunjiDietAPIError("Xunji diet API request failed after retry")


def query_food_data(
    start_date: str,
    end_date: str,
    *,
    include_detail: bool = True,
) -> Any:
    """Read official food records for an explicit bounded date range."""
    start, end = _validate_query_window(start_date, end_date)
    return _post_json(
        DIET_BASE_URL,
        QUERY_ENDPOINT,
        {
            "start_date": start,
            "end_date": end,
            "include_detail": bool(include_detail),
        },
        get_diet_api_key(),
    )


def search_foods(keyword: str, *, limit: int = 8) -> Any:
    """Search official foods using the separate food-search credential."""
    if not isinstance(keyword, str) or not keyword.strip():
        raise ValueError("keyword must be a non-empty string")
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 100:
        raise ValueError("limit must be an integer from 1 to 100")
    return _post_json(
        FOOD_SEARCH_BASE_URL,
        FOOD_SEARCH_ENDPOINT,
        {"keyword": keyword.strip(), "limit": limit},
        get_food_search_api_key(),
    )


def normalize_food_search_response(response: Any) -> List[Dict[str, Any]]:
    """Prefer the expanded ``res.foods`` form, then decode compact ``res.d``."""
    if not isinstance(response, dict):
        raise ValueError("Xunji food-search response must be an object")
    if response.get("success") is False:
        raise _error_from_payload(response)
    res = response.get("res")
    if not isinstance(res, dict):
        raise ValueError("Xunji food-search response is missing res")
    foods = res.get("foods")
    if foods is not None:
        if not isinstance(foods, list):
            raise ValueError("Xunji food-search res.foods must be a list")
        expanded: List[Dict[str, Any]] = []
        for food in foods:
            if not isinstance(food, dict):
                raise ValueError("each official food search result must be an object")
            expanded.append(dict(food))
        return expanded
    compact = res.get("d", [])
    if not isinstance(compact, list):
        raise ValueError("Xunji food-search res.d must be a list")
    expanded = []
    for item in compact:
        if not isinstance(item, list) or len(item) < 9:
            raise ValueError("compact food result must contain nine fields")
        expanded.append(
            {
                "id": item[0],
                "name": item[1],
                "ntr": {
                    "cal": item[2],
                    "carb": item[3],
                    "fat": item[4],
                    "protein": item[5],
                },
                "foodpic": item[6],
                "uniquekey": item[7],
                "units": item[8],
            }
        )
    return expanded


def _numeric(value: Any, field: str, *, minimum: float = 0.0) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{field} must be numeric")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be numeric") from exc
    if not math.isfinite(number) or number < minimum:
        raise ValueError(f"{field} must be finite and >= {minimum}")
    return number


def _validate_ntr(ntr: Any) -> Dict[str, float]:
    if not isinstance(ntr, dict):
        raise ValueError("food record ntr must be an object")
    result: Dict[str, float] = {}
    for field in ("cal", "protein", "fat", "carb"):
        if field not in ntr:
            raise ValueError(f"food record ntr is missing {field}")
        result[field] = _numeric(ntr[field], f"food record ntr.{field}")
    return result


def normalize_food_record(record: Dict[str, Any], day_date: str) -> Dict[str, Any]:
    if not isinstance(record, dict):
        raise ValueError("food record must be an object")
    name = record.get("name")
    unit = record.get("unit")
    if not isinstance(name, str) or not name.strip():
        raise ValueError("food record name must be a non-empty string")
    if not isinstance(unit, str) or not unit.strip():
        raise ValueError("food record unit must be a non-empty string")
    if "amount" not in record:
        raise ValueError("food record is missing amount")
    if "ntr" not in record:
        raise ValueError("food record is missing ntr")
    normalized: Dict[str, Any] = {
        "date": _validate_iso_date(record.get("date") or day_date, "food.date"),
        "name": name.strip(),
        "amount": _numeric(record["amount"], "food record amount"),
        "unit": unit.strip(),
        "ntr": _validate_ntr(record["ntr"]),
        "units": record.get("units", []),
        "raw": dict(record),
    }
    if not isinstance(normalized["units"], list):
        raise ValueError("food record units must be a list when present")
    for field in ("id", "localid", "meal_type", "uniquekey"):
        if field in record:
            normalized[field] = record[field]
    return normalized


def normalize_query_response(response: Any) -> List[Dict[str, Any]]:
    """Normalize documented ``res.days`` while retaining every raw day."""
    if not isinstance(response, dict):
        raise ValueError("Xunji food response must be an object")
    if response.get("success") is False:
        raise _error_from_payload(response)
    res = response.get("res")
    if not isinstance(res, dict):
        raise ValueError("Xunji food response is missing res")
    days = res.get("days")
    if not isinstance(days, list):
        raise ValueError("Xunji food response res.days must be a list")
    normalized_days: List[Dict[str, Any]] = []
    for day in days:
        if not isinstance(day, dict):
            raise ValueError("each Xunji food day must be an object")
        day_date = day.get("date") or day.get("datestr")
        if not isinstance(day_date, str):
            raise ValueError("Xunji food day is missing date")
        day_date = _validate_iso_date(day_date, "day.date")
        foods = day.get("foods", [])
        if not isinstance(foods, list):
            raise ValueError("Xunji food day foods must be a list")
        normalized_days.append(
            {
                "date": day_date,
                "source": "xunji_api",
                "foods": [normalize_food_record(food, day_date) for food in foods],
                "raw_day": dict(day),
            }
        )
    return normalized_days


def _grams_for_food(record: Dict[str, Any]) -> float:
    """Convert a selected official unit to grams without guessing."""
    amount = _numeric(record["amount"], "food record amount")
    raw_unit = str(record["unit"]).strip()
    unit = raw_unit.casefold()
    direct_gram_units = {
        "g": 1.0,
        "gram": 1.0,
        "grams": 1.0,
        "克": 1.0,
        "kg": 1000.0,
        "kilogram": 1000.0,
        "kilograms": 1000.0,
        "千克": 1000.0,
    }
    if unit in direct_gram_units:
        return amount * direct_gram_units[unit]
    units = record.get("units", [])
    if isinstance(units, list):
        for metadata in units:
            if not isinstance(metadata, dict):
                continue
            metadata_unit = metadata.get("unit")
            if not isinstance(metadata_unit, str) or metadata_unit.strip().casefold() != unit:
                continue
            grams_per_unit = metadata.get("gram")
            if grams_per_unit is None:
                continue
            return amount * _numeric(grams_per_unit, "food unit gram", minimum=0.01)
    raise ValueError(f"food record unit {raw_unit!r} cannot convert to grams")


def _stable_remote_meal_id(record: Dict[str, Any]) -> str:
    for field in ("id", "localid"):
        if record.get(field) is not None:
            return f"xunji-{record[field]}"
    identity = json.dumps(
        {
            "date": record.get("date"),
            "meal_type": record.get("meal_type"),
            "name": record.get("name"),
            "amount": record.get("amount"),
            "unit": record.get("unit"),
            "uniquekey": record.get("uniquekey"),
        },
        ensure_ascii=False,
        sort_keys=True,
    ).encode("utf-8")
    return f"xunji-{hashlib.sha256(identity).hexdigest()[:24]}"


def project_food_record(record: Dict[str, Any], *, sync_timestamp: str) -> Dict[str, Any]:
    """Project one official record into the existing daily-meal shape."""
    if not isinstance(sync_timestamp, str):
        raise ValueError("sync_timestamp must be an ISO-8601 timestamp")
    raw_record_date = record.get("date")
    if not isinstance(raw_record_date, str):
        raise ValueError("food record is missing date")
    normalized = normalize_food_record(record, raw_record_date)
    grams = _grams_for_food(normalized)
    factor = grams / 100.0
    ntr = normalized["ntr"]
    meal = {
        "id": _stable_remote_meal_id(normalized),
        "meal_name": normalized.get("meal_type") or "unknown",
        "food_name": normalized["name"],
        "items": [normalized["name"]],
        "calories_kcal": round(ntr["cal"] * factor, 2),
        "protein_g": round(ntr["protein"] * factor, 2),
        "carbs_g": round(ntr["carb"] * factor, 2),
        "fat_g": round(ntr["fat"] * factor, 2),
        "source": "xunji_api",
        "timestamp": sync_timestamp,
        "remote": normalized,
    }
    return meal


def project_xunji_day(
    normalized_day: Dict[str, Any],
    profile: Dict[str, Any],
    *,
    existing_day: Optional[Dict[str, Any]] = None,
    sync_timestamp: str,
) -> Dict[str, Any]:
    """Build a local daily projection while preserving coach-owned context."""
    if not isinstance(normalized_day, dict):
        raise ValueError("normalized_day must be an object")
    timezone = profile.get("timezone")
    if not isinstance(timezone, str) or not timezone.strip():
        raise ValueError("profile.timezone must be a non-empty string")
    raw_day_date = normalized_day.get("date")
    if not isinstance(raw_day_date, str):
        raise ValueError("normalized_day is missing date")
    day_date = _validate_iso_date(raw_day_date, "day.date")
    existing = existing_day or {}
    meals: List[Dict[str, Any]] = []
    pending_foods: List[Dict[str, Any]] = []
    for food in normalized_day.get("foods", []):
        try:
            meals.append(project_food_record(food, sync_timestamp=sync_timestamp))
        except ValueError as exc:
            pending_foods.append({"food": food, "reason": str(exc)})
    projected = {
        "schema_version": "1.1",
        "date": day_date,
        "timezone": timezone,
        "training_status": existing.get("training_status"),
        "training_status_confirmed": existing.get("training_status_confirmed", False),
        "training_confirmation_source": existing.get("training_confirmation_source"),
        "meals": meals,
        "actual_expenditure_kcal": existing.get("actual_expenditure_kcal"),
        "expenditure_source": existing.get("expenditure_source"),
        "notes": existing.get("notes", ""),
        "source": "xunji_api",
        "xunji": {
            "raw_day": normalized_day.get("raw_day", {}),
            "synced_at": sync_timestamp,
            "food_count": len(normalized_day.get("foods", [])),
            "pending_foods": pending_foods,
        },
    }
    return projected


def build_food_upsert_payload(
    foods: List[Dict[str, Any]],
    *,
    client_request_id: Optional[str] = None,
    confirmed: bool = False,
) -> Dict[str, Any]:
    """Build the official write payload only after explicit confirmation."""
    if not isinstance(foods, list) or not foods:
        raise ValueError("foods must be a non-empty list")
    if not confirmed:
        raise UserConfirmationRequired(
            "Xunji food write requires explicit user confirmation"
        )
    for food in foods:
        if not isinstance(food, dict):
            raise ValueError("each food write record must be an object")
    return {
        "client_request_id": client_request_id or str(uuid.uuid4()),
        "dry_run": False,
        "foods": foods,
    }


def upsert_food_data(
    foods: List[Dict[str, Any]], *, confirmed: bool = False, client_request_id: Optional[str] = None
) -> Any:
    payload = build_food_upsert_payload(
        foods, client_request_id=client_request_id, confirmed=confirmed
    )
    return _post_json(DIET_BASE_URL, UPSERT_ENDPOINT, payload, get_diet_api_key())


def upsert_custom_food(
    food: Dict[str, Any], *, confirmed: bool = False, client_request_id: Optional[str] = None
) -> Any:
    if not isinstance(food, dict) or not food:
        raise ValueError("food must be a non-empty object")
    if not confirmed:
        raise UserConfirmationRequired(
            "Xunji custom-food write requires explicit user confirmation"
        )
    payload = {
        "client_request_id": client_request_id or str(uuid.uuid4()),
        "dry_run": False,
        "food": food,
    }
    return _post_json(DIET_BASE_URL, CUSTOM_FOOD_ENDPOINT, payload, get_diet_api_key())


def list_food_templates(payload: Optional[Dict[str, Any]] = None) -> Any:
    return _post_json(
        DIET_BASE_URL,
        TEMPLATES_LIST_ENDPOINT,
        dict(payload or {}),
        get_diet_api_key(),
    )


def apply_food_template(
    payload: Dict[str, Any], *, confirmed: bool = False
) -> Any:
    if not isinstance(payload, dict) or not payload:
        raise ValueError("template payload must be a non-empty object")
    if not confirmed:
        raise UserConfirmationRequired(
            "applying an Xunji food template requires explicit user confirmation"
        )
    request_payload = dict(payload)
    request_payload.setdefault("client_request_id", str(uuid.uuid4()))
    return _post_json(
        DIET_BASE_URL,
        TEMPLATES_APPLY_ENDPOINT,
        request_payload,
        get_diet_api_key(),
    )


def _cache_root(root: Optional[Path]) -> Path:
    return (Path(root).expanduser().resolve() if root else REPO_ROOT) / "data" / "diet" / "xunji"


def _atomic_json_write(destination: Path, payload: Any) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(
        prefix=f".{destination.name}.", suffix=".tmp", dir=str(destination.parent)
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(destination)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def _query_cache_key(start_date: str, end_date: str, include_detail: bool) -> str:
    start, end = _validate_query_window(start_date, end_date)
    return json.dumps(
        {"start_date": start, "end_date": end, "include_detail": bool(include_detail)},
        sort_keys=True,
        separators=(",", ":"),
    )


def _query_index_path(root: Optional[Path]) -> Path:
    return _cache_root(root) / QUERY_INDEX_NAME


def _read_query_index(root: Optional[Path]) -> Dict[str, Any]:
    path = _query_index_path(root)
    if not path.is_file():
        return {"version": 1, "queries": {}}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"version": 1, "queries": {}}
    if not isinstance(payload, dict) or not isinstance(payload.get("queries"), dict):
        return {"version": 1, "queries": {}}
    return payload


def cache_query_result(
    start_date: str,
    end_date: str,
    include_detail: bool,
    days: List[Dict[str, Any]],
    *,
    root: Optional[Path] = None,
) -> List[Path]:
    """Cache days and record the exact query so identical syncs do not refetch."""
    cache_root = _cache_root(root)
    paths = cache_days(days, root=root)
    relative_paths = [str(path.relative_to(cache_root)) for path in paths]
    index = _read_query_index(root)
    index["queries"][_query_cache_key(start_date, end_date, include_detail)] = {
        "start_date": _validate_iso_date(start_date, "start_date"),
        "end_date": _validate_iso_date(end_date, "end_date"),
        "include_detail": bool(include_detail),
        "day_files": relative_paths,
    }
    _atomic_json_write(_query_index_path(root), index)
    return paths


def load_cached_query(
    start_date: str,
    end_date: str,
    include_detail: bool = True,
    *,
    root: Optional[Path] = None,
) -> Optional[List[Dict[str, Any]]]:
    """Return cached days, or ``None`` when the exact query is not cached."""
    index = _read_query_index(root)
    entry = index.get("queries", {}).get(
        _query_cache_key(start_date, end_date, include_detail)
    )
    if not isinstance(entry, dict) or not isinstance(entry.get("day_files"), list):
        return None
    cache_root = _cache_root(root)
    days: List[Dict[str, Any]] = []
    for relative_name in entry["day_files"]:
        if not isinstance(relative_name, str):
            return None
        path = (cache_root / relative_name).resolve()
        if path.parent != cache_root or not path.is_file():
            return None
        try:
            day = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        if not isinstance(day, dict):
            return None
        days.append(day)
    return days


def invalidate_query_cache(
    *, root: Optional[Path] = None, dates: Optional[Iterable[str]] = None
) -> None:
    """Invalidate all or overlapping query entries after a confirmed remote write."""
    index = _read_query_index(root)
    queries = index.get("queries", {})
    if not isinstance(queries, dict):
        return
    normalized_dates = None
    if dates is not None:
        normalized_dates = {_validate_iso_date(value, "date") for value in dates}
    kept: Dict[str, Any] = {}
    for key, entry in queries.items():
        if not isinstance(entry, dict):
            continue
        if normalized_dates is None:
            continue
        try:
            start = _validate_iso_date(entry["start_date"], "start_date")
            end = _validate_iso_date(entry["end_date"], "end_date")
        except (KeyError, ValueError):
            continue
        if any(start <= value <= end for value in normalized_dates):
            continue
        kept[key] = entry
    index["queries"] = kept
    _atomic_json_write(_query_index_path(root), index)


def cache_days(days: Iterable[Dict[str, Any]], *, root: Optional[Path] = None) -> List[Path]:
    """Atomically cache one lossless official day per local date."""
    cache_root = (Path(root).expanduser().resolve() if root else REPO_ROOT) / "data" / "diet" / "xunji"
    cache_root.mkdir(parents=True, exist_ok=True)
    paths: List[Path] = []
    for day in days:
        if not isinstance(day, dict):
            raise ValueError("cached day must be an object")
        raw_day_date = day.get("date")
        if not isinstance(raw_day_date, str):
            raise ValueError("cached day is missing date")
        day_date = _validate_iso_date(raw_day_date, "day.date")
        destination = cache_root / f"{day_date}.json"
        fd, temporary_name = tempfile.mkstemp(
            prefix=f".{destination.name}.", suffix=".tmp", dir=str(destination.parent)
        )
        temporary = Path(temporary_name)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(day, handle, ensure_ascii=False, indent=2)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            temporary.replace(destination)
        except Exception:
            temporary.unlink(missing_ok=True)
            raise
        paths.append(destination)
    return paths


def sync_food_data(
    start_date: str,
    end_date: str,
    *,
    root: Optional[Path] = None,
    sync_timestamp: Optional[str] = None,
    force: bool = False,
) -> Dict[str, Any]:
    """Fetch, mirror, and project official days without deleting omissions."""
    start, end = _validate_query_window(start_date, end_date)
    days = None if force else load_cached_query(start, end, True, root=root)
    cache_hit = days is not None
    if days is None:
        response = query_food_data(start, end, include_detail=True)
        days = normalize_query_response(response)
        cache_query_result(start, end, True, days, root=root)
    profile = load_profile(root)
    synced_at = sync_timestamp or iso_timestamp(profile)

    try:
        from . import diet_log as local_diet_log
    except ImportError:  # pragma: no cover - exercised by direct CLI use
        import diet_log as local_diet_log  # type: ignore

    projections: List[Dict[str, Any]] = []
    for day in days:
        existing = local_diet_log.load_day(day["date"], root=root, profile=profile)
        projections.append(
            project_xunji_day(
                day,
                profile,
                existing_day=existing,
                sync_timestamp=synced_at,
            )
        )
    projection_paths = [local_diet_log.save_day(day, root=root) for day in projections]
    return {
        "days": len(days),
        "foods": sum(len(day.get("foods", [])) for day in days),
        "cache_hit": cache_hit,
        "projection_paths": projection_paths,
        "synced_at": synced_at,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Xunji/Synfit official diet API client")
    sub = parser.add_subparsers(dest="command", required=True)
    query = sub.add_parser("query", help="query official food records")
    query.add_argument("--start", required=True)
    query.add_argument("--end", required=True)
    query.add_argument("--no-detail", action="store_true")
    search = sub.add_parser("search", help="search official foods")
    search.add_argument("keyword")
    search.add_argument("--limit", type=int, default=8)
    sync = sub.add_parser("sync", help="mirror and project official food records")
    sync.add_argument("--start", required=True)
    sync.add_argument("--end", required=True)
    sync.add_argument("--force", action="store_true", help="bypass the exact-query cache")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "query":
            days = normalize_query_response(
                query_food_data(args.start, args.end, include_detail=not args.no_detail)
            )
            print(f"Found {len(days)} Xunji diet days")
            for day in days:
                print(f"{day['date']}: {len(day['foods'])} foods")
        elif args.command == "search":
            foods = normalize_food_search_response(
                search_foods(args.keyword, limit=args.limit)
            )
            print(f"Found {len(foods)} official foods")
        elif args.command == "sync":
            summary = sync_food_data(args.start, args.end, force=args.force)
            print(
                f"Synced {summary['foods']} foods across {summary['days']} days "
                f"from Xunji (cache_hit={summary['cache_hit']})"
            )
        return 0
    except (FileNotFoundError, ValueError, OSError, XunjiDietAPIError) as exc:
        print(f"error: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
