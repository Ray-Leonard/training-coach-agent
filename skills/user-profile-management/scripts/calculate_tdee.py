#!/usr/bin/env python3
"""Deterministic BMR, TDEE, and macro calculations for user profiles."""

from __future__ import annotations

from datetime import date
from typing import Dict


ACTIVITY_MULTIPLIERS = {
    "sedentary": 1.2,
    "light": 1.375,
    "moderate": 1.55,
    "intense": 1.725,
}

PROTEIN_MULTIPLIERS = {
    "cut": 2.2,
    "bulk": 2.0,
    "maintain": 1.8,
}

CALORIE_ADJUSTMENTS = {
    "cut": -500,
    "bulk": 300,
    "maintain": 0,
}


def calculate_age(birth_date_str: str) -> int:
    """Return age in complete years as of today."""
    try:
        birth_date = date.fromisoformat(birth_date_str)
    except (TypeError, ValueError) as exc:
        raise ValueError("birth_date must use YYYY-MM-DD format") from exc

    today = date.today()
    if birth_date > today:
        raise ValueError("birth_date cannot be in the future")
    return today.year - birth_date.year - (
        (today.month, today.day) < (birth_date.month, birth_date.day)
    )


def calculate_bmr(
    gender: str, weight_kg: float, height_cm: float, age: int
) -> float:
    """Calculate Mifflin-St Jeor basal metabolic rate in kcal/day."""
    normalized_gender = str(gender).lower()
    if normalized_gender not in {"male", "female"}:
        raise ValueError("gender must be 'male' or 'female'")
    if weight_kg <= 0 or height_cm <= 0 or age < 0:
        raise ValueError("weight and height must be positive; age cannot be negative")

    gender_constant = 5 if normalized_gender == "male" else -161
    return round(
        10 * float(weight_kg)
        + 6.25 * float(height_cm)
        - 5 * int(age)
        + gender_constant,
        2,
    )


def calculate_tdee(bmr: float, activity_level: str) -> float:
    """Calculate total daily energy expenditure from BMR and activity."""
    normalized_level = str(activity_level).lower()
    if normalized_level not in ACTIVITY_MULTIPLIERS:
        choices = ", ".join(ACTIVITY_MULTIPLIERS)
        raise ValueError(f"activity_level must be one of: {choices}")
    if bmr <= 0:
        raise ValueError("bmr must be positive")
    return round(float(bmr) * ACTIVITY_MULTIPLIERS[normalized_level], 2)


def calculate_macros(
    tdee: float, goal: str, target_weight_kg: float
) -> Dict[str, int]:
    """Return rounded daily calorie and macronutrient targets."""
    normalized_goal = str(goal).lower()
    if normalized_goal not in CALORIE_ADJUSTMENTS:
        raise ValueError("goal must be 'cut', 'bulk', or 'maintain'")
    if tdee <= 0 or target_weight_kg <= 0:
        raise ValueError("tdee and target_weight_kg must be positive")

    calories = float(tdee) + CALORIE_ADJUSTMENTS[normalized_goal]
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


__all__ = [
    "calculate_age",
    "calculate_bmr",
    "calculate_tdee",
    "calculate_macros",
]
