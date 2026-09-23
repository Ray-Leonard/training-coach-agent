#!/usr/bin/env python3
"""Validated storage for explicitly confirmed actual workout sessions."""

from __future__ import annotations

import argparse
import copy
import json
import math
import os
import tempfile
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


REPO_ROOT = Path(__file__).resolve().parents[3]
POUNDS_TO_KG = 0.45359237


def repo_root(root: Optional[Path] = None) -> Path:
    return Path(root).expanduser().resolve() if root is not None else REPO_ROOT


def training_root(root: Optional[Path] = None) -> Path:
    return repo_root(root) / "data" / "training"


def parse_date(value: Any, field: str = "date") -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field} must use YYYY-MM-DD format")
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError as exc:
        raise ValueError(f"{field} must use YYYY-MM-DD format") from exc


def validate_timezone(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("timezone must be a non-empty IANA timezone")
    try:
        ZoneInfo(value)
    except ZoneInfoNotFoundError as exc:
        raise ValueError(f"Unknown IANA timezone: {value}") from exc
    return value


def _profile_timezone(root: Optional[Path] = None) -> str:
    path = repo_root(root) / "data" / "user" / "profile.json"
    if not path.is_file():
        raise FileNotFoundError(f"Profile not found: {path}")
    try:
        profile = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Profile JSON is corrupted: {path}") from exc
    if not isinstance(profile, dict):
        raise ValueError("profile.json must contain a JSON object")
    return validate_timezone(profile.get("timezone"))


def _finite_number(
    value: Any,
    field: str,
    *,
    minimum: float = 0.0,
    maximum: Optional[float] = None,
) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{field} must be numeric")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be numeric") from exc
    if not math.isfinite(number) or number < minimum:
        raise ValueError(f"{field} must be finite and >= {minimum}")
    if maximum is not None and number > maximum:
        raise ValueError(f"{field} must be <= {maximum}")
    return number


def _positive_integer(value: Any, field: str) -> int:
    number = _finite_number(value, field, minimum=1.0)
    if not number.is_integer():
        raise ValueError(f"{field} must be a positive integer")
    return int(number)


def _aware_timestamp(value: Any, field: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError(f"{field} must be an ISO-8601 timestamp")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{field} must include a UTC offset")
    return parsed


def session_path(date_str: str, *, root: Optional[Path] = None) -> Path:
    return training_root(root) / f"{parse_date(date_str)}.json"


def _normalize_set(raw_set: Any, exercise_index: int, set_index: int) -> Dict[str, Any]:
    field = f"exercises[{exercise_index}].sets[{set_index}]"
    if not isinstance(raw_set, dict):
        raise ValueError(f"{field} must be a JSON object")
    has_kg = "weight_kg" in raw_set
    has_lbs = "weight_lbs" in raw_set
    if has_kg == has_lbs:
        raise ValueError(f"{field} requires exactly one of weight_kg or weight_lbs")
    if has_kg:
        weight_kg = _finite_number(raw_set["weight_kg"], f"{field}.weight_kg")
    else:
        pounds = _finite_number(raw_set["weight_lbs"], f"{field}.weight_lbs")
        weight_kg = pounds * POUNDS_TO_KG
    normalized: Dict[str, Any] = {
        "reps": _positive_integer(raw_set.get("reps"), f"{field}.reps"),
        "weight_kg": round(weight_kg, 3),
        "notes": raw_set.get("notes", ""),
    }
    if not isinstance(normalized["notes"], str):
        raise ValueError(f"{field}.notes must be a string")
    if raw_set.get("rpe") is not None:
        normalized["rpe"] = round(
            _finite_number(raw_set["rpe"], f"{field}.rpe", minimum=1.0, maximum=10.0),
            2,
        )
    if raw_set.get("rir") is not None:
        normalized["rir"] = round(
            _finite_number(raw_set["rir"], f"{field}.rir", minimum=0.0, maximum=10.0),
            2,
        )
    return normalized


def _normalize_exercise(raw: Any, index: int) -> Dict[str, Any]:
    field = f"exercises[{index}]"
    if not isinstance(raw, dict):
        raise ValueError(f"{field} must be a JSON object")
    name = raw.get("name")
    if not isinstance(name, str) or not name.strip():
        raise ValueError(f"{field}.name must be a non-empty string")
    muscle_groups = raw.get("muscle_groups")
    if not isinstance(muscle_groups, list) or not muscle_groups:
        raise ValueError(f"{field}.muscle_groups must be a non-empty list")
    if any(not isinstance(item, str) or not item.strip() for item in muscle_groups):
        raise ValueError(f"{field}.muscle_groups entries must be non-empty strings")
    sets = raw.get("sets")
    if not isinstance(sets, list) or not sets:
        raise ValueError(f"{field}.sets must be a non-empty list")
    return {
        "name": name.strip(),
        "muscle_groups": [item.strip() for item in muscle_groups],
        "sets": [_normalize_set(item, index, set_index) for set_index, item in enumerate(sets)],
    }


def normalize_session(
    payload: Dict[str, Any],
    *,
    confirmation_source: str,
    confirmed_at: str,
    profile_timezone: str,
) -> Dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("workout session must be a JSON object")
    date_str = parse_date(payload.get("date"))
    timezone = validate_timezone(payload.get("timezone", profile_timezone))
    if timezone != profile_timezone:
        raise ValueError("session timezone must match profile.timezone")
    title = payload.get("title")
    source = payload.get("source")
    if not isinstance(title, str) or not title.strip():
        raise ValueError("title must be a non-empty string")
    if not isinstance(source, str) or not source.strip():
        raise ValueError("source must be a non-empty string")
    exercises = payload.get("exercises")
    if not isinstance(exercises, list) or not exercises:
        raise ValueError("exercises must be a non-empty list")
    normalized: Dict[str, Any] = {
        "schema_version": "1.0",
        "date": date_str,
        "timezone": timezone,
        "title": title.strip(),
        "source": source.strip(),
        "confirmation": {
            "confirmed": True,
            "source": confirmation_source,
            "confirmed_at": confirmed_at,
        },
        "start_time": payload.get("start_time"),
        "end_time": payload.get("end_time"),
        "exercises": [
            _normalize_exercise(exercise, index)
            for index, exercise in enumerate(exercises)
        ],
    }
    return validate_session(normalized, expected_date=date_str)


def validate_session(
    session: Dict[str, Any],
    *,
    expected_date: Optional[str] = None,
    expected_timezone: Optional[str] = None,
) -> Dict[str, Any]:
    if not isinstance(session, dict):
        raise ValueError("workout session must be a JSON object")
    if session.get("schema_version") != "1.0":
        raise ValueError("schema_version must be '1.0'")
    date_str = parse_date(session.get("date"))
    if expected_date is not None and date_str != parse_date(expected_date):
        raise ValueError("workout session date does not match its filename")
    timezone = validate_timezone(session.get("timezone"))
    if expected_timezone is not None and timezone != expected_timezone:
        raise ValueError("session timezone does not match profile.timezone")
    for field in ("title", "source"):
        if not isinstance(session.get(field), str) or not session[field].strip():
            raise ValueError(f"{field} must be a non-empty string")
    confirmation = session.get("confirmation")
    if not isinstance(confirmation, dict):
        raise ValueError("confirmation must be a JSON object")
    if confirmation.get("confirmed") is not True:
        raise ValueError("only explicitly confirmed workout sessions are actual records")
    if not isinstance(confirmation.get("source"), str) or not confirmation["source"].strip():
        raise ValueError("confirmation.source must be a non-empty string")
    expected_confirmation_source = (
        "xunji_api" if session["source"] == "xunji_api" else "user"
    )
    if confirmation["source"] != expected_confirmation_source:
        raise ValueError(
            "confirmation source must match the workout record source semantics"
        )
    _aware_timestamp(confirmation.get("confirmed_at"), "confirmation.confirmed_at")

    start = session.get("start_time")
    end = session.get("end_time")
    parsed_start = _aware_timestamp(start, "start_time") if start is not None else None
    parsed_end = _aware_timestamp(end, "end_time") if end is not None else None
    if parsed_start is not None:
        local_start = parsed_start.astimezone(ZoneInfo(timezone))
        if local_start.date().isoformat() != date_str:
            raise ValueError("start_time must fall on the session date in its timezone")
    if parsed_start is not None and parsed_end is not None and parsed_end < parsed_start:
        raise ValueError("end_time cannot be earlier than start_time")

    exercises = session.get("exercises")
    if not isinstance(exercises, list) or not exercises:
        raise ValueError("exercises must be a non-empty list")
    session["exercises"] = [
        _normalize_exercise(exercise, index)
        for index, exercise in enumerate(exercises)
    ]
    return session


def _atomic_write_json(path: Path, payload: Any) -> Path:
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


def create_session(
    payload: Dict[str, Any],
    *,
    confirmed: bool = False,
    root: Optional[Path] = None,
    force: bool = False,
) -> Path:
    profile_tz = _profile_timezone(root)
    source = payload.get("source") if isinstance(payload, dict) else None
    api_confirmed = source == "xunji_api"
    if not confirmed and not api_confirmed:
        raise ValueError("manual workout records require explicit confirmation")
    confirmation_source = "xunji_api" if api_confirmed else "user"
    confirmed_at = datetime.now(ZoneInfo(profile_tz)).isoformat(timespec="seconds")
    normalized = normalize_session(
        copy.deepcopy(payload),
        confirmation_source=confirmation_source,
        confirmed_at=confirmed_at,
        profile_timezone=profile_tz,
    )
    destination = session_path(normalized["date"], root=root)
    if destination.exists():
        if not force:
            raise FileExistsError(
                f"workout session already exists: {destination}; use --force to replace it"
            )
        load_session(normalized["date"], root=root)
    return _atomic_write_json(destination, normalized)


def load_session(date_str: str, *, root: Optional[Path] = None) -> Dict[str, Any]:
    normalized_date = parse_date(date_str)
    path = session_path(normalized_date, root=root)
    if not path.is_file():
        raise FileNotFoundError(f"Workout session not found: {path}")
    try:
        session = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Workout session JSON is corrupted: {path}") from exc
    if not isinstance(session, dict):
        raise ValueError(f"Workout session must be a JSON object: {path}")
    return validate_session(
        session,
        expected_date=normalized_date,
        expected_timezone=_profile_timezone(root),
    )


def list_sessions(*, root: Optional[Path] = None) -> List[str]:
    directory = training_root(root)
    if not directory.is_dir():
        return []
    dates: List[str] = []
    for path in sorted(directory.glob("????-??-??.json")):
        session = load_session(path.stem, root=root)
        dates.append(session["date"])
    return dates


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create, list, and load confirmed actual workout sessions"
    )
    parser.add_argument("--root", type=Path, help="repository root (testing/advanced use)")
    sub = parser.add_subparsers(dest="command", required=True)
    create = sub.add_parser("create")
    create.add_argument("--input", type=Path, required=True, help="session JSON input")
    create.add_argument("--confirmed", action="store_true")
    create.add_argument("--force", action="store_true")
    load = sub.add_parser("load")
    load.add_argument("--date", required=True)
    sub.add_parser("list")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "create":
            try:
                payload = json.loads(args.input.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Input JSON is corrupted: {args.input}") from exc
            path = create_session(
                payload,
                confirmed=args.confirmed,
                root=args.root,
                force=args.force,
            )
            print(json.dumps({"saved": str(path)}, ensure_ascii=False, indent=2))
        elif args.command == "load":
            print(
                json.dumps(
                    load_session(args.date, root=args.root),
                    ensure_ascii=False,
                    indent=2,
                )
            )
        else:
            print(json.dumps(list_sessions(root=args.root), ensure_ascii=False, indent=2))
        return 0
    except (FileNotFoundError, ValueError, OSError) as exc:
        print(f"error: {exc}", flush=True)
        return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
