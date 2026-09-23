from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIET_SCRIPTS = ROOT / "skills" / "diet-tracker" / "scripts"
sys.path.insert(0, str(DIET_SCRIPTS))

import sync_diet_data  # noqa: E402


class XunjiDietProjectionTestCase(unittest.TestCase):
    def test_gram_record_projects_to_existing_meal_shape(self) -> None:
        record = {
            "date": "2026-09-20",
            "meal_type": "lunch",
            "name": "鸡胸肉",
            "amount": 150,
            "unit": "g",
            "uniquekey": "official-key",
            "ntr": {"cal": 165, "protein": 31, "fat": 3.6, "carb": 0},
            "units": [],
        }

        meal = sync_diet_data.project_food_record(
            record, sync_timestamp="2026-09-24T12:00:00+08:00"
        )

        self.assertEqual(meal["source"], "xunji_api")
        self.assertEqual(meal["meal_name"], "lunch")
        self.assertEqual(meal["food_name"], "鸡胸肉")
        self.assertEqual(meal["calories_kcal"], 247.5)
        self.assertEqual(meal["protein_g"], 46.5)
        self.assertEqual(meal["fat_g"], 5.4)
        self.assertEqual(meal["carbs_g"], 0.0)
        self.assertEqual(meal["remote"]["uniquekey"], "official-key")

    def test_portion_uses_matching_official_unit_conversion(self) -> None:
        record = {
            "date": "2026-09-20",
            "meal_type": "breakfast",
            "name": "燕麦",
            "amount": 2,
            "unit": "份",
            "ntr": {"cal": 380, "protein": 13, "fat": 7, "carb": 68},
            "units": [{"unit": "份", "count": "1", "gram": 40}],
        }

        meal = sync_diet_data.project_food_record(
            record, sync_timestamp="2026-09-24T12:00:00+08:00"
        )

        self.assertEqual(meal["calories_kcal"], 304.0)
        self.assertEqual(meal["protein_g"], 10.4)
        self.assertEqual(meal["carbs_g"], 54.4)
        self.assertEqual(meal["fat_g"], 5.6)

    def test_unknown_unit_is_rejected_instead_of_treated_as_grams(self) -> None:
        record = {
            "date": "2026-09-20",
            "meal_type": "lunch",
            "name": "未知单位食物",
            "amount": 1,
            "unit": "碗",
            "ntr": {"cal": 100, "protein": 5, "fat": 2, "carb": 10},
            "units": [],
        }
        with self.assertRaisesRegex(ValueError, "cannot convert"):
            sync_diet_data.project_food_record(
                record, sync_timestamp="2026-09-24T12:00:00+08:00"
            )

    def test_day_projection_keeps_unknown_units_as_pending(self) -> None:
        normalized_day = {
            "date": "2026-09-20",
            "foods": [
                {
                    "date": "2026-09-20",
                    "meal_type": "lunch",
                    "name": "未知单位食物",
                    "amount": 1,
                    "unit": "碗",
                    "ntr": {"cal": 100, "protein": 5, "fat": 2, "carb": 10},
                    "units": [],
                }
            ],
            "raw_day": {"date": "2026-09-20"},
        }

        projected = sync_diet_data.project_xunji_day(
            normalized_day,
            {"timezone": "Asia/Shanghai"},
            sync_timestamp="2026-09-24T12:00:00+08:00",
        )

        self.assertEqual(projected["meals"], [])
        self.assertEqual(projected["xunji"]["food_count"], 1)
        self.assertEqual(len(projected["xunji"]["pending_foods"]), 1)

    def test_day_projection_preserves_coach_owned_daily_context(self) -> None:
        normalized_day = {
            "date": "2026-09-20",
            "source": "xunji_api",
            "foods": [
                {
                    "date": "2026-09-20",
                    "meal_type": "lunch",
                    "name": "鸡胸肉",
                    "amount": 150,
                    "unit": "g",
                    "ntr": {"cal": 165, "protein": 31, "fat": 3.6, "carb": 0},
                    "units": [],
                }
            ],
            "raw_day": {"date": "2026-09-20", "foods": []},
        }
        existing_day = {
            "training_status": "training",
            "training_status_confirmed": True,
            "training_confirmation_source": "user",
            "actual_expenditure_kcal": 3200,
            "expenditure_source": "manual",
            "notes": "保留教练备注",
        }

        projected = sync_diet_data.project_xunji_day(
            normalized_day,
            {"timezone": "Asia/Shanghai"},
            existing_day=existing_day,
            sync_timestamp="2026-09-24T12:00:00+08:00",
        )

        self.assertEqual(projected["date"], "2026-09-20")
        self.assertEqual(projected["timezone"], "Asia/Shanghai")
        self.assertEqual(projected["training_status"], "training")
        self.assertEqual(projected["actual_expenditure_kcal"], 3200)
        self.assertEqual(projected["notes"], "保留教练备注")
        self.assertEqual(projected["meals"][0]["source"], "xunji_api")
        self.assertEqual(projected["xunji"]["raw_day"], normalized_day["raw_day"])


if __name__ == "__main__":
    unittest.main()
