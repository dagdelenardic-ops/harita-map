#!/usr/bin/env python3
"""
Add suitable videos from selected YouTube channels to matching events.

Approach:
- Pull latest uploads from channel RSS feeds.
- Use conservative, event-id-based rules for high-confidence title matches.
- Never overwrite an existing `youtube_video_id`.
"""

from __future__ import annotations

import json
import re
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Tuple


BASE_DIR = Path(__file__).resolve().parent.parent
EVENTS_PATH = BASE_DIR / "data" / "events.json"

CHANNEL_IDS: Dict[str, str] = {
    "49w": "UC5_0UPuXT5SAGsbTe2T_PJg",
    "omnibuslive": "UCmZUVTP8dtWqmsVhqt7tPEQ",
    "cnklgl": "UC-xTvXTm-lrLWYk308-Km3A",
}

# Curated high-confidence mappings:
# event_id -> (channel_key, keyword list expected in video title)
EVENT_VIDEO_RULES: Dict[str, Tuple[str, List[str]]] = {
    # 49W
    "eve1b96912": ("49w", ["ronald", "reagan"]),
    # OMNIBUSLIVE
    "ev006": ("omnibuslive", ["hitler", "iktidara", "gelmesi"]),
    "ev421": ("omnibuslive", ["hitler", "delinin", "teki"]),
    # cnklgl
    "ev_tr_1960s_05": ("cnklgl", ["demirel"]),
}


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
    }
)


def normalize_text(value: str) -> str:
    s = (value or "").strip().translate(TR_TRANSLATE).lower()
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return " ".join(s.split())


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
    # Latest-first RSS list: first matching title wins.
    kws = [normalize_text(k) for k in keywords]
    for v in videos:
        t = normalize_text(v.get("title") or "")
        if all(k in t for k in kws):
            return v.get("video_id") or ""
    return ""


def main() -> None:
    data = json.loads(EVENTS_PATH.read_text(encoding="utf-8"))
    events = data.get("events") or []
    if not isinstance(events, list):
        raise SystemExit("events.json: `events` must be a list")

    # Fetch each channel once.
    videos_by_channel: Dict[str, List[Dict[str, str]]] = {}
    for channel_key, channel_id in CHANNEL_IDS.items():
        videos_by_channel[channel_key] = fetch_latest_videos(channel_id)

    event_by_id: Dict[str, dict] = {
        str(e.get("id")): e for e in events if isinstance(e, dict) and e.get("id")
    }

    changed: List[Tuple[str, str, str]] = []  # (event_id, event_title, video_id)
    skipped_existing = 0
    missing_event_ids: List[str] = []
    missing_video_match: List[str] = []
    missing_channels: List[str] = []

    for event_id, (channel_key, keywords) in EVENT_VIDEO_RULES.items():
        ev = event_by_id.get(event_id)
        if not ev:
            missing_event_ids.append(event_id)
            continue
        if ev.get("youtube_video_id"):
            skipped_existing += 1
            continue

        channel_videos = videos_by_channel.get(channel_key)
        if channel_videos is None:
            missing_channels.append(channel_key)
            continue

        video_id = find_video_id_by_keywords(channel_videos, keywords)
        if not video_id:
            missing_video_match.append(event_id)
            continue

        ev["youtube_video_id"] = video_id
        changed.append((event_id, str(ev.get("title") or ""), video_id))

    if changed:
        EVENTS_PATH.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    print("Additional channel video enrichment complete.")
    print(f"- channels fetched: {len(videos_by_channel)}")
    print(f"- rules: {len(EVENT_VIDEO_RULES)}")
    print(f"- updated events: {len(changed)}")
    print(f"- skipped (already had youtube_video_id): {skipped_existing}")
    if missing_channels:
        print(f"- missing channels: {len(missing_channels)} ({', '.join(sorted(set(missing_channels)))})")
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
