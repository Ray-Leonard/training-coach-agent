#!/usr/bin/env python3
"""Deterministic volume, estimated-1RM, frequency, and PR analysis."""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:  # Support package imports and direct CLI execution.
    from . import workout_log
except ImportError:  # pragma: no cover - exercised by direct CLI use
    import workout_log  # type: ignore


def estimated_one_rep_max(weight_kg: float, reps: int) -> Optional[float]:
    """Return Epley estimated 1RM for weighted sets of 1-12 repetitions."""
    if weight_kg <= 0 or reps < 1 or reps > 12:
        return None
    return round(weight_kg * (1 + reps / 30), 2)


def _historical_bests(
    current_date: str, *, root: Optional[Path] = None
) -> Dict[str, float]:
    target = date.fromisoformat(current_date)
    bests: Dict[str, float] = {}
    for date_str in workout_log.list_sessions(root=root):
        if date.fromisoformat(date_str) >= target:
            continue
        session = workout_log.load_session(date_str, root=root)
        for exercise in session["exercises"]:
            key = exercise["name"].casefold()
            for set_record in exercise["sets"]:
                estimate = estimated_one_rep_max(
                    set_record["weight_kg"], set_record["reps"]
                )
                if estimate is not None and estimate > bests.get(key, 0.0):
                    bests[key] = estimate
    return bests


def analyze_session(
    date_str: str,
    *,
    root: Optional[Path] = None,
    lookback_days: int = 28,
) -> Dict[str, Any]:
    if not isinstance(lookback_days, int) or isinstance(lookback_days, bool) or lookback_days < 1:
        raise ValueError("lookback_days must be a positive integer")
    session = workout_log.load_session(date_str, root=root)
    historical = _historical_bests(session["date"], root=root)
    exercise_results: List[Dict[str, Any]] = []
    all_rpe: List[float] = []
    session_volume = 0.0
    for exercise in session["exercises"]:
        volume = 0.0
        estimates: List[float] = []
        for set_record in exercise["sets"]:
            volume += set_record["weight_kg"] * set_record["reps"]
            estimate = estimated_one_rep_max(
                set_record["weight_kg"], set_record["reps"]
            )
            if estimate is not None:
                estimates.append(estimate)
            if set_record.get("rpe") is not None:
                all_rpe.append(set_record["rpe"])
        volume = round(volume, 2)
        session_volume += volume
        best_estimate = max(estimates) if estimates else None
        historical_best = historical.get(exercise["name"].casefold())
        is_pr = bool(
            best_estimate is not None
            and historical_best is not None
            and best_estimate > historical_best
        )
        exercise_results.append(
            {
                "name": exercise["name"],
                "volume_kg_reps": volume,
                "estimated_1rm_kg": best_estimate,
                "historical_best_estimated_1rm_kg": historical_best,
                "is_pr": is_pr,
                "pr_status": "pr" if is_pr else ("baseline" if historical_best is None else "no_pr"),
            }
        )

    target_date = date.fromisoformat(session["date"])
    first_date = target_date - timedelta(days=lookback_days - 1)
    recent_count = sum(
        1
        for item in workout_log.list_sessions(root=root)
        if first_date <= date.fromisoformat(item) <= target_date
    )
    average_rpe = (
        round(sum(all_rpe) / len(all_rpe), 2) if all_rpe else None
    )
    return {
        "schema_version": "1.0",
        "date": session["date"],
        "timezone": session["timezone"],
        "title": session["title"],
        "source": session["source"],
        "session_volume_kg_reps": round(session_volume, 2),
        "average_rpe": average_rpe,
        "recent_frequency": {
            "lookback_days": lookback_days,
            "confirmed_sessions": recent_count,
            "sessions_per_week": round(recent_count / (lookback_days / 7), 2),
        },
        "exercises": exercise_results,
    }


def render_markdown(analysis: Dict[str, Any]) -> str:
    frequency = analysis["recent_frequency"]
    lines = [
        f"# Training analysis — {analysis['date']}",
        "",
        f"- Session: {analysis['title']}",
        f"- Session volume: {analysis['session_volume_kg_reps']} kg-reps",
        f"- Average RPE: {analysis['average_rpe'] if analysis['average_rpe'] is not None else 'not recorded'}",
        f"- Recent frequency: {frequency['confirmed_sessions']} confirmed sessions / "
        f"{frequency['lookback_days']} days ({frequency['sessions_per_week']} per week)",
        "",
        "## Exercises",
        "",
    ]
    for exercise in analysis["exercises"]:
        pr_label = " — PR" if exercise["is_pr"] else ""
        estimate = (
            f"{exercise['estimated_1rm_kg']} kg"
            if exercise["estimated_1rm_kg"] is not None
            else "not applicable"
        )
        lines.append(
            f"- {exercise['name']}: volume {exercise['volume_kg_reps']} kg-reps; "
            f"estimated 1RM {estimate}{pr_label}"
        )
    return "\n".join(lines) + "\n"


def report_path(date_str: str, *, root: Optional[Path] = None) -> Path:
    normalized = workout_log.parse_date(date_str)
    return workout_log.training_root(root) / f"{normalized}-analyze.md"


def write_report(analysis: Dict[str, Any], *, root: Optional[Path] = None) -> Path:
    destination = report_path(analysis["date"], root=root)
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(
        prefix=f".{destination.name}.", suffix=".tmp", dir=str(destination.parent)
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(render_markdown(analysis))
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(destination)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise
    return destination


def analyze_and_save(
    date_str: str,
    *,
    root: Optional[Path] = None,
    lookback_days: int = 28,
) -> Tuple[Dict[str, Any], Path]:
    analysis = analyze_session(date_str, root=root, lookback_days=lookback_days)
    return analysis, write_report(analysis, root=root)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Analyze a confirmed workout and write its Markdown report"
    )
    parser.add_argument("--date", required=True, help="session date in YYYY-MM-DD format")
    parser.add_argument("--lookback-days", type=int, default=28)
    parser.add_argument("--root", type=Path, help="repository root (testing/advanced use)")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        analysis, path = analyze_and_save(
            args.date, root=args.root, lookback_days=args.lookback_days
        )
        print(
            json.dumps(
                {"saved": str(path), "analysis": analysis},
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0
    except (FileNotFoundError, ValueError, OSError) as exc:
        print(f"error: {exc}", flush=True)
        return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
