#!/usr/bin/env python3
"""
Consistency checks to keep Admin + Map aligned.

Validates:
- Every event.country_name is a canonical Turkish name from data/country_mappings.json
- Every event.country_code matches the mapping's iso2 (uppercased)
- No duplicates by (country_name, year, title)
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Tuple


BASE_DIR = Path(__file__).resolve().parent.parent
EVENTS_PATH = BASE_DIR / "data" / "events.json"
COUNTRY_MAPPINGS_PATH = BASE_DIR / "data" / "country_mappings.json"


def main() -> None:
    with open(COUNTRY_MAPPINGS_PATH, "r", encoding="utf-8") as f:
        countries = json.load(f).get("countries", [])

    iso_by_tr = {
        (c.get("turkish") or "").strip(): (c.get("iso2") or "").strip().upper()
        for c in countries
        if (c.get("turkish") or "").strip()
    }
    canonical_tr = set(iso_by_tr.keys())

    with open(EVENTS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    events = data.get("events") or []
    if not isinstance(events, list):
        raise SystemExit("events.json: `events` must be a list")

    bad_names: List[Tuple[int, str]] = []
    bad_codes: List[Tuple[int, str, str, str]] = []

    for i, ev in enumerate(events):
        if not isinstance(ev, dict):
            continue
        name = (ev.get("country_name") or "").strip()
        code = (ev.get("country_code") or "").strip().upper()

        if not name or name not in canonical_tr:
            bad_names.append((i, name))
            continue

        expected = iso_by_tr.get(name, "")
        if expected and code != expected:
            bad_codes.append((i, name, code, expected))

    dup_groups = defaultdict(list)
    for i, ev in enumerate(events):
        if not isinstance(ev, dict):
            continue
        key = (
            (ev.get("country_name") or "").strip(),
            ev.get("year"),
            (ev.get("title") or "").strip(),
        )
        dup_groups[key].append(i)
    dups = [(k, idxs) for k, idxs in dup_groups.items() if len(idxs) > 1]

    ok = True
    if bad_names:
        ok = False
        print("ERROR: Non-canonical country_name values found (index, value):")
        for idx, name in bad_names[:50]:
            print(f"- {idx}: {name!r}")
        if len(bad_names) > 50:
            print(f"... and {len(bad_names) - 50} more")

    if bad_codes:
        ok = False
        print("ERROR: country_code mismatch vs country_mappings (index, name, code, expected):")
        for idx, name, code, expected in bad_codes[:50]:
            print(f"- {idx}: {name} code={code!r} expected={expected!r}")
        if len(bad_codes) > 50:
            print(f"... and {len(bad_codes) - 50} more")

    if dups:
        ok = False
        print("ERROR: Duplicate events by (country_name, year, title):")
        for (name, year, title), idxs in dups[:30]:
            print(f"- {name} {year} {title} -> {len(idxs)} duplicates at indices {idxs[:10]}")
        if len(dups) > 30:
            print(f"... and {len(dups) - 30} more duplicate groups")

    if ok:
        print("OK: events.json is consistent with country_mappings.json")
        print(f"- events: {len(events)}")
        print(f"- countries (canonical): {len({(e.get('country_name') or '').strip() for e in events if isinstance(e, dict)})}")
    else:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

