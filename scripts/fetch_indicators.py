#!/usr/bin/env python3
"""
Fetch up-to-date external datasets and write them to the repo's build-time snapshots.

Primary outputs:
- data/indicators.json (groups + baseline economic/water indicators)
- data/sanctions.json
- data/weather.json
- data/air_quality.json
- data/fx.json

Design notes:
- All outputs are country-keyed using canonical Turkish names from country_mappings.json.
- Strategic snapshots keep the previous successful file if a provider call fails.
- OpenAQ support is optional. If no API key is present, air quality falls back to Open-Meteo.
"""

from __future__ import annotations

import csv
import io
import json
import math
import os
import re
import sys
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from bs4 import BeautifulSoup


BASE_DIR = Path(__file__).resolve().parent.parent
COUNTRY_MAPPINGS_PATH = BASE_DIR / "data" / "country_mappings.json"
COUNTRIES_GEOJSON_PATH = BASE_DIR / "data" / "countries.geojson"
EVENTS_PATH = BASE_DIR / "data" / "events.json"
OUTPUT_PATH = BASE_DIR / "data" / "indicators.json"
SANCTIONS_PATH = BASE_DIR / "data" / "sanctions.json"
WEATHER_PATH = BASE_DIR / "data" / "weather.json"
AIR_QUALITY_PATH = BASE_DIR / "data" / "air_quality.json"
FX_PATH = BASE_DIR / "data" / "fx.json"


USER_AGENT = "Mozilla/5.0 (HaritaBot/1.0; +https://jeopolitik.com.tr)"

# Sources (kept here so URLs are not scattered)
WIKI_NATO_URL = "https://en.wikipedia.org/wiki/Member_states_of_NATO"
WIKI_MIN_WAGE_URL = "https://en.wikipedia.org/wiki/List_of_countries_by_minimum_wage"
BIGMAC_CSV_URL = (
    "https://raw.githubusercontent.com/TheEconomist/big-mac-data/master/output-data/big-mac-full-index.csv"
)
WORLD_BANK_API_TEMPLATE = (
    "https://api.worldbank.org/v2/country/all/indicator/{indicator}"
    "?format=json&per_page=20000&mrv=1"
)
REST_COUNTRIES_URL = (
    "https://restcountries.com/v3.1/all"
    "?fields=name,cca2,currencies,capital,capitalInfo"
)
OPEN_METEO_WEATHER_URL = "https://api.open-meteo.com/v1/forecast"
OPEN_METEO_AIR_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
OPENAQ_BASE_URL = "https://api.openaq.org"
FRANKFURTER_CURRENCIES_URL = "https://api.frankfurter.dev/v1/currencies"
FRANKFURTER_LATEST_URL = "https://api.frankfurter.dev/v1/latest"
FRANKFURTER_DATE_URL = "https://api.frankfurter.dev/v1/{date}"
OPENSANCTIONS_INDEX_URL = "https://data.opensanctions.org/datasets/latest/sanctions/index.json"

WORLD_BANK_AGGREGATES = {
    "AFE", "AFW", "ARB", "CSS", "CEB", "EAP", "EAR", "EAS", "ECA", "ECS", "EMU", "EUU",
    "FCS", "HIC", "HPC", "IBD", "IBT", "IDA", "IDB", "IDX", "INX", "LAC", "LCN", "LDC",
    "LIC", "LMC", "LMY", "LTE", "MEA", "MIC", "MNA", "NAC", "OED", "OSS", "PRE", "PSS",
    "PST", "SAS", "SSA", "SSF", "SST", "TEA", "TEC", "TLA", "TMN", "TSA", "TSS", "UMC",
    "WLD",
}

WORLD_BANK_WATER_INDICATORS = {
    "water_internal_total": {
        "code": "ER.H2O.INTR.K3",
        "label": "Yenilenebilir İç Tatlı Su (milyar m3)",
        "unit": "milyar m3",
        "decimals": 1,
    },
    "water_internal_per_capita": {
        "code": "ER.H2O.INTR.PC",
        "label": "Yenilenebilir İç Tatlı Su / Kişi",
        "unit": "m3/kişi",
        "decimals": 0,
    },
    "water_stress": {
        "code": "ER.H2O.FWST.ZS",
        "label": "Su Stresi",
        "unit": "%",
        "decimals": 1,
    },
    "water_withdrawal_pct_internal": {
        "code": "ER.H2O.FWTL.ZS",
        "label": "Su Çekimi / İç Kaynak",
        "unit": "%",
        "decimals": 1,
    },
    "water_use_agriculture": {
        "code": "ER.H2O.FWAG.ZS",
        "label": "Su Kullanımı: Tarım Payı",
        "unit": "%",
        "decimals": 1,
    },
    "water_use_industry": {
        "code": "ER.H2O.FWIN.ZS",
        "label": "Su Kullanımı: Sanayi Payı",
        "unit": "%",
        "decimals": 1,
    },
    "water_use_domestic": {
        "code": "ER.H2O.FWDM.ZS",
        "label": "Su Kullanımı: Evsel Pay",
        "unit": "%",
        "decimals": 1,
    },
}

OPEN_METEO_WEATHER_FIELDS = [
    "temperature_2m",
    "apparent_temperature",
    "precipitation",
    "cloud_cover",
    "wind_speed_10m",
    "weather_code",
]

OPEN_METEO_AIR_FIELDS = [
    "pm10",
    "pm2_5",
    "nitrogen_dioxide",
    "ozone",
    "european_aqi",
]

SPECIAL_VISUAL_CENTERS = {
    "ABD": (39.8, -98.5),
    "Birleşik Krallık": (52.5, -1.0),
    "Çin": (32.0, 110.0),
    "Fransa": (46.6, 2.2),
    "Kanada": (50.0, -100.0),
    "Rusya": (55.75, 37.61),
    "Ukrayna": (48.3794, 31.1656),
}

OPENAQ_PARAMETER_MAP = {
    "pm25": "pm2_5",
    "pm2_5": "pm2_5",
    "pm10": "pm10",
    "no2": "nitrogen_dioxide",
    "nitrogen_dioxide": "nitrogen_dioxide",
    "o3": "ozone",
    "ozone": "ozone",
}

WEATHER_CODE_LABELS = {
    0: "Acik",
    1: "Az bulutlu",
    2: "Parcali bulutlu",
    3: "Kapali",
    45: "Sis",
    48: "Kirağılı sis",
    51: "Hafif cise",
    53: "Cise",
    55: "Yogun cise",
    56: "Hafif buzlu cise",
    57: "Yogun buzlu cise",
    61: "Hafif yagmur",
    63: "Yagmur",
    65: "Kuvvetli yagmur",
    66: "Hafif buzlu yagmur",
    67: "Kuvvetli buzlu yagmur",
    71: "Hafif kar",
    73: "Kar",
    75: "Yogun kar",
    77: "Kar tanesi",
    80: "Hafif saganak",
    81: "Saganak",
    82: "Kuvvetli saganak",
    85: "Hafif kar saganagi",
    86: "Kuvvetli kar saganagi",
    95: "Gok gurultulu firtina",
    96: "Dolu ihtimalli firtina",
    99: "Siddetli dolulu firtina",
}

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

SPECIAL_CANONICAL_NAMES = {
    "bahamas, the": "Bahamalar",
    "brunei darussalam": "Brunei",
    "cape verde": "Cabo Verde",
    "congo, dem. rep.": "Demokratik Kongo Cumhuriyeti",
    "congo, rep.": "Kongo Cumhuriyeti",
    "cote d'ivoire": "Fildişi Sahili",
    "egypt, arab rep.": "Mısır",
    "gambia, the": "Gambiya",
    "hong kong sar, china": "Hong Kong",
    "iran, islamic rep.": "İran",
    "kyrgyz republic": "Kırgızistan",
    "lao pdr": "Laos",
    "macao sar, china": "Makao",
    "micronesia, fed. sts.": "Mikronezya",
    "russian federation": "Rusya",
    "slovak republic": "Slovakya",
    "syrian arab republic": "Suriye",
    "turkiye": "Türkiye",
    "venezuela, rb": "Venezuela",
    "viet nam": "Vietnam",
    "west bank and gaza": "Filistin",
    "yemen, rep.": "Yemen",
}


@dataclass(frozen=True)
class CountryCanon:
    turkish: str
    english: str
    iso2: str  # uppercased


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


def _load_country_index() -> Tuple[Dict[str, CountryCanon], Dict[str, CountryCanon], Dict[str, CountryCanon]]:
    with open(COUNTRY_MAPPINGS_PATH, "r", encoding="utf-8") as f:
        mappings = json.load(f).get("countries", [])

    lookup: Dict[str, CountryCanon] = {}
    by_turkish: Dict[str, CountryCanon] = {}
    by_iso2: Dict[str, CountryCanon] = {}

    for entry in mappings:
        tr = (entry.get("turkish") or "").strip()
        en = (entry.get("english") or "").strip()
        iso2 = (entry.get("iso2") or "").strip().upper()
        if not tr:
            continue
        canon = CountryCanon(turkish=tr, english=en, iso2=iso2)
        by_turkish[tr] = canon
        if iso2:
            by_iso2[iso2] = canon

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

    return lookup, by_turkish, by_iso2


def _fetch(url: str, *, timeout: int = 30, headers: Optional[Dict[str, str]] = None) -> bytes:
    req_headers = {"User-Agent": USER_AGENT}
    if headers:
        req_headers.update(headers)
    req = urllib.request.Request(url, headers=req_headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def _fetch_json(url: str, *, timeout: int = 30, headers: Optional[Dict[str, str]] = None) -> Any:
    raw = _fetch(url, timeout=timeout, headers=headers)
    return json.loads(raw.decode("utf-8", "ignore"))


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _load_existing_payload(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _snapshot_stub(now_utc: str, provider: str, source_note: str = "") -> Dict[str, Any]:
    return {
        "provider": provider,
        "updated_at_utc": now_utc,
        "source_note": source_note,
        "countries": {},
    }


def _persist_with_fallback(
    path: Path,
    *,
    label: str,
    provider: str,
    now_utc: str,
    fetcher,
) -> Dict[str, Any]:
    try:
        payload = fetcher()
        _write_json(path, payload)
        print(f"- {label}: fresh snapshot -> {path.name}")
        return payload
    except Exception as exc:
        existing = _load_existing_payload(path)
        if existing:
            print(f"WARNING: {label} fetch failed, keeping previous snapshot in {path.name}: {exc}")
            return existing
        fallback = _snapshot_stub(now_utc, provider, f"fetch failed: {exc}")
        _write_json(path, fallback)
        print(f"WARNING: {label} fetch failed, wrote empty snapshot to {path.name}: {exc}")
        return fallback


def _parse_float(value: str) -> Optional[float]:
    if value is None:
        return None
    s = str(value).strip()
    if not s:
        return None
    s = s.replace("\xa0", " ")
    s = re.sub(r"\[[^\]]+\]", "", s).strip()
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
    s = re.sub(r"[^0-9,.\-]", "", s)
    if not s:
        return None
    if "," in s and "." in s:
        s = s.replace(",", "")
    elif "," in s and "." not in s:
        tail = s.split(",")[-1]
        if len(tail) == 3:
            s = s.replace(",", "")
        else:
            s = s.replace(",", ".")
    elif "." in s and "," not in s and s.count(".") > 1:
        s = s.replace(".", "")
    try:
        return float(s)
    except ValueError:
        return None


def _clean_country_name(value: str) -> str:
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
    canon = lookup.get(nk)
    if canon:
        return canon
    special = SPECIAL_CANONICAL_NAMES.get(nk)
    if special:
        return lookup.get(_normalize_lookup_key(special))
    return None


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

    seen = set()
    out = []
    for x in members:
        if x in seen:
            continue
        seen.add(x)
        out.append(x)
    return out, unknown


def fetch_minimum_wage(lookup: Dict[str, CountryCanon]) -> Tuple[Dict[str, Dict[str, Any]], List[str]]:
    html = _fetch(WIKI_MIN_WAGE_URL).decode("utf-8", "ignore")
    soup = BeautifulSoup(html, "html.parser")
    tables = soup.select("table.wikitable")
    if not tables:
        raise RuntimeError("Minimum wage tables not found on Wikipedia page")

    table = tables[0]

    by_country: Dict[str, Dict[str, Any]] = {}
    unknown: List[str] = []

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

        text_cells = [td.get_text(" ", strip=True) for td in tds]
        annual_nominal = _parse_float(text_cells[2]) if len(text_cells) > 2 else None
        work_week_hours = _parse_float(text_cells[4]) if len(text_cells) > 4 else None
        hourly_nominal = _parse_float(text_cells[5]) if len(text_cells) > 5 else None
        effective_date = text_cells[8] if len(text_cells) > 8 else ""

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


def fetch_world_bank_indicator(
    lookup: Dict[str, CountryCanon], indicator_code: str
) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, Any], List[str]]:
    url = WORLD_BANK_API_TEMPLATE.format(indicator=indicator_code)
    payload = _fetch_json(url)
    if not isinstance(payload, list) or len(payload) < 2:
        raise RuntimeError(f"Unexpected World Bank response for {indicator_code}")

    meta_raw = payload[0] if isinstance(payload[0], dict) else {}
    rows = payload[1] if isinstance(payload[1], list) else []

    by_country: Dict[str, Dict[str, Any]] = {}
    unknown: List[str] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        value = row.get("value")
        if value is None:
            continue

        iso3 = (row.get("countryiso3code") or "").strip().upper()
        if not iso3 or iso3 in WORLD_BANK_AGGREGATES:
            continue

        country_obj = row.get("country") or {}
        source_name = _clean_country_name(country_obj.get("value") or "")
        canon = _canonicalize(lookup, source_name)
        if not canon:
            if source_name and source_name not in unknown and len(unknown) < 50:
                unknown.append(source_name)
            continue

        try:
            numeric_value = float(value)
        except (TypeError, ValueError):
            continue

        by_country[canon.turkish] = {
            "value": numeric_value,
            "year": row.get("date"),
            "countryiso3code": iso3,
        }

    meta = {
        "url": url,
        "lastupdated": meta_raw.get("lastupdated"),
        "total": meta_raw.get("total"),
    }
    return by_country, meta, unknown


def fetch_water_indicators(lookup: Dict[str, CountryCanon]) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, List[str]]]:
    indicators: Dict[str, Dict[str, Any]] = {}
    unknown_by_indicator: Dict[str, List[str]] = {}

    for key, config in WORLD_BANK_WATER_INDICATORS.items():
        by_country, wb_meta, unknown = fetch_world_bank_indicator(lookup, config["code"])
        indicators[key] = {
            "label": config["label"],
            "unit": config["unit"],
            "decimals": config["decimals"],
            "source": {
                "type": "worldbank",
                "indicator_code": config["code"],
                **wb_meta,
            },
            "by_country": by_country,
        }
        unknown_by_indicator[key] = unknown

    return indicators, unknown_by_indicator


def _geometry_bbox(points: Iterable[Tuple[float, float]]) -> Optional[Tuple[float, float, float, float]]:
    pts = list(points)
    if not pts:
        return None
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)


def _iter_polygon_points(polygon: List[Any]) -> Iterable[Tuple[float, float]]:
    for ring in polygon or []:
        for point in ring or []:
            if isinstance(point, (list, tuple)) and len(point) >= 2:
                yield float(point[0]), float(point[1])


def _representative_geometry_center(geometry: Dict[str, Any]) -> Optional[Tuple[float, float]]:
    if not isinstance(geometry, dict):
        return None
    gtype = geometry.get("type")
    coords = geometry.get("coordinates") or []
    if gtype == "Polygon":
        bbox = _geometry_bbox(_iter_polygon_points(coords))
        if not bbox:
            return None
        min_x, min_y, max_x, max_y = bbox
        return ((min_y + max_y) / 2.0, (min_x + max_x) / 2.0)
    if gtype == "MultiPolygon":
        best_bbox = None
        best_area = -1.0
        for polygon in coords:
            bbox = _geometry_bbox(_iter_polygon_points(polygon))
            if not bbox:
                continue
            min_x, min_y, max_x, max_y = bbox
            area = abs((max_x - min_x) * (max_y - min_y))
            if area > best_area:
                best_area = area
                best_bbox = bbox
        if not best_bbox:
            return None
        min_x, min_y, max_x, max_y = best_bbox
        return ((min_y + max_y) / 2.0, (min_x + max_x) / 2.0)
    return None


def build_geojson_representative_points(by_turkish: Dict[str, CountryCanon]) -> Dict[str, Tuple[float, float]]:
    if not COUNTRIES_GEOJSON_PATH.exists():
        return {}
    geojson = json.loads(COUNTRIES_GEOJSON_PATH.read_text(encoding="utf-8"))

    centers_by_iso2: Dict[str, Tuple[float, float]] = {}
    centers_by_name: Dict[str, Tuple[float, float]] = {}
    for feature in geojson.get("features") or []:
        if not isinstance(feature, dict):
            continue
        props = feature.get("properties") or {}
        geometry = feature.get("geometry") or {}
        center = _representative_geometry_center(geometry)
        if not center:
            continue
        iso2 = str(props.get("ISO3166-1-Alpha-2") or "").strip().upper()
        name = str(props.get("name") or props.get("NAME") or "").strip()
        if iso2 and iso2 != "-99":
            centers_by_iso2.setdefault(iso2, center)
        if name:
            centers_by_name.setdefault(_normalize_lookup_key(name), center)

    out: Dict[str, Tuple[float, float]] = {}
    for country, canon in by_turkish.items():
        if canon.iso2 and canon.iso2 in centers_by_iso2:
            out[country] = centers_by_iso2[canon.iso2]
            continue
        if canon.english:
            key = _normalize_lookup_key(canon.english)
            if key in centers_by_name:
                out[country] = centers_by_name[key]
    return out


def build_event_fallback_points(lookup: Dict[str, CountryCanon]) -> Dict[str, Tuple[float, float]]:
    if not EVENTS_PATH.exists():
        return {}
    raw = json.loads(EVENTS_PATH.read_text(encoding="utf-8"))
    events = raw.get("events") or []
    score: Dict[str, Dict[Tuple[float, float], Tuple[int, int]]] = defaultdict(dict)
    for event in events:
        if not isinstance(event, dict):
            continue
        canon = _canonicalize(lookup, event.get("country_name") or "")
        if not canon:
            continue
        lat = event.get("lat")
        lon = event.get("lon")
        if not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)):
            continue
        if float(lat) == 0.0 and float(lon) == 0.0:
            continue
        point = (round(float(lat), 4), round(float(lon), 4))
        year = int(event.get("year") or 0)
        count, latest_year = score[canon.turkish].get(point, (0, 0))
        score[canon.turkish][point] = (count + 1, max(latest_year, year))

    out: Dict[str, Tuple[float, float]] = {}
    for country, points in score.items():
        if not points:
            continue
        best_point = max(points.items(), key=lambda item: (item[1][0], item[1][1]))[0]
        out[country] = best_point
    return out


def fetch_rest_country_profiles(
    by_turkish: Dict[str, CountryCanon], by_iso2: Dict[str, CountryCanon]
) -> Dict[str, Dict[str, Any]]:
    rows = _fetch_json(REST_COUNTRIES_URL, timeout=60)
    out: Dict[str, Dict[str, Any]] = {}
    for row in rows or []:
        if not isinstance(row, dict):
            continue
        cca2 = str(row.get("cca2") or "").strip().upper()
        canon = by_iso2.get(cca2)
        if not canon:
            names = row.get("name") or {}
            for candidate in [names.get("common"), names.get("official")]:
                if not candidate:
                    continue
                for known in by_turkish.values():
                    if _normalize_lookup_key(candidate) == _normalize_lookup_key(known.english):
                        canon = known
                        break
                if canon:
                    break
        if not canon:
            continue

        currencies = row.get("currencies") or {}
        currency_code = ""
        currency_name = ""
        if isinstance(currencies, dict) and currencies:
            currency_code = next(iter(currencies.keys()))
            currency_obj = currencies.get(currency_code) or {}
            if isinstance(currency_obj, dict):
                currency_name = str(currency_obj.get("name") or "").strip()

        capital = ""
        capital_list = row.get("capital") or []
        if isinstance(capital_list, list) and capital_list:
            capital = str(capital_list[0] or "").strip()

        lat = None
        lon = None
        capital_info = row.get("capitalInfo") or {}
        latlng = capital_info.get("latlng") or []
        if isinstance(latlng, list) and len(latlng) >= 2:
            try:
                lat = float(latlng[0])
                lon = float(latlng[1])
            except (TypeError, ValueError):
                lat = None
                lon = None

        out[canon.turkish] = {
            "currency_code": currency_code,
            "currency_name": currency_name,
            "capital": capital,
            "lat": lat,
            "lon": lon,
            "coord_source": "restcountries:capitalInfo" if lat is not None and lon is not None else "",
        }
    return out


def build_country_context(
    lookup: Dict[str, CountryCanon],
    by_turkish: Dict[str, CountryCanon],
    by_iso2: Dict[str, CountryCanon],
) -> Dict[str, Dict[str, Any]]:
    profiles = fetch_rest_country_profiles(by_turkish, by_iso2)
    geojson_points = build_geojson_representative_points(by_turkish)
    event_points = build_event_fallback_points(lookup)

    context: Dict[str, Dict[str, Any]] = {}
    for country, canon in by_turkish.items():
        profile = profiles.get(country, {})
        row: Dict[str, Any] = {
            "iso2": canon.iso2.lower(),
            "english": canon.english,
            "currency_code": profile.get("currency_code") or "",
            "currency_name": profile.get("currency_name") or "",
            "location_name": profile.get("capital") or country,
            "lat": None,
            "lon": None,
            "coord_source": "",
        }
        if isinstance(profile.get("lat"), (int, float)) and isinstance(profile.get("lon"), (int, float)):
            row["lat"] = float(profile["lat"])
            row["lon"] = float(profile["lon"])
            row["coord_source"] = profile.get("coord_source") or "restcountries:capitalInfo"
        elif country in SPECIAL_VISUAL_CENTERS:
            row["lat"], row["lon"] = SPECIAL_VISUAL_CENTERS[country]
            row["coord_source"] = "static:visual_center"
        elif country in geojson_points:
            row["lat"], row["lon"] = geojson_points[country]
            row["coord_source"] = "geojson:largest_polygon_bbox"
        elif country in event_points:
            row["lat"], row["lon"] = event_points[country]
            row["coord_source"] = "events:dominant_point"
        context[country] = row

    return context


def _weather_code_bonus(code: int) -> int:
    if code in (95, 96, 99):
        return 35
    if code in (82, 86):
        return 28
    if code in (65, 67, 75):
        return 22
    if code in (61, 63, 71, 73, 80, 81, 85):
        return 14
    if code in (45, 48):
        return 10
    if code in (2, 3):
        return 4
    return 0


def _weather_pressure_score(current: Dict[str, Any]) -> int:
    apparent = float(current.get("apparent_temperature") or 0.0)
    precip = max(0.0, float(current.get("precipitation") or 0.0))
    wind = max(0.0, float(current.get("wind_speed_10m") or 0.0))
    code = int(current.get("weather_code") or 0)

    temp_score = 0.0
    if apparent < 0:
        temp_score = min(30.0, abs(apparent) * 2.0)
    elif apparent > 30:
        temp_score = min(30.0, (apparent - 30.0) * 3.0)
    elif apparent > 24:
        temp_score = min(12.0, (apparent - 24.0) * 2.0)

    precip_score = min(25.0, precip * 12.0)
    wind_score = min(25.0, wind * 0.8)
    code_score = float(_weather_code_bonus(code))
    total = min(100.0, temp_score + precip_score + wind_score + code_score)
    return int(round(total))


def _risk_label_from_score(score: float) -> str:
    if score >= 75:
        return "Çok yüksek"
    if score >= 55:
        return "Yüksek"
    if score >= 35:
        return "Orta"
    if score > 0:
        return "Düşük"
    return "Yok"


def _air_quality_label(aqi: float) -> str:
    if aqi <= 20:
        return "İyi"
    if aqi <= 40:
        return "Orta"
    if aqi <= 60:
        return "Hassas"
    if aqi <= 80:
        return "Kötü"
    if aqi <= 100:
        return "Çok kötü"
    return "Tehlikeli"


def _derive_aqi_from_components(pm25: Optional[float], pm10: Optional[float], no2: Optional[float], ozone: Optional[float]) -> int:
    values = []
    if isinstance(pm25, (int, float)):
        values.append(min(100.0, float(pm25) * 1.6))
    if isinstance(pm10, (int, float)):
        values.append(min(100.0, float(pm10) * 0.8))
    if isinstance(no2, (int, float)):
        values.append(min(100.0, float(no2) * 0.8))
    if isinstance(ozone, (int, float)):
        values.append(min(100.0, float(ozone) * 0.5))
    if not values:
        return 0
    return int(round(max(values)))


def _fx_pressure_label(change_pct: float) -> str:
    if change_pct >= 15:
        return "Yüksek"
    if change_pct >= 7:
        return "Orta"
    if change_pct > 0:
        return "Düşük"
    return "Yok"


def _sanctions_score(matches_count: int, dataset_count: int) -> int:
    if matches_count <= 0:
        return 0
    count_score = 70.0 * min(1.0, math.log10(matches_count + 1) / math.log10(5000))
    dataset_score = 30.0 * min(1.0, dataset_count / 15.0)
    return int(round(min(100.0, count_score + dataset_score)))


def _fetch_open_meteo_weather_country(country: str, ctx: Dict[str, Any]) -> Optional[Tuple[str, Dict[str, Any]]]:
    lat = ctx.get("lat")
    lon = ctx.get("lon")
    if not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)):
        return None

    params = urllib.parse.urlencode(
        {
            "latitude": f"{float(lat):.4f}",
            "longitude": f"{float(lon):.4f}",
            "current": ",".join(OPEN_METEO_WEATHER_FIELDS),
        }
    )
    payload = _fetch_json(f"{OPEN_METEO_WEATHER_URL}?{params}")
    current = payload.get("current") or {}
    if not current:
        return None
    code = int(current.get("weather_code") or 0)
    row = {
        "lat": float(lat),
        "lon": float(lon),
        "location_name": ctx.get("location_name") or country,
        "coord_source": ctx.get("coord_source") or "",
        "current": {
            "time": current.get("time"),
            "temperature_2m": current.get("temperature_2m"),
            "apparent_temperature": current.get("apparent_temperature"),
            "precipitation": current.get("precipitation"),
            "cloud_cover": current.get("cloud_cover"),
            "wind_speed_10m": current.get("wind_speed_10m"),
            "weather_code": code,
            "weather_label": WEATHER_CODE_LABELS.get(code, "Belirsiz"),
        },
    }
    row["pressure_score"] = _weather_pressure_score(row["current"])
    row["pressure_label"] = _risk_label_from_score(row["pressure_score"])
    return country, row


def fetch_weather_snapshot(now_utc: str, country_context: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    countries: Dict[str, Dict[str, Any]] = {}
    failures: List[str] = []
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {
            executor.submit(_fetch_open_meteo_weather_country, country, ctx): country
            for country, ctx in country_context.items()
            if isinstance(ctx.get("lat"), (int, float)) and isinstance(ctx.get("lon"), (int, float))
        }
        for future in as_completed(futures):
            country = futures[future]
            try:
                result = future.result()
                if not result:
                    continue
                name, row = result
                countries[name] = row
            except Exception:
                failures.append(country)

    payload = {
        "provider": "open-meteo",
        "updated_at_utc": now_utc,
        "source_note": "Build-time snapshot from Open-Meteo current weather endpoint.",
        "source": {
            "type": "open-meteo",
            "url": OPEN_METEO_WEATHER_URL,
            "fields": OPEN_METEO_WEATHER_FIELDS,
        },
        "countries": dict(sorted(countries.items())),
    }
    if failures:
        payload["failed_countries"] = sorted(failures)[:20]
    return payload


def _fetch_openaq_country(country: str, ctx: Dict[str, Any], api_key: str) -> Optional[Tuple[str, Dict[str, Any]]]:
    lat = ctx.get("lat")
    lon = ctx.get("lon")
    if not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)):
        return None

    headers = {"X-API-Key": api_key}
    params = urllib.parse.urlencode(
        {
            "coordinates": f"{float(lat):.4f},{float(lon):.4f}",
            "radius": 25000,
            "limit": 1,
            "page": 1,
        }
    )
    location_payload = _fetch_json(f"{OPENAQ_BASE_URL}/v3/locations?{params}", headers=headers, timeout=30)
    results = location_payload.get("results") or []
    if not results:
        return None
    location = results[0]
    location_id = location.get("id")
    if not location_id:
        return None

    sensor_map = {}
    for sensor in location.get("sensors") or []:
        parameter = (((sensor or {}).get("parameter") or {}).get("name") or "").strip().lower().replace(".", "_")
        normalized = OPENAQ_PARAMETER_MAP.get(parameter, parameter)
        if normalized:
            sensor_map[sensor.get("id")] = normalized

    latest_payload = _fetch_json(
        f"{OPENAQ_BASE_URL}/v3/locations/{int(location_id)}/latest?limit=100",
        headers=headers,
        timeout=30,
    )
    latest_results = latest_payload.get("results") or []
    values: Dict[str, float] = {}
    latest_time = ""
    for item in latest_results:
        sensor_id = item.get("sensorsId")
        key = sensor_map.get(sensor_id)
        if not key:
            continue
        value = item.get("value")
        if not isinstance(value, (int, float)):
            continue
        values[key] = float(value)
        utc_time = ((item.get("datetime") or {}).get("utc") or "").strip()
        if utc_time and utc_time > latest_time:
            latest_time = utc_time

    if not values:
        return None

    aqi = _derive_aqi_from_components(
        values.get("pm2_5"),
        values.get("pm10"),
        values.get("nitrogen_dioxide"),
        values.get("ozone"),
    )
    row = {
        "lat": float(lat),
        "lon": float(lon),
        "location_name": location.get("locality") or location.get("name") or ctx.get("location_name") or country,
        "coord_source": ctx.get("coord_source") or "",
        "data_source": "openaq",
        "current": {
            "time": latest_time,
            "pm10": values.get("pm10"),
            "pm2_5": values.get("pm2_5"),
            "nitrogen_dioxide": values.get("nitrogen_dioxide"),
            "ozone": values.get("ozone"),
            "european_aqi": aqi,
        },
        "aqi_label": _air_quality_label(aqi),
        "distance_m": location.get("distance"),
    }
    return country, row


def _fetch_open_meteo_air_country(country: str, ctx: Dict[str, Any]) -> Optional[Tuple[str, Dict[str, Any]]]:
    lat = ctx.get("lat")
    lon = ctx.get("lon")
    if not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)):
        return None

    params = urllib.parse.urlencode(
        {
            "latitude": f"{float(lat):.4f}",
            "longitude": f"{float(lon):.4f}",
            "current": ",".join(OPEN_METEO_AIR_FIELDS),
        }
    )
    payload = _fetch_json(f"{OPEN_METEO_AIR_URL}?{params}")
    current = payload.get("current") or {}
    if not current:
        return None
    aqi = current.get("european_aqi")
    if not isinstance(aqi, (int, float)):
        aqi = _derive_aqi_from_components(
            current.get("pm2_5"),
            current.get("pm10"),
            current.get("nitrogen_dioxide"),
            current.get("ozone"),
        )
    row = {
        "lat": float(lat),
        "lon": float(lon),
        "location_name": ctx.get("location_name") or country,
        "coord_source": ctx.get("coord_source") or "",
        "data_source": "open-meteo-air",
        "current": {
            "time": current.get("time"),
            "pm10": current.get("pm10"),
            "pm2_5": current.get("pm2_5"),
            "nitrogen_dioxide": current.get("nitrogen_dioxide"),
            "ozone": current.get("ozone"),
            "european_aqi": aqi,
        },
        "aqi_label": _air_quality_label(float(aqi or 0.0)),
    }
    return country, row


def fetch_air_quality_snapshot(now_utc: str, country_context: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    api_key = os.environ.get("OPENAQ_API_KEY", "").strip()
    countries: Dict[str, Dict[str, Any]] = {}
    failures: List[str] = []

    if api_key:
        provider = "openaq"
        source_note = "Primary source OpenAQ. Falls back to Open-Meteo when location data is unavailable."
        worker = lambda country, ctx: _fetch_openaq_country(country, ctx, api_key)
    else:
        provider = "open-meteo-air"
        source_note = "OpenAQ requires an API key. Open-Meteo air quality fallback is used."
        worker = _fetch_open_meteo_air_country

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {
            executor.submit(worker, country, ctx): country
            for country, ctx in country_context.items()
            if isinstance(ctx.get("lat"), (int, float)) and isinstance(ctx.get("lon"), (int, float))
        }
        for future in as_completed(futures):
            country = futures[future]
            try:
                result = future.result()
                if not result and api_key:
                    fallback = _fetch_open_meteo_air_country(country, country_context[country])
                    if fallback:
                        result = fallback
                if not result:
                    continue
                name, row = result
                countries[name] = row
            except Exception:
                failures.append(country)

    payload = {
        "provider": provider,
        "updated_at_utc": now_utc,
        "source_note": source_note,
        "source": {
            "type": provider,
            "primary_url": f"{OPENAQ_BASE_URL}/v3/locations" if api_key else OPEN_METEO_AIR_URL,
            "fallback_url": OPEN_METEO_AIR_URL if api_key else "",
        },
        "countries": dict(sorted(countries.items())),
    }
    if failures:
        payload["failed_countries"] = sorted(failures)[:20]
    return payload


def fetch_fx_snapshot(now_utc: str, country_context: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    currency_catalog = _fetch_json(FRANKFURTER_CURRENCIES_URL, timeout=30)
    supported = {str(code).upper(): str(name) for code, name in (currency_catalog or {}).items()}

    currency_to_countries: Dict[str, List[str]] = defaultdict(list)
    for country, ctx in country_context.items():
        code = str(ctx.get("currency_code") or "").upper()
        if code and code in supported:
            currency_to_countries[code].append(country)

    symbols = ",".join(sorted(currency_to_countries))
    if not symbols:
        raise RuntimeError("Frankfurter returned no supported currencies for mapped countries")

    current_payload = _fetch_json(
        f"{FRANKFURTER_LATEST_URL}?base=USD&symbols={urllib.parse.quote(symbols, safe=',')}",
        timeout=30,
    )
    current_date = str(current_payload.get("date") or "")
    if not current_date:
        raise RuntimeError("Frankfurter latest response missing date")
    comparison_date = (datetime.fromisoformat(current_date) - timedelta(days=30)).date().isoformat()
    previous_payload = _fetch_json(
        FRANKFURTER_DATE_URL.format(date=comparison_date)
        + f"?base=USD&symbols={urllib.parse.quote(symbols, safe=',')}",
        timeout=30,
    )

    current_rates = current_payload.get("rates") or {}
    previous_rates = previous_payload.get("rates") or {}
    countries: Dict[str, Dict[str, Any]] = {}
    for currency_code, linked_countries in currency_to_countries.items():
        current_rate = current_rates.get(currency_code)
        previous_rate = previous_rates.get(currency_code)
        if not isinstance(current_rate, (int, float)) or not isinstance(previous_rate, (int, float)) or previous_rate == 0:
            continue
        change_pct = ((float(current_rate) - float(previous_rate)) / float(previous_rate)) * 100.0
        pressure_pct = max(0.0, change_pct)
        for country in linked_countries:
            countries[country] = {
                "currency_code": currency_code,
                "currency_name": supported.get(currency_code) or country_context[country].get("currency_name") or "",
                "current_rate_local_per_usd": float(current_rate),
                "previous_rate_local_per_usd": float(previous_rate),
                "change_pct_30d": round(change_pct, 3),
                "pressure_pct_30d": round(pressure_pct, 3),
                "pressure_label": _fx_pressure_label(pressure_pct),
                "reference_pair": "USD/local",
            }

    return {
        "provider": "frankfurter",
        "updated_at_utc": now_utc,
        "source_note": "30 günlük USD karşısı yerel para baskısı. Pozitif değer yerel para biriminin değer kaybını gösterir.",
        "source": {
            "type": "frankfurter",
            "currencies_url": FRANKFURTER_CURRENCIES_URL,
            "current_date": current_payload.get("date"),
            "comparison_date_requested": comparison_date,
            "comparison_date_resolved": previous_payload.get("date"),
        },
        "countries": dict(sorted(countries.items())),
    }


def fetch_sanctions_snapshot(now_utc: str, by_iso2: Dict[str, CountryCanon]) -> Dict[str, Any]:
    index_payload = _fetch_json(OPENSANCTIONS_INDEX_URL, timeout=60)
    csv_url = ""
    for resource in index_payload.get("resources") or []:
        if resource.get("name") == "targets.simple.csv":
            csv_url = str(resource.get("url") or "").strip()
            break
    if not csv_url:
        raise RuntimeError("OpenSanctions sanctions index has no targets.simple.csv resource")

    stats: Dict[str, Dict[str, Any]] = defaultdict(
        lambda: {
            "matches_count": 0,
            "dataset_counts": Counter(),
            "sample_targets": [],
            "seen_samples": set(),
        }
    )

    req = urllib.request.Request(csv_url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=120) as resp:
        wrapper = io.TextIOWrapper(resp, encoding="utf-8", newline="")
        reader = csv.DictReader(wrapper)
        for row in reader:
            raw_countries = str(row.get("countries") or "").strip()
            if not raw_countries:
                continue
            iso_codes = {
                part.strip().upper()
                for part in raw_countries.split(";")
                if len(part.strip()) == 2
            }
            if not iso_codes:
                continue
            target_name = str(row.get("name") or "").strip()
            dataset_names = [x.strip() for x in str(row.get("dataset") or "").split(";") if x.strip()]
            for iso2 in iso_codes:
                canon = by_iso2.get(iso2)
                if not canon:
                    continue
                country_stat = stats[canon.turkish]
                country_stat["matches_count"] += 1
                for dataset_name in set(dataset_names):
                    country_stat["dataset_counts"][dataset_name] += 1
                if target_name and target_name not in country_stat["seen_samples"] and len(country_stat["sample_targets"]) < 3:
                    country_stat["seen_samples"].add(target_name)
                    country_stat["sample_targets"].append(target_name)

    countries: Dict[str, Dict[str, Any]] = {}
    for country, row in stats.items():
        matches_count = int(row["matches_count"])
        dataset_counts: Counter = row["dataset_counts"]
        unique_datasets = len(dataset_counts)
        risk_score = _sanctions_score(matches_count, unique_datasets)
        countries[country] = {
            "matches_count": matches_count,
            "dataset_count": unique_datasets,
            "risk_score": risk_score,
            "risk_label": _risk_label_from_score(risk_score),
            "top_datasets": [
                {"name": name, "count": count}
                for name, count in dataset_counts.most_common(3)
            ],
            "sample_targets": row["sample_targets"],
        }

    return {
        "provider": "opensanctions",
        "updated_at_utc": now_utc,
        "source_note": "OpenSanctions consolidated sanctions bulk export. Country summaries are derived from targets.simple.csv.",
        "source": {
            "type": "opensanctions-bulk",
            "index_url": index_payload.get("index_url") or OPENSANCTIONS_INDEX_URL,
            "csv_url": csv_url,
            "dataset_updated_at": index_payload.get("updated_at"),
            "last_change": index_payload.get("last_change"),
            "entity_count": index_payload.get("entity_count"),
            "target_count": index_payload.get("target_count"),
        },
        "countries": dict(sorted(countries.items())),
    }


def main() -> None:
    lookup, by_turkish, by_iso2 = _load_country_index()
    now_utc = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    nato_members, nato_unknown = fetch_nato_members(lookup)
    min_wage_by_country, min_wage_unknown = fetch_minimum_wage(lookup)
    bigmac_by_country, bigmac_meta, bigmac_unknown = fetch_big_mac_index(lookup)
    water_indicators, water_unknown = fetch_water_indicators(lookup)

    country_context = build_country_context(lookup, by_turkish, by_iso2)

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
    for name in brics_plus_en:
        canon = _canonicalize(lookup, name)
        if canon:
            brics_plus.append(canon.turkish)
    brics_plus = sorted(set(brics_plus))

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
    for name in g8_en:
        canon = _canonicalize(lookup, name)
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
            **water_indicators,
        },
    }
    _write_json(OUTPUT_PATH, payload)

    sanctions_payload = _persist_with_fallback(
        SANCTIONS_PATH,
        label="OpenSanctions",
        provider="opensanctions",
        now_utc=now_utc,
        fetcher=lambda: fetch_sanctions_snapshot(now_utc, by_iso2),
    )
    weather_payload = _persist_with_fallback(
        WEATHER_PATH,
        label="Open-Meteo weather",
        provider="open-meteo",
        now_utc=now_utc,
        fetcher=lambda: fetch_weather_snapshot(now_utc, country_context),
    )
    air_payload = _persist_with_fallback(
        AIR_QUALITY_PATH,
        label="Air quality",
        provider="air-quality",
        now_utc=now_utc,
        fetcher=lambda: fetch_air_quality_snapshot(now_utc, country_context),
    )
    fx_payload = _persist_with_fallback(
        FX_PATH,
        label="Frankfurter FX",
        provider="frankfurter",
        now_utc=now_utc,
        fetcher=lambda: fetch_fx_snapshot(now_utc, country_context),
    )

    print("Wrote:", OUTPUT_PATH)
    print("- NATO members:", len(nato_members), "(unknown:", len(nato_unknown), ")")
    print("- BRICS+ members:", len(brics_plus))
    print("- Min wage countries:", len(min_wage_by_country), "(unknown:", len(min_wage_unknown), ")")
    print("- Big Mac countries:", len(bigmac_by_country), "as of", bigmac_meta.get("latest_date"))
    for key, indicator in water_indicators.items():
        print(f"- {key}: {len(indicator.get('by_country', {}))} country rows")
        unknown = water_unknown.get(key) or []
        if unknown:
            print(f"  unknown names ({len(unknown)}): {', '.join(unknown[:8])}")

    print("- sanctions countries:", len((sanctions_payload.get("countries") or {})))
    print("- weather countries:", len((weather_payload.get("countries") or {})))
    print("- air quality countries:", len((air_payload.get("countries") or {})))
    print("- fx countries:", len((fx_payload.get("countries") or {})))

    if bigmac_unknown:
        print("- Big Mac unknown names:", ", ".join(bigmac_unknown[:10]))
    if min_wage_unknown:
        print("- Minimum wage unknown names:", ", ".join(min_wage_unknown[:10]))

    if not nato_members or not bigmac_by_country:
        print("ERROR: critical dataset fetch returned empty results", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
