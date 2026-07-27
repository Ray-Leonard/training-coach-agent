#!/usr/bin/env python3
"""Compare merged body records with the records currently stored locally."""

from __future__ import annotations

from typing import Any, Dict, Iterable, Mapping, Tuple


RecordKey = Tuple[Any, Any]


def _index_records(records: Iterable[Mapping[str, Any]]) -> Dict[RecordKey, Mapping[str, Any]]:
    """Index valid records by their sync identity, with later duplicates winning."""
    indexed: Dict[RecordKey, Mapping[str, Any]] = {}
    for record in records:
        key = (record.get("date") or record.get("datestr"), record.get("type"))
        if all(key):
            indexed[key] = record
    return indexed


def count_diff(
    merged_records: Iterable[Mapping[str, Any]],
    local_records: Iterable[Mapping[str, Any]],
) -> Dict[str, int]:
    """Count new, value-changed, unchanged, and removed body records."""
    merged = _index_records(merged_records)
    local = _index_records(local_records)

    new_count = 0
    changed_count = 0
    unchanged_count = 0
    for key, merged_record in merged.items():
        local_record = local.get(key)
        if local_record is None:
            new_count += 1
        elif merged_record.get("value") != local_record.get("value"):
            changed_count += 1
        else:
            unchanged_count += 1

    return {
        "new_count": new_count,
        "changed_count": changed_count,
        "unchanged_count": unchanged_count,
        "removed_count": len(local.keys() - merged.keys()),
    }


def format_summary(diff_result: Mapping[str, int]) -> str:
    """Return a concise human-readable summary of body-log differences."""
    summary = (
        f"Found {diff_result.get('new_count', 0)} new records, "
        f"{diff_result.get('changed_count', 0)} changed, "
        f"{diff_result.get('unchanged_count', 0)} unchanged"
    )
    removed_count = diff_result.get("removed_count", 0)
    if removed_count:
        summary += f", {removed_count} removed"
    return summary


__all__ = ["count_diff", "format_summary"]


if __name__ == "__main__":
    import argparse, json, sys

    p = argparse.ArgumentParser(description="Compare two body-log JSON files")
    p.add_argument("merged", help="Path to merged records JSON")
    p.add_argument("local", help="Path to local records JSON")

    args = p.parse_args()
    with open(args.merged) as f:
        merged = json.load(f)
    with open(args.local) as f:
        local = json.load(f)

    result = count_diff(merged, local)
    print(format_summary(result))
