from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


TESTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(TESTS_DIR))
from test_support import TemporaryRepoMixin

ROOT = Path(__file__).resolve().parents[1]
PLAN_SCRIPTS = ROOT / "skills" / "training-planning" / "scripts"
sys.path.insert(0, str(PLAN_SCRIPTS))

import generate_deload  # noqa: E402
import generate_plan  # noqa: E402
import plan_manager  # noqa: E402


def exercise_names(plan: dict) -> list[str]:
    return [
        exercise["exercise"]
        for day in plan["daily_schedule"]
        if day["strength"] is not None
        for exercise in day["strength"]["exercises"]
    ]


def total_sets(plan: dict) -> int:
    return sum(
        exercise["sets"]
        for day in plan["daily_schedule"]
        if day["strength"] is not None
        for exercise in day["strength"]["exercises"]
    )


class TrainingPlanningTestCase(TemporaryRepoMixin, unittest.TestCase):
    def test_generate_proposal_recommends_split_and_preserves_profile(self) -> None:
        root = self.make_root()
        profile_path = root / "data" / "user" / "profile.json"
        before = profile_path.read_bytes()
        plan = generate_plan.generate_plan(
            start_date="2026-01-10", days=10, root=root
        )
        self.assertEqual(plan["status"], "proposed")
        self.assertEqual(plan["plan_type"], "standard")
        self.assertFalse(plan["confirmation"]["confirmed"])
        self.assertEqual(plan["split"]["name"], "upper-lower")
        self.assertTrue(plan["split"]["recommended_by_generator"])
        self.assertEqual(len(plan["daily_schedule"]), 10)
        self.assertTrue(
            all(day["user_confirmation_required"] for day in plan["daily_schedule"])
        )
        path = generate_plan.save_plan(plan, root=root)
        self.assertTrue(path.is_relative_to(root / "data" / "training-plans"))
        self.assertEqual(profile_path.read_bytes(), before)
        self.assertNotIn("training_split", json.loads(before))
        self.assertFalse((root / "data" / "diet").exists())
        self.assertFalse((root / "data" / "training").exists())
        with self.assertRaisesRegex(ValueError, "data/training-plans"):
            generate_plan.save_plan(
                plan, root=root, output=str(root / "outside.json")
            )

    def test_plan_manager_requires_explicit_confirmation_and_safe_paths(self) -> None:
        root = self.make_root()
        plan = generate_plan.generate_plan(
            start_date="2026-01-10", days=7, split="full-body", root=root
        )
        path = generate_plan.save_plan(plan, root=root)
        self.assertEqual(plan_manager.list_plans(root=root), [path.name])
        self.assertEqual(plan_manager.load_plan(path.name, root=root)["status"], "proposed")
        with self.assertRaisesRegex(ValueError, "explicit user confirmation"):
            plan_manager.confirm_plan(path.name, root=root)
        confirmed_path = plan_manager.confirm_plan(
            path.name, confirmed=True, root=root
        )
        confirmed = plan_manager.load_plan(confirmed_path.name, root=root)
        self.assertEqual(confirmed["status"], "confirmed")
        self.assertTrue(confirmed["confirmation"]["confirmed"])
        self.assertEqual(confirmed["confirmation"]["source"], "user")
        with self.assertRaisesRegex(ValueError, "data/training-plans"):
            plan_manager.load_plan("../profile.json", root=root)

    def test_deload_is_separate_proposal_with_reduced_sets_and_same_movements(self) -> None:
        root = self.make_root()
        profile_path = root / "data" / "user" / "profile.json"
        before = profile_path.read_bytes()
        source = generate_plan.generate_plan(
            start_date="2026-01-10", days=7, split="upper-lower", root=root
        )
        source_path = generate_plan.save_plan(source, root=root)

        deload = generate_deload.generate_deload(source_path.name, root=root)
        self.assertEqual(deload["status"], "proposed")
        self.assertEqual(deload["plan_type"], "deload")
        self.assertFalse(deload["confirmation"]["confirmed"])
        self.assertEqual(deload["deload"]["source_plan_id"], source["id"])
        self.assertEqual(exercise_names(deload), exercise_names(source))
        reduction = (1 - total_sets(deload) / total_sets(source)) * 100
        self.assertGreaterEqual(reduction, 40)
        self.assertLessEqual(reduction, 50)
        self.assertEqual(deload["deload"]["volume_reduction_percent"], round(reduction, 2))

        deload_path = generate_deload.save_deload(deload, root=root)
        self.assertNotEqual(deload_path, source_path)
        self.assertTrue(deload_path.is_relative_to(root / "data" / "training-plans"))
        self.assertEqual(profile_path.read_bytes(), before)

    def test_plan_loading_rejects_corruption_invalid_date_and_timezone(self) -> None:
        root = self.make_root()
        directory = root / "data" / "training-plans"
        directory.mkdir(parents=True)
        corrupt = directory / "corrupt.json"
        corrupt.write_text("{broken", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "corrupted"):
            plan_manager.load_plan(corrupt.name, root=root)
        self.assertEqual(corrupt.read_text(encoding="utf-8"), "{broken")

        with self.assertRaisesRegex(ValueError, "YYYY-MM-DD"):
            generate_plan.generate_plan(
                start_date="2026-02-30", days=7, root=root
            )
        plan = generate_plan.generate_plan(
            start_date="2026-01-10", days=7, root=root
        )
        plan["timezone"] = "Not/IANA"
        invalid = directory / "invalid-timezone.json"
        invalid.write_text(json.dumps(plan), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Unknown IANA timezone"):
            plan_manager.load_plan(invalid.name, root=root)

    def test_ppl_rotation_continues_across_week_boundaries(self) -> None:
        root = self.make_root({"training_days_per_week": 3})
        plan = generate_plan.generate_plan(
            start_date="2026-01-05", days=14, split="ppl", root=root
        )
        session_names = [
            day["strength"]["name"]
            for day in plan["daily_schedule"]
            if day["strength"] is not None
        ]
        self.assertEqual(
            session_names,
            ["Push", "Pull", "Legs", "Upper", "Push", "Pull"],
        )

    def test_deload_validation_rejects_out_of_range_reduction(self) -> None:
        root = self.make_root()
        source = generate_plan.generate_plan(
            start_date="2026-01-10", days=7, root=root
        )
        source_path = generate_plan.save_plan(source, root=root)
        deload = generate_deload.generate_deload(source_path.name, root=root)
        deload["deload"]["volume_reduction_percent"] = 5
        with self.assertRaisesRegex(ValueError, "40 and 50"):
            plan_manager.validate_plan(deload)


if __name__ == "__main__":
    unittest.main()
