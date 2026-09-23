from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any, Dict


DEFAULT_PROFILE: Dict[str, Any] = {
    "sex": "male",
    "birth_date": "2000-01-01",
    "height_cm": 180,
    "timezone": "UTC",
    "goal": "cut",
    "target_weight_kg": 75,
    "initial_weight_kg": 80,
    "target_set_date": "2026-01-01",
    "timeline": None,
    "calorie_delta_kcal": -500,
    "daily_macros": {
        "calories_kcal": 2000,
        "protein_g": 160,
        "carbs_g": 200,
        "fat_g": 60,
    },
    "training_days_per_week": 4,
    "cardio_days_per_week": 2,
    "cardio_minutes_per_session": 30,
    "tdee_kcal": 2500,
    "bmr_kcal": 1700,
}


class TemporaryRepoMixin:
    temp: tempfile.TemporaryDirectory[str]

    def make_root(self, profile_updates: Dict[str, Any] | None = None) -> Path:
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        profile = json.loads(json.dumps(DEFAULT_PROFILE))
        if profile_updates:
            profile.update(profile_updates)
        path = root / "data" / "user" / "profile.json"
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps(profile, indent=2), encoding="utf-8")
        return root

    def tearDown(self) -> None:
        if hasattr(self, "temp"):
            self.temp.cleanup()
