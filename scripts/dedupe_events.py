#!/usr/bin/env python3
"""
Remove exact duplicate events from data/events.json.

Definition of duplicate (conservative):
- same country_name (after strip)
- same year (int)
- same title after normalization (lower, whitespace-collapsed, punctuation-stripped)

When duplicates are found, keep a single "best" record and merge some fields:
- keep the longest description
- preserve youtube/video/wiki links if any exist across the group
- union tags (if present)
"""

from __future__ import annotations

import json
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any, Dict, List, Tuple


def _norm_title(s: str) -> str:
    if not s:
        return ""
    s = s.strip().lower()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = re.sub(r"[\"'’`]", "", s)
    s = re.sub(r"[^a-z0-9ğüşıöç\s\-:]", " ", s, flags=re.IGNORECASE)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _safe_int(x: Any) -> int | None:
    try:
        return int(x)
    except Exception:
        return None


def _score(ev: Dict[str, Any]) -> Tuple[int, int, int, int]:
    # Prefer "richer" records.
    desc_len = len((ev.get("description") or "").strip())
    has_youtube = 1 if (ev.get("youtube_video_id") or ev.get("youtube_url") or ev.get("youtube")) else 0
    has_wiki = 1 if (ev.get("wiki_url") or ev.get("wikipedia_url") or ev.get("source_url")) else 0
    has_coords = 1 if (ev.get("lat") not in (None, 0, 0.0) and ev.get("lon") not in (None, 0, 0.0)) else 0
    return (has_youtube, has_wiki, has_coords, desc_len)


def _merge_into(dst: Dict[str, Any], src: Dict[str, Any]) -> None:
    # Description: keep longer.
    d_dst = (dst.get("description") or "").strip()
    d_src = (src.get("description") or "").strip()
    if len(d_src) > len(d_dst):
        dst["description"] = src.get("description")

    # Prefer preserving links.
    for k in ("youtube_video_id", "youtube_url", "youtube", "wiki_url", "wikipedia_url", "source_url"):
        if not dst.get(k) and src.get(k):
            dst[k] = src.get(k)

    # Coords: keep non-zero if missing.
    if (dst.get("lat") in (None, 0, 0.0) or dst.get("lon") in (None, 0, 0.0)) and (
        src.get("lat") not in (None, 0, 0.0) and src.get("lon") not in (None, 0, 0.0)
    ):
        dst["lat"] = src.get("lat")
        dst["lon"] = src.get("lon")

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


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    events_path = repo_root / "data" / "events.json"
    if not events_path.exists():
        print(f"ERROR: not found: {events_path}", file=sys.stderr)
        return 2

    data = json.loads(events_path.read_text(encoding="utf-8"))
    events = data.get("events", [])
    if not isinstance(events, list):
        print("ERROR: data.events is not a list", file=sys.stderr)
        return 2

    buckets: Dict[Tuple[str, int, str], List[int]] = {}
    for i, ev in enumerate(events):
        if not isinstance(ev, dict):
            continue
        c = (ev.get("country_name") or "").strip()
        y = _safe_int(ev.get("year"))
        t = _norm_title(ev.get("title") or "")
        if not c or y is None or not t:
            continue
        buckets.setdefault((c, y, t), []).append(i)

    removed = 0
    merged_groups = 0
    keep_mask = [True] * len(events)

    for key, idxs in buckets.items():
        if len(idxs) <= 1:
            continue
        merged_groups += 1
        group = [events[i] for i in idxs]
        # Pick best record, then merge others into it.
        best_i = idxs[0]
        best = events[best_i]
        best_score = _score(best)
        for i in idxs[1:]:
            sc = _score(events[i])
            if sc > best_score:
                best_i = i
                best = events[best_i]
                best_score = sc

        for i in idxs:
            if i == best_i:
                continue
            _merge_into(best, events[i])
            keep_mask[i] = False
            removed += 1

    if removed:
        data["events"] = [ev for i, ev in enumerate(events) if keep_mask[i]]
        events_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"dedupe: groups_merged={merged_groups} removed={removed} remaining={len(data.get('events', []))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

