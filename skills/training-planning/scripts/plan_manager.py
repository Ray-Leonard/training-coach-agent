#!/usr/bin/env python3
"""Validate, list, load, and explicitly confirm training-plan proposals."""

from __future__ import annotations

import argparse
import json
import math
import os
import tempfile
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


REPO_ROOT = Path(__file__).resolve().parents[3]
VALID_STATUSES = {"proposed", "confirmed"}
VALID_PLAN_TYPES = {"standard", "deload"}


def repo_root(root: Optional[Path] = None) -> Path:
    return Path(root).expanduser().resolve() if root is not None else REPO_ROOT


def plans_root(root: Optional[Path] = None) -> Path:
    return repo_root(root) / "data" / "training-plans"


def _parse_date(value: Any, field: str) -> date:
    if not isinstance(value, str):
        raise ValueError(f"{field} must use YYYY-MM-DD format")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field} must use YYYY-MM-DD format") from exc


def _timezone(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("timezone must be a non-empty IANA timezone")
    try:
        ZoneInfo(value)
    except ZoneInfoNotFoundError as exc:
        raise ValueError(f"Unknown IANA timezone: {value}") from exc
    return value


def _timestamp(value: Any, field: str, *, optional: bool = False) -> None:
    if value is None and optional:
        return
    if not isinstance(value, str):
        raise ValueError(f"{field} must be an ISO-8601 timestamp")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{field} must include a UTC offset")


def _positive_integer(value: Any, field: str) -> int:
    if isinstance(value, bool):
        raise ValueError(f"{field} must be a positive integer")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be a positive integer") from exc
    if not math.isfinite(number) or number < 1 or not number.is_integer():
        raise ValueError(f"{field} must be a positive integer")
    return int(number)


def _nonnegative_number(value: Any, field: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{field} must be numeric")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be numeric") from exc
    if not math.isfinite(number) or number < 0:
        raise ValueError(f"{field} must be finite and nonnegative")
    return number


def resolve_plan_path(name: str, *, root: Optional[Path] = None) -> Path:
    if not isinstance(name, str) or not name.strip():
        raise ValueError("plan filename must be a non-empty string")
    directory = plans_root(root).resolve()
    candidate = Path(name).expanduser()
    if not candidate.is_absolute():
        candidate = directory / candidate
    candidate = candidate.resolve()
    if not candidate.is_relative_to(directory):
        raise ValueError("plan path must stay inside data/training-plans")
    if candidate.suffix != ".json":
        candidate = candidate.with_suffix(".json")
    return candidate


def _validate_strength(strength: Any, day_index: int) -> None:
    if strength is None:
        return
    if not isinstance(strength, dict):
        raise ValueError(f"daily_schedule[{day_index}].strength must be an object or null")
    exercises = strength.get("exercises")
    if not isinstance(exercises, list) or not exercises:
        raise ValueError(f"daily_schedule[{day_index}].strength.exercises must be a non-empty list")
    for exercise_index, exercise in enumerate(exercises):
        field = f"daily_schedule[{day_index}].strength.exercises[{exercise_index}]"
        if not isinstance(exercise, dict):
            raise ValueError(f"{field} must be a JSON object")
        if not isinstance(exercise.get("exercise"), str) or not exercise["exercise"].strip():
            raise ValueError(f"{field}.exercise must be a non-empty string")
        _positive_integer(exercise.get("sets"), f"{field}.sets")


def validate_plan(plan: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(plan, dict):
        raise ValueError("training plan must be a JSON object")
    for field in ("id", "title"):
        if not isinstance(plan.get(field), str) or not plan[field].strip():
            raise ValueError(f"{field} must be a non-empty string")
    plan_type = plan.get("plan_type")
    if plan_type not in VALID_PLAN_TYPES:
        raise ValueError(f"plan_type must be one of: {', '.join(sorted(VALID_PLAN_TYPES))}")
    status = plan.get("status")
    if status not in VALID_STATUSES:
        raise ValueError(f"status must be one of: {', '.join(sorted(VALID_STATUSES))}")
    timezone = _timezone(plan.get("timezone"))
    _timestamp(plan.get("generated_at"), "generated_at")
    start = _parse_date(plan.get("start_date"), "start_date")
    end = _parse_date(plan.get("end_date"), "end_date")
    days = _positive_integer(plan.get("days"), "days")
    if end != start + timedelta(days=days - 1):
        raise ValueError("end_date must match start_date and days")

    confirmation = plan.get("confirmation")
    if not isinstance(confirmation, dict) or not isinstance(
        confirmation.get("confirmed"), bool
    ):
        raise ValueError("confirmation.confirmed must be boolean")
    if status == "proposed" and confirmation["confirmed"]:
        raise ValueError("a proposed plan cannot be confirmed")
    if status == "confirmed" and not confirmation["confirmed"]:
        raise ValueError("a confirmed plan requires confirmation metadata")
    if confirmation["confirmed"]:
        if not isinstance(confirmation.get("source"), str) or not confirmation["source"].strip():
            raise ValueError("confirmation.source must be a non-empty string")
        _timestamp(confirmation.get("confirmed_at"), "confirmation.confirmed_at")
    else:
        if confirmation.get("source") is not None or confirmation.get("confirmed_at") is not None:
            raise ValueError("unconfirmed proposals cannot carry confirmation metadata")

    split = plan.get("split")
    if not isinstance(split, dict) or not isinstance(split.get("name"), str) or not split["name"].strip():
        raise ValueError("split.name must be a non-empty string")
    schedule = plan.get("daily_schedule")
    if not isinstance(schedule, list) or len(schedule) != days:
        raise ValueError("daily_schedule length must equal days")
    for index, day_record in enumerate(schedule):
        field = f"daily_schedule[{index}]"
        if not isinstance(day_record, dict):
            raise ValueError(f"{field} must be a JSON object")
        expected_date = start + timedelta(days=index)
        if _parse_date(day_record.get("date"), f"{field}.date") != expected_date:
            raise ValueError(f"{field}.date must be sequential from start_date")
        if day_record.get("status") != "planned":
            raise ValueError(f"{field}.status must remain planned")
        if day_record.get("user_confirmation_required") is not True:
            raise ValueError(f"{field}.user_confirmation_required must be true")
        _validate_strength(day_record.get("strength"), index)
        cardio = day_record.get("cardio")
        if cardio is not None:
            if not isinstance(cardio, dict):
                raise ValueError(f"{field}.cardio must be an object or null")
            _nonnegative_number(cardio.get("minutes"), f"{field}.cardio.minutes")
    if plan_type == "deload":
        metadata = plan.get("deload")
        if not isinstance(metadata, dict):
            raise ValueError("deload metadata is required for a deload plan")
        reduction = _nonnegative_number(
            metadata.get("volume_reduction_percent"),
            "deload.volume_reduction_percent",
        )
        if not 40 <= reduction <= 50:
            raise ValueError("deload volume reduction must be between 40 and 50 percent")
        original_total = _positive_integer(
            metadata.get("original_total_sets"), "deload.original_total_sets"
        )
        deload_total = _positive_integer(
            metadata.get("deload_total_sets"), "deload.deload_total_sets"
        )
        if deload_total >= original_total:
            raise ValueError("deload total sets must be lower than original total sets")
        measured_reduction = round(
            (1 - deload_total / original_total) * 100, 2
        )
        if reduction != measured_reduction:
            raise ValueError("deload volume reduction must match its set totals")
    return plan


def load_plan(name: str, *, root: Optional[Path] = None) -> Dict[str, Any]:
    path = resolve_plan_path(name, root=root)
    if not path.is_file():
        raise FileNotFoundError(f"Training plan not found: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Training plan JSON is corrupted: {path}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"Training plan must be a JSON object: {path}")
    return validate_plan(payload)


def list_plans(*, root: Optional[Path] = None) -> List[str]:
    directory = plans_root(root)
    if not directory.is_dir():
        return []
    names: List[str] = []
    for path in sorted(directory.glob("*.json")):
        load_plan(path.name, root=root)
        names.append(path.name)
    return names


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


def save_managed_plan(
    plan: Dict[str, Any],
    name: str,
    *,
    root: Optional[Path] = None,
    force: bool = False,
) -> Path:
    validated = validate_plan(plan)
    destination = resolve_plan_path(name, root=root)
    if destination.exists():
        if not force:
            raise FileExistsError(
                f"training plan already exists: {destination}; use --force to replace it"
            )
        load_plan(destination.name, root=root)
    return _atomic_write_json(destination, validated)


def confirm_plan(
    name: str,
    *,
    confirmed: bool = False,
    root: Optional[Path] = None,
) -> Path:
    if not confirmed:
        raise ValueError("plan confirmation requires explicit user confirmation")
    path = resolve_plan_path(name, root=root)
    plan = load_plan(path.name, root=root)
    plan["status"] = "confirmed"
    plan["confirmation"] = {
        "confirmed": True,
        "source": "user",
        "confirmed_at": datetime.now(ZoneInfo(plan["timezone"])).isoformat(
            timespec="seconds"
        ),
    }
    return save_managed_plan(plan, path.name, root=root, force=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="List, load, and explicitly confirm training-plan proposals"
    )
    parser.add_argument("--root", type=Path, help="repository root (testing/advanced use)")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list")
    load = sub.add_parser("load")
    load.add_argument("--plan", required=True)
    confirm = sub.add_parser("confirm")
    confirm.add_argument("--plan", required=True)
    confirm.add_argument("--confirmed", action="store_true")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "list":
            result: Any = list_plans(root=args.root)
        elif args.command == "load":
            result = load_plan(args.plan, root=args.root)
        else:
            result = {"saved": str(confirm_plan(args.plan, confirmed=args.confirmed, root=args.root))}
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (FileNotFoundError, FileExistsError, ValueError, OSError) as exc:
        print(f"error: {exc}", flush=True)
        return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
