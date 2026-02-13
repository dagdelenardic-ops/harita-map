#!/usr/bin/env python3
"""
Fuzzy de-duplicate events in data/events.json (conservative).

Goal: catch cases like:
- same Wikipedia link but multiple entries for same country+year (often TR/EN variants)
- near-identical titles in the same country+year (e.g. "Silence of the Lambs" vs "The Silence of the Lambs")

Safety rules (high confidence only):
- Only compares events within the same (country_name, year).
- Always merges if wikipedia_url matches (non-empty) within the same country+year.
- Otherwise requires high title similarity; for borderline similarity, requires same category.

When duplicates are found:
- Keep the "best" record (richest fields) and merge data from others.
- Remove the extra records.
"""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Dict, List, Tuple


BASE_DIR = Path(__file__).resolve().parent.parent
EVENTS_PATH = BASE_DIR / "data" / "events.json"


STOPWORDS = {
    # Turkish
    "ve",
    "ile",
    "da",
    "de",
    "bir",
    "bu",
    "su",
    "şu",
    "icin",
    "için",
    "donemi",
    "dönemi",
    "krizi",
    "olayi",
    "olayı",
    "hareketi",
    "hükümeti",
    "hukumeti",
    "yasasi",
    "yasası",
    "anlasmasi",
    "anlaşması",
    "savas",
    "savaşı",
    "catısma",
    "çatışma",
    # English
    "the",
    "a",
    "an",
    "of",
    "and",
    "in",
    "on",
    "to",
    "for",
}


def _norm_title(s: str) -> str:
    if not s:
        return ""
    s = s.strip().lower()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = s.replace("’", "'").replace("‘", "'")
    s = re.sub(r"[\"'`]", "", s)
    s = re.sub(r"[^a-z0-9ğüşıöç\s\-:]", " ", s, flags=re.IGNORECASE)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _tokens(s: str) -> set[str]:
    ns = _norm_title(s)
    parts = re.split(r"[\s\-:]+", ns)
    out = set()
    for p in parts:
        if not p:
            continue
        if p in STOPWORDS:
            continue
        if len(p) <= 2:
            continue
        out.add(p)
    return out


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _title_sim(a: str, b: str) -> Tuple[float, float]:
    na = _norm_title(a)
    nb = _norm_title(b)
    if not na or not nb:
        return 0.0, 0.0
    r = SequenceMatcher(None, na, nb).ratio()
    j = _jaccard(_tokens(na), _tokens(nb))
    return r, j


def _is_probable_duplicate(e1: Dict[str, Any], e2: Dict[str, Any]) -> bool:
    w1 = (e1.get("wikipedia_url") or "").strip()
    w2 = (e2.get("wikipedia_url") or "").strip()
    if w1 and w2 and w1 == w2:
        return True

    t1 = (e1.get("title") or "").strip()
    t2 = (e2.get("title") or "").strip()
    if not t1 or not t2:
        return False

    r, j = _title_sim(t1, t2)
    if r >= 0.97:
        return True

    # Conservative merge for non-wiki duplicates:
    # require same category unless similarity is extremely high.
    c1 = (e1.get("category") or "").strip()
    c2 = (e2.get("category") or "").strip()
    if c1 != c2:
        return False

    if (r >= 0.90 and j >= 0.90) or (j == 1.0 and r >= 0.88):
        return True

    return False


def _score(ev: Dict[str, Any]) -> Tuple[int, int, int, int, int]:
    desc_len = len((ev.get("description") or "").strip())
    has_coords = 1 if (float(ev.get("lat") or 0) != 0.0 or float(ev.get("lon") or 0) != 0.0) else 0
    has_wiki = 1 if (ev.get("wikipedia_url") or "").strip() else 0
    has_youtube = 1 if (ev.get("youtube_video_id") or ev.get("youtube_url") or ev.get("youtube")) else 0
    has_casualties = 1 if ev.get("casualties") is not None else 0
    return (has_wiki, has_youtube, has_coords, has_casualties, desc_len)


def _merge_into(dst: Dict[str, Any], src: Dict[str, Any]) -> None:
    # Keep the longer description.
    d_dst = (dst.get("description") or "").strip()
    d_src = (src.get("description") or "").strip()
    if len(d_src) > len(d_dst):
        dst["description"] = src.get("description")

    # Prefer preserving links.
    for k in ("youtube_video_id", "youtube_url", "youtube", "wikipedia_url", "source_url"):
        if not dst.get(k) and src.get(k):
            dst[k] = src.get(k)

    # Coords: keep non-zero if missing.
    if (float(dst.get("lat") or 0) == 0.0 and float(dst.get("lon") or 0) == 0.0) and (
        float(src.get("lat") or 0) != 0.0 or float(src.get("lon") or 0) != 0.0
    ):
        dst["lat"] = src.get("lat")
        dst["lon"] = src.get("lon")

    # Country code: keep if missing.
    if not (dst.get("country_code") or "").strip() and (src.get("country_code") or "").strip():
        dst["country_code"] = src.get("country_code")

    # Casualties: keep if missing.
    if dst.get("casualties") is None and src.get("casualties") is not None:
        dst["casualties"] = src.get("casualties")

    # Key figures: union.
    kf_dst = dst.get("key_figures") or []
    kf_src = src.get("key_figures") or []
    if isinstance(kf_dst, list) and isinstance(kf_src, list):
        seen = set()
        merged: List[str] = []
        for x in [*kf_dst, *kf_src]:
            xs = str(x).strip()
            if not xs or xs in seen:
                continue
            seen.add(xs)
            merged.append(xs)
        dst["key_figures"] = merged

    # Tags: union.
    t_dst = dst.get("tags")
    t_src = src.get("tags")
    if isinstance(t_dst, list) or isinstance(t_src, list):
        s = set()
        if isinstance(t_dst, list):
            s.update(str(x).strip() for x in t_dst if str(x).strip())
        if isinstance(t_src, list):
            s.update(str(x).strip() for x in t_src if str(x).strip())
        if s:
            dst["tags"] = sorted(s)


@dataclass
class DedupeResult:
    groups: int = 0
    removed: int = 0


def _dedupe(events: List[Dict[str, Any]], countries_filter: set[str] | None) -> Tuple[List[Dict[str, Any]], Dict[str, DedupeResult]]:
    # Group indices by (country, year)
    buckets: Dict[Tuple[str, int], List[int]] = {}
    for i, ev in enumerate(events):
        if not isinstance(ev, dict):
            continue
        c = (ev.get("country_name") or "").strip()
        y = ev.get("year")
        if not c or not isinstance(y, int):
            continue
        if countries_filter and c not in countries_filter:
            continue
        buckets.setdefault((c, y), []).append(i)

    keep = [True] * len(events)
    per_country: Dict[str, DedupeResult] = {}

    # For each bucket, build connected components of duplicates.
    for (country, year), idxs in buckets.items():
        if len(idxs) <= 1:
            continue

        parent = {i: i for i in idxs}

        def find(x: int) -> int:
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        def union(a: int, b: int) -> None:
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[rb] = ra

        for ii in range(len(idxs)):
            for jj in range(ii + 1, len(idxs)):
                i = idxs[ii]
                j = idxs[jj]
                if _is_probable_duplicate(events[i], events[j]):
                    union(i, j)

        comps: Dict[int, List[int]] = {}
        for i in idxs:
            r = find(i)
            comps.setdefault(r, []).append(i)

        for comp in comps.values():
            if len(comp) <= 1:
                continue
            per_country.setdefault(country, DedupeResult()).groups += 1
            # pick best
            best_i = comp[0]
            best_s = _score(events[best_i])
            for i in comp[1:]:
                sc = _score(events[i])
                if sc > best_s:
                    best_i = i
                    best_s = sc
            # merge others into best, remove others
            best = events[best_i]
            for i in comp:
                if i == best_i:
                    continue
                _merge_into(best, events[i])
                keep[i] = False
                per_country[country].removed += 1

    new_events = [ev for i, ev in enumerate(events) if keep[i]]
    return new_events, per_country


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="Write changes to data/events.json")
    ap.add_argument("--countries", default="", help="Comma-separated Turkish country names to restrict (e.g. 'Çin,ABD')")
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

    new_events, per_country = _dedupe([e for e in events if isinstance(e, dict)], countries_filter)

    total_groups = sum(r.groups for r in per_country.values())
    total_removed = sum(r.removed for r in per_country.values())
    print(f"fuzzy_dedupe: groups={total_groups} removed={total_removed} events_before={len(events)} events_after={len(new_events)}")
    for c in sorted(per_country.keys()):
        r = per_country[c]
        print(f"- {c}: groups={r.groups} removed={r.removed}")

    if args.apply and total_removed:
        data["events"] = new_events
        EVENTS_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"wrote: {EVENTS_PATH}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
