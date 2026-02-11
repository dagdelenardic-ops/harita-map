#!/usr/bin/env python3
"""
Add suitable videos from Tarih101YT channel to matching events.

Approach:
- Pull latest channel uploads from YouTube RSS feed.
- Use conservative, event-id-based mappings for high-confidence matches only.
- Do not overwrite existing `youtube_video_id` values unless explicitly requested.
"""

from __future__ import annotations

import json
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Tuple


BASE_DIR = Path(__file__).resolve().parent.parent
EVENTS_PATH = BASE_DIR / "data" / "events.json"

# https://www.youtube.com/@Tarih101YT
TARIH101_CHANNEL_ID = "UCPlTdUoi8jAjEdk1wf5cQug"

# Curated high-confidence mappings:
# event_id -> keyword list expected in Tarih101 video title
EVENT_VIDEO_RULES: Dict[str, List[str]] = {
    # Mısır: Enver Sedat suikastı
    "ev34658728": ["enver", "sedat", "suikast"],
    # Romanya: Çavuşesku rejiminin düşüşü
    "ev34658800": ["çavuşesku", "deviren"],
    "ev_gap_1989_1": ["çavuşesku", "düşüş"],
    # İtalya: Mussolini dönemi sonu
    "ev_it002": ["mussolini", "kaçış"],
}


def fetch_latest_videos(channel_id: str) -> List[Dict[str, str]]:
    feed_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    req = urllib.request.Request(feed_url, headers={"User-Agent": "Mozilla/5.0"})
    xml_bytes = urllib.request.urlopen(req, timeout=30).read()
    root = ET.fromstring(xml_bytes)

    ns = {
        "atom": "http://www.w3.org/2005/Atom",
        "yt": "http://www.youtube.com/xml/schemas/2015",
    }

    out: List[Dict[str, str]] = []
    for entry in root.findall("atom:entry", ns):
        out.append(
            {
                "video_id": entry.findtext("yt:videoId", default="", namespaces=ns).strip(),
                "title": entry.findtext("atom:title", default="", namespaces=ns).strip(),
                "published": entry.findtext("atom:published", default="", namespaces=ns).strip(),
            }
        )
    return out


def find_video_id_by_keywords(videos: List[Dict[str, str]], keywords: List[str]) -> str:
    # Latest-first list from RSS: first matching title wins.
    kws = [k.casefold() for k in keywords]
    for v in videos:
        t = (v.get("title") or "").casefold()
        if all(k in t for k in kws):
            return v.get("video_id") or ""
    return ""


def main() -> None:
    data = json.loads(EVENTS_PATH.read_text(encoding="utf-8"))
    events = data.get("events") or []
    if not isinstance(events, list):
        raise SystemExit("events.json: `events` must be a list")

    videos = fetch_latest_videos(TARIH101_CHANNEL_ID)
    if not videos:
        print("No videos fetched from Tarih101 feed; no changes made.")
        return

    event_by_id: Dict[str, dict] = {
        str(e.get("id")): e for e in events if isinstance(e, dict) and e.get("id")
    }

    changed: List[Tuple[str, str, str]] = []  # (event_id, event_title, video_id)
    skipped_existing = 0
    missing_event_ids: List[str] = []
    missing_video_match: List[str] = []

    for event_id, keywords in EVENT_VIDEO_RULES.items():
        ev = event_by_id.get(event_id)
        if not ev:
            missing_event_ids.append(event_id)
            continue
        if ev.get("youtube_video_id"):
            skipped_existing += 1
            continue
        video_id = find_video_id_by_keywords(videos, keywords)
        if not video_id:
            missing_video_match.append(event_id)
            continue

        ev["youtube_video_id"] = video_id
        changed.append((event_id, str(ev.get("title") or ""), video_id))

    if changed:
        EVENTS_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print("Tarih101 video enrichment complete.")
    print(f"- feed videos fetched: {len(videos)}")
    print(f"- rules: {len(EVENT_VIDEO_RULES)}")
    print(f"- updated events: {len(changed)}")
    print(f"- skipped (already had youtube_video_id): {skipped_existing}")
    if missing_event_ids:
        print(f"- missing event ids: {len(missing_event_ids)} ({', '.join(missing_event_ids)})")
    if missing_video_match:
        print(f"- no matching video in current feed for: {len(missing_video_match)} ({', '.join(missing_video_match)})")
    if changed:
        print("- changes:")
        for event_id, title, video_id in changed:
            print(f"  - {event_id}: {title} -> {video_id}")


if __name__ == "__main__":
    main()

