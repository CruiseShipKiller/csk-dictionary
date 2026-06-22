#!/usr/bin/env python3
"""
build.py — Cruise Dictionary build script

Converts the source CSV into dictionary.json, which the app loads at runtime.

Usage:
    python3 build.py [input.csv] [output.json]

Defaults:
    input  = cruise_dictionary_complete.csv
    output = dictionary.json

CSV columns (header row required): term, def, context, type, cat
  - context is optional per row (leave blank if none)
  - type must be one of: passenger, crew, nautical
  - cat must match a category name in CATEGORIES below

The output JSON has the shape:
    {
      "version": "<ISO timestamp>",
      "categories": [ {"name": "...", "icon": "..."}, ... ],
      "entries":    [ {"term","def","context","type","cat"}, ... ]
    }
Category ORDER in the JSON is the display order in the app.
"""

import csv, json, sys, datetime

# ── Category order + icons. Edit here to add/reorder categories. ──
CATEGORIES = [
    ("Behavior & Archetypes",      "🏊"),
    ("Cabin & Stateroom",          "🛏"),
    ("Dining",                     "🍽"),
    ("Embarkation & Itinerary",    "⚓"),
    ("Onboard Account & Cards",    "💳"),
    ("Loyalty & Casino",           "🎰"),
    ("Crew Jargon",                "🪪"),
    ("Codes & Signals",            "📡"),
    ("Ship Anatomy",               "🚢"),
    ("Abbreviations & Forum Speak","💬"),
    ("Private Islands",            "🏝"),
    ("Sea Conditions & Motion",    "🌊"),
    ("Social Rituals & Events",    "🎉"),
]

VALID_TYPES = {"passenger", "crew", "nautical"}

def build(input_csv, output_json):
    valid_cats = {name for name, _ in CATEGORIES}
    entries = []
    errors = []

    with open(input_csv, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        required = {"term", "def", "type", "cat"}
        missing_cols = required - set(reader.fieldnames or [])
        if missing_cols:
            sys.exit(f"ERROR: CSV missing required columns: {', '.join(sorted(missing_cols))}")

        for i, row in enumerate(reader, start=2):  # row 2 = first data row
            term = (row.get("term") or "").strip()
            definition = (row.get("def") or "").strip()
            context = (row.get("context") or "").strip()
            etype = (row.get("type") or "").strip().lower()
            cat = (row.get("cat") or "").strip()

            if not term:
                errors.append(f"row {i}: empty term")
                continue
            if not definition:
                errors.append(f"row {i}: '{term}' has empty definition")
            if etype not in VALID_TYPES:
                errors.append(f"row {i}: '{term}' has invalid type '{etype}' (must be passenger/crew/nautical)")
            if cat not in valid_cats:
                errors.append(f"row {i}: '{term}' has unknown category '{cat}'")

            entry = {"term": term, "def": definition, "type": etype, "cat": cat}
            if context:
                entry["context"] = context
            entries.append(entry)

    # Duplicate term check
    seen = {}
    for e in entries:
        seen.setdefault(e["term"], 0)
        seen[e["term"]] += 1
    dupes = [t for t, c in seen.items() if c > 1]
    if dupes:
        errors.append("duplicate terms: " + ", ".join(dupes))

    if errors:
        print("BUILD FAILED — fix these issues:\n")
        for e in errors:
            print("  -", e)
        sys.exit(1)

    output = {
        "version": datetime.datetime.now().isoformat(timespec="seconds"),
        "categories": [{"name": name, "icon": icon} for name, icon in CATEGORIES],
        "entries": entries,
    }

    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    # Summary
    from collections import Counter
    by_cat = Counter(e["cat"] for e in entries)
    by_type = Counter(e["type"] for e in entries)
    print(f"BUILD OK → {output_json}")
    print(f"  {len(entries)} entries across {len(CATEGORIES)} categories")
    print(f"  by type: " + ", ".join(f"{t}={n}" for t, n in sorted(by_type.items())))
    print()
    for name, _ in CATEGORIES:
        print(f"  {by_cat.get(name,0):3d}  {name}")
    # Warn about empty categories
    empty = [name for name, _ in CATEGORIES if by_cat.get(name, 0) == 0]
    if empty:
        print("\n  NOTE: empty categories (no entries):", ", ".join(empty))

if __name__ == "__main__":
    inp = sys.argv[1] if len(sys.argv) > 1 else "cruise_dictionary_complete.csv"
    out = sys.argv[2] if len(sys.argv) > 2 else "dictionary.json"
    build(inp, out)
