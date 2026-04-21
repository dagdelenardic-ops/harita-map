#!/usr/bin/env python3
"""
Backfill lightweight hierarchy and context metadata for data/events.json.

This does not invent hard parent/child chains. Instead it adds:
- category branch metadata
- event-level branch / subcategory labels
- context_level (primary / secondary / context)
- topic_slug for future grouping
- context_note for short descriptions

Usage:
  python3 scripts/backfill_event_metadata.py --dry-run
  python3 scripts/backfill_event_metadata.py --apply
"""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from pathlib import Path
from typing import Any, Dict, Iterable, Tuple


BASE_DIR = Path(__file__).resolve().parent.parent
EVENTS_PATH = BASE_DIR / "data" / "events.json"

BRANCH_META: Dict[str, Dict[str, str]] = {
    "conflict": {"label": "Jeopolitik Çatışmalar"},
    "power": {"label": "Siyaset & Güç"},
    "culture_arts": {"label": "Kültür & Sanat"},
    "society": {"label": "Toplum & Dönüşüm"},
    "other": {"label": "Diğer Başlıklar"},
}

CATEGORY_BRANCH = {
    "war": "conflict",
    "genocide": "conflict",
    "terror": "conflict",
    "revolution": "power",
    "leader": "power",
    "politics": "power",
    "diplomacy": "power",
    "culture": "culture_arts",
    "cinema": "culture_arts",
    "music": "culture_arts",
    "time_100": "culture_arts",
}

PRIMARY_TITLE_PATTERNS: Tuple[Tuple[str, ...], ...] = (
    ("bağımsızlık", "independence", "kurtuluş"),
    ("darbe", "coup", "muhtıra"),
    ("işgal", "isgali", "occupation", "invasion"),
    ("savaşı", "muharebesi", "battle", "war", "çıkarma", "blitz"),
    ("devrim", "revolution", "ayaklanma", "isyan"),
)

SECONDARY_TITLE_PATTERNS: Tuple[Tuple[str, ...], ...] = (
    ("anlaşma", "antlaşma", "mutabakat", "pakt", "ateşkes", "üyeliği", "üyelik"),
    ("seçim", "referandum", "anayasa", "reform"),
)


def _slugify(value: str) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-{2,}", "-", text).strip("-")
    return text


def _ensure_period(text: str) -> str:
    clean = str(text or "").strip()
    if not clean:
        return ""
    if re.search(r"[.!?…]$", clean):
        return clean
    return clean + "."


def _branch_for_category(category: str) -> str:
    return CATEGORY_BRANCH.get(str(category or "").strip(), "society")


def _branch_label(branch_key: str) -> str:
    return BRANCH_META.get(branch_key, BRANCH_META["other"])["label"]


def _subcategory_label(category: str, categories: Dict[str, Any]) -> str:
    cat = categories.get(category, {}) if isinstance(categories, dict) else {}
    return str(cat.get("label") or category or "Diğer").strip()


def _category_tier(category: str, categories: Dict[str, Any]) -> int:
    cat = categories.get(category, {}) if isinstance(categories, dict) else {}
    tier = cat.get("tier")
    return tier if isinstance(tier, int) else 3


def _matches_any(title: str, patterns: Iterable[Iterable[str]]) -> bool:
    lowered = str(title or "").lower()
    return any(any(token in lowered for token in group) for group in patterns)


def _context_level(event: Dict[str, Any], categories: Dict[str, Any]) -> str:
    explicit = str(event.get("context_level") or "").strip().lower()
    if explicit in {"primary", "secondary", "context"}:
        return explicit

    title = str(event.get("title") or "")
    if _matches_any(title, PRIMARY_TITLE_PATTERNS):
        return "primary"
    if _matches_any(title, SECONDARY_TITLE_PATTERNS):
        return "secondary"

    tier = _category_tier(str(event.get("category") or ""), categories)
    if tier <= 1:
        return "primary"
    if tier == 2:
        return "secondary"
    return "context"


def _context_note(event: Dict[str, Any], categories: Dict[str, Any]) -> str:
    existing = _ensure_period(event.get("context_note") or "")
    if existing:
        return existing

    description = str(event.get("description") or "").strip()
    if len(description) >= 50:
        return ""

    country = str(event.get("country_name") or "bu ülke").strip()
    title = str(event.get("title") or "bu olay").strip()
    category = str(event.get("category") or "").strip()
    sub_label = _subcategory_label(category, categories).lower()
    branch = _branch_for_category(category)
    branch_label = _branch_label(branch).lower()
    lowered_title = title.lower()

    if any(token in lowered_title for token in ("bağımsızlık", "independence", "kurtuluş")):
        return (
            f"Bu başlık, {country} için egemenlik düzeninin ve dış konumunun yeniden tanımlandığı "
            f"kurucu bir eşik olarak öne çıkar."
        )
    if any(token in lowered_title for token in ("darbe", "coup", "muhtıra")):
        return (
            f"Bu müdahale, {country} içinde iktidar düzenini keskin biçimde değiştirerek sonraki "
            f"siyasal dönemin çerçevesini belirledi."
        )
    if any(token in lowered_title for token in ("işgal", "isgali", "occupation", "invasion")):
        return (
            f"Bu gelişme, {country} açısından askeri dengeyi ve devlet kapasitesini zorlayan "
            f"belirleyici bir güvenlik kırılması yarattı."
        )
    if any(token in lowered_title for token in ("anlaşma", "antlaşma", "mutabakat", "pakt", "ateşkes")):
        return (
            f"Bu adım, {country} için dış ilişkiler hattında yeni bir müzakere zemini ve bölgesel "
            f"denge çerçevesi oluşturdu."
        )
    if any(token in lowered_title for token in ("seçim", "referandum", "anayasa")):
        return (
            f"Bu süreç, {country} içinde meşruiyet, kurumlar ve güç dağılımı tartışmalarını yeniden "
            f"şekillendiren önemli bir siyasal dönemeçti."
        )

    if category == "war":
        return (
            f"Bu çatışma, {country} tarihinde askeri dengeyi ve bölgesel güvenlik hattını etkileyen "
            f"belirleyici bir kırılma yarattı."
        )
    if category == "genocide":
        return (
            f"Bu olay, {country} tarihinde kitlesel şiddet, hafıza siyaseti ve uluslararası vicdan "
            f"üzerinde kalıcı iz bırakan ağır bir kırılma olarak anılır."
        )
    if category in {"revolution", "politics", "leader", "diplomacy"}:
        return (
            f"Bu başlık, {country} için {sub_label} ekseninde güç dengesini değiştiren ve daha geniş "
            f"{branch_label} hattına bağlanan önemli bir dönüm noktasıdır."
        )
    if category in {"culture", "cinema", "music", "time_100"}:
        return (
            f"Bu gelişme, {country} için {sub_label} alanında sembolik etki üreterek toplumsal hafıza "
            f"ve uluslararası görünürlük üzerinde kalıcı iz bıraktı."
        )
    if category == "terror":
        return (
            f"Bu saldırı, {country} içinde güvenlik algısını sert biçimde değiştirerek devletin tehdit "
            f"öncelikleri ve toplumsal psikoloji üzerinde güçlü etki yarattı."
        )

    return (
        f"Bu olay, {country} için {sub_label} hattında öne çıkan ve daha geniş {branch_label} "
        f"akışı içinde anlam kazanan önemli bir dönüm noktasıdır."
    )


def _topic_slug(event: Dict[str, Any]) -> str:
    title_slug = _slugify(event.get("title") or "")
    if not title_slug:
        title_slug = "olay"
    return title_slug[:80]


def backfill_metadata(apply: bool) -> int:
    payload = json.loads(EVENTS_PATH.read_text(encoding="utf-8"))
    categories = payload.get("categories") or {}
    events = payload.get("events") or []
    if not isinstance(categories, dict) or not isinstance(events, list):
        raise SystemExit("events.json format invalid")

    category_updates = 0
    event_updates = 0
    context_notes = 0

    for key, meta in categories.items():
        branch = _branch_for_category(key)
        branch_label = _branch_label(branch)
        changed = False
        if meta.get("branch") != branch:
            meta["branch"] = branch
            changed = True
        if meta.get("branch_label") != branch_label:
            meta["branch_label"] = branch_label
            changed = True
        if changed:
            category_updates += 1

    for event in events:
        if not isinstance(event, dict):
            continue
        category = str(event.get("category") or "").strip()
        branch = _branch_for_category(category)
        branch_label = _branch_label(branch)
        subcategory_label = _subcategory_label(category, categories)
        context_level = _context_level(event, categories)
        topic_slug = _topic_slug(event)
        context_note = _context_note(event, categories)

        changed = False
        for field, value in (
            ("branch", branch),
            ("branch_label", branch_label),
            ("subcategory", category),
            ("subcategory_label", subcategory_label),
            ("context_level", context_level),
            ("topic_slug", topic_slug),
        ):
            if event.get(field) != value:
                event[field] = value
                changed = True

        if context_note and event.get("context_note") != context_note:
            event["context_note"] = context_note
            changed = True
            context_notes += 1

        if changed:
            event_updates += 1

    print(
        f"backfill_event_metadata: categories_updated={category_updates} "
        f"events_updated={event_updates} context_notes={context_notes}"
    )

    if apply:
        EVENTS_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"wrote={EVENTS_PATH}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Write changes to data/events.json")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without writing")
    args = parser.parse_args()
    return backfill_metadata(apply=bool(args.apply))


if __name__ == "__main__":
    raise SystemExit(main())
