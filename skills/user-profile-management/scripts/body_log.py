#!/usr/bin/env python3
"""Manual body-log CRUD — log, delete, list, and save monthly body measurement files."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

REPO_ROOT = Path(__file__).resolve().parents[3]
BODY_LOG_DIR = REPO_ROOT / "data" / "user" / "body-log"


def _today_in_tz(tz_name: str) -> date:
    """Return today's date in the given IANA timezone (e.g., 'Asia/Shanghai')."""
    from datetime import datetime
    from zoneinfo import ZoneInfo
    return datetime.now(ZoneInfo(tz_name)).date()


def _read_profile_timezone() -> str:
    """Read timezone from data/user/profile.json. Returns 'UTC' on failure."""
    profile_path = REPO_ROOT / "data" / "user" / "profile.json"
    try:
        raw = json.loads(profile_path.read_text(encoding="utf-8"))
        tz = raw.get("timezone")
        if tz and isinstance(tz, str):
            return tz
    except Exception:
        pass
    return "UTC"


def _load_month(month: str) -> List[Dict[str, Any]]:
    """Load records for a given YYYY-MM month. Returns empty list if missing."""
    month_path = BODY_LOG_DIR / f"{month}.json"
    if month_path.is_file():
        try:
            return json.loads(month_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return []


def _save_month(records: List[Dict[str, Any]], month: str) -> Path:
    """Write one month of strict JSON body-log data atomically."""
    BODY_LOG_DIR.mkdir(parents=True, exist_ok=True)
    destination = BODY_LOG_DIR / f"{month}.json"
    temporary = destination.with_suffix(".json.tmp")
    temporary.write_text(
        json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    temporary.replace(destination)
    return destination


# ── Public API ──────────────────────────────────────────────────────────────


def log_entry(
    entry_type: str, value: float, unit: str, *, date_str: Optional[str] = None
) -> Path:
    """Add or update a manual body measurement.

    Replaces an existing manual entry with the same (date, type) or appends.
    Returns the written file path.
    """
    entry_date = date_str or _today_in_tz(_read_profile_timezone()).isoformat()
    month = entry_date[:7]
    entry: Dict[str, Any] = {
        "date": entry_date,
        "type": entry_type,
        "value": value,
        "unit": unit,
        "source": "manual",
    }

    records = _load_month(month)
    replaced = False
    for i, record in enumerate(records):
        r_date = record.get("date") or record.get("datestr")
        if (
            r_date == entry_date
            and record.get("type") == entry_type
            and record.get("source") == "manual"
        ):
            records[i] = entry
            replaced = True
            break
    if not replaced:
        records.append(entry)

    return _save_month(records, month)


def delete_entry(date_str: str, entry_type: str) -> int:
    """Delete all manual entries matching (date, type). Returns count deleted."""
    month = date_str[:7]
    records = _load_month(month)
    before = len(records)
    records = [
        r
        for r in records
        if not (
            (r.get("date") or r.get("datestr")) == date_str
            and r.get("type") == entry_type
            and r.get("source") == "manual"
        )
    ]
    if len(records) < before:
        _save_month(records, month)
    return before - len(records)


def list_entries(
    month: Optional[str] = None,
    entry_type: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """List body-log entries, optionally filtered by month or type.

    If month is None, lists all months. Returns date-ascending sorted records.
    """
    if month:
        records = _load_month(month)
        if entry_type:
            records = [r for r in records if r.get("type") == entry_type]
        records.sort(key=lambda r: (r.get("date", ""), r.get("type", "")))
        return records

    all_records: List[Dict[str, Any]] = []
    if BODY_LOG_DIR.is_dir():
        for f in sorted(BODY_LOG_DIR.glob("*.json")):
            try:
                month_records = json.loads(f.read_text(encoding="utf-8"))
                if entry_type:
                    month_records = [
                        r for r in month_records if r.get("type") == entry_type
                    ]
                all_records.extend(month_records)
            except (json.JSONDecodeError, OSError):
                pass
    all_records.sort(key=lambda r: (r.get("date", ""), r.get("type", "")))
    return all_records


__all__ = ["log_entry", "delete_entry", "list_entries"]
