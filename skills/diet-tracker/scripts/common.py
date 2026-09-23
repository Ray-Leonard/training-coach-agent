#!/usr/bin/env python3
"""Shared safe JSON, date, timezone, and validation helpers for Diet Tracker."""

from __future__ import annotations

import json
import math
import os
import tempfile
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, Optional
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


REPO_ROOT = Path(__file__).resolve().parents[3]


def repo_root(root: Optional[Path] = None) -> Path:
    """Return an explicitly supplied repository root or this skill's repo root."""
    return Path(root).expanduser().resolve() if root is not None else REPO_ROOT


def profile_path(root: Optional[Path] = None) -> Path:
    return repo_root(root) / "data" / "user" / "profile.json"


def load_profile(root: Optional[Path] = None) -> Dict[str, Any]:
    path = profile_path(root)
    if not path.is_file():
        raise FileNotFoundError(f"Profile not found: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Profile JSON is corrupted: {path}") from exc
    if not isinstance(payload, dict) or not payload:
        raise ValueError(f"Profile is empty or invalid: {path}")
    return payload


def profile_timezone(profile: Dict[str, Any]) -> str:
    timezone = profile.get("timezone")
    if not isinstance(timezone, str) or not timezone.strip():
        raise ValueError("profile.timezone must be a non-empty IANA timezone")
    try:
        ZoneInfo(timezone)
    except ZoneInfoNotFoundError as exc:
        raise ValueError(f"Unknown IANA timezone: {timezone}") from exc
    return timezone


def now_in_profile_timezone(profile: Dict[str, Any]) -> datetime:
    return datetime.now(ZoneInfo(profile_timezone(profile)))


def today_in_profile_timezone(profile: Dict[str, Any]) -> date:
    return now_in_profile_timezone(profile).date()


def parse_iso_date(value: str, field: str = "date") -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field} must use YYYY-MM-DD format")
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError as exc:
        raise ValueError(f"{field} must use YYYY-MM-DD format") from exc


def iso_timestamp(profile: Dict[str, Any]) -> str:
    return now_in_profile_timezone(profile).isoformat(timespec="seconds")


def finite_number(value: Any, field: str, *, minimum: float = 0.0) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{field} must be numeric")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be numeric") from exc
    if not math.isfinite(number) or number < minimum:
        raise ValueError(f"{field} must be finite and >= {minimum}")
    return number


def atomic_write_json(path: Path, payload: Any) -> Path:
    """Write JSON through a same-directory temporary file and replace atomically."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent)
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(path)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise
    return path


def load_json_object(path: Path) -> Dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(path)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"JSON is corrupted: {path}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"JSON object expected: {path}")
    return payload


def optional_nonnegative(value: Any, field: str) -> Optional[float]:
    if value is None:
        return None
    return finite_number(value, field, minimum=0.0)
