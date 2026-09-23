#!/usr/bin/env python3
"""Generic, profile-driven training-plan generator."""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import tempfile
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


REPO_ROOT = Path(__file__).resolve().parents[3]
PLAN_DIR_NAME = "training-plans"
VALID_SPLITS = {"upper-lower", "full-body", "ppl"}
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*$")


WORKOUTS: Dict[str, List[Dict[str, Any]]] = {
    "upper-lower": [
        {
            "name": "Upper A",
            "focus": "horizontal push/pull and shoulders",
            "exercises": [
                {"exercise": "Bench press or machine press", "sets": 3, "reps": "6-10", "rest_seconds": 120},
                {"exercise": "Chest-supported row", "sets": 3, "reps": "8-12", "rest_seconds": 120},
                {"exercise": "Overhead press", "sets": 3, "reps": "8-10", "rest_seconds": 90},
                {"exercise": "Lat pulldown", "sets": 3, "reps": "8-12", "rest_seconds": 90},
                {"exercise": "Cable curl", "sets": 2, "reps": "10-15", "rest_seconds": 60},
                {"exercise": "Cable triceps pressdown", "sets": 2, "reps": "10-15", "rest_seconds": 60},
            ],
        },
        {
            "name": "Lower A",
            "focus": "squat pattern and trunk stability",
            "exercises": [
                {"exercise": "Squat or leg press", "sets": 3, "reps": "6-10", "rest_seconds": 150},
                {"exercise": "Romanian deadlift", "sets": 3, "reps": "8-12", "rest_seconds": 120},
                {"exercise": "Walking lunge", "sets": 2, "reps": "10-12/side", "rest_seconds": 90},
                {"exercise": "Leg curl", "sets": 2, "reps": "10-15", "rest_seconds": 75},
                {"exercise": "Calf raise", "sets": 3, "reps": "10-15", "rest_seconds": 60},
                {"exercise": "Plank", "sets": 3, "reps": "30-60 sec", "rest_seconds": 60},
            ],
        },
        {
            "name": "Upper B",
            "focus": "vertical push/pull and upper-back volume",
            "exercises": [
                {"exercise": "Incline dumbbell press", "sets": 3, "reps": "8-12", "rest_seconds": 120},
                {"exercise": "Pull-up or assisted pull-up", "sets": 3, "reps": "6-10", "rest_seconds": 120},
                {"exercise": "Seated cable row", "sets": 3, "reps": "8-12", "rest_seconds": 90},
                {"exercise": "Dumbbell lateral raise", "sets": 3, "reps": "12-20", "rest_seconds": 60},
                {"exercise": "Incline curl", "sets": 2, "reps": "10-15", "rest_seconds": 60},
                {"exercise": "Overhead triceps extension", "sets": 2, "reps": "10-15", "rest_seconds": 60},
            ],
        },
        {
            "name": "Lower B",
            "focus": "hinge pattern and unilateral leg work",
            "exercises": [
                {"exercise": "Trap-bar deadlift or deadlift variation", "sets": 3, "reps": "5-8", "rest_seconds": 150},
                {"exercise": "Front squat or goblet squat", "sets": 3, "reps": "8-12", "rest_seconds": 120},
                {"exercise": "Hip thrust", "sets": 3, "reps": "8-12", "rest_seconds": 90},
                {"exercise": "Bulgarian split squat", "sets": 2, "reps": "8-12/side", "rest_seconds": 90},
                {"exercise": "Leg extension", "sets": 2, "reps": "12-15", "rest_seconds": 60},
                {"exercise": "Dead bug", "sets": 3, "reps": "8-12/side", "rest_seconds": 60},
            ],
        },
    ],
    "full-body": [
        {
            "name": "Full Body A",
            "focus": "squat, press, row",
            "exercises": [
                {"exercise": "Squat or leg press", "sets": 3, "reps": "6-10", "rest_seconds": 150},
                {"exercise": "Bench press or machine press", "sets": 3, "reps": "6-10", "rest_seconds": 120},
                {"exercise": "Chest-supported row", "sets": 3, "reps": "8-12", "rest_seconds": 120},
                {"exercise": "Romanian deadlift", "sets": 2, "reps": "8-12", "rest_seconds": 120},
                {"exercise": "Plank", "sets": 3, "reps": "30-60 sec", "rest_seconds": 60},
            ],
        },
        {
            "name": "Full Body B",
            "focus": "hinge, overhead press, vertical pull",
            "exercises": [
                {"exercise": "Trap-bar deadlift or deadlift variation", "sets": 3, "reps": "5-8", "rest_seconds": 150},
                {"exercise": "Overhead press", "sets": 3, "reps": "6-10", "rest_seconds": 120},
                {"exercise": "Lat pulldown or assisted pull-up", "sets": 3, "reps": "8-12", "rest_seconds": 120},
                {"exercise": "Walking lunge", "sets": 2, "reps": "10-12/side", "rest_seconds": 90},
                {"exercise": "Dead bug", "sets": 3, "reps": "8-12/side", "rest_seconds": 60},
            ],
        },
    ],
    "ppl": [
        {
            "name": "Push",
            "focus": "chest, shoulders, triceps",
            "exercises": [
                {"exercise": "Bench press or machine press", "sets": 3, "reps": "6-10", "rest_seconds": 120},
                {"exercise": "Overhead press", "sets": 3, "reps": "8-10", "rest_seconds": 90},
                {"exercise": "Incline dumbbell press", "sets": 3, "reps": "8-12", "rest_seconds": 90},
                {"exercise": "Dumbbell lateral raise", "sets": 3, "reps": "12-20", "rest_seconds": 60},
                {"exercise": "Cable triceps pressdown", "sets": 3, "reps": "10-15", "rest_seconds": 60},
            ],
        },
        {
            "name": "Pull",
            "focus": "back, rear delts, biceps",
            "exercises": [
                {"exercise": "Pull-up or lat pulldown", "sets": 3, "reps": "6-10", "rest_seconds": 120},
                {"exercise": "Chest-supported row", "sets": 3, "reps": "8-12", "rest_seconds": 120},
                {"exercise": "Seated cable row", "sets": 3, "reps": "8-12", "rest_seconds": 90},
                {"exercise": "Reverse fly", "sets": 3, "reps": "12-20", "rest_seconds": 60},
                {"exercise": "Cable curl", "sets": 3, "reps": "10-15", "rest_seconds": 60},
            ],
        },
        {
            "name": "Legs",
            "focus": "quads, hamstrings, glutes, calves",
            "exercises": [
                {"exercise": "Squat or leg press", "sets": 3, "reps": "6-10", "rest_seconds": 150},
                {"exercise": "Romanian deadlift", "sets": 3, "reps": "8-12", "rest_seconds": 120},
                {"exercise": "Walking lunge", "sets": 2, "reps": "10-12/side", "rest_seconds": 90},
                {"exercise": "Leg curl", "sets": 3, "reps": "10-15", "rest_seconds": 75},
                {"exercise": "Calf raise", "sets": 3, "reps": "10-15", "rest_seconds": 60},
            ],
        },
        {
            "name": "Upper",
            "focus": "moderate upper-body volume",
            "exercises": [
                {"exercise": "Incline dumbbell press", "sets": 3, "reps": "8-12", "rest_seconds": 90},
                {"exercise": "Seated cable row", "sets": 3, "reps": "8-12", "rest_seconds": 90},
                {"exercise": "Lat pulldown", "sets": 3, "reps": "8-12", "rest_seconds": 90},
                {"exercise": "Dumbbell lateral raise", "sets": 2, "reps": "12-20", "rest_seconds": 60},
                {"exercise": "Curl and triceps superset", "sets": 2, "reps": "10-15", "rest_seconds": 60},
            ],
        },
    ],
}


def repo_root(root: Optional[Path] = None) -> Path:
    return Path(root).expanduser().resolve() if root is not None else REPO_ROOT


def load_profile(root: Optional[Path] = None) -> Dict[str, Any]:
    path = repo_root(root) / "data" / "user" / "profile.json"
    if not path.is_file():
        raise FileNotFoundError(f"Profile not found: {path}")
    try:
        profile = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Profile JSON is corrupted: {path}") from exc
    if not isinstance(profile, dict) or not profile:
        raise ValueError("profile.json must contain a non-empty object")
    return profile


def timezone_name(profile: Dict[str, Any]) -> str:
    value = profile.get("timezone")
    if not isinstance(value, str) or not value.strip():
        raise ValueError("profile.timezone must be a non-empty IANA timezone")
    try:
        ZoneInfo(value)
    except ZoneInfoNotFoundError as exc:
        raise ValueError(f"Unknown IANA timezone: {value}") from exc
    return value


def parse_date(value: str, field: str = "date") -> date:
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must use YYYY-MM-DD format") from exc


def today(profile: Dict[str, Any]) -> date:
    return datetime.now(ZoneInfo(timezone_name(profile))).date()


def numeric_profile(profile: Dict[str, Any], field: str, minimum: float) -> float:
    raw_value = profile.get(field)
    if isinstance(raw_value, bool) or raw_value is None:
        raise ValueError(f"profile.{field} must be numeric")
    try:
        value = float(raw_value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"profile.{field} must be numeric") from exc
    if not math.isfinite(value) or value < minimum:
        raise ValueError(f"profile.{field} must be >= {minimum}")
    return value


def integer_profile(profile: Dict[str, Any], field: str, minimum: int, maximum: int) -> int:
    value = numeric_profile(profile, field, minimum)
    if not value.is_integer() or value > maximum:
        raise ValueError(f"profile.{field} must be an integer from {minimum} to {maximum}")
    return int(value)


def recommended_split(training_days: int) -> str:
    if training_days <= 2:
        return "full-body"
    if training_days == 3:
        return "ppl"
    return "upper-lower"


def spread_positions(count: int) -> List[int]:
    if count <= 0:
        return []
    if count > 7:
        raise ValueError("weekly training/cardio days cannot exceed 7")
    positions: List[int] = []
    for index in range(count):
        position = (index * 7) // count
        if position not in positions:
            positions.append(position)
    return positions


def atomic_write_json(path: Path, payload: Any) -> Path:
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


def _copy_session(session: Dict[str, Any]) -> Dict[str, Any]:
    return json.loads(json.dumps(session, ensure_ascii=False))


def generate_plan(
    *,
    start_date: Optional[str] = None,
    days: int = 10,
    split: Optional[str] = None,
    root: Optional[Path] = None,
) -> Dict[str, Any]:
    if not isinstance(days, int) or isinstance(days, bool) or not 1 <= days <= 31:
        raise ValueError("days must be an integer between 1 and 31")
    profile = load_profile(root)
    start = parse_date(start_date, "start_date") if start_date else today(profile)
    strength_days = integer_profile(profile, "training_days_per_week", 0, 7)
    cardio_days = integer_profile(profile, "cardio_days_per_week", 0, 7)
    cardio_minutes = numeric_profile(profile, "cardio_minutes_per_session", 0)

    chosen_split = split or recommended_split(strength_days)
    if chosen_split not in VALID_SPLITS:
        raise ValueError(f"split must be one of: {', '.join(sorted(VALID_SPLITS))}")
    recommendation = split is None
    sessions = WORKOUTS[chosen_split]
    strength_positions = set(spread_positions(strength_days))
    cardio_positions = set(spread_positions(cardio_days))
    schedule: List[Dict[str, Any]] = []
    strength_session_index = 0
    for offset in range(days):
        current = start + timedelta(days=offset)
        weekly_position = offset % 7
        strength = None
        if weekly_position in strength_positions and strength_days:
            strength = _copy_session(
                sessions[strength_session_index % len(sessions)]
            )
            strength_session_index += 1
        cardio = None
        if weekly_position in cardio_positions and cardio_days:
            cardio = {
                "planned": True,
                "minutes": round(cardio_minutes, 2),
                "intensity": "easy-to-moderate, conversational pace",
            }
        schedule.append(
            {
                "date": current.isoformat(),
                "status": "planned",
                "user_confirmation_required": True,
                "strength": strength,
                "cardio": cardio,
                "recovery": None if strength or cardio else "rest, mobility, or easy walk as desired",
            }
        )
    tz = timezone_name(profile)
    return {
        "schema_version": "1.0",
        "id": f"{start.isoformat()}-{days}-day-plan",
        "title": f"{days}-day training plan",
        "plan_type": "standard",
        "status": "proposed",
        "confirmation": {
            "confirmed": False,
            "source": None,
            "confirmed_at": None,
        },
        "generated_at": datetime.now(ZoneInfo(tz)).isoformat(timespec="seconds"),
        "timezone": tz,
        "start_date": start.isoformat(),
        "end_date": (start + timedelta(days=days - 1)).isoformat(),
        "days": days,
        "split": {
            "name": chosen_split,
            "recommended_by_generator": recommendation,
            "rationale": (
                "Suggested from the profile's weekly strength frequency; discuss and confirm with the user before treating it as the actual plan."
                if recommendation
                else "Requested split; discuss and confirm with the user before treating it as the actual plan."
            ),
        },
        "source_profile": {
            "goal": profile.get("goal"),
            "target_weight_kg": profile.get("target_weight_kg"),
            "training_days_per_week": strength_days,
            "cardio_days_per_week": cardio_days,
            "cardio_minutes_per_session": cardio_minutes,
        },
        "safety_notes": [
            "Keep 1-3 repetitions in reserve; do not force painful movements.",
            "Use the listed alternatives when equipment or experience differs.",
            "This is a proposed schedule, not a record that training occurred.",
        ],
        "daily_schedule": schedule,
    }


def output_path(
    plan: Dict[str, Any], *, root: Optional[Path] = None, output: Optional[str] = None
) -> Path:
    root_path = repo_root(root)
    directory = (root_path / "data" / PLAN_DIR_NAME).resolve()
    if output:
        candidate = Path(output).expanduser()
        if not candidate.is_absolute():
            candidate = root_path / candidate
        candidate = candidate.resolve()
        if not candidate.is_relative_to(directory):
            raise ValueError("output must stay inside data/training-plans")
        if candidate.suffix != ".json":
            candidate = candidate.with_suffix(".json")
        return candidate
    return directory / f"{plan['start_date']}-{plan['days']}-day-plan.json"


def save_plan(
    plan: Dict[str, Any], *, root: Optional[Path] = None, output: Optional[str] = None, force: bool = False
) -> Path:
    destination = output_path(plan, root=root, output=output)
    if destination.exists() and not force:
        raise FileExistsError(f"plan already exists: {destination}; use --force to replace it")
    return atomic_write_json(destination, plan)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate a generic profile-driven training plan")
    parser.add_argument("--root", type=Path, help="repository root (testing/advanced use)")
    sub = parser.add_subparsers(dest="command", required=True)
    generate = sub.add_parser("generate")
    generate.add_argument("--start")
    generate.add_argument("--days", type=int, default=10)
    generate.add_argument("--split", choices=sorted(VALID_SPLITS))
    generate.add_argument("--output")
    generate.add_argument("--force", action="store_true")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        plan = generate_plan(
            start_date=args.start,
            days=args.days,
            split=args.split,
            root=args.root,
        )
        path = save_plan(plan, root=args.root, output=args.output, force=args.force)
        print(json.dumps({"saved": str(path), "plan": plan}, ensure_ascii=False, indent=2))
        return 0
    except (FileNotFoundError, ValueError, OSError) as exc:
        print(f"error: {exc}", flush=True)
        return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
