from __future__ import annotations

import json
import importlib.util
import sys
import unittest
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(TESTS_DIR))
from test_support import TemporaryRepoMixin


ROOT = Path(__file__).resolve().parents[1]
DIET_SCRIPTS = ROOT / "skills" / "diet-tracker" / "scripts"
sys.path.insert(0, str(DIET_SCRIPTS))

import diet_log  # noqa: E402


def load_calculation_entrypoint():
    path = DIET_SCRIPTS / "calculate_daily_nutrition.py"
    spec = importlib.util.spec_from_file_location("diet_calculation_entrypoint", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class DietTrackerTestCase(TemporaryRepoMixin, unittest.TestCase):
    def test_meal_crud_preserves_required_fields_and_totals(self) -> None:
        root = self.make_root()
        meal = diet_log.add_meal(
            "2026-01-10",
            meal_name="breakfast",
            food_name="oats and yogurt",
            items=["oats", "yogurt"],
            calories_kcal=500,
            protein_g=35,
            carbs_g=60,
            fat_g=12,
            source="manual",
            root=root,
        )
        self.assertEqual(meal["items"], ["oats", "yogurt"])
        self.assertEqual(meal["source"], "manual")
        self.assertIn("timestamp", meal)
        self.assertEqual(diet_log.get_meal("2026-01-10", meal["id"], root=root), meal)
        self.assertEqual(
            diet_log.load_day("2026-01-10", root=root)["schema_version"], "1.1"
        )

        changed = diet_log.update_meal(
            "2026-01-10", meal["id"], calories_kcal=550, root=root
        )
        self.assertEqual(changed["calories_kcal"], 550.0)
        summary = diet_log.summarize_day("2026-01-10", root=root)
        self.assertEqual(summary["intake"]["calories_kcal"], 550.0)
        self.assertEqual(summary["meal_count"], 1)

        self.assertTrue(diet_log.remove_meal("2026-01-10", meal["id"], root=root))
        self.assertFalse(diet_log.remove_meal("2026-01-10", meal["id"], root=root))

    def test_summary_uses_daily_macro_target_and_requires_training_confirmation(self) -> None:
        root = self.make_root()
        diet_log.add_meal(
            "2026-01-10",
            meal_name="daily total",
            food_name="confirmed foods",
            calories_kcal=1900,
            protein_g=150,
            carbs_g=190,
            fat_g=55,
            root=root,
        )

        pending = diet_log.summarize_day("2026-01-10", root=root)
        self.assertFalse(pending["complete"])
        self.assertIn("training_confirmation", pending["pending_reasons"])
        self.assertEqual(pending["target"]["calories_kcal"], 2000.0)
        self.assertEqual(
            pending["target"]["calories_source"],
            "profile.daily_macros.calories_kcal",
        )
        self.assertEqual(pending["progress"]["calories_kcal"]["remaining"], 100.0)
        self.assertIsNone(pending["energy_deficit_kcal"])
        self.assertEqual(pending["expenditure_source"], "profile_tdee_estimate")

        with self.assertRaisesRegex(ValueError, "explicit user confirmation"):
            diet_log.set_training_status("2026-01-10", "rest", root=root)
        diet_log.set_training_status(
            "2026-01-10", "rest", confirmed=True, root=root
        )
        complete = diet_log.summarize_day("2026-01-10", root=root)
        self.assertTrue(complete["complete"])
        self.assertEqual(complete["energy_deficit_kcal"], 600.0)
        self.assertEqual(complete["deficit_kind"], "estimated")

    def test_target_falls_back_to_tdee_plus_calorie_delta(self) -> None:
        root = self.make_root({"daily_macros": {"protein_g": 160}})
        diet_log.add_meal(
            "2026-01-10",
            meal_name="meal",
            food_name="food",
            calories_kcal=1800,
            protein_g=140,
            carbs_g=180,
            fat_g=50,
            root=root,
        )
        summary = diet_log.summarize_day("2026-01-10", root=root)
        self.assertEqual(summary["target"]["calories_kcal"], 2000.0)
        self.assertEqual(
            summary["target"]["calories_source"],
            "profile.tdee_kcal + profile.calorie_delta_kcal",
        )

    def test_legacy_meal_shape_is_normalized_without_losing_values(self) -> None:
        root = self.make_root()
        path = root / "data" / "diet" / "2026-01-10.json"
        path.parent.mkdir(parents=True)
        path.write_text(
            json.dumps(
                {
                    "schema_version": "1.0",
                    "date": "2026-01-10",
                    "timezone": "UTC",
                    "training_status": None,
                    "training_status_confirmed": False,
                    "training_confirmation_source": None,
                    "meals": [
                        {
                            "id": "legacy-meal",
                            "meal_name": "meal",
                            "food_name": "food",
                            "calories_kcal": 400,
                            "protein_g": 30,
                            "carbs_g": 40,
                            "fat_g": 10,
                            "logged_at": "2026-01-10T12:00:00+00:00",
                        }
                    ],
                    "actual_expenditure_kcal": None,
                    "expenditure_source": None,
                    "notes": "",
                }
            ),
            encoding="utf-8",
        )
        meal = diet_log.load_day("2026-01-10", root=root)["meals"][0]
        self.assertEqual(meal["items"], ["food"])
        self.assertEqual(meal["source"], "legacy")
        self.assertEqual(meal["timestamp"], "2026-01-10T12:00:00+00:00")
        self.assertNotIn("logged_at", meal)

    def test_negative_profile_macro_target_is_rejected(self) -> None:
        root = self.make_root(
            {
                "daily_macros": {
                    "calories_kcal": 2000,
                    "protein_g": -1,
                    "carbs_g": 200,
                    "fat_g": 60,
                }
            }
        )
        with self.assertRaisesRegex(ValueError, "protein_g"):
            diet_log.summarize_day("2026-01-10", root=root)

    def test_missing_intake_is_not_reported_as_zero(self) -> None:
        root = self.make_root()
        diet_log.set_training_status(
            "2026-01-10", "training", confirmed=True, root=root
        )
        summary = diet_log.summarize_day("2026-01-10", root=root)
        self.assertIsNone(summary["intake"])
        self.assertIsNone(summary["energy_deficit_kcal"])
        self.assertIn("intake", summary["pending_reasons"])

    def test_manual_expenditure_is_labelled_and_used(self) -> None:
        root = self.make_root()
        diet_log.add_meal(
            "2026-01-10",
            meal_name="meal",
            food_name="food",
            calories_kcal=1800,
            protein_g=140,
            carbs_g=180,
            fat_g=50,
            root=root,
        )
        diet_log.set_training_status(
            "2026-01-10", "training", confirmed=True, root=root
        )
        diet_log.set_expenditure(
            "2026-01-10", 2700, source="manual wearable review", root=root
        )
        summary = diet_log.summarize_day("2026-01-10", root=root)
        self.assertEqual(summary["energy_deficit_kcal"], 900.0)
        self.assertEqual(summary["deficit_kind"], "manual")
        self.assertEqual(summary["expenditure_source"], "manual wearable review")

    def test_corrupt_json_invalid_date_and_timezone_are_rejected_without_overwrite(self) -> None:
        root = self.make_root()
        path = root / "data" / "diet" / "2026-01-10.json"
        path.parent.mkdir(parents=True)
        path.write_text("{not-json", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "corrupted"):
            diet_log.add_meal(
                "2026-01-10",
                meal_name="meal",
                food_name="food",
                calories_kcal=1,
                protein_g=1,
                carbs_g=1,
                fat_g=1,
                root=root,
            )
        self.assertEqual(path.read_text(encoding="utf-8"), "{not-json")
        with self.assertRaisesRegex(ValueError, "YYYY-MM-DD"):
            diet_log.load_day("2026-02-30", root=root)

        profile = json.loads((root / "data" / "user" / "profile.json").read_text())
        day = diet_log._default_day("2026-01-11", profile)
        day["timezone"] = "Not/IANA"
        with self.assertRaisesRegex(ValueError, "Unknown IANA timezone"):
            diet_log.validate_day(day)

    def test_loaded_record_timezone_must_match_profile(self) -> None:
        root = self.make_root()
        profile = json.loads(
            (root / "data" / "user" / "profile.json").read_text(encoding="utf-8")
        )
        day = diet_log._default_day("2026-01-10", profile)
        day["timezone"] = "America/Toronto"
        path = root / "data" / "diet" / "2026-01-10.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(day), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "does not match profile.timezone"):
            diet_log.load_day("2026-01-10", root=root)

    def test_calculation_entrypoint_renders_script_calculated_values(self) -> None:
        root = self.make_root()
        diet_log.add_meal(
            "2026-01-10",
            meal_name="meal",
            food_name="food",
            calories_kcal=500,
            protein_g=40,
            carbs_g=60,
            fat_g=10,
            root=root,
        )
        module = load_calculation_entrypoint()
        result = module.calculate("2026-01-10", root=root)
        report = module.render_markdown(result)
        self.assertEqual(result["target"]["calories_kcal"], 2000.0)
        self.assertIn("500", report)
        self.assertIn("2000", report)
        self.assertIn("training_confirmation", report)


if __name__ == "__main__":
    unittest.main()
