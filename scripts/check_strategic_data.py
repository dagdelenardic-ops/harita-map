#!/usr/bin/env python3
"""
Validate structured strategic datasets used by the map UI.

Checks:
- `data/current_conflicts.json` IDs are unique
- conflict participants are canonical Turkish country names
- conflict links have a source country and a country target or coordinate anchor
- `data/water_sources.json` uses canonical Turkish country names
- strategic snapshot files exist and use canonical Turkish country names
"""

from __future__ import annotations

import json
import unicodedata
from pathlib import Path
from typing import Any, Dict, List


BASE_DIR = Path(__file__).resolve().parent.parent
COUNTRY_MAPPINGS_PATH = BASE_DIR / "data" / "country_mappings.json"
CURRENT_CONFLICTS_PATH = BASE_DIR / "data" / "current_conflicts.json"
WATER_SOURCES_PATH = BASE_DIR / "data" / "water_sources.json"
STRATEGIC_SNAPSHOT_PATHS = {
    "sanctions": BASE_DIR / "data" / "sanctions.json",
    "weather": BASE_DIR / "data" / "weather.json",
    "air_quality": BASE_DIR / "data" / "air_quality.json",
    "fx": BASE_DIR / "data" / "fx.json",
}


def normalize_lookup_key(value: Any) -> str:
    s = str(value or "").strip()
    if not s:
        return ""
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = s.lower().replace("ı", "i")
    s = " ".join(s.split())
    return s


def load_country_index() -> Dict[str, str]:
    raw = json.loads(COUNTRY_MAPPINGS_PATH.read_text(encoding="utf-8")).get("countries", [])
    lookup: Dict[str, str] = {}
    for entry in raw:
        tr = (entry.get("turkish") or "").strip()
        if not tr:
            continue
        for candidate in [entry.get("turkish"), entry.get("english")] + (entry.get("aliases") or []):
            nk = normalize_lookup_key(candidate)
            if nk:
                lookup[nk] = tr
    return lookup


def canonicalize_country(lookup: Dict[str, str], value: Any) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    return lookup.get(normalize_lookup_key(raw), "")


def check_conflicts(lookup: Dict[str, str]) -> List[str]:
    payload = json.loads(CURRENT_CONFLICTS_PATH.read_text(encoding="utf-8"))
    conflicts = payload.get("conflicts") or []
    errors: List[str] = []
    ids = set()

    for idx, conflict in enumerate(conflicts):
        cid = str(conflict.get("id") or "").strip()
        if not cid:
            errors.append(f"conflicts[{idx}]: missing id")
        elif cid in ids:
            errors.append(f"conflicts[{idx}]: duplicate id {cid!r}")
        ids.add(cid)

        for participant in conflict.get("participants") or []:
            if not canonicalize_country(lookup, participant):
                errors.append(f"conflicts[{idx}] {cid!r}: participant not canonical/mapped -> {participant!r}")

        for link_idx, link in enumerate(conflict.get("links") or []):
            source = str(link.get("source") or "").strip()
            if not source:
                errors.append(f"conflicts[{idx}] {cid!r} links[{link_idx}]: missing source")
            elif not canonicalize_country(lookup, source):
                errors.append(f"conflicts[{idx}] {cid!r} links[{link_idx}]: source not canonical/mapped -> {source!r}")

            target = str(link.get("target") or "").strip()
            target_anchor = link.get("target_anchor") or {}
            if target:
                pass
            elif isinstance(target_anchor, dict):
                lat = target_anchor.get("lat")
                lon = target_anchor.get("lon")
                if not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)):
                    errors.append(f"conflicts[{idx}] {cid!r} links[{link_idx}]: target_anchor needs numeric lat/lon")
            else:
                errors.append(f"conflicts[{idx}] {cid!r} links[{link_idx}]: missing target or target_anchor")

    return errors


def check_water_sources(lookup: Dict[str, str]) -> List[str]:
    payload = json.loads(WATER_SOURCES_PATH.read_text(encoding="utf-8"))
    countries = payload.get("countries") or {}
    errors: List[str] = []
    for country in countries:
        canon = canonicalize_country(lookup, country)
        if canon != country:
            errors.append(f"water_sources: key should be canonical Turkish name -> {country!r} (expected {canon!r})")
    return errors


def check_country_keyed_snapshot(name: str, path: Path, lookup: Dict[str, str]) -> List[str]:
    errors: List[str] = []
    if not path.exists():
        return [f"{name}: missing snapshot file -> {path.name}"]

    payload = json.loads(path.read_text(encoding="utf-8"))
    countries = payload.get("countries")
    if not isinstance(countries, dict):
        return [f"{name}: countries must be an object"]

    for country in countries:
        canon = canonicalize_country(lookup, country)
        if canon != country:
            errors.append(f"{name}: key should be canonical Turkish name -> {country!r} (expected {canon!r})")
    return errors


def main() -> None:
    lookup = load_country_index()
    errors = []
    errors.extend(check_conflicts(lookup))
    errors.extend(check_water_sources(lookup))
    for name, path in STRATEGIC_SNAPSHOT_PATHS.items():
        errors.extend(check_country_keyed_snapshot(name, path, lookup))

    if errors:
        print("ERROR: strategic datasets failed validation")
        for err in errors:
            print("-", err)
        raise SystemExit(1)

    print("OK: strategic datasets are valid")


if __name__ == "__main__":
    main()
