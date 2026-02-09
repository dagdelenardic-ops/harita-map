#!/usr/bin/env python3
"""
Normalize country names/codes in data/events.json so Admin + Map use the same canonical Turkish names.

Rules:
- Canonical country name = `turkish` field from data/country_mappings.json
- Accept English names + aliases (incl. ASCII Turkish variants) and normalize them to canonical Turkish
- Fill country_code from iso2 when known
- Remove duplicates that become visible after normalization (same country + year + title)
- Regenerate offline Admin embeds (admin/data.js, admin/country_mappings.js)
"""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


BASE_DIR = Path(__file__).resolve().parent.parent
EVENTS_PATH = BASE_DIR / "data" / "events.json"
COUNTRY_MAPPINGS_PATH = BASE_DIR / "data" / "country_mappings.json"

ADMIN_DIR = BASE_DIR / "admin"
ADMIN_EVENTS_EMBED_PATH = ADMIN_DIR / "data.js"
ADMIN_COUNTRY_MAPPINGS_EMBED_PATH = ADMIN_DIR / "country_mappings.js"


_TR_TRANSLATE = str.maketrans(
    {
        # Turkish diacritics -> ASCII for matching
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
        # Common circumflex variants
        "â": "a",
        "Â": "a",
        "î": "i",
        "Î": "i",
        "û": "u",
        "Û": "u",
    }
)


def _normalize_lookup_key(value: str) -> str:
    """
    Normalize a country name for robust matching across:
    - casing differences
    - Turkish diacritics
    - curly apostrophes
    - extra whitespace
    """
    if value is None:
        return ""
    s = str(value).strip()
    # Normalize curly apostrophes/quotes to ASCII
    s = (
        s.replace("\u2019", "'")
        .replace("\u2018", "'")
        .replace("\u201B", "'")
        .replace("\u02BC", "'")
        .replace("’", "'")
        .replace("‘", "'")
    )
    s = " ".join(s.split())
    s = s.lower()
    s = s.translate(_TR_TRANSLATE)
    return s


@dataclass(frozen=True)
class CountryCanon:
    turkish: str
    iso2: str  # lower-case in mappings


def _load_country_index() -> Tuple[Dict[str, CountryCanon], Dict[str, CountryCanon]]:
    """
    Returns:
    - lookup: normalized string -> CountryCanon
    - by_turkish: canonical Turkish name -> CountryCanon
    """
    with open(COUNTRY_MAPPINGS_PATH, "r", encoding="utf-8") as f:
        mappings = json.load(f).get("countries", [])

    lookup: Dict[str, CountryCanon] = {}
    by_turkish: Dict[str, CountryCanon] = {}

    for entry in mappings:
        tr = (entry.get("turkish") or "").strip()
        iso2 = (entry.get("iso2") or "").strip().lower()
        if not tr:
            continue
        canon = CountryCanon(turkish=tr, iso2=iso2)
        by_turkish[tr] = canon

        keys: List[str] = []
        for k in [entry.get("turkish"), entry.get("english")]:
            if k:
                keys.append(k)
        keys.extend(entry.get("aliases") or [])

        for k in keys:
            nk = _normalize_lookup_key(k)
            if not nk:
                continue
            # If a collision exists, keep the first one deterministically.
            lookup.setdefault(nk, canon)

    return lookup, by_turkish


def _event_rank(e: Dict[str, Any]) -> Tuple[int, int, int, int, int, int, str]:
    """Ranking for selecting the best event among duplicates."""
    event_id = str(e.get("id") or "")
    is_gap = 1 if event_id.startswith("ev_gap_") else 0
    lat = float(e.get("lat") or 0)
    lon = float(e.get("lon") or 0)
    has_coords = 1 if (lat != 0 or lon != 0) else 0
    wiki = (e.get("wikipedia_url") or "").strip()
    has_wiki = 1 if wiki else 0
    desc = (e.get("description") or "").strip()
    desc_len = len(desc)
    has_casualties = 1 if e.get("casualties") is not None else 0
    key_figures_len = len(e.get("key_figures") or [])
    # Higher is better; prefer non-gap IDs, richer data; stable tie-breaker by ID.
    return (
        1 - is_gap,
        has_coords,
        has_wiki,
        desc_len,
        has_casualties,
        key_figures_len,
        event_id,
    )


def _merge_event_fields(target: Dict[str, Any], source: Dict[str, Any]) -> bool:
    """Fill missing fields in target from source. Returns True if anything changed."""
    changed = False
    for field in ["wikipedia_url", "description"]:
        t = (target.get(field) or "").strip()
        s = (source.get(field) or "").strip()
        if not t and s:
            target[field] = s
            changed = True
        elif field == "description" and len(s) > len(t) and t != s:
            # Prefer the longer description for duplicates.
            target[field] = s
            changed = True

    # Coordinates: prefer non-zero
    t_lat = float(target.get("lat") or 0)
    t_lon = float(target.get("lon") or 0)
    s_lat = float(source.get("lat") or 0)
    s_lon = float(source.get("lon") or 0)
    if (t_lat == 0 and t_lon == 0) and (s_lat != 0 or s_lon != 0):
        target["lat"] = s_lat
        target["lon"] = s_lon
        changed = True

    # Country code: keep if missing
    t_cc = (target.get("country_code") or "").strip()
    s_cc = (source.get("country_code") or "").strip()
    if not t_cc and s_cc:
        target["country_code"] = s_cc
        changed = True

    # Casualties: keep if missing
    if target.get("casualties") is None and source.get("casualties") is not None:
        target["casualties"] = source.get("casualties")
        changed = True

    # Key figures: union
    t_kf = target.get("key_figures") or []
    s_kf = source.get("key_figures") or []
    if isinstance(t_kf, list) and isinstance(s_kf, list):
        merged = []
        seen = set()
        for x in [*t_kf, *s_kf]:
            xs = str(x).strip()
            if not xs or xs in seen:
                continue
            seen.add(xs)
            merged.append(xs)
        if merged != t_kf:
            target["key_figures"] = merged
            changed = True

    return changed


def normalize_events() -> None:
    lookup, by_turkish = _load_country_index()

    with open(EVENTS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    events = data.get("events") or []
    if not isinstance(events, list):
        raise SystemExit("events.json: `events` must be a list")

    changed_country = 0
    filled_codes = 0
    standardized_codes = 0

    for ev in events:
        if not isinstance(ev, dict):
            continue
        raw_name = (ev.get("country_name") or "").strip()
        if raw_name:
            canon = lookup.get(_normalize_lookup_key(raw_name))
            if canon and canon.turkish and canon.turkish != raw_name:
                ev["country_name"] = canon.turkish
                changed_country += 1
                raw_name = canon.turkish

        # Standardize country_code to ISO2 when possible
        iso2 = ""
        canon_by_tr = by_turkish.get(raw_name) if raw_name else None
        if canon_by_tr and canon_by_tr.iso2:
            iso2 = canon_by_tr.iso2.upper()

        existing_code = (ev.get("country_code") or "").strip()
        if iso2:
            if not existing_code:
                ev["country_code"] = iso2
                filled_codes += 1
            elif existing_code.upper() != iso2:
                # Keep non-ISO codes (rare), but normalize case for consistent comparisons.
                ev["country_code"] = existing_code.upper()
                standardized_codes += 1
            elif existing_code != iso2:
                ev["country_code"] = iso2
                standardized_codes += 1
        elif existing_code and existing_code != existing_code.upper():
            ev["country_code"] = existing_code.upper()
            standardized_codes += 1

    # Remove duplicates created by canonicalization: same (country_name, year, title)
    grouped: Dict[Tuple[str, Any, str], List[Dict[str, Any]]] = defaultdict(list)
    for ev in events:
        c = (ev.get("country_name") or "").strip()
        y = ev.get("year")
        t = (ev.get("title") or "").strip()
        grouped[(c, y, t)].append(ev)

    unique_events: List[Dict[str, Any]] = []
    removed = 0
    merged_fields = 0

    for _key, group in grouped.items():
        if len(group) == 1:
            unique_events.append(group[0])
            continue

        # Pick the best, then merge missing fields from others.
        best = max(group, key=_event_rank)
        for other in group:
            if other is best:
                continue
            if _merge_event_fields(best, other):
                merged_fields += 1
        unique_events.append(best)
        removed += len(group) - 1

    data["events"] = unique_events

    # Backup + write
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_path = EVENTS_PATH.with_suffix(f".json.bak.{ts}")
    backup_path.write_text(EVENTS_PATH.read_text(encoding="utf-8"), encoding="utf-8")
    EVENTS_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # Regenerate offline Admin embeds
    ADMIN_EVENTS_EMBED_PATH.write_text(
        "window.__EVENTS_DATA__ = " + json.dumps(data, ensure_ascii=False) + ";\n",
        encoding="utf-8",
    )
    with open(COUNTRY_MAPPINGS_PATH, "r", encoding="utf-8") as f:
        country_mappings = json.load(f)
    ADMIN_COUNTRY_MAPPINGS_EMBED_PATH.write_text(
        "window.__COUNTRY_MAPPINGS__ = " + json.dumps(country_mappings.get("countries", []), ensure_ascii=False) + ";\n",
        encoding="utf-8",
    )

    print("Normalization complete.")
    print(f"- Country name changes: {changed_country}")
    print(f"- Country codes filled from mappings: {filled_codes}")
    print(f"- Country codes standardized: {standardized_codes}")
    print(f"- Duplicate events removed (country+year+title): {removed}")
    print(f"- Duplicate merge operations (filled/updated fields): {merged_fields}")
    print(f"- Backup: {backup_path}")
    print(f"- Admin embeds: {ADMIN_EVENTS_EMBED_PATH.name}, {ADMIN_COUNTRY_MAPPINGS_EMBED_PATH.name}")
    print(f"- Final event count: {len(unique_events)}")


if __name__ == "__main__":
    normalize_events()
