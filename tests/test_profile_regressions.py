from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
PROFILE_SCRIPTS = ROOT / "skills" / "user-profile-management" / "scripts"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


body_log = load_module("profile_body_log", PROFILE_SCRIPTS / "body_log.py")
calculate_tdee = load_module("profile_calculate_tdee", PROFILE_SCRIPTS / "calculate_tdee.py")
sync_body_data = load_module("profile_sync_body_data", PROFILE_SCRIPTS / "sync_body_data.py")
compare_body_logs = load_module(
    "profile_compare_body_logs", PROFILE_SCRIPTS / "compare_body_logs.py"
)


class ProfileRegressionTestCase(unittest.TestCase):
    def test_calculation_helpers(self) -> None:
        self.assertEqual(calculate_tdee.derive_activity_multiplier(4, 4, 20), 1.55)
        self.assertEqual(
            calculate_tdee.calculate_target_weight_from_bodyfat(85, 20, 15), 80.0
        )
        timeline = calculate_tdee.estimate_timeline(85, 80, -500, "2026-01-01")
        self.assertTrue(timeline["estimated"])
        self.assertIsNotNone(timeline["target_date"])

    def test_body_log_preserves_corrupt_file(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            body_log.BODY_LOG_DIR = Path(temporary)
            path = body_log.log_entry(
                "weight", 80, "kg", date_str="2026-01-10"
            )
            path.write_text("broken", encoding="utf-8")
            with self.assertRaises(ValueError):
                body_log.log_entry("weight", 81, "kg", date_str="2026-01-10")
            self.assertEqual(path.read_text(encoding="utf-8"), "broken")

    def test_sync_paginates_without_live_api(self) -> None:
        calls = []
        first_page = [
            {
                "id": str(index),
                "datestr": "2026-01-01",
                "type": "weight",
                "value": 80,
                "unit": "kg",
            }
            for index in range(1000)
        ]
        second_page = [
            {
                "id": "last",
                "datestr": "2026-01-02",
                "type": "weight",
                "value": 79,
                "unit": "kg",
            }
        ]

        def fake_post(endpoint, payload, retry_rate_limit=True):
            calls.append(payload["offset"])
            return {
                "res": {
                    "records": first_page if payload["offset"] == 0 else second_page
                }
            }

        with patch.object(sync_body_data, "_post", side_effect=fake_post):
            records = sync_body_data.query_body_data("2026-01-01", "2026-01-03")
        self.assertEqual(calls, [0, 1000])
        self.assertEqual(len(records), 1001)

    def test_compare_detects_source_change(self) -> None:
        result = compare_body_logs.count_diff(
            [
                {
                    "date": "2026-01-01",
                    "type": "weight",
                    "value": 80,
                    "unit": "kg",
                    "source": "xunji_api",
                    "xunji_id": "1",
                }
            ],
            [
                {
                    "date": "2026-01-01",
                    "type": "weight",
                    "value": 80,
                    "unit": "kg",
                    "source": "manual",
                    "xunji_id": None,
                }
            ],
        )
        self.assertEqual(result["changed_count"], 1)


if __name__ == "__main__":
    unittest.main()
