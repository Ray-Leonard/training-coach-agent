#!/usr/bin/env python3
"""Create a separate reduced-volume deload proposal from an existing plan."""

from __future__ import annotations

import argparse
import copy
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo

try:  # Support package imports and direct CLI execution.
    from . import plan_manager
except ImportError:  # pragma: no cover - exercised by direct CLI use
    import plan_manager  # type: ignore


def _strength_exercises(plan: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [
        exercise
        for day in plan["daily_schedule"]
        if day["strength"] is not None
        for exercise in day["strength"]["exercises"]
    ]


def generate_deload(
    source_plan: str, *, root: Optional[Path] = None
) -> Dict[str, Any]:
    source = plan_manager.load_plan(source_plan, root=root)
    if source["plan_type"] == "deload":
        raise ValueError("a deload plan cannot be used as a deload source")
    proposal = copy.deepcopy(source)
    exercises = _strength_exercises(proposal)
    original_sets = [int(exercise["sets"]) for exercise in exercises]
    original_total = sum(original_sets)
    minimum_total = len(exercises)
    target_total = round(original_total * 0.55)
    if original_total == 0 or target_total < minimum_total:
        raise ValueError("source plan has insufficient reducible set volume")

    for exercise in exercises:
        exercise["sets"] = 1
    remaining = target_total - minimum_total
    while remaining:
        made_progress = False
        for exercise, original in zip(exercises, original_sets):
            if remaining == 0:
                break
            if exercise["sets"] < original:
                exercise["sets"] += 1
                remaining -= 1
                made_progress = True
        if not made_progress:
            raise ValueError("unable to reduce source-plan set volume")

    for day in proposal["daily_schedule"]:
        if day["cardio"] is not None:
            day["cardio"]["minutes"] = round(day["cardio"]["minutes"] * 0.55, 2)

    deload_total = sum(exercise["sets"] for exercise in exercises)
    reduction = round((1 - deload_total / original_total) * 100, 2)
    proposal.update(
        {
            "id": f"{source['id']}-deload",
            "title": f"Deload — {source['title']}",
            "plan_type": "deload",
            "status": "proposed",
            "confirmation": {
                "confirmed": False,
                "source": None,
                "confirmed_at": None,
            },
            "generated_at": datetime.now(ZoneInfo(source["timezone"])).isoformat(
                timespec="seconds"
            ),
            "deload": {
                "source_plan_id": source["id"],
                "source_plan_file": plan_manager.resolve_plan_path(
                    source_plan, root=root
                ).name,
                "original_total_sets": original_total,
                "deload_total_sets": deload_total,
                "volume_reduction_percent": reduction,
            },
        }
    )
    safety_notes = proposal.get("safety_notes")
    if not isinstance(safety_notes, list):
        safety_notes = []
        proposal["safety_notes"] = safety_notes
    safety_notes.append(
        "Deload volume is reduced while movements are retained; discuss and confirm the proposal before use."
    )
    return plan_manager.validate_plan(proposal)


def save_deload(
    plan: Dict[str, Any],
    *,
    root: Optional[Path] = None,
    output: Optional[str] = None,
    force: bool = False,
) -> Path:
    plan_manager.validate_plan(plan)
    if plan.get("plan_type") != "deload":
        raise ValueError("save_deload requires a deload plan")
    name = output or f"{plan['start_date']}-{plan['days']}-day-deload-plan.json"
    destination = plan_manager.resolve_plan_path(name, root=root)
    source_name = plan["deload"].get("source_plan_file")
    if source_name and destination == plan_manager.resolve_plan_path(source_name, root=root):
        raise ValueError("a deload must be saved separately from its source plan")
    return plan_manager.save_managed_plan(
        plan, destination.name, root=root, force=force
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a separate 40-50% reduced-volume deload proposal"
    )
    parser.add_argument("--source-plan", required=True)
    parser.add_argument("--output")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--root", type=Path, help="repository root (testing/advanced use)")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        plan = generate_deload(args.source_plan, root=args.root)
        path = save_deload(
            plan, root=args.root, output=args.output, force=args.force
        )
        print(json.dumps({"saved": str(path), "plan": plan}, ensure_ascii=False, indent=2))
        return 0
    except (FileNotFoundError, FileExistsError, ValueError, OSError) as exc:
        print(f"error: {exc}", flush=True)
        return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
