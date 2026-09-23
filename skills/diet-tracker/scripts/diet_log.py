#!/usr/bin/env python3
"""Daily Diet Tracker storage and deterministic macro/deficit calculations."""

from __future__ import annotations

import argparse
import json
import math
import uuid
from datetime import datetime
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
    "items",
    "calories_kcal",
    "protein_g",
    "carbs_g",
    "fat_g",
    "source",
    "timestamp",
}


def diet_root(root: Optional[Path] = None) -> Path:
    return repo_root(root) / "data" / "diet"


def day_path(date_str: str, root: Optional[Path] = None) -> Path:
    normalized = parse_iso_date(date_str)
    return diet_root(root) / f"{normalized}.json"


def _default_day(date_str: str, profile: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "schema_version": "1.1",
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


def _validate_meal(meal: Dict[str, Any], *, allow_legacy: bool = False) -> None:
    if allow_legacy:
        if "items" not in meal and isinstance(meal.get("food_name"), str):
            meal["items"] = [meal["food_name"]]
        meal.setdefault("source", "legacy")
        if "timestamp" not in meal and "logged_at" in meal:
            meal["timestamp"] = meal.pop("logged_at")
    missing = MEAL_REQUIRED_FIELDS - set(meal)
    if missing:
        raise ValueError(f"meal is missing fields: {', '.join(sorted(missing))}")
    for field in ("meal_name", "food_name", "id"):
        if not isinstance(meal[field], str) or not meal[field].strip():
            raise ValueError(f"meal.{field} must be a non-empty string")
    items = meal["items"]
    if not isinstance(items, list) or not items:
        raise ValueError("meal.items must be a non-empty list")
    if any(not isinstance(item, str) or not item.strip() for item in items):
        raise ValueError("meal.items entries must be non-empty strings")
    for field in ("calories_kcal", "protein_g", "carbs_g", "fat_g"):
        value = finite_number(meal[field], f"meal.{field}")
        meal[field] = round(value, 2)
    if not isinstance(meal["source"], str) or not meal["source"].strip():
        raise ValueError("meal.source must be a non-empty string")
    if not isinstance(meal["timestamp"], str):
        raise ValueError("meal.timestamp must be an ISO-8601 timestamp")
    try:
        parsed_timestamp = datetime.fromisoformat(meal["timestamp"])
    except ValueError as exc:
        raise ValueError("meal.timestamp must be an ISO-8601 timestamp") from exc
    if parsed_timestamp.tzinfo is None:
        raise ValueError("meal.timestamp must include a UTC offset")


def validate_day(
    day: Dict[str, Any],
    *,
    expected_date: Optional[str] = None,
    expected_timezone: Optional[str] = None,
) -> Dict[str, Any]:
    if not isinstance(day, dict):
        raise ValueError("daily diet record must be a JSON object")
    schema_version = day.get("schema_version")
    if schema_version not in {"1.0", "1.1"}:
        raise ValueError("schema_version must be '1.0' or '1.1'")
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
    if expected_timezone is not None and timezone != expected_timezone:
        raise ValueError("daily diet record timezone does not match profile.timezone")
    status = day.get("training_status")
    confirmed = day.get("training_status_confirmed")
    if status is not None and status not in VALID_TRAINING_STATUSES:
        raise ValueError("training_status must be null, 'training', or 'rest'")
    if not isinstance(confirmed, bool):
        raise ValueError("training_status_confirmed must be boolean")
    if status is None and confirmed:
        raise ValueError("training_status cannot be confirmed while it is null")
    if status is not None and not confirmed:
        raise ValueError("training_status requires explicit confirmation")
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
    meal_ids = set()
    for meal in meals:
        if not isinstance(meal, dict):
            raise ValueError("each meal must be a JSON object")
        _validate_meal(meal, allow_legacy=schema_version == "1.0")
        if meal["id"] in meal_ids:
            raise ValueError("meal ids must be unique within a daily record")
        meal_ids.add(meal["id"])
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
    return validate_day(
        day,
        expected_date=normalized,
        expected_timezone=profile_timezone(profile),
    )


def save_day(day: Dict[str, Any], *, root: Optional[Path] = None) -> Path:
    payload = dict(day)
    payload["schema_version"] = "1.1"
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
    items: Optional[List[str]] = None,
    source: str = "manual",
    root: Optional[Path] = None,
) -> Dict[str, Any]:
    profile = load_profile(root)
    day = load_day(date_str, root=root, profile=profile)
    meal = {
        "id": f"meal-{uuid.uuid4().hex}",
        "meal_name": meal_name,
        "food_name": food_name,
        "items": list(items) if items is not None else [food_name],
        "calories_kcal": calories_kcal,
        "protein_g": protein_g,
        "carbs_g": carbs_g,
        "fat_g": fat_g,
        "source": source,
        "timestamp": iso_timestamp(profile),
    }
    _validate_meal(meal)
    day["meals"].append(meal)
    save_day(day, root=root)
    return meal


def get_meal(
    date_str: str, meal_id: str, *, root: Optional[Path] = None
) -> Dict[str, Any]:
    day = load_day(date_str, root=root)
    for meal in day["meals"]:
        if meal["id"] == meal_id:
            return json.loads(json.dumps(meal, ensure_ascii=False))
    raise ValueError(f"meal not found: {meal_id}")


def update_meal(
    date_str: str,
    meal_id: str,
    *,
    meal_name: Optional[str] = None,
    food_name: Optional[str] = None,
    items: Optional[List[str]] = None,
    calories_kcal: Optional[float] = None,
    protein_g: Optional[float] = None,
    carbs_g: Optional[float] = None,
    fat_g: Optional[float] = None,
    source: Optional[str] = None,
    root: Optional[Path] = None,
) -> Dict[str, Any]:
    profile = load_profile(root)
    day = load_day(date_str, root=root, profile=profile)
    updates = {
        "meal_name": meal_name,
        "food_name": food_name,
        "items": list(items) if items is not None else None,
        "calories_kcal": calories_kcal,
        "protein_g": protein_g,
        "carbs_g": carbs_g,
        "fat_g": fat_g,
        "source": source,
    }
    if all(value is None for value in updates.values()):
        raise ValueError("at least one meal field must be provided")
    for meal in day["meals"]:
        if meal["id"] != meal_id:
            continue
        candidate = dict(meal)
        candidate.update({key: value for key, value in updates.items() if value is not None})
        _validate_meal(candidate)
        meal.clear()
        meal.update(candidate)
        save_day(day, root=root)
        return json.loads(json.dumps(meal, ensure_ascii=False))
    raise ValueError(f"meal not found: {meal_id}")


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


def _profile_number(
    value: Any, field: str, *, minimum: Optional[float] = None
) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{field} must be numeric")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be numeric") from exc
    if not math.isfinite(number) or (minimum is not None and number < minimum):
        qualifier = f" and >= {minimum}" if minimum is not None else ""
        raise ValueError(f"{field} must be finite{qualifier}")
    return number


def _nutrition_targets(profile: Dict[str, Any]) -> Dict[str, Any]:
    macros = profile.get("daily_macros")
    if macros is None:
        macros = {}
    if not isinstance(macros, dict):
        raise ValueError("profile.daily_macros must be an object when present")

    calorie_value = macros.get("calories_kcal")
    if calorie_value is not None:
        calorie_target = _profile_number(
            calorie_value, "profile.daily_macros.calories_kcal", minimum=0.01
        )
        calorie_source = "profile.daily_macros.calories_kcal"
    else:
        tdee = profile.get("tdee_kcal")
        delta = profile.get("calorie_delta_kcal")
        if tdee is None or delta is None:
            calorie_target = None
            calorie_source = None
        else:
            calorie_target = _profile_number(
                tdee, "profile.tdee_kcal", minimum=0.01
            ) + _profile_number(delta, "profile.calorie_delta_kcal")
            if calorie_target <= 0:
                raise ValueError(
                    "profile.tdee_kcal + profile.calorie_delta_kcal must be positive"
                )
            calorie_source = "profile.tdee_kcal + profile.calorie_delta_kcal"

    targets: Dict[str, Any] = {
        "calories_kcal": round(calorie_target, 2)
        if calorie_target is not None
        else None,
        "calories_source": calorie_source,
    }
    for field in ("protein_g", "carbs_g", "fat_g"):
        value = macros.get(field)
        targets[field] = (
            round(
                _profile_number(
                    value, f"profile.daily_macros.{field}", minimum=0.0
                ),
                2,
            )
            if value is not None
            else None
        )
    return targets


def _macro_progress(
    intake: Optional[Dict[str, float]], targets: Dict[str, Any]
) -> Dict[str, Dict[str, Optional[float]]]:
    progress: Dict[str, Dict[str, Optional[float]]] = {}
    for field in ("calories_kcal", "protein_g", "carbs_g", "fat_g"):
        actual = intake[field] if intake is not None else None
        target = targets.get(field)
        remaining = (
            round(float(target) - float(actual), 2)
            if target is not None and actual is not None
            else None
        )
        percent = (
            round(float(actual) / float(target) * 100, 2)
            if target is not None and actual is not None and float(target) > 0
            else None
        )
        progress[field] = {
            "actual": actual,
            "target": target,
            "remaining": remaining,
            "percent": percent,
        }
    return progress


def summarize_day(date_str: str, *, root: Optional[Path] = None) -> Dict[str, Any]:
    profile = load_profile(root)
    day = load_day(date_str, root=root, profile=profile)
    totals = None
    if day["meals"]:
        totals = {
            "calories_kcal": round(
                sum(float(m["calories_kcal"]) for m in day["meals"]), 2
            ),
            "protein_g": round(
                sum(float(m["protein_g"]) for m in day["meals"]), 2
            ),
            "carbs_g": round(sum(float(m["carbs_g"]) for m in day["meals"]), 2),
            "fat_g": round(sum(float(m["fat_g"]) for m in day["meals"]), 2),
        }
    targets = _nutrition_targets(profile)
    pending: List[str] = []
    if not day["training_status_confirmed"]:
        pending.append("training_confirmation")
    if not day["meals"]:
        pending.append("intake")
    if targets["calories_kcal"] is None:
        pending.append("calorie_target")
    expenditure = day.get("actual_expenditure_kcal")
    expenditure_source = day.get("expenditure_source")
    if expenditure is None:
        profile_tdee = profile.get("tdee_kcal")
        if profile_tdee is not None:
            expenditure = round(finite_number(profile_tdee, "profile.tdee_kcal", minimum=0.01), 2)
            expenditure_source = "profile_tdee_estimate"
        else:
            pending.append("expenditure")
    energy_deficit = None
    if day["training_status_confirmed"] and totals is not None and expenditure is not None:
        energy_deficit = round(float(expenditure) - totals["calories_kcal"], 2)
    deficit_kind = None
    if energy_deficit is not None:
        deficit_kind = (
            "estimated" if expenditure_source == "profile_tdee_estimate" else "manual"
        )
    return {
        "date": day["date"],
        "timezone": day["timezone"],
        "training_status": day["training_status"],
        "training_status_confirmed": day["training_status_confirmed"],
        "meal_count": len(day["meals"]),
        "intake": totals,
        "target": targets,
        "progress": _macro_progress(totals, targets),
        "expenditure_kcal": expenditure,
        "expenditure_source": expenditure_source,
        "energy_deficit_kcal": energy_deficit,
        "deficit_kind": deficit_kind,
        "pending_reasons": pending,
        "complete": not pending,
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
    meal.add_argument("--item", dest="items", action="append")
    meal.add_argument("--source", default="manual")

    get_meal_parser = sub.add_parser("get-meal")
    get_meal_parser.add_argument("--date", required=True)
    get_meal_parser.add_argument("--meal-id", required=True)

    update = sub.add_parser("update-meal")
    update.add_argument("--date", required=True)
    update.add_argument("--meal-id", required=True)
    update.add_argument("--meal-name")
    update.add_argument("--food-name")
    update.add_argument("--item", dest="items", action="append")
    update.add_argument("--calories", type=float)
    update.add_argument("--protein", type=float)
    update.add_argument("--carbs", type=float)
    update.add_argument("--fat", type=float)
    update.add_argument("--source")

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
                items=args.items,
                source=args.source,
                root=args.root,
            )
            _json_print({"meal": meal, "summary": summarize_day(target_date, root=args.root)})
        elif args.command == "get-meal":
            _json_print(get_meal(args.date, args.meal_id, root=args.root))
        elif args.command == "update-meal":
            meal = update_meal(
                args.date,
                args.meal_id,
                meal_name=args.meal_name,
                food_name=args.food_name,
                items=args.items,
                calories_kcal=args.calories,
                protein_g=args.protein,
                carbs_g=args.carbs,
                fat_g=args.fat,
                source=args.source,
                root=args.root,
            )
            _json_print({"meal": meal, "summary": summarize_day(args.date, root=args.root)})
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
