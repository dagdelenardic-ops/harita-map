#!/usr/bin/env python3
"""
Import events from a CSV into data/events.json.

CSV columns (expected):
- country, decade, year, title, category, description

Behavior:
- Map country names to canonical Turkish names using data/country_mappings.json.
- Map category labels (Turkish) to internal category keys.
- Merge by (country_name, year, normalized title):
  - If exists: only update description when incoming is meaningfully longer.
  - If missing: append a new event with deterministic id.
- Fill coords from existing events for that country; otherwise fall back to a country center.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple


BASE_DIR = Path(__file__).resolve().parent.parent
EVENTS_PATH = BASE_DIR / "data" / "events.json"
COUNTRY_MAPPINGS_PATH = BASE_DIR / "data" / "country_mappings.json"


TR_TRANSLATE = str.maketrans(
    {
        "ı": "i",
        "İ": "i",
        "ş": "s",
        "Ş": "s",
        "ğ": "g",
        "Ğ": "g",
        "ü": "u",
        "Ü": "u",
        "ö": "o",
        "Ö": "o",
        "ç": "c",
        "Ç": "c",
        "â": "a",
        "Â": "a",
        "î": "i",
        "Î": "i",
        "û": "u",
        "Û": "u",
        # punctuation variants
        "’": "'",
        "‘": "'",
        "–": "-",
        "—": "-",
    }
)


def norm_key(value: str) -> str:
    s = (value or "").strip().translate(TR_TRANSLATE).lower()
    s = re.sub(r"\s+", " ", s)
    return s


def load_country_lookup() -> Tuple[Dict[str, str], Dict[str, str]]:
    """
    Returns:
    - lookup: normalized string -> canonical Turkish country name
    - iso2: canonical Turkish country name -> ISO2
    """
    data = json.loads(COUNTRY_MAPPINGS_PATH.read_text(encoding="utf-8"))
    countries = data.get("countries") or []
    lookup: Dict[str, str] = {}
    iso2: Dict[str, str] = {}

    for c in countries:
        tr = (c.get("turkish") or "").strip()
        en = (c.get("english") or "").strip()
        code = (c.get("iso2") or "").strip().upper()
        if tr:
            iso2[tr] = code
            lookup.setdefault(norm_key(tr), tr)
        if en and tr:
            lookup.setdefault(norm_key(en), tr)
        for a in (c.get("aliases") or []):
            if a and tr:
                lookup.setdefault(norm_key(a), tr)

    return lookup, iso2


def map_category(raw: str) -> str:
    s = norm_key(raw)
    # strip separators
    s = s.replace("&", " ").replace("/", " ")
    if "savas" in s or "çatış" in s or "catis" in s:
        return "war"
    if "soyk" in s:
        return "genocide"
    if "devrim" in s or "rejim" in s or "darbe" in s:
        return "revolution"
    if "ter" in s:
        return "terror"
    if "diplom" in s or "nato" in s or "bm" in s or "birlesmis" in s:
        return "diplomacy"
    if "lider" in s:
        return "leader"
    if "polit" in s or "ekonomi" in s:
        return "politics"
    if "kultur" in s or "toplum" in s:
        return "culture"
    return "culture"


def decade_from_year(year: int) -> str:
    return f"{(year // 10) * 10}s"


def event_id(country_tr: str, year: int, title: str) -> str:
    h = hashlib.md5(f"{country_tr}|{year}|{norm_key(title)}".encode("utf-8")).hexdigest()[:10]
    return f"ev_csv_{h}"


def build_coords_index(events: List[Dict[str, Any]]) -> Dict[str, Tuple[float, float]]:
    coords: Dict[str, Tuple[float, float]] = {}
    for e in events:
        cn = (e.get("country_name") or "").strip()
        if not cn or cn in coords:
            continue
        try:
            lat = float(e.get("lat") or 0)
            lon = float(e.get("lon") or 0)
        except Exception:
            continue
        if lat == 0 and lon == 0:
            continue
        coords[cn] = (lat, lon)
    return coords


FALLBACK_CENTERS: Dict[str, Tuple[float, float]] = {
    "Hindistan": (20.5937, 78.9629),
    "Afganistan": (33.9391, 67.7100),
    "Nepal": (28.3949, 84.1240),
    "Bangladeş": (23.6850, 90.3563),
    "İtalya": (41.8719, 12.5674),
    "İsviçre": (46.8182, 8.2275),
}


def maybe_update_description(target: Dict[str, Any], incoming_desc: str) -> bool:
    inc = (incoming_desc or "").strip()
    if not inc:
        return False
    cur = (target.get("description") or "").strip()
    # update only if incoming is meaningfully longer
    if len(inc) > len(cur) + 30:
        target["description"] = inc
        return True
    if not cur and inc:
        target["description"] = inc
        return True
    return False


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit("Usage: import_events_from_csv.py <path.csv>")

    csv_path = Path(sys.argv[1]).expanduser().resolve()
    if not csv_path.exists():
        raise SystemExit(f"CSV not found: {csv_path}")

    data = json.loads(EVENTS_PATH.read_text(encoding="utf-8"))
    events = data.get("events") or []
    if not isinstance(events, list):
        raise SystemExit("events.json: `events` must be a list")

    lookup, _iso2 = load_country_lookup()
    coords_index = build_coords_index([e for e in events if isinstance(e, dict)])

    # Index existing by (country_name_tr, year, norm(title))
    idx: Dict[Tuple[str, int, str], Dict[str, Any]] = {}
    for e in events:
        if not isinstance(e, dict):
            continue
        cn = (e.get("country_name") or "").strip()
        y = e.get("year")
        t = (e.get("title") or "").strip()
        if not cn or not isinstance(y, int) or not t:
            continue
        idx[(cn, y, norm_key(t))] = e

    added = 0
    updated = 0
    skipped = 0

    with open(csv_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if not row:
                continue
            raw_country = (row.get("country") or "").strip()
            raw_year = (row.get("year") or "").strip()
            title = (row.get("title") or "").strip()
            raw_category = (row.get("category") or "").strip()
            desc = (row.get("description") or "").strip()

            if not raw_country or not raw_year or not title:
                continue
            try:
                year = int(raw_year)
            except Exception:
                continue

            # Map country to canonical Turkish name
            country_tr = lookup.get(norm_key(raw_country)) or raw_country
            # If still not Turkish and not known, keep as-is; normalize_events may handle later.
            key = (country_tr, year, norm_key(title))

            existing = idx.get(key)
            if existing:
                if maybe_update_description(existing, desc):
                    updated += 1
                else:
                    skipped += 1
                continue

            lat, lon = coords_index.get(country_tr, FALLBACK_CENTERS.get(country_tr, (0.0, 0.0)))
            ev = {
                "id": event_id(country_tr, year, title),
                "country_code": "",  # normalize_events fills
                "country_name": country_tr,
                "lat": lat,
                "lon": lon,
                "decade": decade_from_year(year),
                "year": year,
                "category": map_category(raw_category),
                "title": title,
                "description": desc,
                "wikipedia_url": "",
                "casualties": None,
                "key_figures": [],
            }
            events.append(ev)
            idx[key] = ev
            added += 1

    if added or updated:
        data["events"] = events
        EVENTS_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print("CSV import complete.")
    print(f"- file: {csv_path}")
    print(f"- added: {added}")
    print(f"- updated(desc): {updated}")
    print(f"- skipped: {skipped}")


if __name__ == "__main__":
    main()
