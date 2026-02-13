#!/usr/bin/env python3
"""
Remove obviously contextless events (conservative).

This targets low-quality records such as:
- single-word Latin titles ("Trump", "Presidential", "Crisis", "Election")
- very short / non-informative descriptions ("Trump.", "Kriz.", "Seçim.")
- missing wikipedia_url and no youtube link

It intentionally avoids removing:
- gap filler events (id starts with ev_gap_)
- Turkish single-word titles like "Bağımsızlık" (handled by Latin-title check)
- cinema/music items (media can be single-word)

Usage:
  python3 scripts/remove_contextless_events.py --dry-run
  python3 scripts/remove_contextless_events.py --apply
  python3 scripts/remove_contextless_events.py --apply --countries 'Çin,ABD,Fransa'
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Set


BASE_DIR = Path(__file__).resolve().parent.parent
EVENTS_PATH = BASE_DIR / "data" / "events.json"


HIGH_STAKES_CATEGORIES: Set[str] = {
    "politics",
    "diplomacy",
    "leader",
    "war",
    "revolution",
    "terror",
    "genocide",
    "time_100",
}

TURKISH_CHARS = set("çğıöşüÇĞİÖŞÜ")


def _word_count(s: str) -> int:
    return len([t for t in re.split(r"\s+", (s or "").strip()) if t])


def _is_latin_single_token(title: str) -> bool:
    t = (title or "").strip()
    if not t:
        return False
    if any(ch in TURKISH_CHARS for ch in t):
        return False
    if _word_count(t) != 1:
        return False
    # ASCII-ish token: letters/digits/hyphen/dot/apostrophe
    return bool(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9\-\.']*", t))


def _has_any_link(e: Dict[str, Any]) -> bool:
    if (e.get("wikipedia_url") or "").strip():
        return True
    if e.get("youtube_video_id") or e.get("youtube_url") or e.get("youtube"):
        return True
    return False


def _is_bad_description(desc: str, title: str) -> bool:
    d = (desc or "").strip()
    t = (title or "").strip()
    if not d:
        return True
    if d == t or d == f"{t}.":
        return True
    # One word, or ultra-short two-word stubs.
    if _word_count(d) <= 1:
        return True
    if _word_count(d) <= 2 and len(d) <= 18:
        return True
    return False


def _should_remove(e: Dict[str, Any], countries_filter: Set[str] | None) -> bool:
    if not isinstance(e, dict):
        return False
    if countries_filter:
        c = (e.get("country_name") or "").strip()
        if c not in countries_filter:
            return False

    eid = str(e.get("id") or "")
    if eid.startswith("ev_gap_"):
        return False

    cat = (e.get("category") or "").strip()
    if cat not in HIGH_STAKES_CATEGORIES:
        return False

    if _has_any_link(e):
        return False

    title = (e.get("title") or "").strip()
    if not _is_latin_single_token(title):
        return False

    desc = (e.get("description") or "").strip()
    if not _is_bad_description(desc, title):
        return False

    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="Write changes to data/events.json")
    ap.add_argument("--dry-run", action="store_true", help="Do not write changes (default if --apply not set)")
    ap.add_argument("--countries", default="", help="Comma-separated Turkish country names to restrict (e.g. 'Çin,ABD,Fransa')")
    args = ap.parse_args()

    if not EVENTS_PATH.exists():
        print(f"ERROR: not found: {EVENTS_PATH}")
        return 2

    data = json.loads(EVENTS_PATH.read_text(encoding="utf-8"))
    events = data.get("events", [])
    if not isinstance(events, list):
        print("ERROR: events.json: `events` must be a list")
        return 2

    countries_filter = None
    if args.countries.strip():
        countries_filter = {c.strip() for c in args.countries.split(",") if c.strip()}

    to_remove: List[Dict[str, Any]] = []
    for e in events:
        if isinstance(e, dict) and _should_remove(e, countries_filter):
            to_remove.append(e)

    by_country = Counter((e.get("country_name") or "").strip() for e in to_remove)
    print(f"contextless_remove: candidates={len(to_remove)} events_before={len(events)}")
    if to_remove:
        print("top countries:", by_country.most_common(10))
        for e in sorted(to_remove, key=lambda x: ((x.get("country_name") or ""), x.get("year") or 0, x.get("title") or ""))[:25]:
            print(
                f"- {e.get('country_name')} {e.get('year')} id={e.get('id')} cat={e.get('category')} "
                f"title={e.get('title')!r} desc={e.get('description')!r}"
            )

    if not args.apply:
        # default to dry-run unless explicitly applied
        return 0

    if not to_remove:
        print("No changes to apply.")
        return 0

    remove_ids = {str(e.get("id") or "") for e in to_remove}
    new_events = [e for e in events if not (isinstance(e, dict) and str(e.get("id") or "") in remove_ids)]
    data["events"] = new_events
    EVENTS_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"applied: removed={len(events) - len(new_events)} events_after={len(new_events)} wrote={EVENTS_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

