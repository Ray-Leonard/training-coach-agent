from __future__ import annotations

import json
import math
import sys
import unittest
from pathlib import Path


TESTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(TESTS_DIR))
from test_support import TemporaryRepoMixin

ROOT = Path(__file__).resolve().parents[1]
TRAINING_SCRIPTS = ROOT / "skills" / "training-analyzer" / "scripts"
sys.path.insert(0, str(TRAINING_SCRIPTS))

import analyze_training  # noqa: E402
import workout_log  # noqa: E402


def session_payload(
    date: str = "2026-01-10", *, source: str = "manual"
) -> dict:
    return {
        "date": date,
        "timezone": "UTC",
        "title": "Strength session",
        "source": source,
        "start_time": f"{date}T10:00:00+00:00",
        "end_time": f"{date}T11:00:00+00:00",
        "exercises": [
            {
                "name": "Back Squat",
                "muscle_groups": ["quadriceps", "glutes"],
                "sets": [
                    {
                        "reps": 5,
                        "weight_kg": 100,
                        "rpe": 8,
                        "rir": 2,
                        "notes": "controlled",
                    },
                    {
                        "reps": 5,
                        "weight_lbs": 220.462,
                        "rpe": 9,
                        "notes": "",
                    },
                ],
            }
        ],
    }


class TrainingAnalyzerTestCase(TemporaryRepoMixin, unittest.TestCase):
    def test_manual_session_requires_explicit_confirmation(self) -> None:
        root = self.make_root()
        with self.assertRaisesRegex(ValueError, "explicit confirmation"):
            workout_log.create_session(session_payload(), root=root)
        self.assertFalse((root / "data" / "training" / "2026-01-10.json").exists())

        path = workout_log.create_session(
            session_payload(), confirmed=True, root=root
        )
        self.assertEqual(path, root / "data" / "training" / "2026-01-10.json")
        saved = workout_log.load_session("2026-01-10", root=root)
        self.assertTrue(saved["confirmation"]["confirmed"])
        self.assertEqual(saved["confirmation"]["source"], "user")
        normalized_set = saved["exercises"][0]["sets"][1]
        self.assertAlmostEqual(normalized_set["weight_kg"], 100.0, places=2)
        self.assertNotIn("weight_lbs", normalized_set)
        self.assertEqual(workout_log.list_sessions(root=root), ["2026-01-10"])

    def test_xunji_source_may_be_confirmed_by_source(self) -> None:
        root = self.make_root()
        path = workout_log.create_session(
            session_payload(source="xunji_api"), root=root
        )
        saved = json.loads(path.read_text(encoding="utf-8"))
        self.assertTrue(saved["confirmation"]["confirmed"])
        self.assertEqual(saved["confirmation"]["source"], "xunji_api")

    def test_loaded_confirmation_source_must_match_record_source(self) -> None:
        root = self.make_root()
        path = workout_log.create_session(
            session_payload(), confirmed=True, root=root
        )
        saved = json.loads(path.read_text(encoding="utf-8"))
        saved["confirmation"]["source"] = "xunji_api"
        path.write_text(json.dumps(saved), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "confirmation source"):
            workout_log.load_session("2026-01-10", root=root)

        saved["confirmation"]["source"] = "user"
        saved.pop("schema_version")
        path.write_text(json.dumps(saved), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "schema_version"):
            workout_log.load_session("2026-01-10", root=root)

    def test_validation_rejects_bad_values_dates_timezone_and_times(self) -> None:
        root = self.make_root()
        cases = []
        bad_reps = session_payload()
        bad_reps["exercises"][0]["sets"][0]["reps"] = 0
        cases.append(bad_reps)
        bad_weight = session_payload()
        bad_weight["exercises"][0]["sets"][0]["weight_kg"] = math.inf
        cases.append(bad_weight)
        bad_rpe = session_payload()
        bad_rpe["exercises"][0]["sets"][0]["rpe"] = 11
        cases.append(bad_rpe)
        bad_rir = session_payload()
        bad_rir["exercises"][0]["sets"][0]["rir"] = -1
        cases.append(bad_rir)
        bad_date = session_payload()
        bad_date["date"] = "2026-02-30"
        cases.append(bad_date)
        bad_timezone = session_payload()
        bad_timezone["timezone"] = "Not/IANA"
        cases.append(bad_timezone)
        naive_time = session_payload()
        naive_time["start_time"] = "2026-01-10T10:00:00"
        cases.append(naive_time)
        reverse_time = session_payload()
        reverse_time["end_time"] = "2026-01-10T09:00:00+00:00"
        cases.append(reverse_time)

        for payload in cases:
            with self.subTest(payload=payload):
                with self.assertRaises(ValueError):
                    workout_log.create_session(
                        payload, confirmed=True, root=root, force=True
                    )

    def test_loaded_session_timezone_must_match_profile(self) -> None:
        root = self.make_root()
        path = workout_log.create_session(
            session_payload(), confirmed=True, root=root
        )
        saved = json.loads(path.read_text(encoding="utf-8"))
        saved["timezone"] = "America/New_York"
        path.write_text(json.dumps(saved), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "does not match profile.timezone"):
            workout_log.load_session("2026-01-10", root=root)

    def test_corrupt_session_is_not_overwritten(self) -> None:
        root = self.make_root()
        path = root / "data" / "training" / "2026-01-10.json"
        path.parent.mkdir(parents=True)
        path.write_text("{broken", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "corrupted"):
            workout_log.load_session("2026-01-10", root=root)
        self.assertEqual(path.read_text(encoding="utf-8"), "{broken")

    def test_analysis_calculates_volume_epley_rpe_frequency_and_pr_report(self) -> None:
        root = self.make_root()
        previous = session_payload("2026-01-03")
        previous["exercises"][0]["sets"] = [
            {"reps": 5, "weight_kg": 90, "rpe": 7, "notes": ""}
        ]
        workout_log.create_session(previous, confirmed=True, root=root)

        current = session_payload("2026-01-10")
        current["exercises"][0]["sets"] = [
            {"reps": 5, "weight_kg": 100, "rpe": 8, "notes": ""},
            {"reps": 3, "weight_kg": 110, "rpe": 9, "notes": ""},
        ]
        current["exercises"].append(
            {
                "name": "Bench Press",
                "muscle_groups": ["chest", "triceps"],
                "sets": [
                    {"reps": 10, "weight_kg": 60, "rpe": 7, "notes": ""}
                ],
            }
        )
        workout_log.create_session(current, confirmed=True, root=root)

        analysis, report_path = analyze_training.analyze_and_save(
            "2026-01-10", root=root
        )
        squat = analysis["exercises"][0]
        bench = analysis["exercises"][1]
        self.assertEqual(squat["volume_kg_reps"], 830.0)
        self.assertEqual(squat["estimated_1rm_kg"], 121.0)
        self.assertEqual(squat["historical_best_estimated_1rm_kg"], 105.0)
        self.assertTrue(squat["is_pr"])
        self.assertFalse(bench["is_pr"])
        self.assertEqual(analysis["session_volume_kg_reps"], 1430.0)
        self.assertEqual(analysis["average_rpe"], 8.0)
        self.assertEqual(analysis["recent_frequency"]["confirmed_sessions"], 2)
        self.assertEqual(analysis["recent_frequency"]["sessions_per_week"], 0.5)
        self.assertEqual(
            report_path,
            root / "data" / "training" / "2026-01-10-analyze.md",
        )
        report = report_path.read_text(encoding="utf-8")
        self.assertIn("1430.0", report)
        self.assertIn("PR", report)


if __name__ == "__main__":
    unittest.main()
