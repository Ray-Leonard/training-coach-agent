from __future__ import annotations

import gzip
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
DIET_SCRIPTS = ROOT / "skills" / "diet-tracker" / "scripts"
sys.path.insert(0, str(DIET_SCRIPTS))

import sync_diet_data  # noqa: E402


class XunjiDietSyncTestCase(unittest.TestCase):
    def test_keys_use_the_repository_variable_names(self) -> None:
        with patch.dict(
            sync_diet_data.os.environ,
            {
                "SYNFIT_DIET_DATA_API_KEY": "diet-key-fixture",
                "SYNFIT_FOOD_SEARCH_API_KEY": "search-key-fixture",
            },
            clear=True,
        ):
            self.assertEqual(sync_diet_data.get_diet_api_key(), "diet-key-fixture")
            self.assertEqual(sync_diet_data.get_food_search_api_key(), "search-key-fixture")

    def test_gzip_json_decoder_accepts_compressed_response(self) -> None:
        payload = {"success": True, "res": {"days": []}}
        compressed = gzip.compress(json.dumps(payload).encode("utf-8"))
        self.assertEqual(sync_diet_data.decode_json_response(compressed), payload)

    def test_compact_food_search_response_is_decoded_without_losing_units(self) -> None:
        response = {
            "success": True,
            "res": {
                "d": [[7, "燕麦", 380, 68, 7, 13, "pic", "key-7", [{"unit": "份", "gram": 40}]]]
            },
        }

        foods = sync_diet_data.normalize_food_search_response(response)

        self.assertEqual(foods[0]["id"], 7)
        self.assertEqual(foods[0]["ntr"]["carb"], 68)
        self.assertEqual(foods[0]["uniquekey"], "key-7")
        self.assertEqual(foods[0]["units"][0]["gram"], 40)

    def test_search_does_not_fall_back_to_the_diet_key(self) -> None:
        with patch.dict(sync_diet_data.os.environ, {"SYNFIT_DIET_DATA_API_KEY": "diet-key-fixture"}, clear=True), patch.object(
            sync_diet_data, "_read_dotenv_value", return_value=None
        ):
            with self.assertRaisesRegex(sync_diet_data.XunjiDietAPIError, r"API key|apikey"):
                sync_diet_data.search_foods("燕麦")

    def test_query_normalization_preserves_official_day_and_food_fields(self) -> None:
        day = {
            "date": "2026-09-20",
            "foods": [
                {
                    "id": 101,
                    "date": "2026-09-20",
                    "meal_type": "lunch",
                    "name": "鸡胸肉",
                    "amount": 150,
                    "unit": "g",
                    "uniquekey": "official-key",
                    "ntr": {"cal": 165, "protein": 31, "fat": 3.6, "carb": 0},
                    "units": [{"unit": "g", "count": "100", "gram": 100}],
                }
            ],
            "server_extra": {"kept": True},
        }
        response = {
            "success": True,
            "res": {
                "schema": "food_open_api",
                "schema_version": "1",
                "days": [day],
            },
        }

        normalized = sync_diet_data.normalize_query_response(response)

        self.assertEqual(len(normalized), 1)
        self.assertEqual(normalized[0]["date"], "2026-09-20")
        self.assertEqual(normalized[0]["source"], "xunji_api")
        self.assertEqual(normalized[0]["raw_day"], day)
        self.assertEqual(normalized[0]["foods"][0]["uniquekey"], "official-key")
        self.assertEqual(normalized[0]["foods"][0]["ntr"]["protein"], 31)
        self.assertEqual(normalized[0]["foods"][0]["units"][0]["gram"], 100)

    def test_empty_query_response_is_a_valid_empty_result(self) -> None:
        response = {"success": True, "res": {"days": []}}
        self.assertEqual(sync_diet_data.normalize_query_response(response), [])

    def test_write_payload_requires_explicit_confirmation(self) -> None:
        foods = [
            {
                "date": "2026-09-20",
                "meal_type": "lunch",
                "name": "鸡胸肉",
                "amount": 150,
                "unit": "g",
                "uniquekey": "official-key",
                "ntr": {"cal": 165, "protein": 31, "fat": 3.6, "carb": 0},
            }
        ]
        with self.assertRaises(sync_diet_data.UserConfirmationRequired):
            sync_diet_data.build_food_upsert_payload(
                foods, client_request_id="request-1", confirmed=False
            )

        payload = sync_diet_data.build_food_upsert_payload(
            foods, client_request_id="request-1", confirmed=True
        )
        self.assertEqual(payload["client_request_id"], "request-1")
        self.assertFalse(payload["dry_run"])
        self.assertEqual(payload["foods"], foods)

    def test_query_response_rejects_a_partial_food_record(self) -> None:
        response = {
            "success": True,
            "res": {
                "days": [
                    {
                        "date": "2026-09-20",
                        "foods": [{"name": "incomplete"}],
                    }
                ]
            },
        }
        with self.assertRaisesRegex(ValueError, "food record"):
            sync_diet_data.normalize_query_response(response)

    def test_cache_preserves_the_lossless_raw_day(self) -> None:
        day = {
            "date": "2026-09-20",
            "source": "xunji_api",
            "foods": [],
            "raw_day": {"date": "2026-09-20", "server_extra": {"kept": True}},
        }
        with tempfile.TemporaryDirectory() as directory:
            paths = sync_diet_data.cache_days([day], root=Path(directory))
            cached = json.loads(paths[0].read_text(encoding="utf-8"))

        self.assertEqual(cached["raw_day"], day["raw_day"])

    def test_exact_query_cache_round_trip_and_date_invalidation(self) -> None:
        days = [
            {
                "date": "2026-09-20",
                "source": "xunji_api",
                "foods": [],
                "raw_day": {"date": "2026-09-20"},
            }
        ]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sync_diet_data.cache_query_result(
                "2026-09-20", "2026-09-20", True, days, root=root
            )
            self.assertEqual(
                sync_diet_data.load_cached_query("2026-09-20", "2026-09-20", root=root),
                days,
            )
            sync_diet_data.invalidate_query_cache(root=root, dates=["2026-09-21"])
            self.assertIsNotNone(
                sync_diet_data.load_cached_query("2026-09-20", "2026-09-20", root=root)
            )
            sync_diet_data.invalidate_query_cache(root=root, dates=["2026-09-20"])
            self.assertIsNone(
                sync_diet_data.load_cached_query("2026-09-20", "2026-09-20", root=root)
            )


if __name__ == "__main__":
    unittest.main()
