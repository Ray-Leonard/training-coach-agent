import re
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path.cwd()
DATA_DIR = PROJECT_ROOT / "individual_food_data"
MASTER_FILE = PROJECT_ROOT / "NUTRITION_MASTER.md"


def extract_timestamp(filename: str) -> str:
    # Matches YYYYMMDD_HHMMSS prefix (e.g., 20260405_104158)
    match = re.match(r"(\d{8}_\d{6})_(.+)\.md$", filename)
    return match.group(1) if match else ""


def extract_title(content: str) -> str:
    match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    return match.group(1).strip() if match else "Unknown Title"


def strip_h1(content: str) -> str:
    # Remove the first H1 heading line to avoid duplicate titles in the master file
    return re.sub(r"^#\s+.+\n?", "", content, count=1, flags=re.MULTILINE).strip()


def make_anchor(timestamp: str, title: str) -> str:
    # Build a clean, unique anchor from timestamp + title
    raw = f"{timestamp}-{title.lower()}"
    raw = raw.replace(" ", "-")
    # Keep only alphanumeric, hyphens, and underscores
    raw = re.sub(r"[^a-z0-9\-_]", "", raw)
    return raw


def consolidate_nutrition() -> None:
    if not DATA_DIR.exists():
        print(f"Error: Data directory {DATA_DIR} does not exist.")
        return

    md_files = sorted(DATA_DIR.glob("*.md"), key=lambda f: extract_timestamp(f.name))

    if not md_files:
        print("No markdown files found.")
        return

    # ---- Pass 1: collect titles and pre-compute anchors ----
    entries: list[tuple[str, str, str]] = []  # (timestamp, title, anchor)
    for md_file in md_files:
        content = md_file.read_text(encoding="utf-8")
        title = extract_title(content)
        ts = extract_timestamp(md_file.name)
        anchor = make_anchor(ts, title)
        entries.append((ts, title, anchor))

    # ---- Build Table of Contents ----
    toc_lines = ["## 📋 Table of Contents", ""]
    for ts, title, anchor in entries:
        toc_lines.append(f"- [{ts} {title}](#{anchor})")
    toc = "\n".join(toc_lines)

    # ---- Build body sections ----
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    body_parts = [
        "# 🥗 Master Nutritional Database",
        f"> **Last Updated:** {now}",
        "> This file is auto-generated from `individual_food_data/`. Do not edit manually.",
        "",
    ]

    for (ts, title, anchor), md_file in zip(entries, md_files):
        content = md_file.read_text(encoding="utf-8")
        # Use an explicit HTML anchor tag so TOC links are guaranteed to work
        body_parts.append(f'<a name="{anchor}"></a>')
        body_parts.append(f"## {ts} {title}")
        body_parts.append(strip_h1(content))
        body_parts.append("---")

    final_content = toc + "\n\n---\n\n" + "\n\n".join(body_parts)

    MASTER_FILE.write_text(final_content, encoding="utf-8")
    print(f"Successfully consolidated {len(md_files)} files into {MASTER_FILE}")


if __name__ == "__main__":
    consolidate_nutrition()
