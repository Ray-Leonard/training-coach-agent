#!/usr/bin/env python3
"""Validated manual body-log CRUD with monthly atomic JSON files."""

from __future__ import annotations

import json
import math
import tempfile
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


REPO_ROOT = Path(__file__).resolve().parents[3]
BODY_LOG_DIR = REPO_ROOT / "data" / "user" / "body-log"

TYPE_UNITS = {
    "weight": "kg",
    "bodyfat": "%",
    "neck": "cm",
    "chest": "cm",
    "weist": "cm",
    "shoulder": "cm",
    "bot": "cm",
    "arm_left": "cm",
    "arm_right": "cm",
    "forearm_left": "cm",
    "forearm_right": "cm",
    "leg_left": "cm",
    "leg_right": "cm",
    "cav_left": "cm",
    "cav_right": "cm",
}


def _today_in_tz(tz_name: str) -> date:
    try:
        return datetime.now(ZoneInfo(tz_name)).date()
    except ZoneInfoNotFoundError as exc:
        raise ValueError(f"Unknown IANA timezone: {tz_name}") from exc


def _read_profile_timezone() -> str:
    profile_path = REPO_ROOT / "data" / "user" / "profile.json"
    if not profile_path.is_file():
        return "UTC"
    try:
        raw = json.loads(profile_path.read_text(encoding="utf-8"))
        timezone = raw.get("timezone")
        if isinstance(timezone, str) and timezone.strip():
            return timezone
    except (OSError, json.JSONDecodeError):
        pass
    return "UTC"


def _parse_date(value: Any, field: str = "date") -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field} must use YYYY-MM-DD format")
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError as exc:
        raise ValueError(f"{field} must use YYYY-MM-DD format") from exc


def _validate_number(value: Any, field: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{field} must be numeric")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be numeric") from exc
    if not math.isfinite(number) or number <= 0:
        raise ValueError(f"{field} must be finite and positive")
    return number


def validate_entry(record: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(record, dict):
        raise ValueError("body-log entry must be a JSON object")
    entry_date = _parse_date(record.get("date") or record.get("datestr"))
    entry_type = record.get("type")
    if entry_type not in TYPE_UNITS:
        raise ValueError(f"unsupported body-data type: {entry_type}")
    unit = record.get("unit")
    expected_unit = TYPE_UNITS[entry_type]
    if unit != expected_unit:
        raise ValueError(f"{entry_type} requires unit {expected_unit!r}")
    value = _validate_number(record.get("value"), "value")
    if entry_type == "bodyfat" and value > 100:
        raise ValueError("bodyfat must be between 0 and 100 percent")
    if entry_type != "bodyfat" and value > 1000:
        raise ValueError("body measurement is outside the supported range")
    source = record.get("source") or "manual"
    if not isinstance(source, str) or not source.strip():
        raise ValueError("source must be a non-empty string")
    xunji_id = record.get("xunji_id")
    return {
        "date": entry_date,
        "type": entry_type,
        "value": round(value, 4),
        "unit": unit,
        "source": source.strip(),
        "xunji_id": xunji_id,
    }


def _month_from_date(date_str: str) -> str:
    normalized = _parse_date(date_str)
    return normalized[:7]


def _validate_month(month: str) -> str:
    if not isinstance(month, str):
        raise ValueError("month must use YYYY-MM format")
    try:
        return date.fromisoformat(f"{month}-01").strftime("%Y-%m")
    except ValueError as exc:
        raise ValueError("month must use YYYY-MM format") from exc


def _load_month(month: str) -> List[Dict[str, Any]]:
    normalized_month = _validate_month(month)
    month_path = BODY_LOG_DIR / f"{normalized_month}.json"
    if not month_path.is_file():
        return []
    try:
        payload = json.loads(month_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Body-log file is corrupted: {month_path}") from exc
    if not isinstance(payload, list):
        raise ValueError(f"Body-log file must contain a JSON array: {month_path}")
    records = [validate_entry(record) for record in payload]
    if any(record["date"][:7] != normalized_month for record in records):
        raise ValueError(f"Body-log file contains a record from another month: {month_path}")
    return records


def _save_month(records: List[Dict[str, Any]], month: str) -> Path:
    normalized_month = _validate_month(month)
    canonical = [validate_entry(record) for record in records]
    if any(record["date"][:7] != normalized_month for record in canonical):
        raise ValueError("cannot write a record to the wrong monthly file")
    canonical.sort(key=lambda record: (record["date"], record["type"]), reverse=True)
    BODY_LOG_DIR.mkdir(parents=True, exist_ok=True)
    destination = BODY_LOG_DIR / f"{normalized_month}.json"
    fd, temporary_name = tempfile.mkstemp(
        prefix=f".{destination.name}.", suffix=".tmp", dir=str(BODY_LOG_DIR)
    )
    temporary = Path(temporary_name)
    try:
        with open(fd, "w", encoding="utf-8", closefd=True) as handle:
            json.dump(canonical, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
        temporary.replace(destination)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise
    return destination


def log_entry(
    entry_type: str, value: float, unit: str, *, date_str: Optional[str] = None
) -> Path:
    """Add or replace a manual entry with the same (date, type)."""
    entry_date = _parse_date(date_str or _today_in_tz(_read_profile_timezone()).isoformat())
    entry = validate_entry(
        {
            "date": entry_date,
            "type": entry_type,
            "value": value,
            "unit": unit,
            "source": "manual",
            "xunji_id": None,
        }
    )
    month = entry_date[:7]
    records = _load_month(month)
    replaced = False
    for index, record in enumerate(records):
        if (
            record["date"] == entry_date
            and record["type"] == entry_type
            and record.get("source") == "manual"
        ):
            records[index] = entry
            replaced = True
            break
    if not replaced:
        records.append(entry)
    return _save_month(records, month)


def delete_entry(date_str: str, entry_type: str) -> int:
    entry_date = _parse_date(date_str)
    if entry_type not in TYPE_UNITS:
        raise ValueError(f"unsupported body-data type: {entry_type}")
    month = entry_date[:7]
    records = _load_month(month)
    kept = [
        record
        for record in records
        if not (
            record["date"] == entry_date
            and record["type"] == entry_type
            and record.get("source") == "manual"
        )
    ]
    deleted = len(records) - len(kept)
    if deleted:
        _save_month(kept, month)
    return deleted


def list_entries(
    month: Optional[str] = None,
    entry_type: Optional[str] = None,
) -> List[Dict[str, Any]]:
    if entry_type is not None and entry_type not in TYPE_UNITS:
        raise ValueError(f"unsupported body-data type: {entry_type}")
    if month:
        records = _load_month(month)
        return [r for r in records if entry_type is None or r["type"] == entry_type]
    all_records: List[Dict[str, Any]] = []
    if BODY_LOG_DIR.is_dir():
        for path in sorted(BODY_LOG_DIR.glob("????-??.json")):
            records = _load_month(path.stem)
            all_records.extend(
                record for record in records if entry_type is None or record["type"] == entry_type
            )
    all_records.sort(key=lambda record: (record["date"], record["type"]), reverse=True)
    return all_records


__all__ = ["TYPE_UNITS", "validate_entry", "log_entry", "delete_entry", "list_entries"]


if __name__ == "__main__":  # pragma: no cover
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Validated manual body-log CRUD")
    sub = parser.add_subparsers(dest="cmd", required=True)
    log = sub.add_parser("log")
    log.add_argument("type")
    log.add_argument("value", type=float)
    log.add_argument("unit")
    log.add_argument("date", nargs="?")
    delete = sub.add_parser("delete")
    delete.add_argument("date")
    delete.add_argument("type")
    listing = sub.add_parser("list")
    listing.add_argument("month", nargs="?")
    listing.add_argument("type", nargs="?")
    args = parser.parse_args()
    try:
        if args.cmd == "log":
            path = log_entry(args.type, args.value, args.unit, date_str=args.date)
            print(f"Logged {args.type} to {path}")
        elif args.cmd == "delete":
            print(f"Deleted {delete_entry(args.date, args.type)} entries")
        else:
            print(json.dumps(list_entries(args.month, args.type), ensure_ascii=False, indent=2))
    except (ValueError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2)
