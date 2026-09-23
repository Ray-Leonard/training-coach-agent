from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
DIET_SCRIPTS = ROOT / "skills" / "diet-tracker" / "scripts"
PLAN_SCRIPTS = ROOT / "skills" / "training-planning" / "scripts"
PROFILE_SCRIPTS = ROOT / "skills" / "user-profile-management" / "scripts"
sys.path.insert(0, str(DIET_SCRIPTS))
sys.path.insert(0, str(PLAN_SCRIPTS))

import cut_camp  # noqa: E402
import diet_log  # noqa: E402
import generate_plan  # noqa: E402


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


body_log = load_module("task449_body_log", PROFILE_SCRIPTS / "body_log.py")
calculate_tdee = load_module("task449_calculate_tdee", PROFILE_SCRIPTS / "calculate_tdee.py")
sync_body_data = load_module("task449_sync_body_data", PROFILE_SCRIPTS / "sync_body_data.py")
compare_body_logs = load_module(
    "task449_compare_body_logs", PROFILE_SCRIPTS / "compare_body_logs.py"
)


class Task449TestCase(unittest.TestCase):
    def make_root(self) -> Path:
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        profile_path = root / "data" / "user" / "profile.json"
        profile_path.parent.mkdir(parents=True)
        profile_path.write_text(
            json.dumps(
                {
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
                    "daily_macros": {"calories_kcal": 2000, "protein_g": 160, "carbs_g": 200, "fat_g": 60},
                    "training_days_per_week": 4,
                    "cardio_days_per_week": 2,
                    "cardio_minutes_per_session": 30,
                    "tdee_kcal": 2500,
                    "bmr_kcal": 1700,
                },
                indent=2,
            )
        )
        return root

    def tearDown(self) -> None:
        if hasattr(self, "temp"):
            self.temp.cleanup()

    def test_daily_tracking_requires_confirmation_and_calculates_balance(self):
        root = self.make_root()
        with self.assertRaises(ValueError):
            diet_log.set_training_status("2026-01-10", "training", root=root)
        diet_log.add_meal(
            "2026-01-10",
            meal_name="breakfast",
            food_name="test food",
            calories_kcal=1800,
            protein_g=150,
            carbs_g=180,
            fat_g=60,
            root=root,
        )
        day = diet_log.load_day("2026-01-10", root=root)
        self.assertTrue(
            diet_log.remove_meal("2026-01-10", day["meals"][0]["id"], root=root)
        )
        self.assertFalse(
            diet_log.remove_meal("2026-01-10", day["meals"][0]["id"], root=root)
        )
        diet_log.add_meal(
            "2026-01-10",
            meal_name="breakfast",
            food_name="test food",
            calories_kcal=1800,
            protein_g=150,
            carbs_g=180,
            fat_g=60,
            root=root,
        )
        pending = diet_log.summarize_day("2026-01-10", root=root)
        self.assertFalse(pending["complete"])
        self.assertIn("training_confirmation", pending["pending_reasons"])
        diet_log.set_training_status("2026-01-10", "rest", confirmed=True, root=root)
        complete = diet_log.summarize_day("2026-01-10", root=root)
        self.assertTrue(complete["complete"])
        self.assertEqual(complete["actual_deficit_kcal"], 700.0)
        self.assertEqual(complete["expenditure_source"], "profile_tdee_estimate")

    def test_corrupted_daily_json_is_not_replaced(self):
        root = self.make_root()
        path = root / "data" / "diet" / "2026-01-10.json"
        path.parent.mkdir(parents=True)
        path.write_text("{not-json", encoding="utf-8")
        with self.assertRaises(ValueError):
            diet_log.add_meal(
                "2026-01-10",
                meal_name="breakfast",
                food_name="food",
                calories_kcal=1,
                protein_g=1,
                carbs_g=1,
                fat_g=1,
                root=root,
            )
        self.assertEqual(path.read_text(encoding="utf-8"), "{not-json")

    def test_ten_day_camp_target_and_refresh(self):
        root = self.make_root()
        path = cut_camp.init_camp(
            start_date="2026-01-10",
            days=10,
            target_deficit_kcal=700,
            slug="ten-day-cut",
            root=root,
        )
        camp = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(camp["days"], 10)
        self.assertEqual(camp["target_daily_deficit_kcal"], 700.0)
        self.assertEqual(camp["target_intake_kcal"], 1800)
        diet_log.set_training_status("2026-01-10", "rest", confirmed=True, root=root)
        diet_log.add_meal(
            "2026-01-10",
            meal_name="day-total",
            food_name="confirmed daily intake",
            calories_kcal=1800,
            protein_g=150,
            carbs_g=180,
            fat_g=60,
            root=root,
        )
        refreshed = cut_camp.refresh_camp(path.name, root=root)
        self.assertEqual(refreshed["entries"][0]["status"], "complete")
        self.assertEqual(refreshed["entries"][0]["actual_deficit_kcal"], 700.0)
        self.assertEqual(refreshed["entries"][0]["difference_from_target_kcal"], 0.0)
        summary = cut_camp.camp_summary(path.name, root=root)
        self.assertEqual(summary["completed_days"], 1)
        self.assertEqual(summary["pending_days"], 9)
        self.assertEqual(summary["actual_deficit_total_kcal"], 700.0)
        with self.assertRaises(FileExistsError):
            cut_camp.init_camp(
                start_date="2026-01-10",
                days=10,
                target_deficit_kcal=700,
                slug="ten-day-cut",
                root=root,
            )

    def test_malformed_camp_and_timezone_fail_as_validation_errors(self):
        root = self.make_root()
        path = cut_camp.init_camp(
            start_date="2026-01-10",
            days=1,
            target_deficit_kcal=700,
            slug="validation-camp",
            root=root,
        )
        camp = json.loads(path.read_text(encoding="utf-8"))
        camp["entries"] = [None]
        path.write_text(json.dumps(camp), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "JSON object"):
            cut_camp.camp_summary(path.name, root=root)

        camp["entries"] = [{"date": "2026-01-10"}]
        camp["timezone"] = "Not/IANA"
        path.write_text(json.dumps(camp), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Unknown IANA timezone"):
            cut_camp.camp_summary(path.name, root=root)

        profile = json.loads((root / "data" / "user" / "profile.json").read_text())
        day = diet_log._default_day("2026-01-10", profile)
        day["timezone"] = "Not/IANA"
        with self.assertRaisesRegex(ValueError, "Unknown IANA timezone"):
            diet_log.validate_day(day)

    def test_plan_is_ten_days_and_does_not_modify_profile(self):
        root = self.make_root()
        profile_path = root / "data" / "user" / "profile.json"
        before = profile_path.read_text(encoding="utf-8")
        plan = generate_plan.generate_plan(start_date="2026-01-10", days=10, root=root)
        self.assertEqual(len(plan["daily_schedule"]), 10)
        self.assertEqual(plan["split"]["name"], "upper-lower")
        self.assertTrue(all(day["user_confirmation_required"] for day in plan["daily_schedule"]))
        path = generate_plan.save_plan(plan, root=root)
        self.assertTrue(path.is_relative_to(root / "data" / "training-plans"))
        self.assertEqual(profile_path.read_text(encoding="utf-8"), before)
        with self.assertRaises(ValueError):
            generate_plan.save_plan(plan, root=root, output=str(root / "outside.json"))

    def test_calculation_helpers(self):
        self.assertEqual(calculate_tdee.derive_activity_multiplier(4, 4, 20), 1.55)
        self.assertEqual(calculate_tdee.calculate_target_weight_from_bodyfat(85, 20, 15), 80.0)
        timeline = calculate_tdee.estimate_timeline(85, 80, -500, "2026-01-01")
        self.assertTrue(timeline["estimated"])
        self.assertIsNotNone(timeline["target_date"])
        with self.assertRaises(ValueError):
            calculate_tdee.derive_activity_multiplier(8, 0, 0)
        invalid_root = self.make_root()
        profile_path = invalid_root / "data" / "user" / "profile.json"
        profile = json.loads(profile_path.read_text())
        profile["training_days_per_week"] = 4.5
        profile_path.write_text(json.dumps(profile))
        with self.assertRaises(ValueError):
            generate_plan.generate_plan(start_date="2026-01-10", days=1, root=invalid_root)

    def test_body_log_validates_and_preserves_corruption(self):
        with tempfile.TemporaryDirectory() as temporary:
            body_log.BODY_LOG_DIR = Path(temporary)
            with self.assertRaises(ValueError):
                body_log.log_entry("bodyfat", 101, "%", date_str="2026-01-10")
            with self.assertRaises(ValueError):
                body_log.log_entry("weight", 80, "lb", date_str="2026-01-10")
            path = body_log.log_entry("weight", 80, "kg", date_str="2026-01-10")
            self.assertTrue(path.exists())
            path.write_text("broken", encoding="utf-8")
            with self.assertRaises(ValueError):
                body_log.log_entry("weight", 81, "kg", date_str="2026-01-10")
            self.assertEqual(path.read_text(encoding="utf-8"), "broken")

    def test_sync_paginates_and_merges_local_records(self):
        calls = []
        first_page = [
            {"id": str(index), "datestr": "2026-01-01", "type": "weight", "value": 80, "unit": "kg"}
            for index in range(1000)
        ]
        second_page = [
            {"id": "last", "datestr": "2026-01-02", "type": "weight", "value": 79, "unit": "kg"}
        ]

        def fake_post(endpoint, payload, retry_rate_limit=True):
            calls.append(payload["offset"])
            return {"res": {"records": first_page if payload["offset"] == 0 else second_page}}

        with patch.object(sync_body_data, "_post", side_effect=fake_post):
            records = sync_body_data.query_body_data("2026-01-01", "2026-01-03")
        self.assertEqual(calls, [0, 1000])
        self.assertEqual(len(records), 1001)
        merged = sync_body_data.merge_body_logs(
            [{"date": "2026-01-01", "type": "weight", "value": 79, "unit": "kg", "source": "xunji_api"}],
            [{"date": "2026-01-01", "type": "weight", "value": 80, "unit": "kg", "source": "manual"}],
        )
        self.assertEqual(merged[0]["value"], 79)

    def test_compare_counts_source_and_unit_changes(self):
        result = compare_body_logs.count_diff(
            [{"date": "2026-01-01", "type": "weight", "value": 80, "unit": "kg", "source": "xunji_api", "xunji_id": "1"}],
            [{"date": "2026-01-01", "type": "weight", "value": 80, "unit": "kg", "source": "manual", "xunji_id": None}],
        )
        self.assertEqual(result["changed_count"], 1)


if __name__ == "__main__":
    unittest.main()
