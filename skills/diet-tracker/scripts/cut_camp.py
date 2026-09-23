#!/usr/bin/env python3
"""Configurable multi-day diet-deficit camp management."""

from __future__ import annotations

import argparse
import json
import re
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from .common import (
        atomic_write_json,
        finite_number,
        iso_timestamp,
        load_profile,
        load_json_object,
        parse_iso_date,
        profile_timezone,
        repo_root,
        today_in_profile_timezone,
    )
    from .diet_log import summarize_day
except ImportError:  # pragma: no cover - exercised by direct CLI execution
    from common import (  # type: ignore
        atomic_write_json,
        finite_number,
        iso_timestamp,
        load_profile,
        load_json_object,
        parse_iso_date,
        profile_timezone,
        repo_root,
        today_in_profile_timezone,
    )
    from diet_log import summarize_day  # type: ignore


CAMP_DIR_NAME = "camps"
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*$")


def camp_dir(root: Optional[Path] = None) -> Path:
    return repo_root(root) / "data" / "diet" / CAMP_DIR_NAME


def _safe_slug(slug: str) -> str:
    if not isinstance(slug, str) or not SLUG_RE.fullmatch(slug):
        raise ValueError("slug may contain only lowercase letters, digits, '.', '_' and '-'")
    return slug


def camp_path(reference: str, *, root: Optional[Path] = None) -> Path:
    root_path = repo_root(root)
    directory = camp_dir(root_path).resolve()
    candidate = Path(reference).expanduser()
    if not candidate.is_absolute():
        candidate = directory / candidate
    candidate = candidate.resolve()
    if candidate.parent != directory:
        raise ValueError("camp path must be directly inside data/diet/camps")
    if candidate.suffix != ".json":
        candidate = candidate.with_suffix(".json")
    return candidate


def _target_intake(tdee: float, target_deficit: float) -> int:
    intake = round(tdee - target_deficit)
    if intake <= 0:
        raise ValueError("target deficit leaves no positive target intake")
    return intake


def _empty_entry(day: date) -> Dict[str, Any]:
    return {
        "date": day.isoformat(),
        "status": "pending",
        "training_status": None,
        "actual_intake_kcal": None,
        "expenditure_kcal": None,
        "expenditure_source": None,
        "actual_deficit_kcal": None,
        "difference_from_target_kcal": None,
        "pending_reasons": ["training_confirmation", "intake"],
    }


def validate_camp(camp: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(camp, dict):
        raise ValueError("camp must be a JSON object")
    required = {
        "schema_version",
        "id",
        "start_date",
        "end_date",
        "days",
        "target_daily_deficit_kcal",
        "baseline_tdee_kcal",
        "target_intake_kcal",
        "timezone",
        "entries",
    }
    missing = required - set(camp)
    if missing:
        raise ValueError(f"camp is missing fields: {', '.join(sorted(missing))}")
    start = date.fromisoformat(parse_iso_date(camp["start_date"], "start_date"))
    end = date.fromisoformat(parse_iso_date(camp["end_date"], "end_date"))
    days = int(camp["days"])
    if days < 1 or days > 31 or end != start + timedelta(days=days - 1):
        raise ValueError("camp date range and days are inconsistent")
    finite_number(camp["target_daily_deficit_kcal"], "target_daily_deficit_kcal", minimum=0.01)
    finite_number(camp["baseline_tdee_kcal"], "baseline_tdee_kcal", minimum=0.01)
    finite_number(camp["target_intake_kcal"], "target_intake_kcal", minimum=0.01)
    if not isinstance(camp["entries"], list) or len(camp["entries"]) != days:
        raise ValueError("camp entries must contain exactly one entry per camp day")
    expected = [start + timedelta(days=index) for index in range(days)]
    actual = [date.fromisoformat(parse_iso_date(entry.get("date"), "entry.date")) for entry in camp["entries"]]
    if actual != expected:
        raise ValueError("camp entries must be consecutive and match the camp range")
    return camp


def init_camp(
    *,
    start_date: Optional[str] = None,
    days: int = 10,
    target_deficit_kcal: float,
    slug: Optional[str] = None,
    root: Optional[Path] = None,
    force: bool = False,
) -> Path:
    if not isinstance(days, int) or isinstance(days, bool) or not 1 <= days <= 31:
        raise ValueError("days must be an integer between 1 and 31")
    target_deficit = finite_number(
        target_deficit_kcal, "target_daily_deficit_kcal", minimum=0.01
    )
    profile = load_profile(root)
    start = (
        date.fromisoformat(parse_iso_date(start_date, "start_date"))
        if start_date
        else today_in_profile_timezone(profile)
    )
    tdee = finite_number(profile.get("tdee_kcal"), "profile.tdee_kcal", minimum=0.01)
    timezone = profile_timezone(profile)
    camp_slug = _safe_slug(slug or f"{start.isoformat()}-{days}-day-camp")
    destination = camp_path(camp_slug, root=root)
    if destination.exists() and not force:
        raise FileExistsError(f"camp already exists: {destination}; use force to replace it")
    camp = {
        "schema_version": "1.0",
        "id": camp_slug,
        "title": f"{days}-day cut camp",
        "goal": "cut",
        "start_date": start.isoformat(),
        "end_date": (start + timedelta(days=days - 1)).isoformat(),
        "days": days,
        "target_daily_deficit_kcal": round(target_deficit, 2),
        "baseline_tdee_kcal": round(tdee, 2),
        "target_intake_kcal": _target_intake(tdee, target_deficit),
        "timezone": timezone,
        "created_at": iso_timestamp(profile),
        "updated_at": iso_timestamp(profile),
        "entries": [_empty_entry(start + timedelta(days=index)) for index in range(days)],
    }
    validate_camp(camp)
    return atomic_write_json(destination, camp)


def _load_camp(reference: str, *, root: Optional[Path] = None) -> Dict[str, Any]:
    path = camp_path(reference, root=root)
    camp = load_json_object(path)
    validate_camp(camp)
    return camp


def refresh_camp(reference: str, *, root: Optional[Path] = None) -> Dict[str, Any]:
    root_path = repo_root(root)
    camp = _load_camp(reference, root=root_path)
    for entry in camp["entries"]:
        day_summary = summarize_day(entry["date"], root=root_path)
        entry["training_status"] = (
            day_summary["training_status"]
            if day_summary["training_status_confirmed"]
            else None
        )
        entry["actual_intake_kcal"] = (
            day_summary["intake"]["calories_kcal"] if day_summary["meal_count"] else None
        )
        entry["expenditure_kcal"] = day_summary["expenditure_kcal"]
        entry["expenditure_source"] = day_summary["expenditure_source"]
        if day_summary["complete"]:
            actual = float(day_summary["actual_deficit_kcal"])
            entry["status"] = "complete"
            entry["actual_deficit_kcal"] = round(actual, 2)
            entry["difference_from_target_kcal"] = round(
                actual - float(camp["target_daily_deficit_kcal"]), 2
            )
            entry["pending_reasons"] = []
        else:
            entry["status"] = "pending"
            entry["actual_deficit_kcal"] = None
            entry["difference_from_target_kcal"] = None
            entry["pending_reasons"] = list(day_summary["pending_reasons"])
    profile = load_profile(root_path)
    camp["updated_at"] = iso_timestamp(profile)
    validate_camp(camp)
    atomic_write_json(camp_path(reference, root=root_path), camp)
    return camp


def camp_summary(reference: str, *, root: Optional[Path] = None) -> Dict[str, Any]:
    camp = refresh_camp(reference, root=root)
    complete = [entry for entry in camp["entries"] if entry["status"] == "complete"]
    actual_values = [float(entry["actual_deficit_kcal"]) for entry in complete]
    target = float(camp["target_daily_deficit_kcal"])
    actual_total = round(sum(actual_values), 2)
    target_total = round(target * camp["days"], 2)
    return {
        "id": camp["id"],
        "start_date": camp["start_date"],
        "end_date": camp["end_date"],
        "days": camp["days"],
        "target_daily_deficit_kcal": target,
        "target_total_deficit_kcal": target_total,
        "completed_days": len(complete),
        "pending_days": camp["days"] - len(complete),
        "actual_deficit_total_kcal": actual_total if complete else None,
        "average_actual_deficit_kcal": round(actual_total / len(complete), 2) if complete else None,
        "difference_total_kcal": round(actual_total - target * len(complete), 2) if complete else None,
        "entries": camp["entries"],
    }


def _json_print(payload: Any) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generic multi-day deficit camp manager")
    parser.add_argument("--root", type=Path, help="repository root (testing/advanced use)")
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init")
    init.add_argument("--start")
    init.add_argument("--days", type=int, default=10)
    init.add_argument("--target-deficit", type=float, required=True)
    init.add_argument("--slug")
    init.add_argument("--force", action="store_true")

    for name in ("refresh", "summary"):
        command = sub.add_parser(name)
        command.add_argument("--camp", required=True)
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "init":
            path = init_camp(
                start_date=args.start,
                days=args.days,
                target_deficit_kcal=args.target_deficit,
                slug=args.slug,
                root=args.root,
                force=args.force,
            )
            _json_print({"saved": str(path), "summary": camp_summary(path.name, root=args.root)})
        elif args.command == "refresh":
            _json_print(refresh_camp(args.camp, root=args.root))
        elif args.command == "summary":
            _json_print(camp_summary(args.camp, root=args.root))
        return 0
    except (FileNotFoundError, ValueError, OSError) as exc:
        print(f"error: {exc}", flush=True)
        return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
