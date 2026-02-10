#!/usr/bin/env python3
"""
Reclassify a subset of `culture` events into more specific media categories.

Motivation:
- Keep "hard" geopolitical events (war/revolution/politics) distinct from "soft power" items.
- Avoid films/music showing up as if they are equal-weight to wars in the UI.

This script:
- Ensures category definitions exist (adds music/cinema if missing)
- Moves events from category=culture -> cinema/music using simple heuristics

It is intentionally conservative; it only changes events already tagged as `culture`.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple


BASE_DIR = Path(__file__).resolve().parent.parent
EVENTS_PATH = BASE_DIR / "data" / "events.json"


def _ensure_category_defs(categories: Dict[str, Any]) -> None:
    # NOTE: UI uses `label` + `color`; map markers use `icon` too.
    # `tier` is used by the map UI to render hierarchy (1=major, 2=standard, 3=context).
    defaults: Dict[str, Dict[str, Any]] = {
        "war": {"label": "Savas/Catisma", "icon": "fa-fire", "color": "#e74c3c", "tier": 1},
        "genocide": {"label": "Soykirim", "icon": "fa-skull", "color": "#2c3e50", "tier": 1},
        "revolution": {"label": "Devrim/Rejim Degisikligi", "icon": "fa-flag", "color": "#e67e22", "tier": 1},
        "terror": {"label": "Teror Saldirisi", "icon": "fa-bomb", "color": "#9b59b6", "tier": 2},
        "politics": {"label": "Politika", "icon": "fa-landmark", "color": "#16a085", "tier": 2},
        "diplomacy": {"label": "Diplomasi", "icon": "fa-handshake", "color": "#2ecc71", "tier": 2},
        "leader": {"label": "Onemli Lider", "icon": "fa-user", "color": "#3498db", "tier": 2},
        "time_100": {"label": "Time 100: Yüzyılın En Önemli Kişileri", "color": "#f1c40f", "tier": 3},
        "culture": {"label": "Kültür & Toplum", "color": "#6c5ce7", "tier": 3},
        "cinema": {"label": "Sinema", "icon": "fa-film", "color": "#95a5a6", "tier": 3},
        "music": {"label": "Müzik", "icon": "fa-music", "color": "#e84393", "tier": 3},
    }

    for k, v in defaults.items():
        categories.setdefault(k, {})
        if not isinstance(categories[k], dict):
            categories[k] = {}
        for kk, vv in v.items():
            categories[k].setdefault(kk, vv)


def _text(ev: Dict[str, Any]) -> str:
    return f"{ev.get('title') or ''}\n{ev.get('description') or ''}".strip()


def _should_cinema(t: str) -> bool:
    # Prefer explicit film terms; avoid generic "festival" which is ambiguous.
    return bool(
        re.search(
            r"\b(film|sinema|cannes|oscar|altın palmiye|altin palmiye|prömiyer|promiyer|gösterim|gosterim)\b",
            t,
            re.IGNORECASE,
        )
    )


def _should_music(t: str) -> bool:
    return bool(
        re.search(
            r"\b(müzik|muzik|konser|albüm|album|şarkı|sarki|grup|grammy)\b",
            t,
            re.IGNORECASE,
        )
    )


def main() -> None:
    data = json.loads(EVENTS_PATH.read_text(encoding="utf-8"))
    events = data.get("events") or []
    if not isinstance(events, list):
        raise SystemExit("events.json: `events` must be a list")

    categories = data.get("categories") or {}
    if not isinstance(categories, dict):
        categories = {}
    _ensure_category_defs(categories)
    data["categories"] = categories

    changed = 0
    changed_samples: List[Tuple[str, int, str, str, str]] = []
    for ev in events:
        if not isinstance(ev, dict):
            continue
        if (ev.get("category") or "").strip() != "culture":
            continue
        t = _text(ev)
        if not t:
            continue
        new_cat = None
        if _should_cinema(t):
            new_cat = "cinema"
        elif _should_music(t):
            new_cat = "music"
        if new_cat and new_cat != ev.get("category"):
            ev["category"] = new_cat
            changed += 1
            if len(changed_samples) < 25:
                changed_samples.append(
                    (
                        str(ev.get("country_name") or ""),
                        int(ev.get("year") or 0),
                        str(ev.get("title") or ""),
                        "culture",
                        new_cat,
                    )
                )

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_path = EVENTS_PATH.with_suffix(f".json.bak.{ts}")
    backup_path.write_text(EVENTS_PATH.read_text(encoding="utf-8"), encoding="utf-8")
    EVENTS_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print("Reclassification complete.")
    print(f"- culture -> cinema/music changes: {changed}")
    print(f"- Backup: {backup_path}")
    if changed_samples:
        print("- Sample changes:")
        for country, year, title, old, new in changed_samples[:10]:
            print(f"  - {country} {year}: {title} ({old} -> {new})")


if __name__ == "__main__":
    main()

