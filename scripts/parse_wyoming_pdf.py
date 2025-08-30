"""
Parse "FOOD-STORAGE-TIMES-.pdf" (Wyoming Health) into app/data/foodkeeper.json.

Heuristics:
- Extract tables via pdfplumber; look for columns resembling Item/Food and Refrigerator/Fridge and Freezer/Pantry.
- Normalize durations to readable strings (e.g., "3-5 days").
- Output schema: { "items": [ { "name": str, "shelf_life": { "pantry": str, "fridge": str, "freezer": str } } ] }

Run:
  python scripts/parse_wyoming_pdf.py --pdf ../../FOOD-STORAGE-TIMES-.pdf --out app/data/foodkeeper.json
"""

from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import sys
from typing import Dict, List, Optional

import pdfplumber  # type: ignore


def norm_cell(s: Optional[str]) -> str:
    if s is None:
        return ""
    s = re.sub(r"\s+", " ", s.strip())
    return s


def pick_duration(s: str) -> str:
    if not s:
        return ""
    low = s.lower()
    if any(w in low for w in ["not recommended", "do not", "don't"]):
        return "Not recommended"
    # Examples: 3-5 days, 1 week, 2-3 months, 1-2 wks
    # Normalize common abbreviations
    low = low.replace("wks", "weeks").replace("wk", "week").replace("mos", "months").replace("mo", "month").replace("hrs", "hours").replace("hr", "hour")
    # Keep only a concise phrase (first clause)
    m = re.search(r"(\d+\s*(?:-|to)\s*\d+\s*(days?|weeks?|months?|hours?)|\d+\s*(days?|weeks?|months?|hours?)|\b\d+-\d+\b\s*(days?|weeks?|months?|hours?))", low)
    if m:
        return m.group(0).replace(" to ", "-").strip()
    # Fallback: keep first 4 words
    return " ".join(low.split()[:4])


def parse_pdf(pdf_path: Path) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            try:
                tables = page.extract_tables()
            except Exception:
                tables = []
            for tbl in tables or []:
                if not tbl or len(tbl) < 2:
                    continue
                # Header detection
                header = [norm_cell(x) for x in tbl[0]]
                cols = [h.lower() for h in header]
                # Identify key columns by fuzzy matching
                def find_col(keys: List[str]) -> int | None:
                    for i, c in enumerate(cols):
                        if any(k in c for k in keys):
                            return i
                    return None

                i_item = find_col(["item", "food", "product"]) or 0
                i_fridge = find_col(["refrigerator", "fridge"])
                i_freezer = find_col(["freezer"])
                i_pantry = find_col(["pantry", "room", "counter", "shelf"])  # optional

                # If there's no fridge and freezer, skip
                if i_fridge is None and i_freezer is None and i_pantry is None:
                    continue

                for r in tbl[1:]:
                    if not any(r):
                        continue
                    item = norm_cell(r[i_item] if i_item < len(r) else "")
                    if not item or len(item) < 2:
                        continue
                    pantry = pick_duration(norm_cell(r[i_pantry])) if i_pantry is not None and i_pantry < len(r) else ""
                    fridge = pick_duration(norm_cell(r[i_fridge])) if i_fridge is not None and i_fridge < len(r) else ""
                    freezer = pick_duration(norm_cell(r[i_freezer])) if i_freezer is not None and i_freezer < len(r) else ""

                    # Ignore rows with no durations at all
                    if not any([pantry, fridge, freezer]):
                        continue
                    rows.append({
                        "name": item,
                        "pantry": pantry or "",
                        "fridge": fridge or "",
                        "freezer": freezer or "",
                    })
    return rows


def to_foodkeeper_schema(rows: List[Dict[str, str]]) -> Dict[str, List[Dict[str, object]]]:
    items = []
    seen = set()
    for r in rows:
        name = r["name"].strip()
        key = name.lower()
        if key in seen:
            continue
        seen.add(key)
        items.append({
            "name": name,
            "shelf_life": {
                "pantry": r.get("pantry") or "",
                "fridge": r.get("fridge") or "",
                "freezer": r.get("freezer") or "",
            }
        })
    return {"items": items}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", type=str, required=True, help="Path to FOOD-STORAGE-TIMES-.pdf")
    ap.add_argument("--out", type=str, default="app/data/foodkeeper.json", help="Output JSON path")
    args = ap.parse_args()

    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        print(f"PDF not found: {pdf_path}", file=sys.stderr)
        return 2

    rows = parse_pdf(pdf_path)
    data = to_foodkeeper_schema(rows)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Wrote {len(data['items'])} items to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
