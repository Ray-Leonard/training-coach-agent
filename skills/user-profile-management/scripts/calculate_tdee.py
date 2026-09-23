#!/usr/bin/env python3
"""Deterministic BMR, TDEE, and macro calculations for user profiles."""

from __future__ import annotations

from datetime import date, timedelta
import math
from typing import Dict


def _read_profile_timezone():
    """Read timezone from profile.json. Returns None on failure."""
    import json
    from pathlib import Path
    profile_path = Path(__file__).resolve().parents[3] / "data" / "user" / "profile.json"
    try:
        raw = json.loads(profile_path.read_text(encoding="utf-8"))
        return raw.get("timezone")
    except Exception:
        return None


PROTEIN_MULTIPLIERS = {
    "cut": 2.2,
    "bulk": 2.0,
    "maintain": 1.8,
}

def calculate_age(birth_date_str: str, tz_name: str = None) -> int:
    """Return age in complete years as of today in the given timezone."""
    try:
        birth_date = date.fromisoformat(birth_date_str)
    except (TypeError, ValueError) as exc:
        raise ValueError("birth_date must use YYYY-MM-DD format") from exc

    if tz_name is None:
        tz_name = _read_profile_timezone()
    if tz_name:
        from datetime import datetime
        from zoneinfo import ZoneInfo
        today = datetime.now(ZoneInfo(tz_name)).date()
    else:
        today = date.today()
    if birth_date > today:
        raise ValueError("birth_date cannot be in the future")
    return today.year - birth_date.year - (
        (today.month, today.day) < (birth_date.month, birth_date.day)
    )


def calculate_bmr(
    sex: str, weight_kg: float, height_cm: float, age: int
) -> float:
    """Calculate Mifflin-St Jeor basal metabolic rate in kcal/day."""
    normalized_sex = str(sex).lower()
    if normalized_sex not in {"male", "female"}:
        raise ValueError("sex must be 'male' or 'female'")
    if weight_kg <= 0 or height_cm <= 0 or age < 0:
        raise ValueError("weight and height must be positive; age cannot be negative")

    sex_constant = 5 if normalized_sex == "male" else -161
    return round(
        10 * float(weight_kg)
        + 6.25 * float(height_cm)
        - 5 * int(age)
        + sex_constant,
        2,
    )


def calculate_tdee(bmr: float, multiplier: float) -> float:
    """Calculate total daily energy expenditure from BMR and activity multiplier."""
    if bmr <= 0:
        raise ValueError("bmr must be positive")
    if multiplier <= 0:
        raise ValueError("multiplier must be positive")
    return round(float(bmr) * float(multiplier), 2)


def calculate_macros(
    tdee: float, goal: str, target_weight_kg: float, calorie_delta: float
) -> Dict[str, int]:
    """Return rounded daily calorie and macronutrient targets."""
    normalized_goal = str(goal).lower()
    if normalized_goal not in PROTEIN_MULTIPLIERS:
        raise ValueError("goal must be 'cut', 'bulk', or 'maintain'")
    if tdee <= 0 or target_weight_kg <= 0:
        raise ValueError("tdee and target_weight_kg must be positive")

    try:
        calories = float(tdee) + float(calorie_delta)
    except (TypeError, ValueError) as exc:
        raise ValueError("calorie_delta must be numeric") from exc
    if calories <= 0:
        raise ValueError("calculated calories must be positive")

    protein = float(target_weight_kg) * PROTEIN_MULTIPLIERS[normalized_goal]
    fat = calories * 0.25 / 9
    carbs = (calories - protein * 4 - fat * 9) / 4
    if carbs < 0:
        raise ValueError("calculated carbohydrates are negative; verify inputs")

    return {
        "calories_kcal": round(calories),
        "protein_g": round(protein),
        "carbs_g": round(carbs),
        "fat_g": round(fat),
    }


def derive_activity_multiplier(
    training_days_per_week: int,
    cardio_days_per_week: int,
    cardio_minutes_per_session: float,
) -> float:
    """Derive activity multiplier from weekly exercise metadata."""
    for name, value in (
        ("training_days_per_week", training_days_per_week),
        ("cardio_days_per_week", cardio_days_per_week),
    ):
        if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 7:
            raise ValueError(f"{name} must be an integer from 0 to 7")
    try:
        cardio_minutes = float(cardio_minutes_per_session)
    except (TypeError, ValueError) as exc:
        raise ValueError("cardio_minutes_per_session must be numeric") from exc
    if not math.isfinite(cardio_minutes) or not 0 <= cardio_minutes <= 1440:
        raise ValueError("cardio_minutes_per_session must be between 0 and 1440")
    total_hours = training_days_per_week + cardio_days_per_week * cardio_minutes / 60
    if total_hours < 2:
        return 1.2
    if total_hours < 4:
        return 1.375
    if total_hours < 7:
        return 1.55
    return 1.725


def calculate_target_weight_from_bodyfat(
    current_weight_kg: float,
    current_bodyfat_pct: float,
    target_bodyfat_pct: float,
) -> float:
    """Estimate target weight while holding lean mass constant."""
    weight = float(current_weight_kg)
    current_bf = float(current_bodyfat_pct)
    target_bf = float(target_bodyfat_pct)
    if not math.isfinite(weight) or weight <= 0:
        raise ValueError("current_weight_kg must be positive")
    if not math.isfinite(current_bf) or not 0 <= current_bf < 100:
        raise ValueError("current_bodyfat_pct must be from 0 to less than 100")
    if not math.isfinite(target_bf) or not 0 <= target_bf < 100:
        raise ValueError("target_bodyfat_pct must be from 0 to less than 100")
    return round(weight * (1 - current_bf / 100) / (1 - target_bf / 100), 2)


def estimate_timeline(
    initial_weight_kg: float,
    target_weight_kg: float,
    calorie_delta_kcal: float,
    start_date: str,
) -> Dict[str, object]:
    """Estimate a target date using the documented conservative 0.45 factor."""
    initial = float(initial_weight_kg)
    target = float(target_weight_kg)
    delta = float(calorie_delta_kcal)
    if not all(math.isfinite(value) for value in (initial, target, delta)):
        raise ValueError("timeline inputs must be finite")
    if initial <= 0 or target <= 0:
        raise ValueError("weights must be positive")
    try:
        start = date.fromisoformat(start_date)
    except (TypeError, ValueError) as exc:
        raise ValueError("start_date must use YYYY-MM-DD format") from exc
    weight_difference = abs(target - initial)
    if weight_difference == 0 or delta == 0:
        return {
            "expected_weekly_change_kg": 0.0,
            "weeks": None,
            "target_date": None,
            "estimated": False,
        }
    expected_weekly_change = abs(delta) * 7 / 3500 * 0.45
    weeks = weight_difference / expected_weekly_change
    days = max(1, math.ceil(weeks * 7))
    return {
        "expected_weekly_change_kg": round(expected_weekly_change, 4),
        "weeks": round(weeks, 2),
        "target_date": (start + timedelta(days=days)).isoformat(),
        "estimated": True,
    }


__all__ = [
    "calculate_age",
    "calculate_bmr",
    "calculate_tdee",
    "calculate_macros",
    "derive_activity_multiplier",
    "calculate_target_weight_from_bodyfat",
    "estimate_timeline",
]


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser(description="BMR / TDEE / macro calculator")
    p.add_argument("--sex", required=True, choices=["male", "female"])
    p.add_argument("--birth", required=True, help="Birth date (YYYY-MM-DD)")
    p.add_argument("--height", type=float, required=True, help="Height in cm")
    p.add_argument("--weight", type=float, required=True, help="Weight in kg for BMR")
    p.add_argument("--target", type=float, required=True, help="Target weight in kg for macros")
    p.add_argument("--multiplier", type=float, default=1.55, help="Activity multiplier (e.g. 1.55)")
    p.add_argument("--goal", default="maintain", choices=["cut", "bulk", "maintain"])
    p.add_argument("--delta", type=float, default=0, help="Calorie delta (e.g. -500 for cut)")

    args = p.parse_args()
    age = calculate_age(args.birth)
    bmr = calculate_bmr(args.sex, args.weight, args.height, age)
    tdee = calculate_tdee(bmr, args.multiplier)
    macros = calculate_macros(tdee, args.goal, args.target, args.delta)

    print(f"Age: {age}")
    print(f"BMR: {bmr} kcal")
    print(f"TDEE: {tdee} kcal (×{args.multiplier})")
    print(f"Goal: {args.goal} (delta={args.delta:+.0f})")
    print(f"Macros: {macros['calories_kcal']} kcal | P:{macros['protein_g']}g C:{macros['carbs_g']}g F:{macros['fat_g']}g")
