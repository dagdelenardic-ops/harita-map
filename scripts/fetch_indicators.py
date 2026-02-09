#!/usr/bin/env python3
"""
Fetch up-to-date external datasets and write them to data/indicators.json.

Datasets:
- NATO member states (Wikipedia: Member states of NATO)
- Minimum wage by country (Wikipedia: List of countries by minimum wage)
- Big Mac Index (The Economist GitHub: big-mac-full-index.csv)
- G8 country list (static; canonicalized via country_mappings.json)

Output is keyed by the project's canonical Turkish country names from data/country_mappings.json.
"""

from __future__ import annotations

import csv
import io
import json
import re
import sys
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from bs4 import BeautifulSoup


BASE_DIR = Path(__file__).resolve().parent.parent
COUNTRY_MAPPINGS_PATH = BASE_DIR / "data" / "country_mappings.json"
OUTPUT_PATH = BASE_DIR / "data" / "indicators.json"


USER_AGENT = "Mozilla/5.0 (HaritaBot/1.0; +https://jeopolitik.com.tr)"

# Sources (kept here so URLs are not scattered)
WIKI_NATO_URL = "https://en.wikipedia.org/wiki/Member_states_of_NATO"
WIKI_MIN_WAGE_URL = "https://en.wikipedia.org/wiki/List_of_countries_by_minimum_wage"
BIGMAC_CSV_URL = (
    "https://raw.githubusercontent.com/TheEconomist/big-mac-data/master/output-data/big-mac-full-index.csv"
)


_TR_TRANSLATE = str.maketrans(
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


def _normalize_lookup_key(value: str) -> str:
    if value is None:
        return ""
    s = str(value).strip()
    s = (
        s.replace("\u2019", "'")
        .replace("\u2018", "'")
        .replace("\u201B", "'")
        .replace("\u02BC", "'")
        .replace("’", "'")
        .replace("‘", "'")
    )
    s = " ".join(s.split()).lower()
    s = s.translate(_TR_TRANSLATE)
    return s


@dataclass(frozen=True)
class CountryCanon:
    turkish: str
    iso2: str  # uppercased


def _load_country_index() -> Tuple[Dict[str, CountryCanon], Dict[str, CountryCanon]]:
    with open(COUNTRY_MAPPINGS_PATH, "r", encoding="utf-8") as f:
        mappings = json.load(f).get("countries", [])

    lookup: Dict[str, CountryCanon] = {}
    by_turkish: Dict[str, CountryCanon] = {}

    for entry in mappings:
        tr = (entry.get("turkish") or "").strip()
        iso2 = (entry.get("iso2") or "").strip().upper()
        if not tr:
            continue
        canon = CountryCanon(turkish=tr, iso2=iso2)
        by_turkish[tr] = canon

        keys: List[str] = []
        if entry.get("turkish"):
            keys.append(entry["turkish"])
        if entry.get("english"):
            keys.append(entry["english"])
        keys.extend(entry.get("aliases") or [])

        for k in keys:
            nk = _normalize_lookup_key(k)
            if nk:
                lookup.setdefault(nk, canon)

    return lookup, by_turkish


def _fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read()


def _parse_float(value: str) -> Optional[float]:
    if value is None:
        return None
    s = str(value).strip()
    if not s:
        return None
    s = s.replace("\xa0", " ")
    # Drop bracketed footnotes like [1] or [ 164 ] that often appear in Wikipedia tables.
    s = re.sub(r"\[[^\]]+\]", "", s).strip()
    # Treat known non-values
    lowered = s.lower()
    if any(
        x in lowered
        for x in [
            "no minimum wage",
            "none",
            "n/a",
            "not available",
            "varies",
            "—",
            "–",
        ]
    ):
        return None
    # Remove currency symbols and thousands separators; keep dot and minus
    s = re.sub(r"[^0-9,.\-]", "", s)
    if not s:
        return None
    # Heuristic locale parsing:
    # - If both separators exist: treat comma as thousands, dot as decimal.
    # - If only comma exists: treat as thousands if 3 digits after last comma, else decimal.
    # - If only dot exists: treat as thousands if 3 digits after last dot, else decimal.
    if "," in s and "." in s:
        s = s.replace(",", "")
    elif "," in s and "." not in s:
        tail = s.split(",")[-1]
        if len(tail) == 3:
            s = s.replace(",", "")
        else:
            s = s.replace(",", ".")
    elif "." in s and "," not in s:
        # If there are multiple dots, it's almost certainly a thousands separator format (e.g. 1.234.567).
        # With a single dot, prefer treating it as a decimal separator (e.g. -0.536), since datasets like
        # The Economist's Big Mac Index use dot-decimals.
        if s.count(".") > 1:
            s = s.replace(".", "")
    try:
        return float(s)
    except ValueError:
        return None


def _clean_country_name(value: str) -> str:
    """Remove bracketed footnotes like '[b]' or '[ note 1 ]' from country strings."""
    if value is None:
        return ""
    s = str(value)
    s = re.sub(r"\[[^\]]+\]", "", s)
    s = " ".join(s.split()).strip()
    return s


def _canonicalize(lookup: Dict[str, CountryCanon], name: str) -> Optional[CountryCanon]:
    nk = _normalize_lookup_key(_clean_country_name(name))
    if not nk:
        return None
    return lookup.get(nk)


def fetch_nato_members(lookup: Dict[str, CountryCanon]) -> Tuple[List[str], List[str]]:
    html = _fetch(WIKI_NATO_URL).decode("utf-8", "ignore")
    soup = BeautifulSoup(html, "html.parser")
    table = soup.select_one("table.wikitable")
    if not table:
        raise RuntimeError("NATO table not found on Wikipedia page")

    members: List[str] = []
    unknown: List[str] = []
    for row in table.select("tr"):
        th = row.find("th", attrs={"scope": "row"})
        if not th:
            continue
        name = _clean_country_name(th.get_text(" ", strip=True))
        canon = _canonicalize(lookup, name)
        if canon:
            members.append(canon.turkish)
        else:
            unknown.append(name)

    # Deduplicate while preserving order
    seen = set()
    out = []
    for x in members:
        if x in seen:
            continue
        seen.add(x)
        out.append(x)
    return out, unknown


def fetch_minimum_wage(lookup: Dict[str, CountryCanon]) -> Tuple[Dict[str, Dict[str, Any]], List[str]]:
    """
    Returns:
    - by_country: canonical Turkish -> details {hourly_usd_nominal, annual_usd_nominal, effective_date}
    - unknown country names (not in mappings)
    """
    html = _fetch(WIKI_MIN_WAGE_URL).decode("utf-8", "ignore")
    soup = BeautifulSoup(html, "html.parser")
    tables = soup.select("table.wikitable")
    if not tables:
        raise RuntimeError("Minimum wage tables not found on Wikipedia page")

    # The first table is the global minimum wages by country.
    table = tables[0]

    by_country: Dict[str, Dict[str, Any]] = {}
    unknown: List[str] = []

    # Column order in the global table is stable:
    # Country | Notes | Annual Nominal | Annual PPP | Work week | Hourly Nominal | Hourly PPP | %GDP | Effective date
    # NOTE: Many countries use a "$" symbol for local currency (e.g. CL$, COL$).
    # We only want USD conversions. So:
    # - Match explicit "US$" / "USD" prefixes.
    # - Or match a bare "$" only if it's not preceded by a letter (excludes CL$, COL$, etc).
    #
    # Additionally, some notes contain multiple USD amounts. We pick the maximum value as a
    # pragmatic default (typically the adult/standard wage).
    usd_prefix = r"(?:US\$|USD\$|USD\s*\$|USD|(?<![A-Za-z])\$)"
    usd_before_month_re = re.compile(
        rf"{usd_prefix}\s*([0-9][0-9,\.]*)\s*\)?\s*(?:per\s+month|/month|a\s+month)",
        re.IGNORECASE,
    )
    month_before_usd_re = re.compile(
        rf"(?:per\s+month|/month|a\s+month)[^\d]{{0,40}}{usd_prefix}\s*([0-9][0-9,\.]*)",
        re.IGNORECASE,
    )
    for row in table.select("tbody tr"):
        tds = row.find_all("td", recursive=False)
        if not tds:
            continue

        country_name = _clean_country_name(tds[0].get_text(" ", strip=True))
        canon = _canonicalize(lookup, country_name)
        if not canon:
            unknown.append(country_name)
            continue

        # Defensive: some rows might not have all 8 td cells.
        text_cells = [td.get_text(" ", strip=True) for td in tds]
        # Columns: 0 Country | 1 Notes | 2 Annual Nominal | 3 Annual PPP | 4 Work week | 5 Hourly Nominal | 6 Hourly PPP | 7 %GDP | 8 Effective date
        annual_nominal = _parse_float(text_cells[2]) if len(text_cells) > 2 else None
        work_week_hours = _parse_float(text_cells[4]) if len(text_cells) > 4 else None
        hourly_nominal = _parse_float(text_cells[5]) if len(text_cells) > 5 else None
        effective_date = text_cells[8] if len(text_cells) > 8 else ""

        # If notes contain an explicit monthly USD conversion, use it to sanity-check / override outliers.
        # This helps when the table has inconsistent conversions for a specific country.
        monthly_usd_note = None
        notes = text_cells[1] if len(text_cells) > 1 else ""
        if notes and ("per month" in notes.lower() or "a month" in notes.lower() or "/month" in notes.lower()):
            candidates: List[float] = []
            for m in usd_before_month_re.finditer(notes):
                v = _parse_float(m.group(1))
                if v:
                    candidates.append(v)
            for m in month_before_usd_re.finditer(notes):
                v = _parse_float(m.group(1))
                if v:
                    candidates.append(v)
            if candidates:
                monthly_usd_note = max(candidates)
        if monthly_usd_note and work_week_hours and work_week_hours > 0:
            annual_from_note = monthly_usd_note * 12.0
            hourly_from_note = annual_from_note / (work_week_hours * 52.0)
            if hourly_nominal and hourly_nominal > 0:
                ratio = hourly_nominal / hourly_from_note if hourly_from_note > 0 else 1.0
                if ratio > 2.0 or ratio < 0.5:
                    hourly_nominal = hourly_from_note
                    annual_nominal = annual_from_note
            else:
                hourly_nominal = hourly_from_note
                annual_nominal = annual_from_note

        by_country[canon.turkish] = {
            "hourly_usd_nominal": hourly_nominal,
            "annual_usd_nominal": annual_nominal,
            "monthly_usd_note": monthly_usd_note,
            "effective_date": effective_date,
        }

    return by_country, unknown


def fetch_big_mac_index(lookup: Dict[str, CountryCanon]) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, Any], List[str]]:
    csv_bytes = _fetch(BIGMAC_CSV_URL)
    text = csv_bytes.decode("utf-8", "ignore")
    reader = csv.DictReader(io.StringIO(text))

    rows = list(reader)
    if not rows:
        raise RuntimeError("Big Mac CSV contains no rows")

    # Latest date in dataset
    dates = sorted({r.get("date", "") for r in rows if r.get("date")})
    latest_date = dates[-1] if dates else ""

    by_country: Dict[str, Dict[str, Any]] = {}
    unknown: List[str] = []

    for r in rows:
        if latest_date and r.get("date") != latest_date:
            continue
        name = r.get("name") or ""
        canon = _canonicalize(lookup, name)
        if not canon:
            # Skip aggregates like "Euro area" etc, but keep a short list for debugging.
            if name and name not in unknown and len(unknown) < 50:
                unknown.append(name)
            continue
        by_country[canon.turkish] = {
            "date": r.get("date"),
            "currency_code": r.get("currency_code"),
            "local_price": _parse_float(r.get("local_price")),
            "dollar_price": _parse_float(r.get("dollar_price")),
            "usd_raw": _parse_float(r.get("USD_raw")),
        }

    meta = {"latest_date": latest_date, "rows_latest_date": len(by_country)}
    return by_country, meta, unknown


def main() -> None:
    lookup, _by_tr = _load_country_index()
    now_utc = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    nato_members, nato_unknown = fetch_nato_members(lookup)

    min_wage_by_country, min_wage_unknown = fetch_minimum_wage(lookup)

    bigmac_by_country, bigmac_meta, bigmac_unknown = fetch_big_mac_index(lookup)

    # Static BRICS+ list (as of Jan 2025 expansion, incl. Indonesia; canonicalized via mappings)
    # Source: brics.br (Brazilian BRICS presidency comms).
    brics_plus_en = [
        "Brazil",
        "Russia",
        "India",
        "China",
        "South Africa",
        "Saudi Arabia",
        "Egypt",
        "United Arab Emirates",
        "Ethiopia",
        "Iran",
        "Indonesia",
    ]
    brics_plus = []
    for n in brics_plus_en:
        canon = _canonicalize(lookup, n)
        if canon:
            brics_plus.append(canon.turkish)
    brics_plus = sorted(set(brics_plus))

    # Static G8 list (canonicalized via mappings)
    g8_en = [
        "Canada",
        "France",
        "Germany",
        "Italy",
        "Japan",
        "Russia",
        "United Kingdom",
        "United States",
    ]
    g8 = []
    for n in g8_en:
        canon = _canonicalize(lookup, n)
        if canon:
            g8.append(canon.turkish)
    g8 = sorted(set(g8))

    payload: Dict[str, Any] = {
        "fetched_at_utc": now_utc,
        "groups": {
            "g8": g8,
            "nato": nato_members,
            "brics_plus": brics_plus,
            "sources": {
                "g8": {"type": "static", "note": "Classic G8 members (incl. Russia)"},
                "nato": {"type": "wikipedia", "url": WIKI_NATO_URL},
                "brics_plus": {
                    "type": "static",
                    "note": "BRICS+ full members (incl. Indonesia, Jan 2025 expansion) - see brics.br",
                },
            },
        },
        "indicators": {
            "min_wage": {
                "label": "Asgari Ücret (USD/saat, nominal)",
                "unit": "USD/saat",
                "source": {"type": "wikipedia", "url": WIKI_MIN_WAGE_URL},
                "by_country": min_wage_by_country,
            },
            "bigmac": {
                "label": "Big Mac Endeksi (USD)",
                "unit": "USD",
                "source": {"type": "github", "url": BIGMAC_CSV_URL, **bigmac_meta},
                "by_country": bigmac_by_country,
            },
        },
    }

    OUTPUT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print("Wrote:", OUTPUT_PATH)
    print("- NATO members:", len(nato_members), "(unknown:", len(nato_unknown), ")")
    print("- BRICS+ members:", len(brics_plus))
    print("- Min wage countries:", len(min_wage_by_country), "(unknown:", len(min_wage_unknown), ")")
    print("- Big Mac countries:", len(bigmac_by_country), "as of", bigmac_meta.get("latest_date"))

    # Exit non-zero only if critical datasets are empty.
    if not nato_members or not bigmac_by_country:
        print("ERROR: critical dataset fetch returned empty results", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
