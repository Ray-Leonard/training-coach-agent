#!/usr/bin/env python3
"""Xunji (Synfit) body-data API client — query and upsert operations."""

from __future__ import annotations

import gzip
import json
import os
import time
import uuid
from datetime import date
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


BASE_URL = "https://api.xunjiapp.cn"
QUERY_ENDPOINT = "/open/body/query_gzip"
UPSERT_ENDPOINT = "/open/body/upsert_gzip"
MIN_ENDPOINT_INTERVAL_SECONDS = 15.0
REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_ENV_PATH = REPO_ROOT / ".env"
BODY_LOG_DIR = REPO_ROOT / "data" / "user" / "body-log"
_LAST_CALL_AT: Dict[str, float] = {}


class XunjiAPIError(RuntimeError):
    """A safe, user-actionable Xunji API error."""

    def __init__(
        self, message: str, *, code: Optional[str] = None, retry_after_ms: int = 0
    ) -> None:
        super().__init__(message)
        self.code = code
        self.retry_after_ms = retry_after_ms


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


def get_api_key() -> Optional[str]:
    """Return the API key from the environment or repo .env, without crashing."""
    return os.environ.get("SYNFIT_BODY_DATA_API_KEY") or _read_dotenv_value(
        DEFAULT_ENV_PATH, "SYNFIT_BODY_DATA_API_KEY"
    )


def _decode_response(raw: bytes, content_encoding: str) -> Any:
    if content_encoding.lower() == "gzip" or raw.startswith(b"\x1f\x8b"):
        raw = gzip.decompress(raw)
    if not raw:
        return {}
    return json.loads(raw.decode("utf-8"))


def _error_from_payload(payload: Any, status: Optional[int] = None) -> XunjiAPIError:
    body = payload if isinstance(payload, dict) else {}
    code = str(body.get("code") or body.get("error_code") or status or "api_error")
    message = str(body.get("message") or body.get("msg") or "Xunji API request failed")
    try:
        retry_after_ms = int(body.get("retry_after_ms") or 0)
    except (TypeError, ValueError):
        retry_after_ms = 0
    return XunjiAPIError(message, code=code, retry_after_ms=retry_after_ms)


def _is_rate_limit(error: XunjiAPIError) -> bool:
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


def _post(endpoint: str, payload: Dict[str, Any], *, retry_rate_limit: bool = True) -> Any:
    api_key = get_api_key()
    if not api_key:
        raise XunjiAPIError(
            "SYNFIT_BODY_DATA_API_KEY is not configured", code="apikey_missing"
        )

    attempts = 2 if retry_rate_limit else 1
    for attempt in range(attempts):
        _respect_endpoint_interval(endpoint)
        request = Request(
            f"{BASE_URL}{endpoint}",
            data=json.dumps(payload).encode("utf-8"),
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
                    raw, exc.headers.get("Content-Encoding", "") if exc.headers else ""
                )
            except (OSError, UnicodeDecodeError, json.JSONDecodeError):
                result = {"message": f"Xunji API HTTP {exc.code}"}
            error = _error_from_payload(result, exc.code)
            if attempt == 0 and _is_rate_limit(error):
                time.sleep(max(error.retry_after_ms / 1000, 15.0))
                continue
            raise error from exc
        except (URLError, TimeoutError) as exc:
            raise XunjiAPIError(f"Unable to reach Xunji API: {exc}") from exc
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise XunjiAPIError("Xunji API returned an unreadable response") from exc

        if isinstance(result, dict) and (
            result.get("success") is False or result.get("error")
        ):
            error = _error_from_payload(result)
            if attempt == 0 and _is_rate_limit(error):
                time.sleep(max(error.retry_after_ms / 1000, 15.0))
                continue
            raise error
        return result
    raise XunjiAPIError("Xunji API request failed after retry")


def _validate_iso_date(value: str, field: str) -> str:
    try:
        return date.fromisoformat(value).isoformat()
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must use YYYY-MM-DD format") from exc


def query_body_data(
    start_date: str, end_date: str, types: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """Query Xunji and return its parsed records array."""
    start = _validate_iso_date(start_date, "start_date")
    end = _validate_iso_date(end_date, "end_date")
    if start > end:
        raise ValueError("start_date cannot be after end_date")
    payload: Dict[str, Any] = {
        "start_date": start,
        "end_date": end,
        "include_latest": True,
        "include_records": True,
        "limit": 1000,
        "offset": 0,
    }
    if types:
        payload["types"] = list(types)
    response = _post(QUERY_ENDPOINT, payload)
    if isinstance(response, list):
        return response
    if not isinstance(response, dict):
        return []
    res = response.get("res") or response.get("data") or response
    if isinstance(res, dict) and isinstance(res.get("records"), list):
        return res["records"]
    return []


def _normalize_api_record(record: Dict[str, Any]) -> Dict[str, Any]:
    normalized: Dict[str, Any] = {
        "date": record.get("date") or record.get("datestr"),
        "type": record.get("type"),
        "value": record.get("value", record.get("weight")),
        "unit": record.get("unit"),
        "source": "xunji_api",
    }
    if record.get("id") is not None:
        normalized["xunji_id"] = record["id"]
    return normalized


def merge_body_logs(
    api_records: Iterable[Dict[str, Any]],
    local_records: Iterable[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Deduplicate on (date, type), with normalized API records winning."""
    merged: Dict[tuple, Dict[str, Any]] = {}
    for record in local_records:
        item = dict(record)
        key = (item.get("date") or item.get("datestr"), item.get("type"))
        if all(key):
            item["date"] = key[0]
            merged[key] = item
    for record in api_records:
        item = _normalize_api_record(record)
        key = (item.get("date"), item.get("type"))
        if all(key):
            merged[key] = item
    return sorted(merged.values(), key=lambda item: (item["date"], item["type"]))


def upsert_body_data(
    records: List[Dict[str, Any]], dry_run: bool = True
) -> Any:
    """Upsert body data; confirmed writes require an explicit dry_run=False call."""
    if not isinstance(records, list) or not records:
        raise ValueError("records must be a non-empty list")
    payload: Dict[str, Any] = {
        "schema_version": "1.0",
        "client_request_id": str(uuid.uuid4()),
        "dry_run": bool(dry_run),
        "records": records,
    }
    if not dry_run:
        payload["confirmed"] = True
    return _post(UPSERT_ENDPOINT, payload)


def save_body_log(records: Iterable[Dict[str, Any]], month: str) -> Path:
    """Write one month of strict JSON body-log data and return its path."""
    try:
        month_date = date.fromisoformat(f"{month}-01")
    except (TypeError, ValueError) as exc:
        raise ValueError("month must use YYYY-MM format") from exc
    normalized_month = month_date.strftime("%Y-%m")
    selected = [
        {**dict(record), "date": record.get("date") or record.get("datestr")}
        for record in records
        if str(record.get("date") or record.get("datestr", "")).startswith(
            f"{normalized_month}-"
        )
    ]
    _KEEP_FIELDS = {"date", "type", "value", "unit", "source", "xunji_id"}
    for r in selected:
        r.pop("datestr", None)
        r.pop("weight", None)   # duplicate of value
        r.pop("label", None)
        r.pop("label_en", None)
        # normalize source and xunji_id from id
        if not r.get("source"):
            r["source"] = "xunji_api" if r.get("id") is not None else "xunji_api"
        if r.get("id") is not None and not r.get("xunji_id"):
            r["xunji_id"] = r["id"]
        r.pop("id", None)
        for k in list(r):
            if k not in _KEEP_FIELDS:
                del r[k]
    selected.sort(key=lambda item: (item.get("date", ""), item.get("type", "")), reverse=True)
    BODY_LOG_DIR.mkdir(parents=True, exist_ok=True)
    destination = BODY_LOG_DIR / f"{normalized_month}.json"
    temporary = destination.with_suffix(".json.tmp")
    temporary.write_text(
        json.dumps(selected, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    temporary.replace(destination)
    return destination


__all__ = [
    "XunjiAPIError",
    "get_api_key",
    "query_body_data",
    "merge_body_logs",
    "upsert_body_data",
    "save_body_log",
]
