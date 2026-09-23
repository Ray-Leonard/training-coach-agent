#!/usr/bin/env python3
"""Calculate and render a daily nutrition report from the canonical diet record."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

try:  # Support package imports and direct CLI execution.
    from . import diet_log
    from .common import load_profile, today_in_profile_timezone
except ImportError:  # pragma: no cover - exercised by direct CLI use
    import diet_log  # type: ignore
    from common import load_profile, today_in_profile_timezone  # type: ignore


def calculate(
    date_str: Optional[str] = None, *, root: Optional[Path] = None
) -> Dict[str, Any]:
    """Return the validated, script-calculated daily summary."""
    if date_str is None:
        profile = load_profile(root)
        date_str = today_in_profile_timezone(profile).isoformat()
    return diet_log.summarize_day(date_str, root=root)


def _display(value: Any) -> str:
    return "pending" if value is None else str(value)


def render_markdown(summary: Dict[str, Any]) -> str:
    """Render calculated fields without performing nutrition arithmetic."""
    intake = summary["intake"]
    target = summary["target"]
    progress = summary["progress"]
    lines = [
        f"# Daily nutrition — {summary['date']}",
        "",
        f"- Training status: {_display(summary['training_status'])}",
        f"- Calories: {_display(None if intake is None else intake['calories_kcal'])} / "
        f"{_display(target['calories_kcal'])} kcal",
        f"- Calorie target source: {_display(target['calories_source'])}",
    ]
    for label, field in (
        ("Protein", "protein_g"),
        ("Carbs", "carbs_g"),
        ("Fat", "fat_g"),
    ):
        values = progress[field]
        lines.append(
            f"- {label}: {_display(values['actual'])} / {_display(values['target'])} g"
        )
    lines.extend(
        [
            f"- Expenditure: {_display(summary['expenditure_kcal'])} kcal "
            f"({_display(summary['expenditure_source'])})",
            f"- Energy deficit: {_display(summary['energy_deficit_kcal'])} kcal "
            f"({_display(summary['deficit_kind'])})",
            f"- Status: {'complete' if summary['complete'] else 'pending'}",
        ]
    )
    if summary["pending_reasons"]:
        lines.append(f"- Pending reasons: {', '.join(summary['pending_reasons'])}")
    return "\n".join(lines) + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Calculate a daily target-versus-intake nutrition report"
    )
    parser.add_argument("--date", help="local date in YYYY-MM-DD format")
    parser.add_argument("--root", type=Path, help="repository root (testing/advanced use)")
    parser.add_argument("--json", action="store_true", help="print structured JSON")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        summary = calculate(args.date, root=args.root)
        if args.json:
            print(json.dumps(summary, ensure_ascii=False, indent=2))
        else:
            print(render_markdown(summary), end="")
        return 0
    except (FileNotFoundError, ValueError, OSError) as exc:
        print(f"error: {exc}", flush=True)
        return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
