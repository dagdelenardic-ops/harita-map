#!/usr/bin/env python3
"""
Normalize/fix Wikipedia links in data/events.json.

Goals:
- Prefer Turkish Wikipedia article when available; otherwise fall back to English.
- Replace legacy Google-Translate + Special:Search links with direct article URLs.
- Store the resolved link in `wikipedia_url` and remove `[Wikipedia](...)` from descriptions.
- Regenerate offline Admin embeds (admin/data.js, admin/country_mappings.js).
"""

from __future__ import annotations

import argparse
import json
import re
import time
import urllib.parse
from pathlib import Path
from typing import Dict, Optional, Tuple

import requests


BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_EVENTS_PATH = BASE_DIR / "data" / "events.json"
ADMIN_DIR = BASE_DIR / "admin"
ADMIN_EVENTS_EMBED_PATH = ADMIN_DIR / "data.js"
ADMIN_COUNTRY_MAPPINGS_EMBED_PATH = ADMIN_DIR / "country_mappings.js"
COUNTRY_MAPPINGS_PATH = BASE_DIR / "data" / "country_mappings.json"

USER_AGENT = "Mozilla/5.0 (HaritaBot/1.0; +https://jeopolitik.com.tr)"


WIKI_MD_RE = re.compile(r"\[Wikipedia\]\(([^)]+)\)")


def _strip_wiki_md(desc: str) -> str:
    if not desc:
        return ""
    s = str(desc)
    # Remove well-formed markdown links
    s = re.sub(r"\s*\[Wikipedia\]\([^)]+\)", "", s)
    # Remove incomplete/truncated patterns (seen in a couple of gap-fill descriptions)
    s = re.sub(r"\s*\[Wikipedia\]\([^\n]*$", "", s)
    return s.strip()


def _extract_wiki_md_url(desc: str) -> str:
    if not desc:
        return ""
    m = WIKI_MD_RE.search(desc)
    if m:
        return (m.group(1) or "").strip()
    # If it's truncated, we can't safely extract a URL here.
    return ""


def _unwrap_translate(url: str) -> str:
    if not url:
        return ""
    try:
        p = urllib.parse.urlparse(url)
        if p.netloc not in ("translate.google.com", "translate.googleusercontent.com"):
            return url
        q = urllib.parse.parse_qs(p.query)
        u = (q.get("u") or [""])[0]
        return u or url
    except Exception:
        return url


def _parse_wikipedia_url(url: str) -> Optional[Tuple[str, str, str]]:
    """
    Returns:
    - (lang, kind, value)
      kind: "page" (value=title) | "search" (value=query)
    """
    if not url:
        return None
    try:
        p = urllib.parse.urlparse(url)
    except Exception:
        return None
    if not p.netloc.endswith(".wikipedia.org"):
        return None
    lang = p.netloc.split(".")[0]

    # /wiki/<title>
    if p.path.startswith("/wiki/"):
        tail = p.path[len("/wiki/") :]
        tail = urllib.parse.unquote(tail)
        if tail.startswith("Special:Search"):
            q = urllib.parse.parse_qs(p.query)
            query = (q.get("search") or [""])[0]
            return (lang, "search", query.strip())
        title = tail.replace("_", " ").strip()
        if title:
            return (lang, "page", title)
        return None

    # /w/index.php?title=... or ...?search=...
    if p.path.endswith("/w/index.php"):
        q = urllib.parse.parse_qs(p.query)
        if q.get("search"):
            return (lang, "search", (q.get("search") or [""])[0].strip())
        if q.get("title"):
            title = (q.get("title") or [""])[0]
            title = urllib.parse.unquote(title).replace("_", " ").strip()
            if title:
                return (lang, "page", title)
        return None

    return None


def _wiki_url(lang: str, title: str) -> str:
    t = (title or "").strip().replace(" ", "_")
    if not t:
        return ""
    return f"https://{lang}.wikipedia.org/wiki/{urllib.parse.quote(t)}"


class WikiResolver:
    def __init__(self) -> None:
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})
        self.search_cache: Dict[Tuple[str, str], str] = {}
        self.langlink_cache: Dict[Tuple[str, str, str], str] = {}
        self._last_req = 0.0

    def _throttle(self) -> None:
        # Be kind: tiny delay between API calls.
        now = time.time()
        if now - self._last_req < 0.05:
            time.sleep(0.05 - (now - self._last_req))
        self._last_req = time.time()

    def search_title(self, query: str, lang: str) -> str:
        q = (query or "").strip()
        if not q:
            return ""
        key = (lang, q)
        if key in self.search_cache:
            return self.search_cache[key]

        self._throttle()
        try:
            r = self.session.get(
                f"https://{lang}.wikipedia.org/w/api.php",
                params={
                    "action": "query",
                    "list": "search",
                    "srsearch": q,
                    "srlimit": 1,
                    "format": "json",
                    "utf8": 1,
                },
                timeout=10,
            )
            if r.status_code != 200:
                self.search_cache[key] = ""
                return ""
            data = r.json()
            hits = (data.get("query") or {}).get("search") or []
            title = (hits[0].get("title") if hits else "") or ""
            self.search_cache[key] = title
            return title
        except Exception:
            self.search_cache[key] = ""
            return ""

    def langlink_title(self, from_title: str, from_lang: str, to_lang: str) -> str:
        title = (from_title or "").strip()
        if not title:
            return ""
        key = (from_lang, to_lang, title)
        if key in self.langlink_cache:
            return self.langlink_cache[key]

        self._throttle()
        try:
            r = self.session.get(
                f"https://{from_lang}.wikipedia.org/w/api.php",
                params={
                    "action": "query",
                    "prop": "langlinks",
                    "titles": title,
                    "redirects": 1,
                    "lllang": to_lang,
                    "format": "json",
                    "utf8": 1,
                },
                timeout=10,
            )
            if r.status_code != 200:
                self.langlink_cache[key] = ""
                return ""
            data = r.json()
            pages = (data.get("query") or {}).get("pages") or {}
            out = ""
            for page in pages.values():
                ll = page.get("langlinks") or []
                if ll:
                    out = (ll[0].get("*") or ll[0].get("title") or "").strip()
                    break
            self.langlink_cache[key] = out
            return out
        except Exception:
            self.langlink_cache[key] = ""
            return ""

    def resolve_prefer_tr(self, url_or_title: str, from_lang: str = "en") -> str:
        """
        Given an EN title or EN url, prefer TR page when an interlanguage link exists.
        Returns a direct article URL (TR or EN).
        """
        s = (url_or_title or "").strip()
        if not s:
            return ""
        parsed = _parse_wikipedia_url(s)
        if parsed and parsed[1] == "page":
            lang, _kind, title = parsed
            if lang == "tr":
                return _wiki_url("tr", title)
            if lang == "en":
                tr_title = self.langlink_title(title, "en", "tr")
                return _wiki_url("tr", tr_title) if tr_title else _wiki_url("en", title)
            return _wiki_url(lang, title)

        # Treat as a title in from_lang
        title = s.replace("_", " ").strip()
        if from_lang == "tr":
            return _wiki_url("tr", title)
        if from_lang == "en":
            tr_title = self.langlink_title(title, "en", "tr")
            return _wiki_url("tr", tr_title) if tr_title else _wiki_url("en", title)
        return ""

    def resolve_by_query(self, query: str, country: str = "") -> str:
        q = (query or "").strip()
        c = (country or "").strip()
        if not q:
            return ""

        # Prefer disambiguation with country first (often yields better event-specific pages).
        tr_queries = [f"{c} {q}", q] if c else [q]
        en_queries = tr_queries

        # 1) TR search
        for qq in tr_queries:
            t = self.search_title(qq, "tr")
            if t:
                return _wiki_url("tr", t)

        # 2) EN search (then map to TR if possible)
        t_en = ""
        for qq in en_queries:
            t_en = self.search_title(qq, "en")
            if t_en:
                break
        if t_en:
            tr_title = self.langlink_title(t_en, "en", "tr")
            return _wiki_url("tr", tr_title) if tr_title else _wiki_url("en", t_en)

        return ""


def fix_wiki_links(events_path: Path) -> None:
    data = json.loads(events_path.read_text(encoding="utf-8"))
    events = data.get("events") or []

    resolver = WikiResolver()

    updated_desc = 0
    updated_wiki = 0
    filled_wiki = 0
    kept_wiki = 0
    unresolved = 0

    for ev in events:
        if not isinstance(ev, dict):
            continue

        title = (ev.get("title") or "").strip()
        country = (ev.get("country_name") or "").strip()

        desc = ev.get("description") or ""
        desc_has_wiki = "[Wikipedia](" in desc
        desc_url = _extract_wiki_md_url(desc)
        clean_desc = _strip_wiki_md(desc)
        if clean_desc != desc:
            ev["description"] = clean_desc
            updated_desc += 1

        old_url = (ev.get("wikipedia_url") or "").strip()
        candidate_url = _unwrap_translate(old_url or desc_url)

        new_url = ""

        has_hint = bool(old_url) or bool(desc_url) or desc_has_wiki

        if has_hint:
            parsed = _parse_wikipedia_url(candidate_url)
            if parsed:
                lang, kind, value = parsed
                if kind == "page":
                    if lang == "tr":
                        new_url = _wiki_url("tr", value)
                    elif lang == "en":
                        new_url = resolver.resolve_prefer_tr(value, from_lang="en")
                    else:
                        new_url = _wiki_url(lang, value)
                elif kind == "search":
                    query = value or title
                    new_url = resolver.resolve_by_query(query, country=country)
            else:
                # No usable URL: resolve from the event's title (only when we had a wiki hint).
                new_url = resolver.resolve_by_query(title, country=country)

        if new_url:
            if not old_url:
                ev["wikipedia_url"] = new_url
                filled_wiki += 1
            elif new_url != old_url:
                ev["wikipedia_url"] = new_url
                updated_wiki += 1
            else:
                kept_wiki += 1
        else:
            # Keep existing url if any, otherwise mark unresolved.
            if old_url:
                kept_wiki += 1
            else:
                unresolved += 1

    events_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # Regenerate offline Admin embeds
    ADMIN_EVENTS_EMBED_PATH.write_text(
        "window.__EVENTS_DATA__ = " + json.dumps(data, ensure_ascii=False) + ";\n",
        encoding="utf-8",
    )
    country_mappings = json.loads(COUNTRY_MAPPINGS_PATH.read_text(encoding="utf-8"))
    ADMIN_COUNTRY_MAPPINGS_EMBED_PATH.write_text(
        "window.__COUNTRY_MAPPINGS__ = "
        + json.dumps(country_mappings.get("countries") or [], ensure_ascii=False)
        + ";\n",
        encoding="utf-8",
    )

    print("Wiki normalization complete.")
    print(f"- Description wiki links removed: {updated_desc}")
    print(f"- wikipedia_url filled (was empty): {filled_wiki}")
    print(f"- wikipedia_url updated (existing changed): {updated_wiki}")
    print(f"- wikipedia_url unchanged: {kept_wiki}")
    print(f"- unresolved (still empty): {unresolved}")
    print(f"- wrote: {events_path}")
    print(f"- admin embeds: {ADMIN_EVENTS_EMBED_PATH}, {ADMIN_COUNTRY_MAPPINGS_EMBED_PATH}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--events", default=str(DEFAULT_EVENTS_PATH), help="Path to events.json")
    args = parser.parse_args()
    fix_wiki_links(Path(args.events))


if __name__ == "__main__":
    main()
