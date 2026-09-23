#!/usr/bin/env python3
"""Daily Diet Tracker storage and deterministic macro/deficit calculations."""

from __future__ import annotations

import argparse
import json
import math
import uuid
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional

try:  # Support both package imports and direct CLI execution.
    from .common import (
        atomic_write_json,
        finite_number,
        iso_timestamp,
        load_profile,
        load_json_object,
        parse_iso_date,
        profile_timezone,
        repo_root,
        today_in_profile_timezone,
    )
except ImportError:  # pragma: no cover - exercised by the CLI
    from common import (  # type: ignore
        atomic_write_json,
        finite_number,
        iso_timestamp,
        load_profile,
        load_json_object,
        parse_iso_date,
        profile_timezone,
        repo_root,
        today_in_profile_timezone,
    )


VALID_TRAINING_STATUSES = {"training", "rest"}
DAY_FIELDS = {
    "schema_version",
    "date",
    "timezone",
    "training_status",
    "training_status_confirmed",
    "training_confirmation_source",
    "meals",
    "actual_expenditure_kcal",
    "expenditure_source",
    "notes",
}
MEAL_REQUIRED_FIELDS = {
    "id",
    "meal_name",
    "food_name",
    "calories_kcal",
    "protein_g",
    "carbs_g",
    "fat_g",
}


def diet_root(root: Optional[Path] = None) -> Path:
    return repo_root(root) / "data" / "diet"


def day_path(date_str: str, root: Optional[Path] = None) -> Path:
    normalized = parse_iso_date(date_str)
    return diet_root(root) / f"{normalized}.json"


def _default_day(date_str: str, profile: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "schema_version": "1.0",
        "date": parse_iso_date(date_str),
        "timezone": profile_timezone(profile),
        "training_status": None,
        "training_status_confirmed": False,
        "training_confirmation_source": None,
        "meals": [],
        "actual_expenditure_kcal": None,
        "expenditure_source": None,
        "notes": "",
    }


def _validate_meal(meal: Dict[str, Any]) -> None:
    missing = MEAL_REQUIRED_FIELDS - set(meal)
    if missing:
        raise ValueError(f"meal is missing fields: {', '.join(sorted(missing))}")
    for field in ("meal_name", "food_name", "id"):
        if not isinstance(meal[field], str) or not meal[field].strip():
            raise ValueError(f"meal.{field} must be a non-empty string")
    for field in ("calories_kcal", "protein_g", "carbs_g", "fat_g"):
        value = finite_number(meal[field], f"meal.{field}")
        meal[field] = round(value, 2)
    if "logged_at" in meal and not isinstance(meal["logged_at"], str):
        raise ValueError("meal.logged_at must be a string when present")


def validate_day(day: Dict[str, Any], *, expected_date: Optional[str] = None) -> Dict[str, Any]:
    if not isinstance(day, dict):
        raise ValueError("daily diet record must be a JSON object")
    raw_date = day.get("date")
    if not isinstance(raw_date, str):
        raise ValueError("date must use YYYY-MM-DD format")
    date_str = parse_iso_date(raw_date, "date")
    if expected_date is not None and date_str != parse_iso_date(expected_date):
        raise ValueError("daily diet record date does not match its filename")
    timezone = day.get("timezone")
    if not isinstance(timezone, str) or not timezone.strip():
        raise ValueError("daily diet record timezone must be a non-empty string")
    profile_timezone({"timezone": timezone})
    status = day.get("training_status")
    confirmed = day.get("training_status_confirmed")
    if status is not None and status not in VALID_TRAINING_STATUSES:
        raise ValueError("training_status must be null, 'training', or 'rest'")
    if not isinstance(confirmed, bool):
        raise ValueError("training_status_confirmed must be boolean")
    if status is None and confirmed:
        raise ValueError("training_status cannot be confirmed while it is null")
    confirmation_source = day.get("training_confirmation_source")
    if confirmed and (
        not isinstance(confirmation_source, str) or not confirmation_source.strip()
    ):
        raise ValueError(
            "training_confirmation_source is required for a confirmed training status"
        )
    meals = day.get("meals")
    if not isinstance(meals, list):
        raise ValueError("meals must be a list")
    for meal in meals:
        if not isinstance(meal, dict):
            raise ValueError("each meal must be a JSON object")
        _validate_meal(meal)
    expenditure = day.get("actual_expenditure_kcal")
    if expenditure is not None:
        day["actual_expenditure_kcal"] = round(
            finite_number(expenditure, "actual_expenditure_kcal", minimum=0.01), 2
        )
        if not isinstance(day.get("expenditure_source"), str) or not day[
            "expenditure_source"
        ].strip():
            raise ValueError("expenditure_source is required with actual expenditure")
    return day


def load_day(
    date_str: str, *, root: Optional[Path] = None, profile: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    normalized = parse_iso_date(date_str)
    profile = profile or load_profile(root)
    path = day_path(normalized, root)
    if not path.is_file():
        return _default_day(normalized, profile)
    day = load_json_object(path)
    return validate_day(day, expected_date=normalized)


def save_day(day: Dict[str, Any], *, root: Optional[Path] = None) -> Path:
    payload = dict(day)
    payload.setdefault("schema_version", "1.0")
    validated = validate_day(payload, expected_date=payload.get("date"))
    return atomic_write_json(day_path(validated["date"], root), validated)


def _resolve_date(value: Optional[str], profile: Dict[str, Any]) -> str:
    return parse_iso_date(value) if value else today_in_profile_timezone(profile).isoformat()


def set_training_status(
    date_str: str,
    status: str,
    *,
    confirmed: bool = False,
    root: Optional[Path] = None,
) -> Path:
    if not confirmed:
        raise ValueError("training status requires explicit user confirmation")
    if status not in VALID_TRAINING_STATUSES:
        raise ValueError("status must be 'training' or 'rest'")
    profile = load_profile(root)
    day = load_day(date_str, root=root, profile=profile)
    day["training_status"] = status
    day["training_status_confirmed"] = True
    day["training_confirmation_source"] = "user"
    day["timezone"] = profile_timezone(profile)
    return save_day(day, root=root)


def add_meal(
    date_str: str,
    *,
    meal_name: str,
    food_name: str,
    calories_kcal: float,
    protein_g: float,
    carbs_g: float,
    fat_g: float,
    root: Optional[Path] = None,
) -> Dict[str, Any]:
    profile = load_profile(root)
    day = load_day(date_str, root=root, profile=profile)
    meal = {
        "id": f"meal-{uuid.uuid4().hex}",
        "meal_name": meal_name,
        "food_name": food_name,
        "calories_kcal": calories_kcal,
        "protein_g": protein_g,
        "carbs_g": carbs_g,
        "fat_g": fat_g,
        "logged_at": iso_timestamp(profile),
    }
    _validate_meal(meal)
    day["meals"].append(meal)
    save_day(day, root=root)
    return meal


def remove_meal(date_str: str, meal_id: str, *, root: Optional[Path] = None) -> bool:
    profile = load_profile(root)
    day = load_day(date_str, root=root, profile=profile)
    before = len(day["meals"])
    day["meals"] = [meal for meal in day["meals"] if meal["id"] != meal_id]
    if len(day["meals"]) == before:
        return False
    save_day(day, root=root)
    return True


def set_expenditure(
    date_str: str,
    expenditure_kcal: float,
    *,
    source: str = "manual",
    root: Optional[Path] = None,
) -> Path:
    profile = load_profile(root)
    day = load_day(date_str, root=root, profile=profile)
    day["actual_expenditure_kcal"] = round(
        finite_number(expenditure_kcal, "actual_expenditure_kcal", minimum=0.01), 2
    )
    if not isinstance(source, str) or not source.strip():
        raise ValueError("source must be a non-empty string")
    day["expenditure_source"] = source.strip()
    return save_day(day, root=root)


def summarize_day(date_str: str, *, root: Optional[Path] = None) -> Dict[str, Any]:
    profile = load_profile(root)
    day = load_day(date_str, root=root, profile=profile)
    totals = {
        "calories_kcal": round(sum(float(m["calories_kcal"]) for m in day["meals"]), 2),
        "protein_g": round(sum(float(m["protein_g"]) for m in day["meals"]), 2),
        "carbs_g": round(sum(float(m["carbs_g"]) for m in day["meals"]), 2),
        "fat_g": round(sum(float(m["fat_g"]) for m in day["meals"]), 2),
    }
    pending: List[str] = []
    if not day["training_status_confirmed"]:
        pending.append("training_confirmation")
    if not day["meals"]:
        pending.append("intake")
    expenditure = day.get("actual_expenditure_kcal")
    expenditure_source = day.get("expenditure_source")
    if expenditure is None:
        profile_tdee = profile.get("tdee_kcal")
        if profile_tdee is not None:
            expenditure = round(finite_number(profile_tdee, "profile.tdee_kcal", minimum=0.01), 2)
            expenditure_source = "profile_tdee_estimate"
        else:
            pending.append("expenditure")
    actual_deficit = None
    if not pending and expenditure is not None:
        actual_deficit = round(float(expenditure) - totals["calories_kcal"], 2)
    return {
        "date": day["date"],
        "timezone": day["timezone"],
        "training_status": day["training_status"],
        "training_status_confirmed": day["training_status_confirmed"],
        "meal_count": len(day["meals"]),
        "intake": totals,
        "expenditure_kcal": expenditure,
        "expenditure_source": expenditure_source,
        "actual_deficit_kcal": actual_deficit,
        "pending_reasons": pending,
        "complete": actual_deficit is not None,
    }


def list_days(*, root: Optional[Path] = None) -> List[str]:
    directory = diet_root(root)
    if not directory.is_dir():
        return []
    return sorted(path.stem for path in directory.glob("????-??-??.json"))


def _json_print(payload: Any) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generic daily diet tracker")
    parser.add_argument("--root", type=Path, help="repository root (testing/advanced use)")
    sub = parser.add_subparsers(dest="command", required=True)

    status = sub.add_parser("set-training-status")
    status.add_argument("status", choices=sorted(VALID_TRAINING_STATUSES))
    status.add_argument("--date")
    status.add_argument("--confirmed", action="store_true")

    meal = sub.add_parser("add-meal")
    meal.add_argument("--date")
    meal.add_argument("--meal-name", required=True)
    meal.add_argument("--food-name", required=True)
    meal.add_argument("--calories", type=float, required=True)
    meal.add_argument("--protein", type=float, required=True)
    meal.add_argument("--carbs", type=float, required=True)
    meal.add_argument("--fat", type=float, required=True)

    remove = sub.add_parser("remove-meal")
    remove.add_argument("--date", required=True)
    remove.add_argument("--meal-id", required=True)

    expenditure = sub.add_parser("set-expenditure")
    expenditure.add_argument("--date", required=True)
    expenditure.add_argument("--kcal", type=float, required=True)
    expenditure.add_argument("--source", default="manual")

    summary = sub.add_parser("summary")
    summary.add_argument("--date")

    listing = sub.add_parser("list")
    listing.add_argument("--date")

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        profile = load_profile(args.root)
        if args.command == "set-training-status":
            target_date = _resolve_date(args.date, profile)
            path = set_training_status(
                target_date, args.status, confirmed=args.confirmed, root=args.root
            )
            _json_print({"saved": str(path), "summary": summarize_day(target_date, root=args.root)})
        elif args.command == "add-meal":
            target_date = _resolve_date(args.date, profile)
            meal = add_meal(
                target_date,
                meal_name=args.meal_name,
                food_name=args.food_name,
                calories_kcal=args.calories,
                protein_g=args.protein,
                carbs_g=args.carbs,
                fat_g=args.fat,
                root=args.root,
            )
            _json_print({"meal": meal, "summary": summarize_day(target_date, root=args.root)})
        elif args.command == "remove-meal":
            removed = remove_meal(args.date, args.meal_id, root=args.root)
            _json_print({"removed": removed, "summary": summarize_day(args.date, root=args.root)})
        elif args.command == "set-expenditure":
            path = set_expenditure(
                args.date, args.kcal, source=args.source, root=args.root
            )
            _json_print({"saved": str(path), "summary": summarize_day(args.date, root=args.root)})
        elif args.command == "summary":
            target_date = _resolve_date(args.date, profile)
            _json_print(summarize_day(target_date, root=args.root))
        elif args.command == "list":
            if args.date:
                _json_print(summarize_day(args.date, root=args.root))
            else:
                _json_print(list_days(root=args.root))
        return 0
    except (FileNotFoundError, ValueError, OSError) as exc:
        print(f"error: {exc}", flush=True)
        return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
