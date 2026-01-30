#!/usr/bin/env python3
import csv
import json
import re
import sys

HEADERS = {
    "title": "Paper Title",
    "year": "Year Published",
    "date_started": "Date of starting reading",
    "status": "Current Reading Status",
    "tags": "Tags/Keys (separate by comma)",
    "clarity": "Rate the Clarity and Quality of the Paper",
    "relevance": "How relevant is this paper to your current research/work?",
    "main_finding": "Summarize the main finding or conclusion (each start with a hyphen)",
    "interesting": "Interesting points (each start with a hyphen)",
}

def norm_tags(s: str):
    if not s:
        return []
    return [t.strip() for t in s.split(",") if t.strip()]

def safe_int(x):
    try:
        return int(str(x).strip())
    except:
        return None

def split_hyphen_lines(s: str):
    """
    Your sheet uses: each bullet starts with a hyphen.
    We accept:
      - one bullet per line starting with '-'
      - or paragraphs containing '- ' bullets
    Returns list[str] without the hyphen prefix.
    """
    if not s:
        return []

    # Normalize newlines
    s = str(s).replace("\r\n", "\n").replace("\r", "\n").strip()
    if not s:
        return []

    lines = []
    for raw in s.split("\n"):
        raw = raw.strip()
        if not raw:
            continue

        # If user followed rule: "- something"
        m = re.match(r"^\-\s*(.+)$", raw)
        if m:
            lines.append(m.group(1).strip())
        else:
            # If no leading '-', keep it as a single line note
            lines.append(raw)

    # Remove empties
    return [ln for ln in lines if ln]

def pick(row, header):
    # CSV headers must match exactly; but we also strip whitespace just in case.
    # We'll create a lookup that is whitespace-tolerant.
    return row.get(header, "")

def make_id(title: str, year):
    base = (title or "").strip().lower()
    base = re.sub(r"[^a-z0-9]+", "-", base).strip("-")
    if year:
        return f"{base[:80]}-{year}"
    return base[:80] or None

def parse_likert(x):
    # Keeps as string; later you can map to numeric if you want.
    # Handles empty cells safely.
    s = str(x).strip()
    return s if s else ""

inp, outp = sys.argv[1], sys.argv[2]

items = []
with open(inp, newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)

    # Build a whitespace-normalized header map once
    fieldnames = reader.fieldnames or []
    normalized = { (h or "").strip(): h for h in fieldnames }

    def get(row, wanted):
        key = wanted.strip()
        real = normalized.get(key, wanted)
        return (row.get(real) or "").strip()

    for i, row in enumerate(reader, start=1):
        title = get(row, HEADERS["title"])
        year = safe_int(get(row, HEADERS["year"]))

        status = get(row, HEADERS["status"])
        tags = norm_tags(get(row, HEADERS["tags"]))

        main_finding = split_hyphen_lines(get(row, HEADERS["main_finding"]))
        interesting = split_hyphen_lines(get(row, HEADERS["interesting"]))

        # Create stable-ish ID (good for future linking)
        pid = make_id(title, year) or f"paper-{i}"

        items.append({
            "id": pid,
            "title": title,
            "year_published": year,
            "date_started": get(row, HEADERS["date_started"]),
            "status": status,
            "tags": tags,
            "clarity_quality": parse_likert(get(row, HEADERS["clarity"])),
            "relevance": parse_likert(get(row, HEADERS["relevance"])),
            "main_finding": main_finding,
            "interesting_points": interesting,
        })

# Default sorting suggestion: newest started reading first (string sort fallback)
# We'll keep raw order as Sheet order; UI can sort later.

with open(outp, "w", encoding="utf-8") as f:
    json.dump(items, f, ensure_ascii=False, indent=2)
