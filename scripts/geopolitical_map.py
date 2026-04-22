#!/usr/bin/env python3
"""
Geopolitical History Map - Interactive world map showing major events from the last 100 years.
"""

import json
import os
import unicodedata
from pathlib import Path
from typing import Any, Dict, List

import folium
from folium.plugins import MarkerCluster
import branca


class GeopoliticalMap:
    """Create interactive geopolitical history maps."""

    DECADES = ["1920s", "1930s", "1940s", "1950s", "1960s", "1970s", "1980s", "1990s", "2000s", "2010s", "2020s"]

    def __init__(self, data_path: str = None):
        self.base_dir = Path(__file__).parent.parent
        self.data_path = data_path or self.base_dir / "data" / "events.json"
        self.output_dir = self.base_dir / "output"
        self.events = []
        self.categories = {}
        self.build_info = {}
        self._load_data()

    # Mapping of specific events to 32. Gün YouTube video IDs
    VIDEO_MAPPINGS = {
        "Kıbrıs Barış Harekatı": "9owC4fHLRIc",
        "12 Eylül Darbesi": "arGodO-a1sE",
        "12 Eylül Askeri Darbesi": "arGodO-a1sE",
        "Berlin Duvarı'nın Yıkılışı": "A7bU6-w017Y",
        "Berlin Duvarı'nın Yıkılması": "A7bU6-w017Y",
        "Körfez Savaşı": "W0JA9b_uMKs",
        "Bosna Savaşı": "ngDfMflSwD8",
        # Loose matching keys
        "Kıbrıs": "9owC4fHLRIc",
        "12 Eylül": "arGodO-a1sE",
        "Berlin Duvarı": "A7bU6-w017Y",
        "Körfez": "W0JA9b_uMKs",
        "Bosna": "ngDfMflSwD8",
        "Bosna Hersek": "ngDfMflSwD8"
    }

    def _load_data(self):
        with open(self.data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.events = data.get('events', [])
            self.categories = data.get('categories', {})

        # Keep Admin + Map aligned: normalize decade from year and ensure every used category
        # has a definition (some datasets include categories that were not added to `categories`).
        if not isinstance(self.events, list):
            self.events = []
        if not isinstance(self.categories, dict):
            self.categories = {}

        for ev in self.events:
            if not isinstance(ev, dict):
                continue
            try:
                y = int(ev.get("year"))
            except Exception:
                continue
            ev["decade"] = f"{(y // 10) * 10}s"

        used_categories = {
            (ev.get("category") or "").strip()
            for ev in self.events
            if isinstance(ev, dict)
        }
        used_categories.discard("")
        default_category_defs = {
            "war": {"label": "Savas/Catisma", "icon": "fa-fire", "color": "#e74c3c", "tier": 1},
            "genocide": {"label": "Soykirim", "icon": "fa-skull", "color": "#2c3e50", "tier": 1},
            "revolution": {"label": "Devrim/Rejim Degisikligi", "icon": "fa-flag", "color": "#e67e22", "tier": 1},
            "terror": {"label": "Teror Saldirisi", "icon": "fa-bomb", "color": "#9b59b6", "tier": 2},
            "politics": {"label": "Politika", "icon": "fa-landmark", "color": "#16a085", "tier": 2},
            "diplomacy": {"label": "Diplomasi", "icon": "fa-handshake", "color": "#2ecc71", "tier": 2},
            "leader": {"label": "Onemli Lider", "icon": "fa-user", "color": "#3498db", "tier": 2},
            "time_100": {"label": "Time 100: Yüzyılın En Önemli Kişileri", "color": "#f1c40f", "tier": 3},
            "culture": {"label": "Kültür & Toplum", "color": "#9b59b6", "tier": 3},
            "cinema": {"label": "Sinema", "icon": "fa-film", "color": "#95a5a6", "tier": 3},
            "music": {"label": "Müzik", "icon": "fa-music", "color": "#e84393", "tier": 3},
        }
        # Backfill missing display metadata for known categories without overwriting user customizations.
        for k, v in default_category_defs.items():
            if k not in self.categories:
                continue
            if not isinstance(self.categories.get(k), dict):
                self.categories[k] = {}
            for kk, vv in v.items():
                self.categories[k].setdefault(kk, vv)
        for cat in sorted(used_categories):
            if cat in self.categories:
                continue
            self.categories[cat] = default_category_defs.get(
                cat,
                {"label": cat, "icon": "fa-tag", "color": "#7f8c8d", "tier": 3},
            )

        # Load GeoJSON for country boundaries
        geojson_path = self.base_dir / "data" / "countries.geojson"
        self.geojson_data = None
        if geojson_path.exists():
            with open(geojson_path, 'r', encoding='utf-8') as f:
                self.geojson_data = json.load(f)
        self._patch_geojson_france()

        # Load Master Country Mappings
        mappings_path = self.base_dir / "data" / "country_mappings.json"
        self.country_mappings = []
        self.turkish_to_english = {}
        self.english_to_turkish = {}
        self.turkish_to_iso = {}
        self.country_lookup = {}
        if mappings_path.exists():
            with open(mappings_path, 'r', encoding='utf-8') as f:
                mappings_data = json.load(f)
                self.country_mappings = mappings_data.get('countries', [])
                # Build lookup dictionaries
                for c in self.country_mappings:
                    tr = (c.get('turkish') or '').strip()
                    en = (c.get('english') or '').strip()
                    iso = (c.get('iso2') or '').strip()
                    aliases = c.get('aliases', []) or []
                    
                    if tr and en:
                        self.turkish_to_english[tr] = en
                        self.english_to_turkish[en] = tr
                    if tr and iso:
                        self.turkish_to_iso[tr] = iso
                    for candidate in [tr, en] + aliases:
                        nk = self._normalize_lookup_key(candidate)
                        if nk and tr:
                            self.country_lookup.setdefault(nk, tr)
                    # Handle aliases
                    for alias in aliases:
                        if alias and en:
                            self.english_to_turkish[alias] = tr
                            self.turkish_to_english[alias] = en
                        if alias and iso:
                            self.turkish_to_iso[alias] = iso

        # Load Country Metadata
        metadata_path = self.base_dir / "data" / "country_metadata.json"
        self.country_metadata = {}
        if metadata_path.exists():
            with open(metadata_path, 'r', encoding='utf-8') as f:
                raw_metadata = json.load(f)
            self.country_metadata = self._normalize_country_metadata(raw_metadata)

        # Optional narrative notes for water sourcing
        water_sources_path = self.base_dir / "data" / "water_sources.json"
        self.water_sources = {"updated_at_utc": "", "countries": {}}
        if water_sources_path.exists():
            try:
                with open(water_sources_path, 'r', encoding='utf-8') as f:
                    raw_water_sources = json.load(f)
                self.water_sources = self._normalize_country_keyed_payload(raw_water_sources)
            except Exception as e:
                print(f"WARNING: Failed to load water_sources.json: {e}")
                self.water_sources = {"updated_at_utc": "", "countries": {}}

        # Structured current conflicts for map overlay + sidebar
        current_conflicts_path = self.base_dir / "data" / "current_conflicts.json"
        self.current_conflicts = {"updated_at_utc": "", "source_note": "", "conflicts": []}
        if current_conflicts_path.exists():
            try:
                with open(current_conflicts_path, 'r', encoding='utf-8') as f:
                    raw_conflicts = json.load(f)
                self.current_conflicts = self._normalize_current_conflicts(raw_conflicts)
            except Exception as e:
                print(f"WARNING: Failed to load current_conflicts.json: {e}")
                self.current_conflicts = {"updated_at_utc": "", "source_note": "", "conflicts": []}

        # Load external indicators/groups (NATO, G8, minimum wage, Big Mac, etc.)
        indicators_path = self.base_dir / "data" / "indicators.json"
        self.indicators = {}
        if indicators_path.exists():
            try:
                with open(indicators_path, 'r', encoding='utf-8') as f:
                    self.indicators = json.load(f)
            except Exception as e:
                print(f"WARNING: Failed to load indicators.json: {e}")
                self.indicators = {}

        # Strategic build-time snapshots
        self.strategic_snapshots = {
            "sanctions": {"provider": "opensanctions", "updated_at_utc": "", "countries": {}},
            "weather": {"provider": "open-meteo", "updated_at_utc": "", "countries": {}},
            "air_quality": {"provider": "air-quality", "updated_at_utc": "", "countries": {}},
            "fx": {"provider": "frankfurter", "updated_at_utc": "", "countries": {}},
        }
        for key in list(self.strategic_snapshots.keys()):
            snapshot_path = self.base_dir / "data" / f"{key}.json"
            if not snapshot_path.exists():
                continue
            try:
                with open(snapshot_path, 'r', encoding='utf-8') as f:
                    raw_snapshot = json.load(f)
                self.strategic_snapshots[key] = self._normalize_country_keyed_payload(raw_snapshot)
            except Exception as e:
                print(f"WARNING: Failed to load {snapshot_path.name}: {e}")

        # Enrich events with video links (32. Gün vb.)
        for event in self.events:
            title = event.get('title', '')
            vid_id = self.VIDEO_MAPPINGS.get(title)
            if not vid_id:
                title_lower = title.lower()
                for key, vid in self.VIDEO_MAPPINGS.items():
                    if key.lower() in title_lower:
                        vid_id = vid
                        break
            if vid_id:
                event['youtube_video_id'] = vid_id
        # Mükerrer azalt: aynı (ülke, video) en fazla bir olayda kalsın; en uygun olayda tut
        self._deduplicate_youtube_per_country()

    def _deduplicate_youtube_per_country(self) -> None:
        """Aynı (ülke, video) birden fazla olayda varsa videoyu sadece en uygun olayda bırakır."""
        from collections import defaultdict
        key_to_events = defaultdict(list)
        for ev in self.events:
            vid = ev.get('youtube_video_id')
            if not vid:
                continue
            c = ev.get('country_name', '')
            key_to_events[(c, vid)].append(ev)
        for (_, _), group in key_to_events.items():
            if len(group) <= 1:
                continue
            # En iyi: tam başlık VIDEO_MAPPINGS'te varsa, yoksa yıla göre (yeni → eski)
            def score(e):
                exact = 2 if self.VIDEO_MAPPINGS.get(e.get('title')) else 0
                return (exact, -(e.get('year') or 0))
            group.sort(key=score, reverse=True)
            for e in group[1:]:
                e.pop('youtube_video_id', None)

    def _patch_geojson_france(self) -> None:
        """GeoJSON'da 'France' bazen sadece French Guiana geometrisine sahip. Onu 'French Guiana' yapıp
        ana Fransa (metropolitan) için yeni feature ekler; böylece Fransa'ya hover'da bayrak çıkar."""
        if not self.geojson_data or 'features' not in self.geojson_data:
            return

        # If France includes overseas territories, the overall bbox becomes huge and the flag overlay
        # gets distorted. Keep only metropolitan France (+Corsica) polygons for the "France" feature.
        EU_BBOX = (-10.0, 35.0, 20.0, 60.0)  # lon_min, lat_min, lon_max, lat_max

        def _poly_bbox(poly):
            if not poly or not poly[0]:
                return None
            ring = poly[0]
            lons = [pt[0] for pt in ring if isinstance(pt, (list, tuple)) and len(pt) >= 2]
            lats = [pt[1] for pt in ring if isinstance(pt, (list, tuple)) and len(pt) >= 2]
            if not lons or not lats:
                return None
            return min(lons), min(lats), max(lons), max(lats)

        def _bbox_within(b, window):
            if not b:
                return False
            minlon, minlat, maxlon, maxlat = b
            wminlon, wminlat, wmaxlon, wmaxlat = window
            return (wminlon <= minlon <= wmaxlon) and (wminlat <= minlat <= wmaxlat) and (wminlon <= maxlon <= wmaxlon) and (wminlat <= maxlat <= wmaxlat)

        france_feature = None
        for f in self.geojson_data["features"]:
            props = f.get("properties") or {}
            if props.get("name") == "France":
                france_feature = f
                break

        if france_feature:
            geom = france_feature.get("geometry") or {}
            if geom.get("type") == "MultiPolygon":
                coords = geom.get("coordinates") or []
                metro = []
                non_metro = []
                for poly in coords:
                    b = _poly_bbox(poly)
                    if _bbox_within(b, EU_BBOX):
                        metro.append(poly)
                    else:
                        non_metro.append(poly)

                if metro:
                    geom["coordinates"] = metro
                    france_feature["geometry"] = geom
                    props = france_feature.setdefault("properties", {})
                    if props.get("ISO3166-1-Alpha-2") in (None, "", "-99"):
                        props["ISO3166-1-Alpha-2"] = "FR"
                    if props.get("ISO3166-1-Alpha-3") in (None, "", "-99"):
                        props["ISO3166-1-Alpha-3"] = "FRA"
                    return

            # If we couldn't extract metropolitan France, rename this feature so lookups don't grab it.
            props = france_feature.setdefault("properties", {})
            props["name"] = "France (Overseas)"

        # Add metropolitan France from a local GeoJSON snippet (kept small and bbox-correct for flag masking).
        france_path = self.base_dir / "data" / "france_metropolitan.geojson"
        if france_path.exists():
            try:
                france_data = json.loads(france_path.read_text(encoding="utf-8"))
                for f in france_data.get("features", []):
                    props = f.setdefault("properties", {})
                    props.setdefault("name", "France")
                    props.setdefault("ISO3166-1-Alpha-3", "FRA")
                    props.setdefault("ISO3166-1-Alpha-2", "FR")
                    self.geojson_data["features"].append(f)
                return
            except Exception as e:
                print(f"WARNING: failed to load france_metropolitan.geojson: {e}")

        # Last resort fallback: approximate box geometry (better than nothing, but less accurate).
        self.geojson_data["features"].append(
            {
                "type": "Feature",
                "properties": {"name": "France", "ISO3166-1-Alpha-3": "FRA", "ISO3166-1-Alpha-2": "FR"},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[-5.5, 41.0], [10.0, 41.0], [10.0, 51.5], [-5.5, 51.5], [-5.5, 41.0]]],
                },
            }
        )

    def _normalize_lookup_key(self, value: Any) -> str:
        if value is None:
            return ""
        s = str(value).strip()
        if not s:
            return ""
        s = (
            s.replace("\u2019", "'")
            .replace("\u2018", "'")
            .replace("\u201B", "'")
            .replace("\u02BC", "'")
            .replace("’", "'")
            .replace("‘", "'")
        )
        s = " ".join(s.split())
        s = unicodedata.normalize("NFKD", s)
        s = "".join(ch for ch in s if not unicodedata.combining(ch))
        s = s.lower().replace("ı", "i")
        return s

    def _canonicalize_country_name(self, value: Any) -> str:
        raw = str(value or "").strip()
        if not raw:
            return ""
        key = self._normalize_lookup_key(raw)
        if key in self.country_lookup:
            return self.country_lookup[key]
        return raw

    def _merge_unique_objects(self, existing: List[Dict[str, Any]], incoming: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        seen = set()
        merged: List[Dict[str, Any]] = []
        for item in (existing or []) + (incoming or []):
            if not isinstance(item, dict):
                continue
            key = json.dumps(item, sort_keys=True, ensure_ascii=False)
            if key in seen:
                continue
            seen.add(key)
            merged.append(item)
        return merged

    def _normalize_rivalries(self, rivalries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        seen = set()
        normalized = []
        for item in rivalries or []:
            if not isinstance(item, dict):
                continue
            rival = self._canonicalize_country_name(item.get("rival"))
            row = dict(item)
            if rival:
                row["rival"] = rival
            key = (
                row.get("rival", ""),
                row.get("text", ""),
                row.get("status", ""),
                row.get("year", ""),
                row.get("url", ""),
            )
            if key in seen:
                continue
            seen.add(key)
            normalized.append(row)
        return normalized

    def _normalize_country_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        normalized: Dict[str, Dict[str, Any]] = {}
        for raw_name, raw_meta in (metadata or {}).items():
            if not isinstance(raw_meta, dict):
                continue
            country = self._canonicalize_country_name(raw_name)
            if not country:
                continue
            current = normalized.setdefault(country, {})

            for field in ["predecessor", "demographics"]:
                incoming = str(raw_meta.get(field) or "").strip()
                existing = str(current.get(field) or "").strip()
                if incoming and (not existing or existing == "-" or len(incoming) > len(existing)):
                    current[field] = incoming

            incoming_rivals = [
                self._canonicalize_country_name(x) or x
                for x in (raw_meta.get("rivals") or [])
                if str(x or "").strip()
            ]
            if incoming_rivals:
                current["rivals"] = sorted(set((current.get("rivals") or []) + incoming_rivals), key=lambda x: self._normalize_lookup_key(x))

            incoming_rivalries = self._normalize_rivalries(raw_meta.get("rivalries") or [])
            if incoming_rivalries:
                current["rivalries"] = self._normalize_rivalries((current.get("rivalries") or []) + incoming_rivalries)

            incoming_felaketler = [x for x in (raw_meta.get("felaketler") or []) if isinstance(x, dict)]
            if incoming_felaketler:
                current["felaketler"] = self._merge_unique_objects(current.get("felaketler") or [], incoming_felaketler)

            incoming_key_conflict = raw_meta.get("key_conflict")
            if isinstance(incoming_key_conflict, dict):
                if not current.get("key_conflict"):
                    current["key_conflict"] = dict(incoming_key_conflict)
                else:
                    existing_text = str((current.get("key_conflict") or {}).get("text") or "")
                    incoming_text = str(incoming_key_conflict.get("text") or "")
                    if incoming_text and len(incoming_text) > len(existing_text):
                        current["key_conflict"] = dict(incoming_key_conflict)

            for field in ["code", "flag_url", "water_profile"]:
                if raw_meta.get(field) and not current.get(field):
                    current[field] = raw_meta[field]

        return normalized

    def _normalize_country_keyed_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(payload, dict):
            return {"updated_at_utc": "", "countries": {}}
        countries = payload.get("countries") or {}
        normalized_countries = {}
        for raw_name, raw_note in (countries or {}).items():
            if not isinstance(raw_note, dict):
                continue
            country = self._canonicalize_country_name(raw_name)
            if not country:
                continue
            normalized_countries[country] = raw_note
        normalized = dict(payload)
        normalized["countries"] = normalized_countries
        normalized.setdefault("updated_at_utc", "")
        return normalized

    def _normalize_current_conflicts(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        normalized_conflicts = []
        seen_ids = set()
        for item in payload.get("conflicts", []) if isinstance(payload, dict) else []:
            if not isinstance(item, dict):
                continue
            conflict_id = str(item.get("id") or "").strip()
            if not conflict_id or conflict_id in seen_ids:
                continue
            seen_ids.add(conflict_id)

            conflict = dict(item)
            conflict["participants"] = [
                self._canonicalize_country_name(x) or str(x).strip()
                for x in (item.get("participants") or [])
                if str(x or "").strip()
            ]

            normalized_links = []
            for link in item.get("links", []) or []:
                if not isinstance(link, dict):
                    continue
                row = dict(link)
                if row.get("source"):
                    row["source"] = self._canonicalize_country_name(row.get("source")) or row.get("source")
                if row.get("target"):
                    row["target"] = self._canonicalize_country_name(row.get("target")) or row.get("target")
                normalized_links.append(row)
            conflict["links"] = normalized_links
            normalized_conflicts.append(conflict)

        return {
            "updated_at_utc": payload.get("updated_at_utc", ""),
            "source_note": payload.get("source_note", ""),
            "conflicts": normalized_conflicts,
        }

    def _get_custom_css_js(self) -> str:
        """Get custom CSS and JavaScript for the map."""
        # Large data (events, geojson, metadata) now loaded async from separate files
        # Only small config data stays inline
        categories_json = json.dumps(self.categories, ensure_ascii=False)

        # Decades are part of the UI filter; derive from data (do not hardcode).
        decades_set = {
            str((e or {}).get("decade") or "").strip()
            for e in (self.events or [])
            if isinstance(e, dict)
        }
        decades_set.discard("")

        def _decade_sort_key(d: str):
            try:
                # "1990s" -> 1990
                return (0, int(d[:-1]))
            except Exception:
                return (1, d)

        decades_json = json.dumps(sorted(decades_set, key=_decade_sort_key), ensure_ascii=False)
        
        # Serialize master mappings for JavaScript (small, kept inline)
        turkish_to_english_json = json.dumps(self.turkish_to_english, ensure_ascii=False)
        english_to_turkish_json = json.dumps(self.english_to_turkish, ensure_ascii=False)
        turkish_to_iso_json = json.dumps(self.turkish_to_iso, ensure_ascii=False)

        parse_md_js = r'''
function parseMarkdownLinks(text) {
    if (!text) return "";
    return text.replace(/\[([^\]]+)\]\((https?:\/\/[^\s\)]+)\)/g, '<a href="$2" target="_blank" style="color: #3498db; text-decoration: underline;">$1</a>');
}
'''

        return f'''
<title>Jeopolitik Tarih Haritası | Son 100 Yılın Önemli Olayları</title>
<meta charset="UTF-8">
<meta name="description" content="Son 100 yılın dünya tarihindeki en önemli jeopolitik olaylarını interaktif harita üzerinde keşfedin. Savaşlar, antlaşmalar ve krizler.">
<meta name="keywords" content="jeopolitik, tarih, dünya haritası, interaktif harita, askeri tarih, siyasi tarih, olaylar">
<meta name="author" content="Jeopolitik Map">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0">

<!-- Open Graph / Facebook -->
<meta property="og:type" content="website">
<meta property="og:url" content="https://jeopolitik.com.tr/">
<meta property="og:title" content="Jeopolitik Tarih Haritası | Son 100 Yılın Önemli Olayları">
<meta property="og:description" content="Son 100 yılın dünya tarihindeki en önemli jeopolitik olaylarını interaktif harita üzerinde keşfedin.">
<meta property="og:image" content="https://jeopolitik.com.tr/og-image.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:locale" content="tr_TR">
<meta property="og:site_name" content="Jeopolitik Tarih Haritası">

<!-- Twitter -->
<meta property="twitter:card" content="summary_large_image">
<meta property="twitter:url" content="https://jeopolitik.com.tr/">
<meta property="twitter:title" content="Jeopolitik Tarih Haritası | Son 100 Yılın Önemli Olayları">
<meta property="twitter:description" content="Son 100 yılın dünya tarihindeki en önemli jeopolitik olaylarını interaktif harita üzerinde keşfedin.">
<meta property="twitter:image" content="https://jeopolitik.com.tr/og-image.png">

<link rel="canonical" href="https://jeopolitik.com.tr/" />

<!-- JSON-LD Structured Data -->
<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "WebApplication",
  "name": "Jeopolitik Tarih Haritası",
  "url": "https://jeopolitik.com.tr",
  "description": "Son 100 yılın dünya tarihindeki en önemli jeopolitik olaylarını interaktif harita üzerinde keşfedin.",
  "applicationCategory": "EducationalApplication",
  "operatingSystem": "Web",
  "offers": {{ "@type": "Offer", "price": "0", "priceCurrency": "TRY" }},
  "author": {{ "@type": "Organization", "name": "Jeopolitik Map", "url": "https://jeopolitik.com.tr" }},
  "inLanguage": "tr",
  "screenshot": "https://jeopolitik.com.tr/og-image.png",
  "dateModified": "{self.build_info.get('build_time','2026-03-26')}",
  "aggregateRating": {{ "@type": "AggregateRating", "ratingValue": "4.8", "ratingCount": "120" }}
}}
</script>
<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "Dataset",
  "name": "Dünya Jeopolitik Olayları Veritabanı",
  "description": "1920'den günümüze 3900+ jeopolitik olay, 138 ülke, 13 ekonomik gösterge içeren açık veri seti.",
  "url": "https://jeopolitik.com.tr",
  "license": "https://creativecommons.org/licenses/by-nc/4.0/",
  "creator": {{ "@type": "Organization", "name": "Jeopolitik Map" }},
  "temporalCoverage": "1920/2026",
  "spatialCoverage": {{ "@type": "Place", "name": "World" }},
  "variableMeasured": ["Yaptırım Riski", "İklim Baskısı", "Hava Kalitesi PM2.5", "Kur Baskısı", "Asgari Ücret", "Big Mac Endeksi", "Su Stresi"],
  "keywords": ["jeopolitik", "tarih", "dünya haritası", "savaşlar", "krizler", "ekonomik göstergeler", "su kaynakları"]
}}
</script>

<!-- PWA -->
<link rel="manifest" href="/manifest.json">
<meta name="theme-color" content="#1a1a2e">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<link rel="apple-touch-icon" href="/icon-192.png">

<!-- Preconnect -->
<link rel="preconnect" href="https://tile.openstreetmap.org" crossorigin>
<link rel="dns-prefetch" href="https://tile.openstreetmap.org">
<link rel="preconnect" href="https://flagcdn.com" crossorigin>
<link rel="dns-prefetch" href="https://flagcdn.com">
<link href="https://fonts.googleapis.com/css2?family=Oswald:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<style>
    * {{
        font-family: 'Oswald', 'Impact', 'Segoe UI', Roboto, sans-serif;
    }}
    
    /* Grain Texture for Military Feel */
    body::after {{
        content: "";
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        pointer-events: none;
        z-index: 9000;
        background: url('data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADIAAAAyBAMAAADsEZWCAAAAGFBMVEUAAAA5OTkAAABDQ0NMTExERERmZmZQUFA58lcOAAAACHRSTlMAMwAqzMzMVO5rW7IAAABDSURBVDjLY2AYBaNgKLgChANS0NzczsBwYAoDc8MhBobbUxgY7jCBhCGSDEwNIAlfEwOMJ0Y3iE83iE83iE830MAoGAUjAQAAq11Bhp31ZKcAAAAASUVORK5CYII=');
        opacity: 0.05;
    }}

    /* Video Embed Styles */
    .video-container {{
        position: relative;
        padding-bottom: 56.25%; /* 16:9 */
        height: 0;
        margin: 10px 0;
        border-radius: 8px;
        overflow: hidden;
        background: #000;
        box-shadow: 0 2px 8px rgba(0,0,0,0.2);
    }}
    .video-container iframe {{
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        border: 0;
    }}
    .video-label {{
        font-size: 11px;
        font-weight: 600;
        color: #c0392b;
        margin-bottom: 4px;
        display: flex;
        align-items: center;
        gap: 6px;
    }}
    .video-label::before {{
        content: '▶';
        font-size: 10px;
    }}

    .conflict-label {{
        background: rgba(255, 255, 255, 0.85);
        border: 1px solid rgba(192, 57, 43, 0.4);
        border-radius: 4px;
        color: #c0392b;
        font-weight: 800;
        font-size: 11px;
        padding: 1px 5px;
        text-shadow: none;
        white-space: nowrap;
        display: inline-block;
        text-align: center;
    }}

    /* Control Panel - Glass Design */
    .control-panel {{
        position: fixed;
        top: 10px;
        right: 10px;
        z-index: 1000;
        background: rgba(14, 21, 27, 0.78);
        backdrop-filter: blur(20px) saturate(130%);
        -webkit-backdrop-filter: blur(20px) saturate(130%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        color: #ecf0f1;
        padding: 15px;
        border-radius: 14px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.35), inset 0 0 0 1px rgba(255,255,255,0.04);
        max-height: 90vh;
        overflow-y: auto;
        width: 280px;
        transition: transform 0.25s ease, opacity 0.25s ease;
    }}
    .control-panel h3 {{
        margin: 0 0 12px 0;
        font-size: 16px;
        font-weight: 600;
        color: #ecf0f1;
        border-bottom: 2px solid rgba(52, 152, 219, 0.5);
        padding-bottom: 8px;
    }}
    /* Accordion sections */
    .control-section {{
        margin-bottom: 6px;
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 10px;
        overflow: hidden;
        transition: border-color 0.2s;
    }}
    .control-section:hover {{
        border-color: rgba(255, 255, 255, 0.1);
    }}
    .control-section.open {{
        border-color: rgba(52, 152, 219, 0.15);
        background: rgba(255, 255, 255, 0.03);
    }}
    .acc-header {{
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 10px 12px;
        cursor: pointer;
        user-select: none;
        transition: background 0.15s;
    }}
    .acc-header:hover {{
        background: rgba(255, 255, 255, 0.04);
    }}
    .acc-icon {{
        width: 20px;
        height: 20px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 6px;
        background: var(--acc-color, rgba(52,152,219,0.15));
        color: var(--acc-text, #3498db);
        flex-shrink: 0;
    }}
    .acc-icon svg {{
        width: 12px;
        height: 12px;
        fill: currentColor;
    }}
    .acc-title {{
        flex: 1;
        font-size: 12px;
        font-weight: 600;
        color: rgba(236, 240, 241, 0.85);
        letter-spacing: 0.3px;
    }}
    .acc-badge {{
        font-size: 9px;
        padding: 1px 6px;
        border-radius: 10px;
        background: rgba(255, 255, 255, 0.08);
        color: rgba(255, 255, 255, 0.5);
        font-weight: 600;
    }}
    .acc-chevron {{
        width: 14px;
        height: 14px;
        color: rgba(255, 255, 255, 0.3);
        transition: transform 0.25s ease;
        flex-shrink: 0;
    }}
    .control-section.open .acc-chevron {{
        transform: rotate(180deg);
        color: rgba(52, 152, 219, 0.6);
    }}
    .acc-body {{
        max-height: 0;
        overflow: hidden;
        transition: max-height 0.3s ease, padding 0.3s ease;
        padding: 0 10px;
    }}
    .control-section.open .acc-body {{
        max-height: 600px;
        padding: 0 10px 10px;
    }}
    .acc-actions {{
        display: flex;
        gap: 4px;
        margin-bottom: 6px;
    }}
    .acc-actions button {{
        flex: 1;
        padding: 3px 0;
        font-size: 9px;
        font-weight: 600;
        letter-spacing: 0.5px;
        text-transform: uppercase;
        border: 1px solid rgba(255, 255, 255, 0.08);
        background: rgba(255, 255, 255, 0.04);
        color: rgba(255, 255, 255, 0.4);
        border-radius: 4px;
        cursor: pointer;
        transition: all 0.15s;
    }}
    .acc-actions button:hover {{
        background: rgba(52, 152, 219, 0.15);
        color: #74b9ff;
        border-color: rgba(52, 152, 219, 0.3);
    }}

    .ai-search-panel {{
        display: flex;
        flex-direction: column;
        gap: 8px;
    }}
    .ai-search-form {{
        display: flex;
        gap: 6px;
    }}
    .ai-search-input {{
        flex: 1;
        min-width: 0;
        padding: 8px 9px;
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 8px;
        background: rgba(255, 255, 255, 0.06);
        color: #ecf0f1;
        font-size: 12px;
        outline: none;
    }}
    .ai-search-input:focus {{
        border-color: rgba(52, 152, 219, 0.55);
        box-shadow: 0 0 0 2px rgba(52, 152, 219, 0.16);
    }}
    .ai-search-input::placeholder {{
        color: rgba(236, 240, 241, 0.42);
    }}
    .ai-search-button {{
        flex-shrink: 0;
        padding: 8px 10px;
        border: 1px solid rgba(52, 152, 219, 0.42);
        border-radius: 8px;
        background: rgba(52, 152, 219, 0.18);
        color: #dff1ff;
        font-size: 11px;
        font-weight: 700;
        cursor: pointer;
    }}
    .ai-search-button:hover {{
        background: rgba(52, 152, 219, 0.28);
    }}
    .ai-search-button:disabled {{
        opacity: 0.55;
        cursor: wait;
    }}
    .ai-search-status {{
        min-height: 14px;
        font-size: 10px;
        line-height: 1.4;
        color: rgba(236, 240, 241, 0.55);
    }}
    .ai-search-status.error {{
        color: #ffb4a8;
    }}
    .ai-search-summary {{
        font-size: 10px;
        line-height: 1.45;
        color: rgba(236, 240, 241, 0.72);
    }}
    .ai-search-results {{
        display: flex;
        flex-direction: column;
        gap: 6px;
        max-height: 260px;
        overflow-y: auto;
    }}
    .ai-result-item {{
        width: 100%;
        text-align: left;
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 8px;
        background: rgba(255, 255, 255, 0.04);
        color: #ecf0f1;
        padding: 8px;
        cursor: pointer;
    }}
    .ai-result-item:hover {{
        border-color: rgba(52, 152, 219, 0.34);
        background: rgba(52, 152, 219, 0.1);
    }}
    .ai-result-meta {{
        display: flex;
        align-items: center;
        gap: 6px;
        flex-wrap: wrap;
        margin-bottom: 4px;
        color: rgba(236, 240, 241, 0.58);
        font-size: 10px;
    }}
    .ai-result-category {{
        padding: 2px 6px;
        border-radius: 6px;
        color: #ffffff;
        font-weight: 700;
    }}
    .ai-result-title {{
        font-size: 12px;
        font-weight: 700;
        line-height: 1.35;
    }}
    .ai-result-snippet {{
        margin-top: 4px;
        font-size: 10px;
        line-height: 1.4;
        color: rgba(236, 240, 241, 0.58);
    }}

    /* Decade toggle chips */
    .decade-grid {{
        display: flex;
        flex-wrap: wrap;
        gap: 4px;
    }}
    .decade-item {{
        display: flex;
        align-items: center;
        gap: 0;
        font-size: 11px;
        font-weight: 500;
        padding: 4px 10px;
        background: rgba(255, 255, 255, 0.04);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 16px;
        cursor: pointer;
        color: rgba(255, 255, 255, 0.45);
        transition: all 0.2s;
        position: relative;
    }}
    .decade-item input {{
        display: none;
    }}
    .decade-item:hover {{
        background: rgba(52, 152, 219, 0.1);
        border-color: rgba(52, 152, 219, 0.25);
        color: rgba(255, 255, 255, 0.7);
    }}
    .decade-item:has(input:checked) {{
        background: rgba(52, 152, 219, 0.18);
        border-color: rgba(52, 152, 219, 0.4);
        color: #74b9ff;
        box-shadow: 0 0 8px rgba(52, 152, 219, 0.15);
    }}
    .decade-item:has(input:checked)::before {{
        content: "";
        width: 5px;
        height: 5px;
        border-radius: 50%;
        background: #3498db;
        margin-right: 5px;
        box-shadow: 0 0 4px #3498db;
    }}

    /* Category checkboxes - Hierarchical */
    .category-list {{
        display: flex;
        flex-direction: column;
        gap: 3px;
    }}
    .category-item input[type="checkbox"] {{
        display: none;
    }}
    .category-tier-group {{
        display: flex;
        flex-direction: column;
        gap: 3px;
    }}
    .category-tier-label {{
        font-size: 9px;
        font-weight: 700;
        letter-spacing: 1.2px;
        text-transform: uppercase;
        color: rgba(236, 240, 241, 0.35);
        padding: 6px 4px 2px;
        margin-top: 4px;
    }}
    .category-tier-label:first-child {{
        margin-top: 0;
    }}
    /* Tier 1 = Critical (full width, prominent) */
    .category-item {{
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 12px;
        padding: 6px 8px;
        background: rgba(255, 255, 255, 0.04);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 8px;
        cursor: pointer;
        color: #b2bec3;
        transition: all 0.15s;
    }}
    .category-item.tier-1 {{
        padding: 8px 10px;
        background: rgba(255, 255, 255, 0.06);
        border-color: rgba(255, 255, 255, 0.1);
        font-weight: 600;
        color: #dfe6e9;
        font-size: 12px;
    }}
    .category-item.tier-1 .category-color {{
        width: 16px;
        height: 16px;
        box-shadow: 0 0 8px var(--tier-color, rgba(0,0,0,0.3));
    }}
    /* Tier 2 = Important (slight indent) */
    .category-item.tier-2 {{
        margin-left: 10px;
        padding: 5px 8px;
        font-size: 11px;
        border-color: rgba(255, 255, 255, 0.05);
        background: rgba(255, 255, 255, 0.025);
    }}
    /* Tier 3 = Minor (more indent, smaller) */
    .category-item.tier-3 {{
        margin-left: 20px;
        padding: 4px 8px;
        font-size: 11px;
        opacity: 0.8;
        border-color: rgba(255, 255, 255, 0.04);
        background: rgba(255, 255, 255, 0.015);
    }}
    .category-item:hover {{
        background: rgba(255, 255, 255, 0.08);
        color: #dfe6e9;
    }}
    .category-item:has(input:checked) {{
        background: rgba(255, 255, 255, 0.07);
        border-color: rgba(255, 255, 255, 0.12);
        color: #ecf0f1;
    }}
    .category-item:has(input:not(:checked)) {{
        opacity: 0.45;
    }}
    .category-item:has(input:not(:checked)):hover {{
        opacity: 0.7;
    }}
    .category-color {{
        width: 12px;
        height: 12px;
        border-radius: 50%;
        flex-shrink: 0;
        box-shadow: 0 0 6px rgba(0,0,0,0.3);
        transition: transform 0.15s;
    }}
    .category-item:has(input:checked) .category-color {{
        transform: scale(1.15);
        box-shadow: 0 0 10px var(--tier-color, rgba(0,0,0,0.4));
    }}
    /* Hierarchy connector lines */
    .category-tier-group {{
        position: relative;
        padding-left: 0;
    }}
    .category-tier-group.has-indent {{
        border-left: 1px solid rgba(255, 255, 255, 0.06);
        margin-left: 6px;
        padding-left: 0;
    }}

    /* Stats - Glass + Pulse */
    .stats-box {{
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.08);
        padding: 12px;
        border-radius: 10px;
        text-align: center;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }}
    .stats-box::after {{
        content: '';
        position: absolute;
        inset: 0;
        background: radial-gradient(circle at center, rgba(52,152,219,0.1), transparent 70%);
        opacity: 0;
        transition: opacity 0.5s;
        pointer-events: none;
    }}
    .stats-box.pulse::after {{
        opacity: 1;
        animation: statsPulse 0.6s ease-out;
    }}
    @keyframes statsPulse {{
        0% {{ opacity: 1; transform: scale(0.8); }}
        100% {{ opacity: 0; transform: scale(1.5); }}
    }}
    .stats-box .count {{
        font-size: 26px;
        font-weight: 700;
        color: #ecf0f1;
        transition: transform 0.2s ease;
    }}
    .stats-box.pulse .count {{
        animation: countBounce 0.3s ease;
    }}
    @keyframes countBounce {{
        0% {{ transform: scale(1); }}
        50% {{ transform: scale(1.15); }}
        100% {{ transform: scale(1); }}
    }}
    .stats-box .label {{
        font-size: 11px;
        color: rgba(236, 240, 241, 0.6);
    }}

    /* Country Sidebar - Glass Design */
    .country-sidebar {{
        position: fixed;
        top: 0;
        left: -420px;
        width: 420px;
        height: 100vh;
        background: rgba(14, 21, 27, 0.82);
        backdrop-filter: blur(18px) saturate(140%);
        -webkit-backdrop-filter: blur(18px) saturate(140%);
        color: #ecf0f1;
        border-right: 1px solid rgba(255, 255, 255, 0.08);
        box-shadow: 4px 0 30px rgba(0,0,0,0.45), inset 0 0 0 1px rgba(255,255,255,0.04);
        overflow-y: auto;
        z-index: 2000;
        transform: translateX(0);
        transition: transform 0.35s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    }}
    .country-sidebar.open {{
        transform: translateX(420px);
    }}
    /* Scroll progress indicator */
    .sidebar-scroll-progress {{
        position: sticky;
        top: 0;
        left: 0;
        width: 100%;
        height: 3px;
        z-index: 10;
        background: transparent;
    }}
    .sidebar-scroll-progress .bar {{
        height: 100%;
        background: linear-gradient(90deg, #00cec9, #0984e3);
        transform-origin: left;
        transform: scaleX(0);
        transition: transform 0.15s ease-out;
        border-radius: 0 2px 2px 0;
    }}
    .sidebar-header {{
        position: relative;
        padding: 20px 48px 20px 20px;
        background: rgba(44, 62, 80, 0.6);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        color: white;
        overflow: hidden;
    }}
    .sidebar-header .flag-bg {{
        position: absolute;
        inset: 0;
        background-size: cover;
        background-position: center;
        opacity: 0.08;
        pointer-events: none;
    }}
    .sidebar-header h2 {{
        margin: 0;
        font-size: 20px;
        font-weight: 600;
        position: relative;
        z-index: 1;
    }}
    .sidebar-header .event-count {{
        font-size: 13px;
        opacity: 0.8;
        margin-top: 5px;
        position: relative;
        z-index: 1;
    }}
    .close-sidebar {{
        position: absolute;
        top: 50%;
        right: 8px;
        transform: translateY(-50%);
        background: rgba(255,255,255,0.12);
        backdrop-filter: blur(8px);
        -webkit-backdrop-filter: blur(8px);
        border: 1px solid rgba(255,255,255,0.15);
        color: white;
        width: 32px;
        height: 32px;
        border-radius: 50%;
        font-size: 20px;
        line-height: 1;
        cursor: pointer;
        opacity: 0.8;
        z-index: 2;
        transition: all 0.2s;
    }}
    .close-sidebar:hover {{
        opacity: 1;
        background: rgba(255,255,255,0.22);
        transform: translateY(-50%) scale(1.1);
    }}

    /* Sidebar Tab Navigation */
    .sidebar-tabs {{
        display: flex;
        gap: 0;
        padding: 0 12px;
        background: rgba(0,0,0,0.2);
        border-bottom: 1px solid rgba(255,255,255,0.06);
        position: sticky;
        top: 3px;
        z-index: 5;
    }}
    .sidebar-tab {{
        flex: 1;
        padding: 10px 8px;
        font-size: 11px;
        font-weight: 600;
        color: rgba(236,240,241,0.5);
        background: transparent;
        border: none;
        border-bottom: 2px solid transparent;
        cursor: pointer;
        transition: all 0.2s;
        text-align: center;
        letter-spacing: 0.3px;
    }}
    .sidebar-tab:hover {{
        color: rgba(236,240,241,0.8);
        background: rgba(255,255,255,0.03);
    }}
    .sidebar-tab.active {{
        color: #74b9ff;
        border-bottom-color: #3498db;
        background: rgba(52,152,219,0.06);
    }}
    .sidebar-tab svg {{
        display: block;
        margin: 0 auto 3px;
        opacity: 0.7;
    }}
    .sidebar-tab.active svg {{
        opacity: 1;
    }}
    .sidebar-tab-panel {{
        display: none;
        animation: tabFadeIn 0.25s ease;
    }}
    .sidebar-tab-panel.active {{
        display: block;
    }}
    @keyframes tabFadeIn {{
        from {{ opacity: 0; transform: translateY(6px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}

    /* Group Cards (NATO/G8/BRICS) */
    .group-card {{
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 10px 12px;
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 10px;
        cursor: pointer;
        transition: all 0.25s ease;
        position: relative;
        overflow: hidden;
    }}
    .group-card::before {{
        content: '';
        position: absolute;
        inset: 0;
        opacity: 0;
        transition: opacity 0.3s;
        pointer-events: none;
    }}
    .group-card:hover {{
        background: rgba(255,255,255,0.06);
        border-color: rgba(255,255,255,0.15);
    }}
    .group-card.active {{
        border-color: var(--group-color, rgba(52,152,219,0.5));
        box-shadow: 0 0 16px rgba(52,152,219,0.12), inset 0 0 0 1px rgba(52,152,219,0.1);
    }}
    .group-card.active::before {{
        opacity: 1;
        background: radial-gradient(ellipse at left center, var(--group-glow, rgba(52,152,219,0.08)), transparent 70%);
    }}
    .group-card-icon {{
        width: 28px;
        height: 28px;
        flex-shrink: 0;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 8px;
        background: rgba(255,255,255,0.05);
        transition: all 0.25s;
    }}
    .group-card.active .group-card-icon {{
        background: var(--group-bg, rgba(52,152,219,0.15));
    }}
    .group-card-icon svg {{
        width: 16px;
        height: 16px;
        opacity: 0.6;
        transition: all 0.25s;
    }}
    .group-card.active .group-card-icon svg {{
        opacity: 1;
        filter: drop-shadow(0 0 4px currentColor);
    }}
    .group-card-label {{
        font-size: 12px;
        font-weight: 500;
        color: #b2bec3;
        transition: color 0.2s;
    }}
    .group-card.active .group-card-label {{
        color: #ecf0f1;
    }}
    .group-card-count {{
        margin-left: auto;
        font-size: 10px;
        color: rgba(236,240,241,0.4);
        padding: 2px 6px;
        border-radius: 999px;
        background: rgba(255,255,255,0.04);
    }}

    .sidebar-content {{
        flex: 1;
        overflow-y: auto;
        padding: 0;
        position: relative;
    }}
    /* Vertical timeline line */
    .sidebar-content::before {{
        content: '';
        position: absolute;
        top: 0;
        bottom: 0;
        left: 28px;
        width: 2px;
        background: linear-gradient(180deg, rgba(0, 206, 201, 0.3), rgba(9, 132, 227, 0.15), transparent);
        pointer-events: none;
        z-index: 1;
    }}

    /* Timeline in sidebar */
    .decade-section {{
        border-bottom: 1px solid rgba(255, 255, 255, 0.06);
    }}
    .decade-header {{
        padding: 12px 20px 12px 48px;
        background: rgba(45, 52, 54, 0.5);
        font-weight: 600;
        font-size: 14px;
        color: #ecf0f1;
        cursor: pointer;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-left: none;
        position: relative;
        transition: background 0.2s;
    }}
    /* Timeline dot on decade header */
    .decade-header::before {{
        content: '';
        position: absolute;
        left: 22px;
        top: 50%;
        transform: translateY(-50%);
        width: 12px;
        height: 12px;
        border-radius: 50%;
        background: #00cec9;
        border: 2px solid rgba(14, 21, 27, 0.8);
        z-index: 2;
        box-shadow: 0 0 8px rgba(0, 206, 201, 0.4);
        transition: all 0.2s;
    }}
    .decade-header:hover {{
        background: rgba(53, 59, 72, 0.7);
    }}
    .decade-header:hover::before {{
        transform: translateY(-50%) scale(1.2);
        box-shadow: 0 0 12px rgba(0, 206, 201, 0.6);
    }}
    .decade-header .count {{
        background: rgba(9, 132, 227, 0.3);
        color: #74b9ff;
        padding: 2px 8px;
        border-radius: 10px;
        font-size: 11px;
        border: 1px solid rgba(116, 185, 255, 0.2);
    }}
    .decade-events {{
        display: none;
        background: transparent;
        padding-bottom: 6px;
    }}
    .decade-events.open {{
        display: block;
    }}
    /* Glass event cards */
    .event-item {{
        padding: 14px 16px 14px 48px;
        margin: 4px 8px 4px 8px;
        border-radius: 8px;
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-left: 4px solid var(--cat-color, #636e72);
        background: rgba(255, 255, 255, 0.03);
        position: relative;
        transition: all 0.2s;
    }}
    /* Small timeline dot on event */
    .event-item::before {{
        content: '';
        position: absolute;
        left: 16px;
        top: 20px;
        width: 6px;
        height: 6px;
        border-radius: 50%;
        background: var(--cat-color, #636e72);
        opacity: 0.7;
        z-index: 2;
    }}
    .event-item:hover {{
        background: rgba(255, 255, 255, 0.07);
        border-color: rgba(255, 255, 255, 0.12);
        transform: translateX(2px);
    }}
    .event-item:last-child {{
        border-bottom: none;
    }}
    .event-item.tier-1 {{
        border-left-width: 5px;
        background: rgba(255, 255, 255, 0.06);
        border-color: rgba(255, 255, 255, 0.1);
        box-shadow: 0 2px 8px rgba(0,0,0,0.15);
    }}
    .event-item.tier-1::before {{
        width: 8px;
        height: 8px;
        opacity: 1;
        box-shadow: 0 0 6px var(--cat-color, #636e72);
    }}
    .event-item.tier-3 {{
        border-left-width: 3px;
        background: rgba(255, 255, 255, 0.015);
        opacity: 0.88;
    }}
    .event-item.event-enter {{
        animation: eventItemIn 0.22s ease both;
        animation-delay: var(--event-enter-delay, 0ms);
    }}
    .event-item.event-removing {{
        overflow: hidden;
        pointer-events: none;
        animation: eventItemOut 0.18s ease forwards;
    }}
    @keyframes eventItemIn {{
        from {{
            opacity: 0;
            transform: translateX(-8px);
        }}
        to {{
            opacity: 1;
            transform: translateX(0);
        }}
    }}
    @keyframes eventItemOut {{
        from {{
            opacity: 1;
            transform: translateX(0);
        }}
        to {{
            opacity: 0;
            transform: translateX(-10px);
            max-height: 0;
            margin: 0;
            padding-top: 0;
            padding-bottom: 0;
            border-width: 0;
        }}
    }}
    .sidebar-empty {{
        padding: 16px 18px;
        color: #95a5a6;
        font-size: 13px;
        font-style: italic;
        border-left: 3px solid #4b5563;
        background: rgba(255, 255, 255, 0.02);
        margin: 12px;
    }}
    .event-year {{
        font-size: 12px;
        color: #b2bec3;
        margin-bottom: 4px;
    }}
    .event-item.tier-1 .event-year {{
        color: #dfe6e9;
    }}
    .event-title {{
        font-weight: 600;
        font-size: 14px;
        color: #dfe6e9;
        margin-bottom: 6px;
    }}
    .event-item.tier-1 .event-title {{
        font-size: 15px;
        font-weight: 700;
        letter-spacing: 0.2px;
    }}
    .event-item.tier-3 .event-title {{
        font-size: 13px;
        font-weight: 500;
    }}
    .event-category {{
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 3px 9px;
        border-radius: 999px;
        font-size: 10px;
        font-weight: 600;
        color: white;
        background: var(--cat-color, #636e72);
        border: 1px solid rgba(255, 255, 255, 0.12);
        margin-bottom: 10px;
    }}
    .event-desc {{
        font-size: 12px;
        color: #bdc3c7;
        line-height: 1.5;
        margin-bottom: 8px;
    }}
    .event-item.tier-3 .event-desc {{
        font-size: 11.5px;
    }}
    .event-links {{
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-bottom: 8px;
    }}
    .event-wiki {{
        font-size: 11px;
        color: #74b9ff;
        text-decoration: none;
        border: 1px solid rgba(116,185,255,0.35);
        padding: 2px 8px;
        border-radius: 999px;
        display: inline-flex;
        align-items: center;
        gap: 6px;
    }}
    .event-wiki:hover {{
        color: #dfe6e9;
        border-color: rgba(116,185,255,0.6);
        background: rgba(116,185,255,0.08);
    }}
    
    /* Metadata Card - Dark Theme */
    .country-meta-card {{
        margin: 10px 12px;
        background: rgba(255, 255, 255, 0.03);
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.07);
        overflow: hidden;
        transition: border-color 0.2s;
    }}
    .country-meta-card:hover {{
        border-color: rgba(255, 255, 255, 0.12);
    }}
    .country-meta-card summary {{
        padding: 10px 15px;
        cursor: pointer;
        font-weight: 600;
        font-size: 13px;
        color: #dfe6e9;
        user-select: none;
        display: flex;
        align-items: center;
        justify-content: space-between;
        background: rgba(255, 255, 255, 0.04);
        border-radius: 12px 12px 0 0;
        transition: background 0.15s;
    }}
    .country-meta-card summary::marker {{ content: ''; }}
    .country-meta-card summary::-webkit-details-marker {{ display: none; }}
    .country-meta-card summary::after {{
        content: '';
        width: 0; height: 0;
        border-left: 5px solid transparent;
        border-right: 5px solid transparent;
        border-top: 5px solid rgba(255,255,255,0.4);
        transition: transform 0.2s;
        flex-shrink: 0;
    }}
    .country-meta-card[open] summary::after {{
        transform: rotate(180deg);
    }}
    .country-meta-card summary:hover {{ background: rgba(255, 255, 255, 0.08); }}
    .country-meta-card[open] summary {{
        border-bottom: 1px solid rgba(255, 255, 255, 0.06);
    }}
    .country-meta-content {{
        padding: 15px;
        font-size: 13px;
        line-height: 1.6;
        color: #b2bec3;
    }}
    .meta-row {{ margin-bottom: 10px; }}
    .meta-label {{ color: rgba(0, 206, 201, 0.7); font-size: 10px; text-transform: uppercase; letter-spacing: 0.8px; font-weight: 600; display: block; margin-bottom: 3px; }}
    .meta-row strong, .country-meta-content strong {{ color: #ecf0f1; }}
    .country-meta-content ul {{ padding-left: 16px; margin: 6px 0; }}
    .country-meta-content li {{ margin-bottom: 3px; color: #dfe6e9; }}

    /* Country Flag Overlay */
    .country-flag-overlay {{
        position: fixed;
        pointer-events: none;
        z-index: 800;
        transition: opacity 0.3s ease;
    }}
    .flag-pattern-defs {{
        position: absolute;
        width: 0;
        height: 0;
    }}

    /* Popup styles */
    .leaflet-popup-content {{
        font-family: 'Noto Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
        margin: 12px !important;
    }}
    .leaflet-popup-content-wrapper {{
        border-radius: 10px !important;
    }}
    .popup-container {{
        min-width: 280px;
        max-width: 320px;
    }}
    .popup-header {{
        border-bottom: 1px solid #eee;
        padding-bottom: 10px;
        margin-bottom: 10px;
    }}
    .popup-country {{
        font-size: 18px;
        font-weight: 600;
        color: #2c3e50;
        margin: 0;
    }}
    .popup-count {{
        font-size: 12px;
        color: #666;
        margin-top: 2px;
    }}
    .popup-preview {{
        margin-bottom: 12px;
    }}
    .popup-event {{
        padding: 8px 0;
        border-bottom: 1px solid #f0f0f0;
    }}
    .popup-event:last-child {{
        border-bottom: none;
    }}
    .popup-event-year {{
        font-size: 11px;
        color: #888;
    }}
    .popup-event-title {{
        font-size: 13px;
        font-weight: 500;
        color: #333;
        margin: 2px 0;
    }}
    .popup-event-cat {{
        display: inline-block;
        padding: 1px 6px;
        border-radius: 8px;
        font-size: 9px;
        color: white;
    }}
    .popup-btn {{
        display: block;
        width: 100%;
        padding: 10px;
        background: #3498db;
        color: white;
        border: none;
        border-radius: 6px;
        cursor: pointer;
        font-size: 13px;
        font-weight: 500;
        text-align: center;
    }}
    .popup-btn:hover {{
        background: #2980b9;
    }}

    /* Mobil: paneller kolay kapansın, daha fazla harita alanı */
    @media (max-width: 768px) {{
        .country-sidebar {{
            width: 100%;
            left: -100%;
        }}
        .country-sidebar.open {{
            transform: translateX(100%);
        }}
        .control-panel {{
            width: min(320px, 92vw);
            max-height: 80vh;
            transform: translateX(110%);
            opacity: 0;
            pointer-events: none;
        }}
        .control-panel.mobile-open {{
            transform: translateX(0);
            opacity: 1;
            pointer-events: auto;
        }}
        .panel-toggle {{
            display: block;
        }}
        .panel-fab {{
            display: inline-flex;
            width: auto !important;
            height: auto !important;
            max-width: 130px;
            padding: 10px 16px !important;
            font-size: 13px;
        }}
        .panel-handle {{
            display: inline-flex;
        }}
        .build-info {{
            right: 10px;
            left: auto;
            font-size: 10px;
        }}
        .share-fab {{
            bottom: 16px;
            right: 16px;
        }}
    }}
    @media (min-width: 769px) {{
        .panel-toggle {{
            display: none;
        }}
        .panel-fab {{
            display: none;
        }}
        .panel-handle {{
            display: none;
        }}
    }}
    .panel-toggle {{
        /* display is controlled by media queries */
        width: 100%;
        padding: 8px;
        margin-bottom: 8px;
        background: #3498db;
        color: white;
        border: none;
        border-radius: 6px;
        cursor: pointer;
        font-size: 13px;
        font-weight: 700;
        position: sticky;
        top: 0;
        z-index: 1;
    }}
    .panel-fab {{
        /* display is controlled by media queries */
        position: fixed;
        top: 10px;
        right: 10px;
        z-index: 1101;
        padding: 10px 12px;
        border-radius: 999px;
        background: #3498db;
        color: white;
        border: none;
        cursor: pointer;
        font-size: 13px;
        font-weight: 800;
        letter-spacing: 0.2px;
        box-shadow: 0 6px 22px rgba(0,0,0,0.22);
        align-items: center;
        gap: 8px;
    }}
    .panel-fab.hidden {{ display: none; }}
    .panel-fab:active {{ transform: scale(0.98); }}
    .panel-handle {{
        /* display is controlled by media queries */
        position: fixed;
        top: 50%;
        right: 6px;
        transform: translateY(-50%);
        z-index: 1102;
        width: 36px;
        height: 46px;
        border-radius: 12px;
        background: rgba(14, 21, 27, 0.75);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.12);
        box-shadow: 0 8px 22px rgba(0,0,0,0.3);
        color: #74b9ff;
        cursor: pointer;
        align-items: center;
        justify-content: center;
        -webkit-tap-highlight-color: transparent;
        touch-action: manipulation;
    }}
    .panel-handle:active {{
        transform: translateY(-50%) scale(0.98);
    }}
    .panel-handle-icon {{
        font-size: 22px;
        font-weight: 900;
        line-height: 1;
        display: block;
    }}
    .build-info {{
        position: fixed;
        right: 300px;
        bottom: 8px;
        z-index: 1200;
        background: rgba(0, 0, 0, 0.7);
        color: #ecf0f1;
        padding: 6px 8px;
        border-radius: 6px;
        font-size: 11px;
        letter-spacing: 0.2px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.25);
    }}
    .build-info a {{
        color: #f1c40f;
        text-decoration: none;
        margin-left: 6px;
        font-weight: 600;
    }}
    .app-footer {{
        position: fixed;
        left: 8px;
        bottom: 8px;
        z-index: 1200;
        background: rgba(0, 0, 0, 0.55);
        color: rgba(236, 240, 241, 0.92);
        padding: 5px 10px;
        border-radius: 999px;
        font-size: 11px;
        letter-spacing: 0.2px;
        border: 1px solid rgba(255, 255, 255, 0.16);
        box-shadow: 0 2px 8px rgba(0,0,0,0.22);
        pointer-events: none;
        user-select: none;
        backdrop-filter: blur(2px);
    }}
    .group-badge {{
        display: inline-block;
        padding: 2px 8px;
        border-radius: 999px;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.2px;
        margin-right: 6px;
        line-height: 1.4;
    }}
    .group-badge.g8 {{
        background: rgba(241, 196, 15, 0.18);
        border: 1px solid rgba(241, 196, 15, 0.55);
        color: #f1c40f;
    }}
    .group-badge.nato {{
        background: rgba(52, 152, 219, 0.18);
        border: 1px solid rgba(52, 152, 219, 0.55);
        color: #3498db;
    }}
    .group-badge.brics {{
        background: rgba(88, 101, 242, 0.16);
        border: 1px solid rgba(88, 101, 242, 0.55);
        color: #5865f2;
    }}
    .indicator-select {{
        width: 100%;
        padding: 8px 10px;
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 8px;
        background: rgba(255, 255, 255, 0.06);
        color: #ecf0f1;
        font-size: 12px;
        cursor: pointer;
        appearance: none;
        -webkit-appearance: none;
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath d='M2 4l4 4 4-4' fill='none' stroke='%2395a5a6' stroke-width='1.5' stroke-linecap='round'/%3E%3C/svg%3E");
        background-repeat: no-repeat;
        background-position: right 8px center;
        padding-right: 28px;
        transition: all 0.15s;
    }}
    .indicator-select:hover {{
        border-color: rgba(255, 255, 255, 0.2);
        background-color: rgba(255, 255, 255, 0.09);
    }}
    .indicator-select option {{
        background: #1e272e;
        color: #ecf0f1;
    }}
    .indicator-legend {{
        font-size: 11px;
        color: #dfe6e9;
        background: rgba(255, 255, 255, 0.04);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 8px;
        padding: 8px 10px;
    }}
    .indicator-legend-title {{
        font-size: 16px;
        font-weight: 800;
        letter-spacing: 0.8px;
        text-transform: uppercase;
        color: #ecf0f1;
    }}
    .indicator-legend-desc {{
        margin-top: 4px;
        font-size: 11px;
        line-height: 1.45;
        color: rgba(236, 240, 241, 0.7);
    }}
    .indicator-legend-detail {{
        margin-top: 6px;
        font-size: 10px;
        line-height: 1.4;
        color: rgba(236, 240, 241, 0.6);
    }}
    .legend-bar {{
        height: 8px;
        border-radius: 999px;
        margin: 6px 0 4px 0;
        background: linear-gradient(90deg, #e8f5e9 0%, #1b5e20 100%);
        position: relative;
        overflow: hidden;
    }}
    .legend-bar::after {{
        content: '';
        position: absolute;
        inset: 0;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.15), transparent);
        animation: legendShimmer 3s ease-in-out infinite;
    }}
    @keyframes legendShimmer {{
        0%, 100% {{ transform: translateX(-100%); }}
        50% {{ transform: translateX(100%); }}
    }}
    .legend-row {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 8px;
        font-size: 11px;
        color: rgba(236, 240, 241, 0.6);
    }}
    .active-indicator-banner {{
        position: fixed;
        top: 16px;
        left: 50%;
        transform: translateX(-50%);
        z-index: 1250;
        width: min(620px, calc(100vw - 560px));
        min-width: 360px;
        padding: 14px 18px;
        border-radius: 16px;
        background: rgba(7, 18, 31, 0.88);
        border: 1px solid rgba(255, 255, 255, 0.14);
        box-shadow: 0 16px 40px rgba(0, 0, 0, 0.28);
        backdrop-filter: blur(10px);
        color: #f4f7fb;
    }}
    /* Hover data = hero section (top, big, changes) */
    .active-indicator-hover {{
        font-size: 22px;
        font-weight: 800;
        letter-spacing: 0.5px;
        line-height: 1.2;
        color: #ffffff;
        min-height: 28px;
        transition: opacity 0.15s ease;
    }}
    .active-indicator-hover.empty {{
        font-size: 13px;
        font-weight: 400;
        color: rgba(190, 206, 221, 0.6);
        letter-spacing: 0;
    }}
    /* Indicator name = subtitle */
    .active-indicator-title {{
        margin-top: 4px;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 1.4px;
        text-transform: uppercase;
        color: rgba(255, 255, 255, 0.55);
    }}
    /* Divider line */
    .active-indicator-divider {{
        height: 1px;
        margin: 10px 0;
        background: rgba(255, 255, 255, 0.1);
    }}
    /* Description = bottom, smaller */
    .active-indicator-desc {{
        font-size: 11px;
        line-height: 1.4;
        color: rgba(230, 236, 242, 0.7);
    }}
    .active-indicator-meta {{
        margin-top: 4px;
        font-size: 10px;
        line-height: 1.35;
        color: rgba(190, 206, 221, 0.6);
    }}
    .active-indicator-kicker {{
        display: none;
    }}
    @media (max-width: 768px) {{
        .active-indicator-banner {{
            top: 12px;
            left: 16px;
            right: 16px;
            transform: none;
            width: auto;
            min-width: 0;
            padding: 12px 14px;
        }}
        .active-indicator-hover {{
            font-size: 18px;
        }}
    }}
</style>

<!-- Sidebar always visible -->
<div class="country-sidebar" id="countrySidebar">
    <div class="sidebar-scroll-progress"><div class="bar" id="sidebarScrollBar"></div></div>
    <div class="sidebar-header">
        <div class="flag-bg" id="sidebarFlagBg"></div>
        <h2 id="sidebarCountryName">Ülke</h2>
        <div class="event-count" id="sidebarEventCount">0 olay</div>
        <button class="close-sidebar" onclick="closeSidebar()">×</button>
    </div>
    <div class="sidebar-tabs">
        <button class="sidebar-tab active" data-tab="events" onclick="switchSidebarTab('events')">
            <svg width="14" height="14" viewBox="0 0 16 16" fill="none"><path d="M4 2h8v12l-4-2-4 2V2z" stroke="currentColor" stroke-width="1.3"/></svg>
            Olaylar
        </button>
        <button class="sidebar-tab" data-tab="data" onclick="switchSidebarTab('data')">
            <svg width="14" height="14" viewBox="0 0 16 16" fill="none"><rect x="2" y="7" width="3" height="7" rx="0.5" fill="currentColor" opacity="0.7"/><rect x="6.5" y="4" width="3" height="10" rx="0.5" fill="currentColor" opacity="0.7"/><rect x="11" y="2" width="3" height="12" rx="0.5" fill="currentColor" opacity="0.7"/></svg>
            Veri
        </button>
        <button class="sidebar-tab" data-tab="relations" onclick="switchSidebarTab('relations')">
            <svg width="14" height="14" viewBox="0 0 16 16" fill="none"><circle cx="4" cy="8" r="2" stroke="currentColor" stroke-width="1.2"/><circle cx="12" cy="8" r="2" stroke="currentColor" stroke-width="1.2"/><path d="M6 8h4" stroke="currentColor" stroke-width="1.2" stroke-dasharray="2 1"/></svg>
            İlişkiler
        </button>
    </div>
    <div class="sidebar-tab-panel active" id="tabEvents">
        <div class="sidebar-content" id="sidebarContent"></div>
    </div>
    <div class="sidebar-tab-panel" id="tabData">
        <div class="sidebar-content" id="countryMetaContainer"></div>
    </div>
    <div class="sidebar-tab-panel" id="tabRelations">
        <div class="sidebar-content" id="countryRelationsContainer"></div>
    </div>
</div>

<button class="panel-fab" id="panelFab" onclick="toggleFilterPanel()" aria-label="Filtreleri aç/kapat" aria-expanded="false">
    Filtreler
</button>

<div class="control-panel" id="controlPanel">
    <button class="panel-toggle" id="panelToggle" onclick="toggleFilterPanel()" aria-label="Filtreleri aç/kapat" aria-expanded="false">Filtreler</button>
    <h3>Jeopolitik Tarih Haritası</h3>

    <div class="instructions">
        Ülkeye tıklayın veya marker'a basın. Filtreleri kullanarak olayları daraltabilirsiniz.
    </div>

    <!-- Accordion: AI Arama -->
    <div class="control-section open" id="accAiSearch">
        <div class="acc-header" onclick="toggleAcc('accAiSearch')">
            <div class="acc-icon" style="--acc-color:rgba(52,152,219,0.15);--acc-text:#74b9ff;">
                <svg viewBox="0 0 24 24"><path d="M10 4a6 6 0 104.47 10.02l3.75 3.75 1.41-1.41-3.75-3.75A6 6 0 0010 4zm0 2a4 4 0 110 8 4 4 0 010-8z"/></svg>
            </div>
            <span class="acc-title">AI Arama</span>
            <span class="acc-badge">Vertex</span>
            <svg class="acc-chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 9l6 6 6-6"/></svg>
        </div>
        <div class="acc-body">
            <div class="ai-search-panel">
                <div class="ai-search-form">
                    <input class="ai-search-input" id="aiSearchInput" type="search" autocomplete="off" placeholder="Örn. petrol krizleri">
                    <button class="ai-search-button" id="aiSearchButton" type="button" onclick="aiSearch()">Ara</button>
                </div>
                <div class="ai-search-status" id="aiSearchStatus">Doğal dilde olay arayın.</div>
                <div class="ai-search-summary" id="aiSummary"></div>
                <div class="ai-search-results" id="aiResultsList"></div>
            </div>
        </div>
    </div>

    <!-- Accordion: Zaman Dilimi -->
    <div class="control-section open" id="accDecades">
        <div class="acc-header" onclick="toggleAcc('accDecades')">
            <div class="acc-icon" style="--acc-color:rgba(52,152,219,0.15);--acc-text:#3498db;">
                <svg viewBox="0 0 24 24"><path d="M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10 10-4.5 10-10S17.5 2 12 2zm0 18c-4.4 0-8-3.6-8-8s3.6-8 8-8 8 3.6 8 8-3.6 8-8 8zm.5-13H11v6l5.2 3.2.8-1.3-4.5-2.7V7z"/></svg>
            </div>
            <span class="acc-title">Zaman Dilimi</span>
            <span class="acc-badge" id="decadeBadge">11/11</span>
            <svg class="acc-chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 9l6 6 6-6"/></svg>
        </div>
        <div class="acc-body">
            <div class="acc-actions">
                <button onclick="event.stopPropagation();selectAllDecades()">Tümü</button>
                <button onclick="event.stopPropagation();selectNoDecades()">Hiçbiri</button>
            </div>
            <div class="decade-grid" id="decadeFilters"></div>
        </div>
    </div>

    <!-- Accordion: Kategoriler -->
    <div class="control-section open" id="accCategories">
        <div class="acc-header" onclick="toggleAcc('accCategories')">
            <div class="acc-icon" style="--acc-color:rgba(231,76,60,0.15);--acc-text:#e74c3c;">
                <svg viewBox="0 0 24 24"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg>
            </div>
            <span class="acc-title">Kategoriler</span>
            <span class="acc-badge" id="catBadge"></span>
            <svg class="acc-chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 9l6 6 6-6"/></svg>
        </div>
        <div class="acc-body">
            <div class="acc-actions">
                <button onclick="event.stopPropagation();selectAllCategories()">Tümü</button>
                <button onclick="event.stopPropagation();selectNoCategories()">Hiçbiri</button>
            </div>
            <div class="category-list" id="categoryFilters"></div>
        </div>
    </div>

    <!-- Accordion: Özel Listeler -->
    <div class="control-section" id="accSpecial">
        <div class="acc-header" onclick="toggleAcc('accSpecial')">
            <div class="acc-icon" style="--acc-color:rgba(241,196,15,0.15);--acc-text:#f1c40f;">
                <svg viewBox="0 0 24 24"><path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-5 14H7v-2h7v2zm3-4H7v-2h10v2zm0-4H7V7h10v2z"/></svg>
            </div>
            <span class="acc-title">Özel Listeler</span>
            <svg class="acc-chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 9l6 6 6-6"/></svg>
        </div>
        <div class="acc-body">
            <div class="category-list">
                <label class="category-item" style="background: rgba(241, 196, 15, 0.06); border: 1px solid rgba(241, 196, 15, 0.15);">
                    <input type="checkbox" checked onchange="toggleSpecial('time_100')" id="special-time_100" style="display:none;">
                    <span class="category-color" style="background: #f1c40f; box-shadow: 0 0 5px #f1c40f;"></span>
                    Time 100: Yüzyılın Kişileri
                </label>
                <label class="category-item" style="background: rgba(231, 76, 60, 0.06); border: 1px solid rgba(231, 76, 60, 0.15);">
                    <input type="checkbox" checked onchange="toggleConflictArrows()" id="toggle-arrows" style="display:none;">
                    <span class="category-color" style="background: #e74c3c; box-shadow: 0 0 5px #e74c3c;"></span>
                    Çatışma Okları
                </label>
            </div>
        </div>
    </div>

    <!-- Accordion: Ülke Grupları -->
    <div class="control-section" id="accGroups">
        <div class="acc-header" onclick="toggleAcc('accGroups')">
            <div class="acc-icon" style="--acc-color:rgba(46,204,113,0.15);--acc-text:#2ecc71;">
                <svg viewBox="0 0 24 24"><path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm-6 6v2h12v-2c0-2.67-4-4.13-6-4.13S6 15.33 6 18z"/></svg>
            </div>
            <span class="acc-title">Ülke Grupları</span>
            <svg class="acc-chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 9l6 6 6-6"/></svg>
        </div>
        <div class="acc-body">
            <div style="display:flex; flex-direction:column; gap:6px;">
                <div class="group-card" id="group-nato-card" onclick="toggleCountryGroupCard('nato')" style="--group-color:rgba(52,152,219,0.5);--group-glow:rgba(52,152,219,0.08);--group-bg:rgba(52,152,219,0.15);">
                    <input type="checkbox" id="group-nato" style="display:none;">
                    <div class="group-card-icon" style="color:#3498db;">
                        <svg viewBox="0 0 16 16" fill="none"><path d="M8 1l1.8 3.6L14 5.4l-3 2.9.7 4.1L8 10.4l-3.7 2 .7-4.1-3-2.9 4.2-.8L8 1z" stroke="currentColor" stroke-width="1.2" stroke-linejoin="round"/><circle cx="8" cy="7" r="1.5" fill="currentColor" opacity="0.5"/></svg>
                    </div>
                    <span class="group-card-label">NATO</span>
                    <span class="group-card-count" id="natoCount"></span>
                </div>
                <div class="group-card" id="group-g8-card" onclick="toggleCountryGroupCard('g8')" style="--group-color:rgba(241,196,15,0.5);--group-glow:rgba(241,196,15,0.08);--group-bg:rgba(241,196,15,0.15);">
                    <input type="checkbox" id="group-g8" style="display:none;">
                    <div class="group-card-icon" style="color:#f1c40f;">
                        <svg viewBox="0 0 16 16" fill="none"><circle cx="8" cy="8" r="5.5" stroke="currentColor" stroke-width="1.2"/><text x="8" y="10.5" text-anchor="middle" font-size="6" font-weight="700" fill="currentColor">8</text></svg>
                    </div>
                    <span class="group-card-label">G8</span>
                    <span class="group-card-count" id="g8Count"></span>
                </div>
                <div class="group-card" id="group-brics-card" onclick="toggleCountryGroupCard('brics_plus')" style="--group-color:rgba(88,101,242,0.5);--group-glow:rgba(88,101,242,0.08);--group-bg:rgba(88,101,242,0.15);">
                    <input type="checkbox" id="group-brics_plus" style="display:none;">
                    <div class="group-card-icon" style="color:#5865f2;">
                        <svg viewBox="0 0 16 16" fill="none"><rect x="2" y="9" width="4" height="5" rx="0.5" fill="currentColor" opacity="0.6"/><rect x="6" y="5" width="4" height="9" rx="0.5" fill="currentColor" opacity="0.7"/><rect x="10" y="2" width="4" height="12" rx="0.5" fill="currentColor" opacity="0.8"/></svg>
                    </div>
                    <span class="group-card-label">BRICS+</span>
                    <span class="group-card-count" id="bricsCount"></span>
                </div>
            </div>
        </div>
    </div>

    <!-- Accordion: Gösterge Katmanları -->
    <div class="control-section" id="accIndicators">
        <div class="acc-header" onclick="toggleAcc('accIndicators')">
            <div class="acc-icon" style="--acc-color:rgba(155,89,182,0.15);--acc-text:#9b59b6;">
                <svg viewBox="0 0 24 24"><path d="M3.5 18.49l6-6.01 4 4L22 6.92l-1.41-1.41-7.09 7.97-4-4L2 16.99z"/></svg>
            </div>
            <span class="acc-title">Gösterge Katmanları</span>
            <span class="acc-badge">13</span>
            <svg class="acc-chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 9l6 6 6-6"/></svg>
        </div>
        <div class="acc-body">
            <select class="indicator-select" id="indicatorSelect" onchange="setIndicatorMode(this.value)">
                <option value="">Gösterge kapalı</option>
                <option value="sanctions_risk_score">Yaptırım / Risk</option>
                <option value="weather_pressure_score">İklim Baskısı</option>
                <option value="air_quality_pm25">Hava Kalitesi (PM2.5)</option>
                <option value="fx_pressure_score">Kur Baskısı (30g USD)</option>
                <option value="min_wage">Asgari Ücret (USD/saat)</option>
                <option value="bigmac">Big Mac Endeksi (USD)</option>
                <option value="water_internal_total">İç Tatlı Su (milyar m3)</option>
                <option value="water_internal_per_capita">İç Tatlı Su / Kişi</option>
                <option value="water_stress">Su Stresi</option>
                <option value="water_withdrawal_pct_internal">Su Çekimi / İç Kaynak</option>
                <option value="water_use_agriculture">Su Kullanımı: Tarım</option>
                <option value="water_use_industry">Su Kullanımı: Sanayi</option>
                <option value="water_use_domestic">Su Kullanımı: Evsel</option>
            </select>
            <div class="indicator-legend" id="indicatorLegend" style="display:none;"></div>
        </div>
    </div>

<div class="stats-box">
    <div class="count" id="visibleCount">0</div>
    <div class="label">görünen olay</div>
</div>
</div>

<div class="build-info" id="buildInfo">
    Build: {self.build_info.get("build_time_utc", "unknown")}
    <a href="/healthz.json" target="_blank" rel="noopener">health</a>
    <div id="indicatorHoverInfo" style="margin-top:2px; color:#bdc3c7;"></div>
</div>

<div class="active-indicator-banner" id="activeIndicatorBanner" style="display:none;">
    <div class="active-indicator-hover empty" id="activeIndicatorHover">Bir ülkenin üzerine gelin.</div>
    <div class="active-indicator-title" id="activeIndicatorTitle"></div>
    <div class="active-indicator-divider"></div>
    <div class="active-indicator-desc" id="activeIndicatorDesc"></div>
    <div class="active-indicator-meta" id="activeIndicatorMeta"></div>
</div>

<div class="app-footer" id="appFooter">Jeopolitik harita Alpha 1.0 - Gurur Sönmez</div>

<button class="panel-handle" id="panelHandle" onclick="toggleFilterPanel()" aria-label="Filtre panelini aç/kapat" aria-expanded="true">
    <span class="panel-handle-icon" id="panelHandleIcon" aria-hidden="true">›</span>
</button>

<script>
{parse_md_js}
// --- Async Data Loading ---
// Small data stays inline (categories, decades are tiny)
const categories = {categories_json};
const decades = {decades_json};

// Large data loaded asynchronously from separate files
let allEvents = [];
let countryMeta = {{}};
let waterSourceData = {{}};
let currentConflictData = {{}};
let externalData = {{}};
let strategicSnapshotData = {{}};
let countryGroups = {{ g8: new Set(), nato: new Set(), brics_plus: new Set() }};
let baseIndicators = {{}};
let waterSourceNotes = {{}};
let activeConflicts = [];

// Loading overlay
(function() {{
    const overlay = document.createElement('div');
    overlay.id = 'loadingOverlay';
    overlay.innerHTML = '<div style="text-align:center;color:#ecf0f1;font-family:sans-serif;"><div style="font-size:18px;font-weight:600;margin-bottom:12px;">Jeopolitik Harita Yükleniyor...</div><div id="loadProgress" style="font-size:13px;opacity:0.7;">Veriler indiriliyor</div></div>';
    overlay.style.cssText = 'position:fixed;inset:0;z-index:9999;display:flex;align-items:center;justify-content:center;background:rgba(10,15,20,0.92);backdrop-filter:blur(8px);transition:opacity 0.4s;';
    document.body.appendChild(overlay);
}})();

async function loadAppData() {{
    const progress = document.getElementById('loadProgress');
    try {{
        progress.textContent = 'Harita verileri indiriliyor...';
        const [eventsRes, geoRes, metaRes] = await Promise.all([
            fetch('events_data.json'),
            fetch('geo.json'),
            fetch('meta.json')
        ]);

        progress.textContent = 'Veriler işleniyor...';
        const [eventsData, geoData, metaData] = await Promise.all([
            eventsRes.json(),
            geoRes.json(),
            metaRes.json()
        ]);

        // Assign to globals
        allEvents = eventsData;
        window.countriesGeoJSON = geoData;

        countryMeta = metaData.country_metadata || {{}};
        waterSourceData = metaData.water_sources || {{}};
        currentConflictData = metaData.current_conflicts || {{}};
        externalData = metaData.indicators || {{}};
        strategicSnapshotData = metaData.strategic_snapshots || {{}};

        // Derived data
        countryGroups = {{
            g8: new Set((externalData.groups && externalData.groups.g8) ? externalData.groups.g8 : []),
            nato: new Set((externalData.groups && externalData.groups.nato) ? externalData.groups.nato : []),
            brics_plus: new Set((externalData.groups && externalData.groups.brics_plus) ? externalData.groups.brics_plus : [])
        }};
        baseIndicators = (externalData && externalData.indicators) ? externalData.indicators : {{}};
        waterSourceNotes = (waterSourceData && waterSourceData.countries) ? waterSourceData.countries : {{}};
        activeConflicts = Array.isArray(currentConflictData && currentConflictData.conflicts) ? currentConflictData.conflicts : [];

        // Also set global name mappings from meta
        window.geoJSONNameMap = metaData.turkish_to_english || {{}};
        window.reverseNameMap = metaData.english_to_turkish || {{}};
        window.turkishToIso = metaData.turkish_to_iso || {{}};

        // Rebuild indicator data now that async data is available
        rebuildIndicatorData();

        console.log('Data loaded: ' + allEvents.length + ' events, ' + geoData.features.length + ' countries');
        progress.textContent = 'Harita başlatılıyor...';
        return true;
    }} catch(err) {{
        console.error('Data loading failed:', err);
        progress.textContent = 'Veri yükleme hatası: ' + err.message;
        progress.style.color = '#e74c3c';
        // Dismiss loading overlay after 5 seconds so user can still see the map tiles
        setTimeout(function() {{
            const ov = document.getElementById('loadingOverlay');
            if (ov) {{ ov.style.opacity = '0'; setTimeout(() => ov.remove(), 400); }}
        }}, 5000);
        return false;
    }}
}}

function buildStrategicIndicators(snapshots) {{
    const sanctions = (snapshots && snapshots.sanctions) ? snapshots.sanctions : {{}};
    const weather = (snapshots && snapshots.weather) ? snapshots.weather : {{}};
    const airQuality = (snapshots && snapshots.air_quality) ? snapshots.air_quality : {{}};
    const fx = (snapshots && snapshots.fx) ? snapshots.fx : {{}};
    const out = {{}};

    out.sanctions_risk_score = {{
        label: 'Yaptirim / Risk',
        unit: 'puan',
        decimals: 0,
        source: {{
            type: sanctions.provider || 'opensanctions',
            updated_at_utc: sanctions.updated_at_utc || '',
            dataset_updated_at: sanctions.source && sanctions.source.dataset_updated_at ? sanctions.source.dataset_updated_at : '',
            note: sanctions.source_note || ''
        }},
        by_country: Object.fromEntries(
            Object.entries((sanctions && sanctions.countries) ? sanctions.countries : {{}}).map(([country, row]) => [
                country,
                Object.assign({{}}, row || {{}}, {{
                    value: (row && typeof row.risk_score === 'number') ? row.risk_score : null
                }})
            ])
        )
    }};

    out.weather_pressure_score = {{
        label: 'Iklim Baskisi',
        unit: 'puan',
        decimals: 0,
        source: {{
            type: weather.provider || 'open-meteo',
            updated_at_utc: weather.updated_at_utc || '',
            note: weather.source_note || ''
        }},
        by_country: Object.fromEntries(
            Object.entries((weather && weather.countries) ? weather.countries : {{}}).map(([country, row]) => [
                country,
                Object.assign({{}}, row || {{}}, {{
                    value: (row && typeof row.pressure_score === 'number') ? row.pressure_score : null
                }})
            ])
        )
    }};

    out.air_quality_pm25 = {{
        label: 'Hava Kalitesi (PM2.5)',
        unit: 'µg/m³',
        decimals: 1,
        source: {{
            type: airQuality.provider || 'air-quality',
            updated_at_utc: airQuality.updated_at_utc || '',
            note: airQuality.source_note || ''
        }},
        by_country: Object.fromEntries(
            Object.entries((airQuality && airQuality.countries) ? airQuality.countries : {{}}).map(([country, row]) => [
                country,
                Object.assign({{}}, row || {{}}, {{
                    value: (row && row.current && typeof row.current.pm2_5 === 'number') ? row.current.pm2_5 : null
                }})
            ])
        )
    }};

    out.fx_pressure_score = {{
        label: 'Kur Baskisi (30 gun USD)',
        unit: '%',
        decimals: 1,
        source: {{
            type: fx.provider || 'frankfurter',
            updated_at_utc: fx.updated_at_utc || '',
            current_date: fx.source && fx.source.current_date ? fx.source.current_date : '',
            comparison_date_resolved: fx.source && fx.source.comparison_date_resolved ? fx.source.comparison_date_resolved : '',
            note: fx.source_note || ''
        }},
        by_country: Object.fromEntries(
            Object.entries((fx && fx.countries) ? fx.countries : {{}}).map(([country, row]) => [
                country,
                Object.assign({{}}, row || {{}}, {{
                    value: (row && typeof row.pressure_pct_30d === 'number') ? row.pressure_pct_30d : null
                }})
            ])
        )
    }};

    return out;
}}

// These are rebuilt after async data loads via rebuildIndicatorData()
let strategicIndicators = {{}};
let externalIndicators = {{}};
let strategicCountries = {{ sanctions: {{}}, weather: {{}}, air_quality: {{}}, fx: {{}} }};

function rebuildIndicatorData() {{
    strategicIndicators = buildStrategicIndicators(strategicSnapshotData);
    externalIndicators = Object.assign({{}}, baseIndicators, strategicIndicators);
    strategicCountries = {{
        sanctions: (strategicSnapshotData && strategicSnapshotData.sanctions && strategicSnapshotData.sanctions.countries) ? strategicSnapshotData.sanctions.countries : {{}},
        weather: (strategicSnapshotData && strategicSnapshotData.weather && strategicSnapshotData.weather.countries) ? strategicSnapshotData.weather.countries : {{}},
        air_quality: (strategicSnapshotData && strategicSnapshotData.air_quality && strategicSnapshotData.air_quality.countries) ? strategicSnapshotData.air_quality.countries : {{}},
        fx: (strategicSnapshotData && strategicSnapshotData.fx && strategicSnapshotData.fx.countries) ? strategicSnapshotData.fx.countries : {{}}
    }};
    window.externalIndicators = externalIndicators;
    console.log('Indicator data rebuilt:', Object.keys(externalIndicators).length, 'indicators');
}}

// Expose to window for other injected scripts
window.countryGroups = countryGroups;
window.externalIndicators = externalIndicators;
window.activeCountryGroup = null; // 'g8' | 'nato' | 'brics_plus' | null
window.activeIndicator = '';
window.currentConflicts = activeConflicts;

// State
let selectedDecades = new Set(decades);
// Initialize special list state
let showTime100 = true;
window.showConflictArrows = true;
// Remove 'time_100' from standard categories set to avoid double toggle issues if it's there
let selectedCategories = new Set(Object.keys(categories).filter(c => c !== 'time_100'));

function buildConflictIndex(conflicts) {{
    const index = {{}};
    (conflicts || []).forEach(conflict => {{
        const touched = new Set();
        (conflict.participants || []).forEach(country => {{
            const key = String(country || '').trim();
            if (!key || touched.has(key)) return;
            touched.add(key);
            if (!index[key]) index[key] = [];
            index[key].push(conflict);
        }});
        (conflict.links || []).forEach(link => {{
            ['source', 'target'].forEach(field => {{
                const key = String((link && link[field]) || '').trim();
                if (!key || touched.has(key)) return;
                touched.add(key);
                if (!index[key]) index[key] = [];
                index[key].push(conflict);
            }});
        }});
    }});
    return index;
}}

const conflictsByCountry = buildConflictIndex(activeConflicts);
window.conflictsByCountry = conflictsByCountry;

function formatNumberTr(value, digits = 0) {{
    if (typeof value !== 'number' || Number.isNaN(value)) return '-';
    return new Intl.NumberFormat('tr-TR', {{
        minimumFractionDigits: digits,
        maximumFractionDigits: digits
    }}).format(value);
}}

function getIndicatorDecimals(indicatorKey) {{
    const ind = externalIndicators[indicatorKey] || {{}};
    if (typeof ind.decimals === 'number') return ind.decimals;
    if (indicatorKey === 'min_wage' || indicatorKey === 'bigmac') return 2;
    return 1;
}}

function formatIndicatorValue(indicatorKey, value) {{
    if (typeof value !== 'number' || Number.isNaN(value)) return '-';
    const decimals = getIndicatorDecimals(indicatorKey);
    const raw = formatNumberTr(value, decimals);
    const unit = ((externalIndicators[indicatorKey] || {{}}).unit || '').trim();
    if (indicatorKey === 'min_wage' || indicatorKey === 'bigmac') {{
        return `$${{raw}}${{indicatorKey === 'min_wage' ? '/saat' : ''}}`;
    }}
    return unit ? `${{raw}} ${{unit}}` : raw;
}}

function escapeHtml(value) {{
    return String(value == null ? '' : value)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}}

function stripSearchMarkup(value) {{
    return String(value == null ? '' : value).replace(/<[^>]*>/g, '').replace(/\s+/g, ' ').trim();
}}

function setAiSearchStatus(text, isError = false) {{
    const el = document.getElementById('aiSearchStatus');
    if (!el) return;
    el.textContent = text || '';
    el.classList.toggle('error', Boolean(isError));
}}

function initAiSearch() {{
    const input = document.getElementById('aiSearchInput');
    if (!input) return;
    input.addEventListener('keydown', function(event) {{
        if (event.key === 'Enter') {{
            event.preventDefault();
            aiSearch();
        }}
    }});
}}

function getAiResultCountry(result) {{
    return String(
        result.country_name ||
        result.country ||
        result.countryName ||
        result.country_tr ||
        ''
    ).trim();
}}

function getAiResultTitle(result) {{
    return String(result.title || result.event_title || result.name || 'Olay').trim();
}}

function openAiSearchResult(result) {{
    const country = getAiResultCountry(result);
    const rawLat = result.lat !== undefined ? result.lat : result.latitude;
    const rawLon = result.lon !== undefined ? result.lon : (result.lng !== undefined ? result.lng : result.longitude);
    const lat = Number(rawLat);
    const lon = Number(rawLon);

    if (country && typeof window.openSidebar === 'function') {{
        window.openSidebar(country);
    }}

    const hasUsableCoords = Number.isFinite(lat) && Number.isFinite(lon) && !(lat === 0 && lon === 0);
    if (window.geoMap && hasUsableCoords) {{
        window.geoMap.flyTo([lat, lon], Math.max(window.geoMap.getZoom(), 5), {{ duration: 0.7 }});
        return;
    }}

    const layers = country && window.markerLayersByCountry ? window.markerLayersByCountry[country] : null;
    const firstLayer = layers && layers.length ? layers[0] : null;
    if (window.geoMap && firstLayer && typeof firstLayer.getLatLng === 'function') {{
        window.geoMap.flyTo(firstLayer.getLatLng(), Math.max(window.geoMap.getZoom(), 5), {{ duration: 0.7 }});
    }}
}}

function renderAiSearchResults(data) {{
    const summaryDiv = document.getElementById('aiSummary');
    const listDiv = document.getElementById('aiResultsList');
    if (!summaryDiv || !listDiv) return;

    const results = Array.isArray(data.results) ? data.results : [];
    summaryDiv.textContent = stripSearchMarkup(data.summary || '');
    listDiv.innerHTML = '';

    if (!results.length) {{
        setAiSearchStatus('Sonuç bulunamadı.', false);
        return;
    }}

    setAiSearchStatus(`${{results.length}} sonuç bulundu.`, false);
    const fragment = document.createDocumentFragment();
    results.forEach(result => {{
        const item = document.createElement('button');
        item.type = 'button';
        item.className = 'ai-result-item';
        item.addEventListener('click', () => openAiSearchResult(result));

        const meta = document.createElement('div');
        meta.className = 'ai-result-meta';

        const catKey = String(result.category || '').trim();
        if (catKey) {{
            const cat = categories[catKey] || {{}};
            const badge = document.createElement('span');
            badge.className = 'ai-result-category';
            badge.style.background = cat.color || '#718096';
            badge.textContent = cat.label || catKey;
            meta.appendChild(badge);
        }}

        const year = result.year ? String(result.year) : '';
        const country = getAiResultCountry(result);
        [year, country].filter(Boolean).forEach(value => {{
            const span = document.createElement('span');
            span.textContent = value;
            meta.appendChild(span);
        }});

        const score = Number(result.score);
        if (Number.isFinite(score) && score > 0) {{
            const span = document.createElement('span');
            span.textContent = `${{Math.round(score * 100)}}%`;
            meta.appendChild(span);
        }}

        const title = document.createElement('div');
        title.className = 'ai-result-title';
        title.textContent = getAiResultTitle(result);

        item.appendChild(meta);
        item.appendChild(title);

        const snippet = stripSearchMarkup(result.snippet || result.description || '');
        if (snippet) {{
            const desc = document.createElement('div');
            desc.className = 'ai-result-snippet';
            desc.textContent = snippet.length > 240 ? snippet.slice(0, 237) + '...' : snippet;
            item.appendChild(desc);
        }}

        fragment.appendChild(item);
    }});
    listDiv.appendChild(fragment);
}}

async function aiSearch() {{
    const input = document.getElementById('aiSearchInput');
    const button = document.getElementById('aiSearchButton');
    const summaryDiv = document.getElementById('aiSummary');
    const listDiv = document.getElementById('aiResultsList');
    const query = input ? input.value.trim() : '';
    if (!query) {{
        setAiSearchStatus('Aramak için bir konu yazın.', true);
        return;
    }}

    if (button) button.disabled = true;
    if (summaryDiv) summaryDiv.textContent = '';
    if (listDiv) listDiv.innerHTML = '';
    setAiSearchStatus('Aranıyor...', false);

    try {{
        const response = await fetch(`/api/search?q=${{encodeURIComponent(query)}}&limit=10`, {{
            headers: {{ 'Accept': 'application/json' }}
        }});
        let data = {{}};
        try {{
            data = await response.json();
        }} catch (_err) {{
            data = {{ error: `HTTP ${{response.status}}` }};
        }}
        if (!response.ok) {{
            throw new Error(data.error || `HTTP ${{response.status}}`);
        }}
        renderAiSearchResults(data);
    }} catch (err) {{
        setAiSearchStatus('Arama hatası: ' + (err && err.message ? err.message : String(err)), true);
    }} finally {{
        if (button) button.disabled = false;
    }}
}}

function formatIndicatorTimestamp(value) {{
    if (!value) return '';
    return String(value).replace('T', ' ').replace('Z', ' UTC');
}}

function getIndicatorSourceLabel(sourceType) {{
    const labels = {{
        worldbank: 'World Bank',
        'open-meteo': 'Open-Meteo',
        'open-meteo-air': 'Open-Meteo Air',
        openaq: 'OpenAQ',
        frankfurter: 'Frankfurter',
        opensanctions: 'OpenSanctions'
    }};
    return labels[sourceType] || sourceType || '';
}}

function getIndicatorDisplayLabel(indicatorKey) {{
    const labels = {{
        sanctions_risk_score: 'Yaptırım / Risk',
        weather_pressure_score: 'İklim Baskısı',
        air_quality_pm25: 'Hava Kalitesi (PM2.5)',
        fx_pressure_score: 'Kur Baskısı (30g USD)',
        min_wage: 'Asgari Ücret (USD/saat)',
        bigmac: 'Big Mac Endeksi (USD)',
        water_internal_total: 'İç Tatlı Su (milyar m3)',
        water_internal_per_capita: 'İç Tatlı Su / Kişi',
        water_stress: 'Su Stresi',
        water_withdrawal_pct_internal: 'Su Çekimi / İç Kaynak',
        water_use_agriculture: 'Su Kullanımı: Tarım',
        water_use_industry: 'Su Kullanımı: Sanayi',
        water_use_domestic: 'Su Kullanımı: Evsel'
    }};
    return labels[indicatorKey] || ((externalIndicators[indicatorKey] || {{}}).label || indicatorKey);
}}

function getIndicatorNarrative(indicatorKey) {{
    const notes = {{
        sanctions_risk_score: {{
            description: 'Ulke bazli yaptirim yogunlugunu ve liste temasini renk skalasina cevirir.',
            detail: 'Koyu tonlar daha yuksek yaptirim/risk birikimini, acik tonlar daha dusuk gorunurlugu gosterir.'
        }},
        weather_pressure_score: {{
            description: 'Baskent veya merkez noktadaki guncel hava kosullarindan uretilen iklim baskisi skorudur.',
            detail: 'Sicaklik, hissedilen sicaklik, ruzgar ve bulutluluk birlikte okunur.'
        }},
        air_quality_pm25: {{
            description: 'PM2.5 yogunlugu ulkelerin merkez noktasinda hava kalitesini karsilastirir.',
            detail: 'Ek satirda PM10, NO2, O3 ve AQI bilgileri varsa birlikte gosterilir.'
        }},
        fx_pressure_score: {{
            description: 'Yerel para biriminin USD karsisinda son 30 gundeki baskisini izler.',
            detail: 'Koyu tonlar daha sert kur hareketi, acik tonlar daha sinirli baski anlamina gelir.'
        }},
        min_wage: {{
            description: 'Saatlik nominal asgari ucret seviyesini ulkeler arasinda karsilastirir.',
            detail: 'Yan kartta yillik nominal karsilik ve veri tarihi yazilir.'
        }},
        bigmac: {{
            description: 'Big Mac fiyatini dolar cinsinden ulkeler arasinda karsilastirir.',
            detail: 'Yerel fiyat ve para birimi bilgisi hover detayinda gorulur.'
        }},
        water_internal_total: {{
            description: 'Ulkenin ic yenilenebilir tatli su hacmini toplu buyukluk olarak gosterir.',
            detail: 'Detay satirinda yil, varsa ana su kaynaklari ve bagimlilik notu yazilir.'
        }},
        water_internal_per_capita: {{
            description: 'Kisi basina dusen ic yenilenebilir tatli su miktarini karsilastirir.',
            detail: 'Dusuk degerler kisitli tatli su tabanina isaret eder.'
        }},
        water_stress: {{
            description: 'Su cekiminin mevcut yenilenebilir kaynaga bindirdigi baskiyi gosterir.',
            detail: 'Koyu tonlar daha yuksek su stresi ve kirilganlik anlamina gelir.'
        }},
        water_withdrawal_pct_internal: {{
            description: 'Toplam su cekiminin ic kaynaklara gore ne kadar yuksek oldugunu olcer.',
            detail: 'Yuksek oran, yenilenebilir ic tabanin daha sert kullanildigini ima eder.'
        }},
        water_use_agriculture: {{
            description: 'Toplam cekilen suyun ne kadarinin tarimda kullanildigini gosterir.',
            detail: 'Talimat baskisi, kuraklik ve sulama bagimliligini okumak icin yararlidir.'
        }},
        water_use_industry: {{
            description: 'Toplam cekilen suyun sanayi kullanimina ayrilan payini gosterir.',
            detail: 'Uretim ve enerji yogun ekonomilerde daha belirgin olabilir.'
        }},
        water_use_domestic: {{
            description: 'Toplam cekilen suyun evsel kullanim payini gosterir.',
            detail: 'Sehirlesme ve altyapi baskisini anlamak icin yardimci bir gostergedir.'
        }}
    }};
    return notes[indicatorKey] || {{
        description: 'Secili gosterge ulkeler arasindaki goreli farki renk skalasi ile gosterir.',
        detail: 'Hover satirinda secili ulke icin ayrintili aciklama verilir.'
    }};
}}

function buildIndicatorMetaText(indicatorKey, stats) {{
    const ind = externalIndicators[indicatorKey] || {{}};
    const source = ind.source || {{}};
    const sourceLabel = getIndicatorSourceLabel(source.type);
    const parts = [];
    const minText = formatIndicatorValue(indicatorKey, stats.min);
    const maxText = formatIndicatorValue(indicatorKey, stats.max);

    parts.push(`Renk araligi: ${{minText}} - ${{maxText}}`);
    parts.push(`Kapsam: ${{formatNumberTr(stats.count, 0)}} ulke`);
    if (sourceLabel) parts.push(`Kaynak: ${{sourceLabel}}`);
    if (source.dataset_updated_at) {{
        parts.push(`Dataset: ${{formatIndicatorTimestamp(source.dataset_updated_at)}}`);
    }}
    if (source.latest_date) {{
        parts.push(`Veri tarihi: ${{formatIndicatorTimestamp(source.latest_date)}}`);
    }}
    if (source.current_date) {{
        const comparisonText = source.comparison_date_resolved
            ? ` / ${{formatIndicatorTimestamp(source.comparison_date_resolved)}}`
            : '';
        parts.push(`Karsilastirma: ${{formatIndicatorTimestamp(source.current_date)}}${{comparisonText}}`);
    }}
    if (source.lastupdated) {{
        parts.push(`Kaynak guncelleme: ${{formatIndicatorTimestamp(source.lastupdated)}}`);
    }}
    if (source.updated_at_utc) {{
        parts.push(`Snapshot: ${{formatIndicatorTimestamp(source.updated_at_utc)}}`);
    }}
    if (source.note) {{
        parts.push(String(source.note));
    }}
    return parts.filter(Boolean).join(' · ');
}}

function getWaterContext(countryName) {{
    const note = waterSourceNotes[countryName];
    if (!note) return '';
    const parts = [];
    if (Array.isArray(note.primary_sources) && note.primary_sources.length) {{
        parts.push(`Baslica kaynaklar: ${{note.primary_sources.join(', ')}}.`);
    }}
    if (note.dependency) {{
        parts.push(`Bagimlilik: ${{note.dependency}}`);
    }}
    if (note.risk) {{
        parts.push(`Risk: ${{note.risk}}`);
    }}
    return parts.join(' ');
}}

function buildIndicatorCompactText(countryName, indicatorKey) {{
    const label = getIndicatorDisplayLabel(indicatorKey);
    const details = getIndicatorDetails(countryName, indicatorKey);
    const value = getIndicatorValue(countryName, indicatorKey);
    if (!details || typeof value !== 'number' || Number.isNaN(value)) {{
        return `${{label}} · ${{countryName}}: veri yok`;
    }}
    const status = details.risk_label || details.pressure_label || details.aqi_label || details.pressure_label || '';
    return status
        ? `${{label}} · ${{countryName}}: ${{formatIndicatorValue(indicatorKey, value)}} (${{status}})`
        : `${{label}} · ${{countryName}}: ${{formatIndicatorValue(indicatorKey, value)}}`;
}}

function buildIndicatorCountryDetail(countryName, indicatorKey) {{
    const label = getIndicatorDisplayLabel(indicatorKey);
    const details = getIndicatorDetails(countryName, indicatorKey);
    const value = getIndicatorValue(countryName, indicatorKey);
    if (!details || typeof value !== 'number' || Number.isNaN(value)) {{
        return `${{countryName}}: ${{label}} icin veri yok.`;
    }}

    if (indicatorKey === 'sanctions_risk_score') {{
        const parts = [`${{countryName}}: ${{formatIndicatorValue(indicatorKey, value)}} (${{details.risk_label || 'Belirsiz'}}).`];
        const density = [];
        if (typeof details.matches_count === 'number') density.push(`${{formatNumberTr(details.matches_count, 0)}} eslesme`);
        if (typeof details.dataset_count === 'number') density.push(`${{formatNumberTr(details.dataset_count, 0)}} liste`);
        if (density.length) parts.push(`Yogunluk: ${{density.join(', ')}}.`);
        if (Array.isArray(details.top_datasets) && details.top_datasets.length) {{
            const datasets = details.top_datasets
                .slice(0, 2)
                .map(row => `${{row.name}} (${{formatNumberTr(row.count || 0, 0)}})`)
                .join(', ');
            parts.push(`En yogun listeler: ${{datasets}}.`);
        }}
        return parts.join(' ');
    }}

    if (indicatorKey === 'weather_pressure_score') {{
        const current = details.current || {{}};
        const parts = [`${{countryName}}: ${{formatIndicatorValue(indicatorKey, value)}} (${{details.pressure_label || 'Belirsiz'}}).`];
        if (details.location_name) parts.push(`Konum: ${{details.location_name}}.`);
        const weatherBits = [];
        if (typeof current.temperature_2m === 'number') weatherBits.push(`sicaklik ${{formatNumberTr(current.temperature_2m, 1)}} C`);
        if (typeof current.apparent_temperature === 'number') weatherBits.push(`hissedilen ${{formatNumberTr(current.apparent_temperature, 1)}} C`);
        if (typeof current.wind_speed_10m === 'number') weatherBits.push(`ruzgar ${{formatNumberTr(current.wind_speed_10m, 1)}} km/s`);
        if (typeof current.cloud_cover === 'number') weatherBits.push(`bulut ${{formatNumberTr(current.cloud_cover, 0)}}%`);
        if (current.weather_label) weatherBits.push(`durum ${{current.weather_label}}`);
        if (weatherBits.length) parts.push(`Kosullar: ${{weatherBits.join(', ')}}.`);
        if (current.time) parts.push(`Olcum: ${{formatIndicatorTimestamp(current.time)}}.`);
        return parts.join(' ');
    }}

    if (indicatorKey === 'air_quality_pm25') {{
        const current = details.current || {{}};
        const parts = [`${{countryName}}: PM2.5 ${{formatIndicatorValue(indicatorKey, value)}} (${{details.aqi_label || 'Belirsiz'}}).`];
        if (details.location_name) parts.push(`Konum: ${{details.location_name}}.`);
        const airBits = [];
        if (typeof current.pm10 === 'number') airBits.push(`PM10 ${{formatNumberTr(current.pm10, 1)}}`);
        if (typeof current.nitrogen_dioxide === 'number') airBits.push(`NO2 ${{formatNumberTr(current.nitrogen_dioxide, 1)}}`);
        if (typeof current.ozone === 'number') airBits.push(`O3 ${{formatNumberTr(current.ozone, 1)}}`);
        if (typeof current.european_aqi === 'number') airBits.push(`AQI ${{formatNumberTr(current.european_aqi, 0)}}`);
        if (airBits.length) parts.push(`Ek olcumler: ${{airBits.join(', ')}}.`);
        if (details.data_source) parts.push(`Saglayici: ${{getIndicatorSourceLabel(details.data_source)}}.`);
        if (current.time) parts.push(`Olcum: ${{formatIndicatorTimestamp(current.time)}}.`);
        return parts.join(' ');
    }}

    if (indicatorKey === 'fx_pressure_score') {{
        const parts = [`${{countryName}}: ${{formatIndicatorValue(indicatorKey, value)}} kur baskisi (${{details.pressure_label || 'Belirsiz'}}).`];
        if (details.currency_code) parts.push(`Para birimi: ${{details.currency_code}}.`);
        const rateBits = [];
        if (typeof details.current_rate_local_per_usd === 'number') {{
            rateBits.push(`1 USD = ${{formatNumberTr(details.current_rate_local_per_usd, 4)}} ${{details.currency_code || ''}}`);
        }}
        if (typeof details.previous_rate_local_per_usd === 'number') {{
            rateBits.push(`30 gun once ${{formatNumberTr(details.previous_rate_local_per_usd, 4)}} ${{details.currency_code || ''}}`);
        }}
        if (rateBits.length) parts.push(`Kur: ${{rateBits.join(', ')}}.`);
        return parts.join(' ');
    }}

    if (indicatorKey === 'min_wage') {{
        const parts = [`${{countryName}}: ${{formatIndicatorValue(indicatorKey, value)}}.`];
        if (typeof details.annual_usd_nominal === 'number') parts.push(`Yillik nominal: $${{formatNumberTr(details.annual_usd_nominal, 0)}}.`);
        if (details.effective_date) parts.push(`Gecerlilik: ${{details.effective_date}}.`);
        return parts.join(' ');
    }}

    if (indicatorKey === 'bigmac') {{
        const parts = [`${{countryName}}: ${{formatIndicatorValue(indicatorKey, value)}}.`];
        if (typeof details.local_price === 'number') {{
            parts.push(`Yerel fiyat: ${{formatNumberTr(details.local_price, 2)}} ${{details.currency_code || ''}}.`);
        }}
        if (details.date) parts.push(`Tarih: ${{details.date}}.`);
        return parts.join(' ');
    }}

    if (indicatorKey.startsWith('water_')) {{
        const parts = [`${{countryName}}: ${{formatIndicatorValue(indicatorKey, value)}}.`];
        if (details.year) parts.push(`Yil: ${{details.year}}.`);
        const context = getWaterContext(countryName);
        if (context) parts.push(context);
        return parts.join(' ');
    }}

    return `${{countryName}}: ${{formatIndicatorValue(indicatorKey, value)}}.`;
}}

function setActiveIndicatorHoverText(text, isEmpty = false) {{
    const el = document.getElementById('activeIndicatorHover');
    if (!el) return;
    el.textContent = text;
    if (isEmpty) {{
        el.classList.add('empty');
    }} else {{
        el.classList.remove('empty');
    }}
}}

function updateActiveIndicatorBanner() {{
    const banner = document.getElementById('activeIndicatorBanner');
    const titleEl = document.getElementById('activeIndicatorTitle');
    const descEl = document.getElementById('activeIndicatorDesc');
    const metaEl = document.getElementById('activeIndicatorMeta');
    if (!banner || !titleEl || !descEl || !metaEl) return;

    const key = window.activeIndicator;
    if (!key) {{
        banner.style.display = 'none';
        setActiveIndicatorHoverText('Bir ulkenin uzerine gelin.', true);
        return;
    }}

    const ind = externalIndicators[key];
    const stats = computeIndicatorStats(key);
    if (!ind || !stats) {{
        banner.style.display = 'none';
        setActiveIndicatorHoverText('Bir ulkenin uzerine gelin.', true);
        return;
    }}

    const narrative = getIndicatorNarrative(key);
    titleEl.textContent = getIndicatorDisplayLabel(key).toLocaleUpperCase('tr-TR');
    descEl.textContent = narrative.description;
    metaEl.textContent = [narrative.detail, buildIndicatorMetaText(key, stats)].filter(Boolean).join(' ');
    banner.style.display = '';

    if (window.activeIndicatorHoverCountry) {{
        setActiveIndicatorHoverText(buildIndicatorCountryDetail(window.activeIndicatorHoverCountry, key), false);
    }} else {{
        setActiveIndicatorHoverText('Bir ulkenin uzerine gelin.', true);
    }}
}}

function getCountryConflicts(countryName) {{
    return (conflictsByCountry[countryName] || []).filter(conflict => (conflict.status || 'active') !== 'historical');
}}

function getConflictIntensityLabel(level) {{
    if (level === 'high') return 'Yuksek';
    if (level === 'medium') return 'Orta';
    if (level === 'low') return 'Dusuk';
    return 'Belirsiz';
}}

function getConflictIntensityColor(level) {{
    if (level === 'high') return '#c0392b';
    if (level === 'medium') return '#d35400';
    if (level === 'low') return '#2980b9';
    return '#7f8c8d';
}}

// Initialize filters
function initFilters() {{
    const decadeContainer = document.getElementById('decadeFilters');
    decades.forEach(decade => {{
        const item = document.createElement('label');
        item.className = 'decade-item';
        item.innerHTML = `
            <input type="checkbox" checked onchange="toggleDecade('${{decade}}')" id="decade-${{decade}}">
            ${{decade}}
        `;
        decadeContainer.appendChild(item);
    }});

    // SVG icons for categories
    const categorySVG = {{
        war: '<svg width="14" height="14" viewBox="0 0 16 16" fill="none"><path d="M8 1L2 14h12L8 1z" fill="currentColor" opacity="0.9"/><path d="M7.5 6v4M7.5 11.5v1" stroke="#1e272e" stroke-width="1.5" stroke-linecap="round"/></svg>',
        genocide: '<svg width="14" height="14" viewBox="0 0 16 16" fill="none"><circle cx="8" cy="8" r="6" stroke="currentColor" stroke-width="1.5"/><path d="M5 6h.01M11 6h.01M6 11c.5-1 3.5-1 4 0" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/></svg>',
        revolution: '<svg width="14" height="14" viewBox="0 0 16 16" fill="none"><path d="M8 2v5M5 7h6M6 12l2-3 2 3" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>',
        terror: '<svg width="14" height="14" viewBox="0 0 16 16" fill="none"><circle cx="8" cy="8" r="3" fill="currentColor" opacity="0.7"/><path d="M8 2v2M8 12v2M2 8h2M12 8h2M4 4l1.5 1.5M10.5 10.5L12 12M12 4l-1.5 1.5M5.5 10.5L4 12" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/></svg>',
        politics: '<svg width="14" height="14" viewBox="0 0 16 16" fill="none"><path d="M3 12V7l5-4 5 4v5a1 1 0 01-1 1H4a1 1 0 01-1-1z" stroke="currentColor" stroke-width="1.3" stroke-linejoin="round"/><path d="M6 13v-3h4v3" stroke="currentColor" stroke-width="1.2"/></svg>',
        diplomacy: '<svg width="14" height="14" viewBox="0 0 16 16" fill="none"><path d="M2 8c2-3 4-3 6 0s4 3 6 0" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/><circle cx="5" cy="8" r="1.5" fill="currentColor" opacity="0.5"/><circle cx="11" cy="8" r="1.5" fill="currentColor" opacity="0.5"/></svg>',
        leader: '<svg width="14" height="14" viewBox="0 0 16 16" fill="none"><path d="M8 2l1.5 3 3.5.5-2.5 2.5.5 3.5L8 10l-3 1.5.5-3.5L3 5.5l3.5-.5L8 2z" fill="currentColor" opacity="0.8"/></svg>',
        culture: '<svg width="14" height="14" viewBox="0 0 16 16" fill="none"><path d="M4 2h8v12l-4-2-4 2V2z" stroke="currentColor" stroke-width="1.3" stroke-linejoin="round"/></svg>',
        cinema: '<svg width="14" height="14" viewBox="0 0 16 16" fill="none"><rect x="2" y="3" width="12" height="10" rx="1" stroke="currentColor" stroke-width="1.2"/><path d="M6 6.5l4 2-4 2v-4z" fill="currentColor" opacity="0.8"/></svg>',
        music: '<svg width="14" height="14" viewBox="0 0 16 16" fill="none"><path d="M6 12V4l7-2v8" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/><circle cx="4" cy="12" r="2" fill="currentColor" opacity="0.7"/><circle cx="11" cy="10" r="2" fill="currentColor" opacity="0.7"/></svg>',
    }};

    const catContainer = document.getElementById('categoryFilters');
    const catEntries = Object.entries(categories)
        .filter(([key, _cat]) => key !== 'time_100')
        .sort((a, b) => {{
            const ta = (a[1] && typeof a[1].tier === 'number') ? a[1].tier : 2;
            const tb = (b[1] && typeof b[1].tier === 'number') ? b[1].tier : 2;
            if (ta !== tb) return ta - tb;
            const la = (a[1] && a[1].label) ? a[1].label : a[0];
            const lb = (b[1] && b[1].label) ? b[1].label : b[0];
            return String(la).localeCompare(String(lb), 'tr');
        }});

    // Group by tier and render with hierarchy
    const tierLabels = {{ 1: 'Kritik Olaylar', 2: 'Önemli Olaylar', 3: 'Kültür & Yaşam' }};
    let currentTier = 0;
    let tierGroup = null;

    catEntries.forEach(([key, cat]) => {{
        if (key === 'time_100') return;
        const tier = (cat && typeof cat.tier === 'number') ? cat.tier : 2;

        // New tier group
        if (tier !== currentTier) {{
            currentTier = tier;
            // Add tier label
            const label = document.createElement('div');
            label.className = 'category-tier-label';
            label.textContent = tierLabels[tier] || `Tier ${{tier}}`;
            catContainer.appendChild(label);

            // Create tier group container
            tierGroup = document.createElement('div');
            tierGroup.className = `category-tier-group${{tier > 1 ? ' has-indent' : ''}}`;
            catContainer.appendChild(tierGroup);
        }}

        const svg = categorySVG[key] || '';
        const item = document.createElement('label');
        item.className = `category-item tier-${{tier}}`;
        item.style.setProperty('--tier-color', cat.color);
        item.innerHTML = `
            <input type="checkbox" checked onchange="toggleCategory('${{key}}')" id="cat-${{key}}">
            <span class="category-color" style="background: ${{cat.color}}; color: ${{cat.color}}; display:flex;align-items:center;justify-content:center;">${{svg || ''}}</span>
            ${{cat.label}}
        `;
        (tierGroup || catContainer).appendChild(item);
    }});

    updateVisibleCount();
    updateIndicatorLegend();
}}

function toggleCountryGroup(groupKey) {{
    if (!countryGroups[groupKey] || countryGroups[groupKey].size === 0) {{
        console.warn('Unknown/empty group:', groupKey);
        return;
    }}

    window.activeCountryGroup = (window.activeCountryGroup === groupKey) ? null : groupKey;

    // Update hidden checkboxes
    const g8Box = document.getElementById('group-g8');
    const natoBox = document.getElementById('group-nato');
    const bricsBox = document.getElementById('group-brics_plus');
    if (g8Box) g8Box.checked = window.activeCountryGroup === 'g8';
    if (natoBox) natoBox.checked = window.activeCountryGroup === 'nato';
    if (bricsBox) bricsBox.checked = window.activeCountryGroup === 'brics_plus';

    // Update group card visual state
    ['nato', 'g8', 'brics_plus'].forEach(gk => {{
        const cardId = gk === 'brics_plus' ? 'group-brics-card' : `group-${{gk}}-card`;
        const card = document.getElementById(cardId);
        if (card) {{
            if (window.activeCountryGroup === gk) {{
                card.classList.add('active');
            }} else {{
                card.classList.remove('active');
            }}
        }}
    }});

    updateVisibleCount();
    updateMarkerVisibility();
    updateExternalOverlays();
}}

// Wrapper for SVG group cards
function toggleCountryGroupCard(groupKey) {{
    toggleCountryGroup(groupKey);
}}

// Update group counts after data loads
function updateGroupCounts() {{
    const natoEl = document.getElementById('natoCount');
    const g8El = document.getElementById('g8Count');
    const bricsEl = document.getElementById('bricsCount');
    if (natoEl && countryGroups.nato) natoEl.textContent = countryGroups.nato.size + ' ülke';
    if (g8El && countryGroups.g8) g8El.textContent = countryGroups.g8.size + ' ülke';
    if (bricsEl && countryGroups.brics_plus) bricsEl.textContent = countryGroups.brics_plus.size + ' ülke';
}}

// Sidebar Tab Navigation
function switchSidebarTab(tabName) {{
    document.querySelectorAll('.sidebar-tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.sidebar-tab-panel').forEach(p => p.classList.remove('active'));

    const tab = document.querySelector(`.sidebar-tab[data-tab="${{tabName}}"]`);
    const panel = document.getElementById(tabName === 'events' ? 'tabEvents' : tabName === 'data' ? 'tabData' : 'tabRelations');
    if (tab) tab.classList.add('active');
    if (panel) panel.classList.add('active');
}}

// Stats countup with pulse animation
function updateVisibleCountAnimated(newCount) {{
    const el = document.getElementById('visibleCount');
    if (!el) return;
    const oldCount = parseInt(el.textContent) || 0;
    if (oldCount === newCount) return;

    const box = el.closest('.stats-box');
    if (box) {{
        box.classList.remove('pulse');
        void box.offsetWidth; // force reflow
        box.classList.add('pulse');
        setTimeout(() => box.classList.remove('pulse'), 700);
    }}

    // Simple countup
    if (Math.abs(newCount - oldCount) < 20) {{
        el.textContent = newCount;
        return;
    }}
    const duration = 300;
    const startTime = performance.now();
    function animate(now) {{
        const elapsed = now - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3);
        el.textContent = Math.round(oldCount + (newCount - oldCount) * eased);
        if (progress < 1) requestAnimationFrame(animate);
    }}
    requestAnimationFrame(animate);
}}

function setIndicatorMode(mode) {{
    window.activeIndicator = mode || '';
    updateExternalOverlays();
}}

function getActiveGroupSet() {{
    if (!window.activeCountryGroup) return null;
    return countryGroups[window.activeCountryGroup] || null;
}}

function formatUsd(value, suffix = '') {{
    if (typeof value !== 'number' || Number.isNaN(value)) return '-';
    return '$' + value.toFixed(2) + suffix;
}}

function getIndicatorDetails(countryName, indicatorKey) {{
    const ind = externalIndicators[indicatorKey];
    if (!ind || !ind.by_country) return null;
    return ind.by_country[countryName] || null;
}}

function getIndicatorValue(countryName, indicatorKey) {{
    const d = getIndicatorDetails(countryName, indicatorKey);
    if (!d) return null;
    if (typeof d.value === 'number' && !Number.isNaN(d.value)) return d.value;
    if (indicatorKey === 'min_wage') return d.hourly_usd_nominal;
    if (indicatorKey === 'bigmac') return d.dollar_price;
    return null;
}}

function computeIndicatorStats(indicatorKey) {{
    const ind = externalIndicators[indicatorKey];
    if (!ind || !ind.by_country) return null;
    const values = [];
    Object.entries(ind.by_country).forEach(([country, d]) => {{
        const v = getIndicatorValue(country, indicatorKey);
        if (typeof v === 'number' && !Number.isNaN(v)) values.push(v);
    }});
    if (values.length === 0) return null;
    const min = Math.min(...values);
    const max = Math.max(...values);
    return {{ min, max, count: values.length }};
}}

function clamp01(x) {{
    if (x < 0) return 0;
    if (x > 1) return 1;
    return x;
}}

function hexToRgb(hex) {{
    const h = (hex || '').replace('#', '');
    if (h.length !== 6) return [0, 0, 0];
    return [
        parseInt(h.slice(0, 2), 16),
        parseInt(h.slice(2, 4), 16),
        parseInt(h.slice(4, 6), 16)
    ];
}}

function rgbToHex(r, g, b) {{
    const toHex = (n) => n.toString(16).padStart(2, '0');
    return '#' + toHex(r) + toHex(g) + toHex(b);
}}

function lerp(a, b, t) {{
    return a + (b - a) * t;
}}

function lerpColor(c1, c2, t) {{
    const [r1, g1, b1] = hexToRgb(c1);
    const [r2, g2, b2] = hexToRgb(c2);
    const tt = clamp01(t);
    return rgbToHex(
        Math.round(lerp(r1, r2, tt)),
        Math.round(lerp(g1, g2, tt)),
        Math.round(lerp(b1, b2, tt))
    );
}}

function getIndicatorGradient(indicatorKey) {{
    if (indicatorKey === 'sanctions_risk_score') return ['#fff4cc', '#7f1d1d'];
    if (indicatorKey === 'weather_pressure_score') return ['#e0f2fe', '#1d4ed8'];
    if (indicatorKey === 'air_quality_pm25') return ['#ecfdf5', '#b91c1c'];
    if (indicatorKey === 'fx_pressure_score') return ['#fff7ed', '#9a3412'];
    if (indicatorKey === 'water_internal_total') return ['#edf8fb', '#005b96'];
    if (indicatorKey === 'water_internal_per_capita') return ['#f1fbff', '#0b7285'];
    if (indicatorKey === 'water_stress') return ['#fff4cc', '#c0392b'];
    if (indicatorKey === 'water_withdrawal_pct_internal') return ['#fdebd0', '#d35400'];
    if (indicatorKey === 'water_use_agriculture') return ['#eef8e6', '#2d6a4f'];
    if (indicatorKey === 'water_use_industry') return ['#edf2f7', '#4a5568'];
    if (indicatorKey === 'water_use_domestic') return ['#eef6ff', '#2563eb'];
    if (indicatorKey === 'bigmac') return ['#fff3e0', '#e65100'];
    // default: min_wage
    return ['#e8f5e9', '#1b5e20'];
}}

function indicatorStyle(feature) {{
    const key = window.activeIndicator;
    if (!key) {{
        return {{ fillOpacity: 0, opacity: 0, weight: 0, color: 'transparent' }};
    }}

    const geoName = (feature.properties && (feature.properties.name || feature.properties.NAME)) || '';
    const canon = reverseNameMap[geoName] || geoName;
    const v = getIndicatorValue(canon, key);
    if (typeof v !== 'number' || Number.isNaN(v)) {{
        return {{ fillOpacity: 0, opacity: 0, weight: 0, color: 'transparent' }};
    }}

    const stats = computeIndicatorStats(key);
    if (!stats) {{
        return {{ fillOpacity: 0, opacity: 0, weight: 0, color: 'transparent' }};
    }}

    const denom = (stats.max - stats.min) || 1;
    const t = (v - stats.min) / denom;
    const [c1, c2] = getIndicatorGradient(key);
    const fill = lerpColor(c1, c2, t);
    return {{
        fillColor: fill,
        fillOpacity: 0.28,
        color: '#111',
        weight: 0.6,
        opacity: 0.35
    }};
}}

function groupStyle(feature) {{
    const groupKey = window.activeCountryGroup;
    if (!groupKey) {{
        return {{ fillOpacity: 0, opacity: 0, weight: 0, color: 'transparent' }};
    }}
    const set = countryGroups[groupKey];
    if (!set) {{
        return {{ fillOpacity: 0, opacity: 0, weight: 0, color: 'transparent' }};
    }}
    const geoName = (feature.properties && (feature.properties.name || feature.properties.NAME)) || '';
    const canon = reverseNameMap[geoName] || geoName;
    if (!set.has(canon)) {{
        return {{ fillOpacity: 0, opacity: 0, weight: 0, color: 'transparent' }};
    }}
    const color = (groupKey === 'nato')
        ? '#3498db'
        : (groupKey === 'brics_plus')
            ? '#5865f2'
            : '#f1c40f';
    return {{
        fillColor: color,
        fillOpacity: 0.12,
        color: color,
        weight: 1.2,
        opacity: 0.65
    }};
}}

function initExternalOverlays() {{
    if (!window.geoMap || !window.countriesGeoJSON) return;
    if (!window.groupOverlayLayer) {{
        window.groupOverlayLayer = L.geoJSON(window.countriesGeoJSON, {{
            interactive: false,
            style: groupStyle
        }}).addTo(window.geoMap);
    }}
    if (!window.indicatorOverlayLayer) {{
        window.indicatorOverlayLayer = L.geoJSON(window.countriesGeoJSON, {{
            interactive: false,
            style: indicatorStyle
        }}).addTo(window.geoMap);
    }}
    updateExternalOverlays();
}}

function updateIndicatorLegend() {{
    const el = document.getElementById('indicatorLegend');
    if (!el) return;

    const key = window.activeIndicator;
    if (!key) {{
        el.style.display = 'none';
        el.innerHTML = '';
        return;
    }}

    const ind = externalIndicators[key];
    const stats = computeIndicatorStats(key);
    if (!ind || !stats) {{
        el.style.display = 'none';
        el.innerHTML = '';
        return;
    }}

    const [c1, c2] = getIndicatorGradient(key);
    const label = getIndicatorDisplayLabel(key);
    const narrative = getIndicatorNarrative(key);
    const metaText = buildIndicatorMetaText(key, stats);

    el.style.display = '';
    el.innerHTML = `
        <div class="indicator-legend-title">${{escapeHtml(String(label).toLocaleUpperCase('tr-TR'))}}</div>
        <div class="indicator-legend-desc">${{escapeHtml(narrative.description)}}</div>
        <div class="legend-bar" style="background: linear-gradient(90deg, ${{c1}} 0%, ${{c2}} 100%);"></div>
        <div class="legend-row">
            <span>${{escapeHtml(formatIndicatorValue(key, stats.min))}}</span>
            <span>${{escapeHtml(formatIndicatorValue(key, stats.max))}}</span>
        </div>
        <div class="indicator-legend-detail">${{escapeHtml(narrative.detail)}}</div>
        <div class="indicator-legend-detail">${{escapeHtml(metaText)}}</div>
    `;
}}

function updateExternalOverlays() {{
    if (window.groupOverlayLayer) window.groupOverlayLayer.setStyle(groupStyle);
    if (window.indicatorOverlayLayer) window.indicatorOverlayLayer.setStyle(indicatorStyle);
    updateIndicatorLegend();
    updateActiveIndicatorBanner();
}}

function updateIndicatorHoverInfo(countryName) {{
    const el = document.getElementById('indicatorHoverInfo');
    if (!el) return;
    window.activeIndicatorHoverCountry = countryName || '';
    const key = window.activeIndicator;
    if (!key) {{
        el.textContent = '';
        updateActiveIndicatorBanner();
        return;
    }}
    el.textContent = buildIndicatorCompactText(countryName, key);
    updateActiveIndicatorBanner();
}}

function clearIndicatorHoverInfo() {{
    const el = document.getElementById('indicatorHoverInfo');
    if (el) el.textContent = '';
    window.activeIndicatorHoverCountry = '';
    setActiveIndicatorHoverText('Bir ulkenin uzerine gelin.', true);
}}

function toggleSpecial(type) {{
    if (type === 'time_100') {{
        showTime100 = !showTime100;
    }}
    updateVisibleCount();
    updateMarkerVisibility();
}}

function toggleConflictArrows() {{
    window.showConflictArrows = !window.showConflictArrows;
    if (window.showConflictArrows) {{
        if (window._lastArrowConflictId) {{
            showConflictOnMap(window._lastArrowConflictId, window._lastArrowCountry || '');
        }} else if (window._lastArrowCountry && window._lastArrowRivalries) {{
            drawRivalryArrows(window._lastArrowCountry, window._lastArrowRivalries);
        }} else {{
            if (window.drawGlobalActiveArrows) window.drawGlobalActiveArrows();
        }}
    }} else {{
        // Clear arrows immediately
        if (window.hoi4Layer) window.hoi4Layer.setArrows([]);
    }}
}}

function toggleDecade(decade) {{
    if (selectedDecades.has(decade)) {{
        selectedDecades.delete(decade);
    }} else {{
        selectedDecades.add(decade);
    }}
    updateFilterBadges();
    updateVisibleCount();
    updateMarkerVisibility();
}}

function toggleCategory(category) {{
    if (selectedCategories.has(category)) {{
        selectedCategories.delete(category);
    }} else {{
        selectedCategories.add(category);
    }}
    updateFilterBadges();
    updateVisibleCount();
    updateMarkerVisibility();
}}

function toggleAcc(id) {{
    const el = document.getElementById(id);
    if (el) el.classList.toggle('open');
}}

function updateFilterBadges() {{
    const db = document.getElementById('decadeBadge');
    if (db) db.textContent = selectedDecades.size + '/' + decades.length;
    const cb = document.getElementById('catBadge');
    if (cb) {{
        const total = Object.keys(categories).filter(c => c !== 'time_100').length;
        cb.textContent = selectedCategories.size + '/' + total;
    }}
}}

function selectAllDecades() {{
    selectedDecades = new Set(decades);
    decades.forEach(d => document.getElementById('decade-' + d).checked = true);
    updateFilterBadges();
    updateVisibleCount();
    updateMarkerVisibility();
}}

function selectNoDecades() {{
    selectedDecades.clear();
    decades.forEach(d => document.getElementById('decade-' + d).checked = false);
    updateFilterBadges();
    updateVisibleCount();
    updateMarkerVisibility();
}}

function selectAllCategories() {{
    const standardCats = Object.keys(categories).filter(c => c !== 'time_100');
    selectedCategories = new Set(standardCats);
    standardCats.forEach(c => {{
        const el = document.getElementById('cat-' + c);
        if (el) el.checked = true;
    }});
    updateFilterBadges();
    updateVisibleCount();
    updateMarkerVisibility();
}}

function selectNoCategories() {{
    selectedCategories.clear();
    Object.keys(categories).forEach(c => {{
        const el = document.getElementById('cat-' + c);
        if (el) el.checked = false;
    }});
    updateFilterBadges();
    updateVisibleCount();
    updateMarkerVisibility();
}}

function isEventVisibleByFilters(e) {{
    if (!selectedDecades.has(e.decade)) return false;
    if (e.category === 'time_100') return showTime100;
    return selectedCategories.has(e.category);
}}

function updateVisibleCount() {{
    const groupSet = getActiveGroupSet();
    const count = allEvents.filter(e => {{
        if (groupSet && !groupSet.has(e.country_name)) return false;
        return isEventVisibleByFilters(e);
    }}).length;
    updateVisibleCountAnimated(count);
}}

// Track markers by country for filtering
const markersByCountry = {{}};

function updateMarkerVisibility() {{
    // Get filtered events by country
    const visibleCountries = new Set();
    
    allEvents.forEach(e => {{
        if (isEventVisibleByFilters(e)) {{
            visibleCountries.add(e.country_name);
        }}
    }});
    
    // Update marker visibility
    Object.entries(markersByCountry).forEach(([country, marker]) => {{
        if (visibleCountries.has(country)) {{
            marker.setOpacity(1);
            marker._icon.style.display = '';
        }} else {{
            marker.setOpacity(0);
            marker._icon.style.display = 'none';
        }}
    }});
}}

function getFilteredCountryEvents(countryName) {{
    const groupSet = getActiveGroupSet();
    if (groupSet && !groupSet.has(countryName)) return [];
    return allEvents.filter(e => {{
        const matchesCountry = e.country_name === countryName;
        return matchesCountry && isEventVisibleByFilters(e);
    }}).sort((a, b) => b.year - a.year);
}}

// Sidebar functions
// --- HELPER FUNCTIONS ---

function findCountryFeature(countryName) {{
    if (!window.geoMap) return null;
    let found = null;
    
    // 1. Try L.geoJSON layers if we have them accessibly
    // We didn't store them globally easily, but we have countriesGeoJSON data
    if (window.countriesGeoJSON) {{
        window.countriesGeoJSON.features.forEach(f => {{
            if (f.properties.NAME === countryName || f.properties.NAME_LONG === countryName || 
                (window.countryCodeMap && window.countryCodeMap[f.properties.NAME] === countryName)) {{
                found = f;
            }}
        }});
    }}
    return found;
}}

// HOI4 Flag Masking
// HOI4 Flag Masking - Singleton Pattern
function initFlagOverlaySingleton() {{
    if (!window.geoMap) return;
    
    // Check if already exists
    if (window.flagOverlayLayer) return;

    // Create persistent SVG layer
    const svgNS = "http://www.w3.org/2000/svg";
    const overlayPane = window.geoMap.getPanes().overlayPane;
    
    const svg = document.createElementNS(svgNS, "svg");
    svg.setAttribute('class', 'country-flag-overlay leaflet-zoom-hide');
    svg.style.position = 'absolute';
    svg.style.pointerEvents = 'none';
    svg.style.zIndex = 400; 
    svg.style.opacity = 0; // Hidden by default
    svg.style.transition = 'opacity 0.2s ease';
    
    // Defs for ClipPath
    const defs = document.createElementNS(svgNS, "defs");
    const clipPath = document.createElementNS(svgNS, "clipPath");
    const uniqueId = 'flag-clip-path-singleton';
    clipPath.setAttribute("id", uniqueId);
    
    const path = document.createElementNS(svgNS, "path");
    clipPath.appendChild(path);
    defs.appendChild(clipPath);
    svg.appendChild(defs);
    
    // Image
    const img = document.createElementNS(svgNS, "image");
    img.setAttribute("preserveAspectRatio", "none");
    img.setAttribute("style", "clip-path: url(#" + uniqueId + ");");
    svg.appendChild(img);
    
    overlayPane.appendChild(svg);
    
    // Store globals
    window.flagOverlayLayer = svg;
    window.flagOverlayPath = path;
    window.flagOverlayImage = img;
    window.currentFlagCountry = null;

    // Map Events for Repositioning
    function updateOverlayPosition() {{
        if (!window.flagOverlayLayer || !window.currentFlagCountry) return;
        
        const feature = findCountryFeature(window.currentFlagCountry);
        if (!feature) return;

        const bounds = L.geoJSON(feature).getBounds();
        const map = window.geoMap;

        const p1 = map.latLngToLayerPoint(bounds.getNorthWest());
        const p2 = map.latLngToLayerPoint(bounds.getSouthEast());
        
        const margin = 50;
        const minX = Math.min(p1.x, p2.x) - margin;
        const minY = Math.min(p1.y, p2.y) - margin;
        const w = Math.abs(p1.x - p2.x) + margin*2;
        const h = Math.abs(p1.y - p2.y) + margin*2;
        
        svg.style.left = minX + 'px';
        svg.style.top = minY + 'px';
        svg.style.width = w + 'px';
        svg.style.height = h + 'px';
        svg.setAttribute('viewBox', `0 0 ${{w}} ${{h}}`);
        
        // Project Points
        function project(latlng) {{
            const p = map.latLngToLayerPoint(L.latLng(latlng[1], latlng[0]));
            return [p.x - minX, p.y - minY];
        }}
        
        let pathData = "";
        const geom = feature.geometry;
        const coords = geom.coordinates;
        
        function ringToPath(ring) {{
             return "M" + ring.map(c => project(c).join(",")).join("L") + "Z";
        }}
        
        if (geom.type === 'Polygon') {{
            pathData = coords.map(ringToPath).join(" ");
        }} else if (geom.type === 'MultiPolygon') {{
            pathData = coords.map(poly => poly.map(ringToPath).join(" ")).join(" ");
        }}
        
        path.setAttribute("d", pathData);
        img.setAttribute("x", 0);
        img.setAttribute("y", 0);
        img.setAttribute("width", w);
        img.setAttribute("height", h);
    }}

    window.geoMap.on('moveend zoomend', updateOverlayPosition);
    // Expose update function
    window.updateFlagOverlayPosition = updateOverlayPosition;
}}

function highlightCountryWithFlag(countryName) {{
    if (!window.geoMap) return;
    
    // Ensure Singleton Exists
    if (!window.flagOverlayLayer) {{
        initFlagOverlaySingleton();
    }}
    
    // If same country, just show
    if (window.currentFlagCountry === countryName) {{
        window.flagOverlayLayer.style.opacity = 0.25;
        return;
    }}

    // 1. Get Feature
    const feature = findCountryFeature(countryName);
    if (!feature) {{
        clearCountryHighlight(); 
        return;
    }}
    
    // 2. Determine Flag URL
    let flagCode = null;
    let flagUrl = null;

    // Group override: show NATO flag when NATO group is active and the country is a NATO member.
    const NATO_FLAG_URL = 'https://upload.wikimedia.org/wikipedia/commons/thumb/5/5d/Flag_of_NATO.svg/640px-Flag_of_NATO.svg.png';
    if (window.activeCountryGroup === 'nato' && countryGroups && countryGroups.nato && countryGroups.nato.has(countryName)) {{
        flagUrl = NATO_FLAG_URL;
    }}

    // Special Case: Manual Overrides / Special Territories
    if (!flagUrl && specialFlagUrls[countryName]) {{
        flagUrl = specialFlagUrls[countryName];
    }} 
    // Strategy A: Check countryCodeMap (name -> iso) which is the source of truth for this project
    else if (!flagUrl && window.countryCodeMap && window.countryCodeMap[countryName]) {{
        flagCode = window.countryCodeMap[countryName];
    }}
    // Strategy B: Check Meta (if available) - converting 3-char code if needed
    else if (!flagUrl && countryMeta[countryName] && countryMeta[countryName].code) {{
        const c = countryMeta[countryName].code;
        if (c.length === 2) flagCode = c.toLowerCase();
        else if (c.length === 3) {{
             const map3to2 = {{
                "TUR": "tr", "GRC": "gr", "USA": "us", "RUS": "ru", "UKR": "ua", 
                "DEU": "de", "FRA": "fr", "GBR": "gb", "CHN": "cn", "IRN": "ir",
                "IRQ": "iq", "SYR": "sy", "AZE": "az", "ARM": "am", "ISR": "il",
                "CYP": "cy", "EGY": "eg", "ITA": "it"
            }};
            flagCode = map3to2[c] || c.substring(0,2).toLowerCase();
        }}
    }}
    // Strategy C: Check Feature Properties directly (often has ISO codes)
    else if (!flagUrl && feature.properties && feature.properties['ISO3166-1-Alpha-2']) {{
        const iso = feature.properties['ISO3166-1-Alpha-2'];
        if (iso && iso !== '-99') flagCode = iso.toLowerCase();
    }}

    // Construct URL if code found
    if (flagCode && !flagUrl) {{
        flagUrl = `https://flagcdn.com/w640/${{flagCode}}.png`;
    }}

    if (!flagUrl) {{
        window.flagOverlayLayer.style.opacity = 0;
        window.currentFlagCountry = null;
        return;
    }}

    // 3. Update Singleton
    window.currentFlagCountry = countryName;
    window.flagOverlayImage.setAttribute("href", flagUrl);
    
    // Update Position & Shape
    window.updateFlagOverlayPosition();
    
    // Show
    window.flagOverlayLayer.style.opacity = 0.25;
}}


// Sidebar functions

function buildWaterHtml(countryName) {{
    const total = getIndicatorDetails(countryName, 'water_internal_total');
    const perCapita = getIndicatorDetails(countryName, 'water_internal_per_capita');
    const stress = getIndicatorDetails(countryName, 'water_stress');
    const withdrawal = getIndicatorDetails(countryName, 'water_withdrawal_pct_internal');
    const useAgri = getIndicatorDetails(countryName, 'water_use_agriculture');
    const useIndustry = getIndicatorDetails(countryName, 'water_use_industry');
    const useDomestic = getIndicatorDetails(countryName, 'water_use_domestic');
    const note = waterSourceNotes[countryName] || null;

    if (!total && !perCapita && !stress && !withdrawal && !useAgri && !useIndustry && !useDomestic && !note) {{
        return '';
    }}

    const usageBits = [];
    if (useAgri && typeof useAgri.value === 'number') usageBits.push(`Tarim %${{formatNumberTr(useAgri.value, 1)}}`);
    if (useIndustry && typeof useIndustry.value === 'number') usageBits.push(`Sanayi %${{formatNumberTr(useIndustry.value, 1)}}`);
    if (useDomestic && typeof useDomestic.value === 'number') usageBits.push(`Evsel %${{formatNumberTr(useDomestic.value, 1)}}`);

    const sourceList = (note && Array.isArray(note.primary_sources) && note.primary_sources.length > 0)
        ? `<ul style="margin:6px 0 0 18px; padding:0;">${{note.primary_sources.map(item => `<li>${{item}}</li>`).join('')}}</ul>`
        : '<div style="color:#7f8c8d; font-style:italic;">Detayli kaynak notu henuz eklenmedi.</div>';

    return `
        <details class="country-meta-card" open>
            <summary>
                <span><svg width="14" height="14" viewBox="0 0 16 16" fill="none" style="vertical-align:-2px;margin-right:6px;"><path d="M8 2C5 6 2 8 2 11a6 6 0 1012 0c0-3-3-5-6-9z" fill="#3498db" opacity="0.7"/></svg>Su Kaynaklari</span>
            </summary>
            <div class="country-meta-content">
                <div class="meta-row">
                    <span class="meta-label">Ic Su Stoku</span>
                    <div>${{total ? `${{formatNumberTr(total.value, 1)}} milyar m3 <div style="font-size:11px;color:#7f8c8d;">${{total.year || '-'}} verisi</div>` : '-'}}</div>
                </div>
                <div class="meta-row">
                    <span class="meta-label">Kisi Basi</span>
                    <div>${{perCapita ? `${{formatNumberTr(perCapita.value, 0)}} m3 <div style="font-size:11px;color:#7f8c8d;">${{perCapita.year || '-'}} verisi</div>` : '-'}}</div>
                </div>
                <div class="meta-row">
                    <span class="meta-label">Su Stresi</span>
                    <div>${{stress ? `${{formatNumberTr(stress.value, 1)}}%` : '-'}}</div>
                </div>
                <div class="meta-row">
                    <span class="meta-label">Cekim / Ic Kaynak</span>
                    <div>${{withdrawal ? `${{formatNumberTr(withdrawal.value, 1)}}%` : '-'}}</div>
                </div>
                <div class="meta-row" style="align-items:flex-start;">
                    <span class="meta-label">Kullanim</span>
                    <div>${{usageBits.length > 0 ? usageBits.join(' · ') : '-'}}</div>
                </div>
                <div class="meta-row" style="align-items:flex-start;">
                    <span class="meta-label">Baslica Kaynaklar</span>
                    <div>${{sourceList}}</div>
                </div>
                ${{
                    note && note.dependency
                        ? `<div class="meta-row" style="align-items:flex-start;"><span class="meta-label">Bagimlilik</span><div>${{note.dependency}}</div></div>`
                        : ''
                }}
                ${{
                    note && note.risk
                        ? `<div class="meta-row" style="align-items:flex-start;"><span class="meta-label">Risk</span><div>${{note.risk}}</div></div>`
                        : ''
                }}
                <div style="font-size:10px;color:#7f8c8d;margin-top:6px;">
                    Dunya Bankasi su verileri ve yerel notlar birlikte gosterilir.
                </div>
            </div>
        </details>
    `;
}}

function buildCurrentConflictHtml(countryName) {{
    const conflicts = getCountryConflicts(countryName);
    if (!conflicts || conflicts.length === 0) return '';

    const updated = currentConflictData && currentConflictData.updated_at_utc
        ? `<div style="font-size:10px;color:#7f8c8d;margin-top:6px;">Snapshot: ${{currentConflictData.updated_at_utc}}</div>`
        : '';

    return `
        <details class="country-meta-card" open>
            <summary>
                <span><svg width="14" height="14" viewBox="0 0 16 16" fill="none" style="vertical-align:-2px;margin-right:6px;"><path d="M8 1L2 14h12L8 1z" fill="#e74c3c" opacity="0.8"/><path d="M7.5 6v4M7.5 11.5v1" stroke="#fff" stroke-width="1.5" stroke-linecap="round"/></svg>Guncel Catismalar</span>
            </summary>
            <div class="country-meta-content">
                ${{
                    conflicts.map(conflict => {{
                        const color = getConflictIntensityColor(conflict.intensity);
                        const firstSource = Array.isArray(conflict.sources) && conflict.sources.length > 0 ? conflict.sources[0] : null;
                        const tagText = Array.isArray(conflict.tags) && conflict.tags.length > 0
                            ? `<div style="font-size:11px;color:#95a5a6;margin-top:3px;">${{conflict.tags.join(' · ')}}</div>`
                            : '';
                        const sourceHtml = firstSource && firstSource.url
                            ? `<a href="${{firstSource.url}}" target="_blank" style="color:#8ecae6;text-decoration:none;font-size:11px;">${{firstSource.label}} ↗</a>`
                            : '';
                        return `
                            <div style="border:1px solid rgba(255,255,255,0.08); border-radius:10px; padding:10px; margin-bottom:10px; background:rgba(255,255,255,0.02);">
                                <div style="display:flex; align-items:center; justify-content:space-between; gap:8px;">
                                    <div style="font-weight:700; color:#ecf0f1;">${{conflict.label}}</div>
                                    <span style="background:${{color}}; color:white; border-radius:999px; padding:2px 8px; font-size:11px;">${{getConflictIntensityLabel(conflict.intensity)}}</span>
                                </div>
                                <div style="font-size:12px; color:#bdc3c7; margin-top:5px;">${{conflict.summary || '-'}}</div>
                                ${{tagText}}
                                <div style="display:flex; align-items:center; justify-content:space-between; gap:8px; margin-top:8px;">
                                    <div style="font-size:11px; color:#7f8c8d;">${{conflict.started_at || '-'}} → ${{conflict.updated_at || '-'}}</div>
                                    <button onclick="showConflictOnMap('${{conflict.id}}', '${{countryName}}')" style="background:#e74c3c; border:none; color:white; border-radius:999px; padding:6px 10px; font-size:11px; cursor:pointer;">Haritada Goster</button>
                                </div>
                                ${{sourceHtml}}
                            </div>
                        `;
                    }}).join('')
                }}
                ${{updated}}
            </div>
        </details>
    `;
}}

function formatSignedNumber(value, digits = 1, suffix = '') {{
    if (typeof value !== 'number' || Number.isNaN(value)) return '-';
    const sign = value > 0 ? '+' : '';
    return `${{sign}}${{formatNumberTr(value, digits)}}${{suffix}}`;
}}

function buildSanctionsHtml(countryName) {{
    const row = strategicCountries.sanctions[countryName] || null;
    const snapshot = strategicSnapshotData && strategicSnapshotData.sanctions ? strategicSnapshotData.sanctions : {{}};
    const datasets = row && Array.isArray(row.top_datasets) && row.top_datasets.length > 0
        ? `<ul style="margin:6px 0 0 18px; padding:0;">${{row.top_datasets.map(item => `<li>${{item.name}} <span style="color:#7f8c8d;">(${{item.count}})</span></li>`).join('')}}</ul>`
        : '<div style="color:#7f8c8d;font-style:italic;">Veri yok</div>';
    const samples = row && Array.isArray(row.sample_targets) && row.sample_targets.length > 0
        ? `<div style="font-size:11px;color:#bdc3c7;">${{row.sample_targets.join(' · ')}}</div>`
        : '<div style="color:#7f8c8d;font-style:italic;">Ornek hedef yok</div>';
    const updated = snapshot.updated_at_utc
        ? `<div style="font-size:10px;color:#7f8c8d;margin-top:6px;">Snapshot: ${{snapshot.updated_at_utc}}</div>`
        : '';

    return `
        <details class="country-meta-card" open>
            <summary>
                <span><svg width="14" height="14" viewBox="0 0 16 16" fill="none" style="vertical-align:-2px;margin-right:6px;"><circle cx="8" cy="8" r="6" stroke="#f39c12" stroke-width="1.5" fill="none"/><path d="M8 5v4M8 11v1" stroke="#f39c12" stroke-width="1.5" stroke-linecap="round"/></svg>Yaptirim / Risk</span>
            </summary>
            <div class="country-meta-content">
                <div class="meta-row">
                    <span class="meta-label">Risk Skoru</span>
                    <div>${{row ? `${{row.risk_score || 0}}/100 <span style="font-size:11px;color:#7f8c8d;">${{row.risk_label || '-'}}</span>` : 'Veri yok'}}</div>
                </div>
                <div class="meta-row">
                    <span class="meta-label">Ilgili Kayit</span>
                    <div>${{row ? formatNumberTr(row.matches_count || 0, 0) : '-'}}</div>
                </div>
                <div class="meta-row" style="align-items:flex-start;">
                    <span class="meta-label">Baslica Listeler</span>
                    <div>${{datasets}}</div>
                </div>
                <div class="meta-row" style="align-items:flex-start;">
                    <span class="meta-label">Ornekler</span>
                    <div>${{samples}}</div>
                </div>
                ${{
                    snapshot.source_note
                        ? `<div style="font-size:10px;color:#7f8c8d;margin-top:6px;">${{snapshot.source_note}}</div>`
                        : ''
                }}
                ${{updated}}
            </div>
        </details>
    `;
}}

function buildWeatherRiskHtml(countryName) {{
    const row = strategicCountries.weather[countryName] || null;
    const snapshot = strategicSnapshotData && strategicSnapshotData.weather ? strategicSnapshotData.weather : {{}};
    const current = row && row.current ? row.current : null;
    const updated = snapshot.updated_at_utc
        ? `<div style="font-size:10px;color:#7f8c8d;margin-top:6px;">Snapshot: ${{snapshot.updated_at_utc}}</div>`
        : '';

    return `
        <details class="country-meta-card" open>
            <summary>
                <span><svg width="14" height="14" viewBox="0 0 16 16" fill="none" style="vertical-align:-2px;margin-right:6px;"><circle cx="8" cy="6" r="4" fill="#e67e22" opacity="0.6"/><path d="M3 12h10" stroke="#e67e22" stroke-width="1.2" stroke-linecap="round"/><path d="M5 14h6" stroke="#e67e22" stroke-width="1" stroke-linecap="round" opacity="0.5"/></svg>Iklim Baskisi</span>
            </summary>
            <div class="country-meta-content">
                <div class="meta-row">
                    <span class="meta-label">Durum</span>
                    <div>${{current ? `${{current.weather_label || '-'}} <span style="font-size:11px;color:#7f8c8d;">${{current.time || '-'}}</span>` : 'Veri yok'}}</div>
                </div>
                <div class="meta-row">
                    <span class="meta-label">Skor</span>
                    <div>${{row ? `${{row.pressure_score || 0}}/100 <span style="font-size:11px;color:#7f8c8d;">${{row.pressure_label || '-'}}</span>` : '-'}}</div>
                </div>
                <div class="meta-row">
                    <span class="meta-label">Sicaklik</span>
                    <div>${{current && typeof current.temperature_2m === 'number' ? `${{formatNumberTr(current.temperature_2m, 1)}} °C` : '-'}}</div>
                </div>
                <div class="meta-row">
                    <span class="meta-label">Hissedilen</span>
                    <div>${{current && typeof current.apparent_temperature === 'number' ? `${{formatNumberTr(current.apparent_temperature, 1)}} °C` : '-'}}</div>
                </div>
                <div class="meta-row">
                    <span class="meta-label">Ruzgar</span>
                    <div>${{current && typeof current.wind_speed_10m === 'number' ? `${{formatNumberTr(current.wind_speed_10m, 1)}} km/sa` : '-'}}</div>
                </div>
                <div class="meta-row">
                    <span class="meta-label">Yagis</span>
                    <div>${{current && typeof current.precipitation === 'number' ? `${{formatNumberTr(current.precipitation, 1)}} mm` : '-'}}</div>
                </div>
                <div class="meta-row">
                    <span class="meta-label">Nokta</span>
                    <div>${{row ? `${{row.location_name || countryName}} <span style="font-size:11px;color:#7f8c8d;">(${{row.coord_source || '-'}})</span>` : '-'}}</div>
                </div>
                ${{updated}}
            </div>
        </details>
    `;
}}

function buildAirQualityHtml(countryName) {{
    const row = strategicCountries.air_quality[countryName] || null;
    const snapshot = strategicSnapshotData && strategicSnapshotData.air_quality ? strategicSnapshotData.air_quality : {{}};
    const current = row && row.current ? row.current : null;
    const updated = snapshot.updated_at_utc
        ? `<div style="font-size:10px;color:#7f8c8d;margin-top:6px;">Snapshot: ${{snapshot.updated_at_utc}}</div>`
        : '';

    return `
        <details class="country-meta-card" open>
            <summary>
                <span><svg width="14" height="14" viewBox="0 0 16 16" fill="none" style="vertical-align:-2px;margin-right:6px;"><path d="M2 8h4a2 2 0 100-4H2M4 12h5a2 2 0 100-4H4" stroke="#27ae60" stroke-width="1.3" stroke-linecap="round"/></svg>Hava Kalitesi</span>
            </summary>
            <div class="country-meta-content">
                <div class="meta-row">
                    <span class="meta-label">EAQI</span>
                    <div>${{current && typeof current.european_aqi === 'number' ? `${{formatNumberTr(current.european_aqi, 0)}} <span style="font-size:11px;color:#7f8c8d;">${{row.aqi_label || '-'}}</span>` : 'Veri yok'}}</div>
                </div>
                <div class="meta-row">
                    <span class="meta-label">PM2.5</span>
                    <div>${{current && typeof current.pm2_5 === 'number' ? `${{formatNumberTr(current.pm2_5, 1)}} µg/m³` : '-'}}</div>
                </div>
                <div class="meta-row">
                    <span class="meta-label">PM10</span>
                    <div>${{current && typeof current.pm10 === 'number' ? `${{formatNumberTr(current.pm10, 1)}} µg/m³` : '-'}}</div>
                </div>
                <div class="meta-row">
                    <span class="meta-label">NO2</span>
                    <div>${{current && typeof current.nitrogen_dioxide === 'number' ? `${{formatNumberTr(current.nitrogen_dioxide, 1)}} µg/m³` : '-'}}</div>
                </div>
                <div class="meta-row">
                    <span class="meta-label">Ozon</span>
                    <div>${{current && typeof current.ozone === 'number' ? `${{formatNumberTr(current.ozone, 1)}} µg/m³` : '-'}}</div>
                </div>
                <div class="meta-row">
                    <span class="meta-label">Kaynak</span>
                    <div>${{row ? `${{row.data_source || snapshot.provider || '-'}} <span style="font-size:11px;color:#7f8c8d;">${{current && current.time ? current.time : ''}}</span>` : '-'}}</div>
                </div>
                ${{updated}}
            </div>
        </details>
    `;
}}

function buildFxPressureHtml(countryName) {{
    const row = strategicCountries.fx[countryName] || null;
    const snapshot = strategicSnapshotData && strategicSnapshotData.fx ? strategicSnapshotData.fx : {{}};
    const updated = snapshot.updated_at_utc
        ? `<div style="font-size:10px;color:#7f8c8d;margin-top:6px;">Snapshot: ${{snapshot.updated_at_utc}}</div>`
        : '';
    const sourceDates = snapshot.source && snapshot.source.current_date
        ? `<div style="font-size:10px;color:#7f8c8d;margin-top:4px;">${{snapshot.source.current_date}} vs ${{snapshot.source.comparison_date_resolved || '-'}}</div>`
        : '';
    const changeText = row
        ? `${{formatSignedNumber(row.change_pct_30d, 1, '%')}} <span style="font-size:11px;color:#7f8c8d;">${{row.pressure_label || '-'}}</span>`
        : 'Veri yok';

    return `
        <details class="country-meta-card" open>
            <summary>
                <span><svg width="14" height="14" viewBox="0 0 16 16" fill="none" style="vertical-align:-2px;margin-right:6px;"><path d="M2 12l3-4 3 2 4-6 2 3" stroke="#9b59b6" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>Kur Baskisi</span>
            </summary>
            <div class="country-meta-content">
                <div class="meta-row">
                    <span class="meta-label">30 Gunluk Degisim</span>
                    <div>${{changeText}}${{sourceDates}}</div>
                </div>
                <div class="meta-row">
                    <span class="meta-label">1 USD</span>
                    <div>${{row && typeof row.current_rate_local_per_usd === 'number' ? `${{formatNumberTr(row.current_rate_local_per_usd, 3)}} ${{row.currency_code || ''}}` : '-'}}</div>
                </div>
                <div class="meta-row">
                    <span class="meta-label">30 Gun Once</span>
                    <div>${{row && typeof row.previous_rate_local_per_usd === 'number' ? `${{formatNumberTr(row.previous_rate_local_per_usd, 3)}} ${{row.currency_code || ''}}` : '-'}}</div>
                </div>
                <div class="meta-row">
                    <span class="meta-label">Yerel Para</span>
                    <div>${{row ? `${{row.currency_name || '-'}} <span style="font-size:11px;color:#7f8c8d;">(${{row.currency_code || ''}})</span>` : '-'}}</div>
                </div>
                ${{
                    snapshot.source_note
                        ? `<div style="font-size:10px;color:#7f8c8d;margin-top:6px;">${{snapshot.source_note}}</div>`
                        : ''
                }}
                ${{updated}}
            </div>
        </details>
    `;
}}

function buildEconomyHtml(countryName) {{
    const badges = [];
    if (countryGroups.g8 && countryGroups.g8.has(countryName)) {{
        badges.push('<span class="group-badge g8">G8</span>');
    }}
    if (countryGroups.nato && countryGroups.nato.has(countryName)) {{
        badges.push('<span class="group-badge nato">NATO</span>');
    }}
    if (countryGroups.brics_plus && countryGroups.brics_plus.has(countryName)) {{
        badges.push('<span class="group-badge brics">BRICS+</span>');
    }}

    const minw = getIndicatorDetails(countryName, 'min_wage');
    const bigmac = getIndicatorDetails(countryName, 'bigmac');

    const minwHourly = (minw && typeof minw.hourly_usd_nominal === 'number')
        ? formatUsd(minw.hourly_usd_nominal, '/saat')
        : '-';
    const minwMonthly = (minw && typeof minw.monthly_usd_note === 'number')
        ? formatUsd(minw.monthly_usd_note, '/ay')
        : '';
    const minwText = minwMonthly
        ? `${{minwMonthly}} <span style="font-size:11px;color:#7f8c8d;">(${{minwHourly}})</span>`
        : minwHourly;
    const minwDate = (minw && minw.effective_date)
        ? `<div style="font-size:11px;color:#7f8c8d;">${{minw.effective_date}}</div>`
        : '';

    const bigmacText = (bigmac && typeof bigmac.dollar_price === 'number')
        ? formatUsd(bigmac.dollar_price)
        : '-';
    const bigmacExtra = (bigmac && typeof bigmac.local_price === 'number' && bigmac.currency_code)
        ? `<div style="font-size:11px;color:#7f8c8d;">${{bigmac.local_price}} ${{bigmac.currency_code}}</div>`
        : '';
    const bigmacDate = (bigmac && bigmac.date)
        ? `<div style="font-size:11px;color:#7f8c8d;">${{bigmac.date}}</div>`
        : '';

    const fetched = (externalData && externalData.fetched_at_utc)
        ? `<div style="font-size:10px;color:#7f8c8d;margin-top:6px;">Veri çekildi: ${{externalData.fetched_at_utc}}</div>`
        : '';

    return `
        <details class="country-meta-card" open>
            <summary>
                <span><svg width="14" height="14" viewBox="0 0 16 16" fill="none" style="vertical-align:-2px;margin-right:6px;"><rect x="2" y="7" width="3" height="7" rx="1" fill="#2ecc71" opacity="0.6"/><rect x="6.5" y="4" width="3" height="10" rx="1" fill="#2ecc71" opacity="0.8"/><rect x="11" y="2" width="3" height="12" rx="1" fill="#2ecc71"/></svg>Üyelik & Ekonomi</span>
            </summary>
            <div class="country-meta-content">
                <div class="meta-row">
                    <span class="meta-label">Üyelik</span>
                    <div>${{badges.join(' ') || '-'}}</div>
                </div>
                <div class="meta-row">
                    <span class="meta-label">Asgari Ücret</span>
                    <div>${{minwText}}${{minwDate}}</div>
                </div>
                <div class="meta-row">
                    <span class="meta-label">Big Mac</span>
                    <div>${{bigmacText}}${{bigmacExtra}}${{bigmacDate}}</div>
                </div>
                ${{fetched}}
            </div>
        </details>
    `;
}}

let sidebarRefreshTimer = null;

function getSidebarDecadeOpenState() {{
    const state = {{}};
    const sidebarContent = document.getElementById('sidebarContent');
    if (!sidebarContent) return state;
    sidebarContent.querySelectorAll('.decade-section').forEach(section => {{
        const decade = section.getAttribute('data-decade');
        const events = section.querySelector('.decade-events');
        if (!decade || !events) return;
        state[decade] = events.classList.contains('open');
    }});
    return state;
}}

function renderSidebarEvents(countryName, countryEvents, options = {{}}) {{
    const sidebarContent = document.getElementById('sidebarContent');
    if (!sidebarContent) return;

    const preserveOpenState = !!options.preserveOpenState;
    const animateEnter = !!options.animateEnter;
    const openState = preserveOpenState ? getSidebarDecadeOpenState() : {{}};

    const byDecade = {{}};
    countryEvents.forEach(e => {{
        if (!byDecade[e.decade]) byDecade[e.decade] = [];
        byDecade[e.decade].push(e);
    }});

    let html = '';
    decades.forEach(decade => {{
        if (!byDecade[decade] || byDecade[decade].length === 0) return;

        const events = byDecade[decade].slice().sort((a, b) => {{
            const ca = categories[a.category] || {{}};
            const cb = categories[b.category] || {{}};
            const ta = (ca && typeof ca.tier === 'number') ? ca.tier : 2;
            const tb = (cb && typeof cb.tier === 'number') ? cb.tier : 2;
            if (ta !== tb) return ta - tb;
            return a.year - b.year;
        }});
        const isOpen = (openState[decade] !== undefined) ? openState[decade] : true;

        html += `
            <div class="decade-section" data-decade="${{decade}}">
                <div class="decade-header" onclick="toggleDecadeSection(this)">
                    ${{decade}}
                    <span class="count">${{events.length}}</span>
                </div>
                <div class="decade-events${{isOpen ? ' open' : ''}}">
        `;

        events.forEach(e => {{
            const cat = categories[e.category] || {{}};
            const catLabel = cat.label || e.category;
            const catColor = cat.color || '#636e72';
            const tier = (cat && typeof cat.tier === 'number') ? cat.tier : 2;
            const videoHtml = e.youtube_video_id
                ? `<div class="video-container"><iframe src="https://www.youtube.com/embed/${{e.youtube_video_id}}?rel=0" allowfullscreen></iframe></div>`
                : '';
            const wikiHtml = e.wikipedia_url
                ? `<div class="event-links"><a class="event-wiki" href="${{e.wikipedia_url}}" target="_blank" rel="noopener noreferrer">Wikipedia <span aria-hidden="true">↗</span></a></div>`
                : '';
            const categoryHtml = `<div class="event-category">${{catLabel}}</div>`;
            const eventId = String(e.id || '');

            html += `
                <div class="event-item tier-${{tier}}" data-event-id="${{eventId}}" data-category="${{e.category}}" data-decade="${{e.decade}}" style="--cat-color:${{catColor}}">
                    <div class="event-year">${{e.year}}</div>
                    <div class="event-title">${{e.title}}</div>
                    ${{categoryHtml}}
                    <div class="event-desc">${{parseMarkdownLinks(e.description)}}</div>
                    ${{wikiHtml}}
                    ${{videoHtml}}
                </div>
            `;
        }});

        html += '</div></div>';
    }});

    if (!html) {{
        html = '<div class="sidebar-empty">Aktif filtrelere göre bu ülke için görünür olay yok.</div>';
    }}

    sidebarContent.innerHTML = html;
    const countEl = document.getElementById('sidebarEventCount');
    if (countEl) countEl.textContent = countryEvents.length + ' olay';

    if (animateEnter) {{
        const items = sidebarContent.querySelectorAll('.event-item');
        items.forEach((item, index) => {{
            item.style.setProperty('--event-enter-delay', `${{Math.min(index, 12) * 16}}ms`);
            item.classList.add('event-enter');
        }});
    }}
}}

function refreshOpenSidebarEvents(forceImmediate = false) {{
    const sidebar = document.getElementById('countrySidebar');
    if (!sidebar || !sidebar.classList.contains('open')) return;

    const nameEl = document.getElementById('sidebarCountryName');
    const countryName = window.activeCountrySelection || ((nameEl && nameEl.textContent) ? nameEl.textContent.trim() : '');
    if (!countryName) return;

    const nextEvents = getFilteredCountryEvents(countryName);
    const sidebarContent = document.getElementById('sidebarContent');
    if (!sidebarContent) return;

    if (sidebarRefreshTimer) {{
        clearTimeout(sidebarRefreshTimer);
        sidebarRefreshTimer = null;
    }}

    const nextIds = new Set(nextEvents.map(e => String(e.id || '')));
    let hasRemoval = false;

    if (!forceImmediate) {{
        sidebarContent.querySelectorAll('.event-item').forEach(item => {{
            const id = item.getAttribute('data-event-id') || '';
            if (!id || !nextIds.has(id)) {{
                item.classList.add('event-removing');
                hasRemoval = true;
            }}
        }});
    }}

    const applyRender = () => {{
        renderSidebarEvents(countryName, nextEvents, {{
            preserveOpenState: true,
            animateEnter: true
        }});
    }};

    if (hasRemoval) {{
        sidebarRefreshTimer = setTimeout(() => {{
            sidebarRefreshTimer = null;
            applyRender();
        }}, 190);
    }} else {{
        applyRender();
    }}
}}

function openSidebar(countryName) {{
    console.log("Opening sidebar for:", countryName);
    const countryEvents = getFilteredCountryEvents(countryName);
    console.log(`Found ${{countryEvents.length}} events for ${{countryName}}`); // DEBUG

    if (countryEvents.length === 0) {{
        console.log("No events found for", countryName);
    }}

    // Reset to events tab when opening new country
    switchSidebarTab('events');

    // Update Header
    const titleElem = document.getElementById('sidebarCountryName');
    if (titleElem) titleElem.innerText = countryName;

    // 1. Highlight
    highlightCountryWithFlag(countryName);

    // 2. Open Sidebar UI
    const sidebar = document.getElementById('countrySidebar');
    sidebar.classList.add('open'); // Slide in
    window.activeCountrySelection = countryName;
    
    document.getElementById('sidebarCountryName').textContent = countryName;
    document.getElementById('sidebarEventCount').textContent = countryEvents.length + ' olay';

    // Set flag background in header
    const flagBg = document.getElementById('sidebarFlagBg');
    if (flagBg) {{
        const code = countryCodeMap[countryName] || '';
        if (code) {{
            flagBg.style.backgroundImage = `url(https://flagcdn.com/w640/${{code}}.png)`;
        }} else {{
            flagBg.style.backgroundImage = 'none';
        }}
    }}

    // Setup scroll progress bar
    const sidebarEl = document.getElementById('countrySidebar');
    const scrollBar = document.getElementById('sidebarScrollBar');
    if (sidebarEl && scrollBar) {{
        sidebarEl.onscroll = function() {{
            const scrollTop = sidebarEl.scrollTop;
            const scrollHeight = sidebarEl.scrollHeight - sidebarEl.clientHeight;
            const progress = scrollHeight > 0 ? scrollTop / scrollHeight : 0;
            scrollBar.style.transform = `scaleX(${{progress}})`;
        }};
    }}

    // 3. Render Metadata - with smart lookup
    const metaContainer = document.getElementById('countryMetaContainer');
    
    // Try to find meta using multiple name variants
    function findCountryMeta(name) {{
        // Direct lookup
        if (countryMeta[name]) return {{ meta: countryMeta[name], key: name }};
        
        // Try Turkish name via reverseNameMap (English -> Turkish)
        const turkishName = reverseNameMap[name];
        if (turkishName && countryMeta[turkishName]) return {{ meta: countryMeta[turkishName], key: turkishName }};
        
        // Try geoJSONNameMap reverse (if name is Turkish, find English then meta)
        const englishName = geoJSONNameMap[name];
        if (englishName && countryMeta[englishName]) return {{ meta: countryMeta[englishName], key: englishName }};
        
        // Special case variants
        const variants = [
            name.replace('ı', 'i').replace('İ', 'I'),
            name.replace('ü', 'u').replace('Ü', 'U'),
            name.replace('ö', 'o').replace('Ö', 'O'),
            name.replace('ş', 's').replace('Ş', 'S'),
            name.replace('ğ', 'g').replace('Ğ', 'G'),
            name.replace('ç', 'c').replace('Ç', 'C'),
        ];
        for (const v of variants) {{
            if (countryMeta[v]) return {{ meta: countryMeta[v], key: v }};
        }}
        
        return null;
    }}
    
    const metaResult = findCountryMeta(countryName);
    const conflictHtml = buildCurrentConflictHtml(countryName);
    const waterHtml = buildWaterHtml(countryName);
    const sanctionsHtml = buildSanctionsHtml(countryName);
    const weatherRiskHtml = buildWeatherRiskHtml(countryName);
    const airQualityHtml = buildAirQualityHtml(countryName);
    const fxHtml = buildFxPressureHtml(countryName);
    const econHtml = buildEconomyHtml(countryName);
    const countryConflicts = getCountryConflicts(countryName);
    if (metaContainer && metaResult) {{
        const meta = metaResult.meta;
        const countryKey = metaResult.key; // Use the key that matched for arrow drawing
        metaContainer.innerHTML = `
            <details class="country-meta-card" open>
                <summary>
                    <span><svg width="14" height="14" viewBox="0 0 16 16" fill="none" style="vertical-align:-2px;margin-right:6px;"><path d="M8 1l1 3h3l-2.5 2 1 3L8 7.5 5.5 9l1-3L4 4h3L8 1z" fill="#f1c40f" opacity="0.8"/></svg>İstihbarat Raporu</span>
                </summary>
                <div class="country-meta-content">
                    <div class="meta-row">
                        <span class="meta-label">Önceki Rejim</span>
                        <div>${{meta.predecessor || '-'}}</div>
                    </div>
                     ${{
                        (meta.rivalries && meta.rivalries.length > 0)
                        ? `
                        ${{
                            countryConflicts.length === 0
                                ? `
                                <div class="meta-row" style="align-items:flex-start;">
                                    <span class="meta-label">Aktif Cepheler</span>
                                    <div style="margin-top:2px; display:flex; flex-direction:column; gap:4px;">
                                        ${{
                                            (() => {{
                                                const active = meta.rivalries.filter(r => !r.status || r.status === 'active');
                                                if (active.length === 0) return '<div style="color:#7f8c8d; font-style:italic;">Yok</div>';
                                                return active.map(r => 
                                                `<div style="display:flex; align-items:center; gap:5px; margin-bottom:5px;">
                                                    <button onclick="drawSingleArrow('${{countryName}}', '${{r.rival}}')" style="background:#e74c3c; border:none; color:white; border-radius:50%; width:16px; height:16px; font-size:10px; cursor:pointer;" title="Haritada Göster">🎯</button>
                                                    <a href="${{r.url}}" target="_blank" style="color:#bdc3c7;text-decoration:none;font-weight:600; font-size:12px;">${{r.rival}}: ${{r.text}} ↗</a>
                                                </div>`
                                                ).join('');
                                            }})()
                                        }}
                                    </div>
                                </div>
                                `
                                : ''
                        }}
                        <div class="meta-row" style="align-items:flex-start; margin-top:10px; border-top:1px dashed rgba(255,255,255,0.1); padding-top:10px;">
                            <span class="meta-label">Tarihi / Pasif Çatışmalar</span>
                            <div style="margin-top:2px; display:flex; flex-direction:column; gap:4px;">
                                ${{
                                    (() => {{
                                        const historical = meta.rivalries.filter(r => r.status === 'historical');
                                        if (historical.length === 0) return '<div style="color:#7f8c8d; font-style:italic;">Yok</div>';
                                        return historical.map(r => 
                                        `<div style="display:flex; align-items:center; gap:5px; margin-bottom:5px;">
                                            <button onclick="drawSingleArrow('${{countryName}}', '${{r.rival}}')" style="background:#95a5a6; border:none; color:white; border-radius:50%; width:16px; height:16px; font-size:10px; cursor:pointer;" title="Haritada Göster">⏱</button>
                                            <a href="${{r.url}}" target="_blank" style="color:#95a5a6;text-decoration:none;font-size:12px;">${{r.rival}}: ${{r.text}} ↗</a>
                                        </div>`
                                        ).join('');
                                    }})()
                                }}
                            </div>
                        </div>
                        `
                        : ''
                    }}
                    <div class="meta-row">
                        <span class="meta-label">Demografi</span>
                        <div>${{meta.demographics || '-'}}</div>
                    </div>
                </div>
            </details>
        `;
        metaContainer.innerHTML += conflictHtml + sanctionsHtml + weatherRiskHtml + airQualityHtml + fxHtml + waterHtml + econHtml;
        
        // 4. Draw Arrows
        if (countryConflicts.length > 0) {{
            drawCountryConflicts(countryName, countryConflicts);
        }} else if (meta.rivalries) {{
            drawRivalryArrows(countryKey, meta.rivalries);
        }} else if (window.hoi4Layer) {{
             window.hoi4Layer.setArrows([]);
        }}
    }} else {{
        if (metaContainer) metaContainer.innerHTML = conflictHtml + sanctionsHtml + weatherRiskHtml + airQualityHtml + fxHtml + waterHtml + econHtml;
        if (countryConflicts.length > 0) {{
            drawCountryConflicts(countryName, countryConflicts);
        }} else if (window.hoi4Layer) {{
            window.hoi4Layer.setArrows([]);
        }}
    }}

    // 5. Render Events List
    renderSidebarEvents(countryName, countryEvents, {{
        preserveOpenState: false,
        animateEnter: false
    }});

    // 6. Populate Relations Tab
    const relContainer = document.getElementById('countryRelationsContainer');
    if (relContainer) {{
        let relHtml = '';
        const meta = (metaResult && metaResult.meta) ? metaResult.meta : {{}};

        // Rivalries
        if (meta.rivalries && meta.rivalries.length > 0) {{
            relHtml += `<details class="country-meta-card" open>
                <summary><span><svg width="14" height="14" viewBox="0 0 16 16" fill="none" style="vertical-align:-2px;margin-right:6px;"><path d="M2 8h4M10 8h4M8 2v4M8 10v4" stroke="#e74c3c" stroke-width="1.5" stroke-linecap="round"/></svg>Rakipler & Gerilimler <span style="font-size:10px;opacity:0.5;">(${{meta.rivalries.length}})</span></span></summary>
                <div class="country-meta-content">
                    ${{meta.rivalries.map(r => {{
                        const rival = r.rival || r.country || r;
                        const text = r.text || r.reason || '';
                        const status = r.status || '';
                        const statusColors = {{active:'#e74c3c',war:'#ff0000',tension:'#e67e22',frozen:'#3498db',cold:'#95a5a6',competition:'#f39c12',normalized:'#2ecc71',managed:'#27ae60',complex:'#9b59b6',severed:'#c0392b','cold_peace':'#7f8c8d','post-war':'#d35400',resolved:'#2ecc71'}};
                        const dot = status ? `<span style="display:inline-block;width:6px;height:6px;border-radius:50%;background:${{statusColors[status]||'#95a5a6'}};margin-right:4px;box-shadow:0 0 4px ${{statusColors[status]||'#95a5a6'}};"></span>` : '';
                        const statusLabels = {{active:'Aktif',war:'Savaş',tension:'Gerilim',frozen:'Dondurulmuş',cold:'Soğuk',competition:'Rekabet',normalized:'Normalleşti',managed:'Yönetilen',complex:'Karmaşık',severed:'Kopuk','cold_peace':'Soğuk Barış','post-war':'Savaş Sonrası',resolved:'Çözüldü'}};
                        const statusText = status ? `<span style="font-size:9px;color:${{statusColors[status]||'#95a5a6'}};font-weight:600;text-transform:uppercase;letter-spacing:0.5px;">${{dot}}${{statusLabels[status]||status}}</span>` : '';
                        return `<div class="meta-row" style="padding:6px 0;border-bottom:1px solid rgba(255,255,255,0.04);">
                            <div style="display:flex;justify-content:space-between;align-items:center;">
                                <span class="meta-label" style="font-weight:600;color:#ecf0f1;">${{rival}}</span>
                                ${{statusText}}
                            </div>
                            <div style="font-size:11px;color:#95a5a6;margin-top:2px;">${{text}}</div>
                        </div>`;
                    }}).join('')}}
                </div>
            </details>`;
        }}

        // Allies
        if (meta.allies && meta.allies.length > 0) {{
            relHtml += `<details class="country-meta-card" open>
                <summary><span><svg width="14" height="14" viewBox="0 0 16 16" fill="none" style="vertical-align:-2px;margin-right:6px;"><path d="M4 12c0-2 2-3 4-3s4 1 4 3" stroke="#2ecc71" stroke-width="1.2" stroke-linecap="round"/><circle cx="8" cy="5.5" r="2.5" stroke="#2ecc71" stroke-width="1.2"/></svg>Müttefikler <span style="font-size:10px;opacity:0.5;">(${{meta.allies.length}})</span></span></summary>
                <div class="country-meta-content">
                    <div style="display:flex;gap:5px;flex-wrap:wrap;">
                        ${{meta.allies.map(a => `<span style="padding:3px 10px;background:rgba(46,204,113,0.1);border:1px solid rgba(46,204,113,0.2);border-radius:12px;font-size:11px;color:#2ecc71;cursor:pointer;" onclick="highlightCountryWithFlag('${{a}}')">${{a}}</span>`).join('')}}
                    </div>
                </div>
            </details>`;
        }}

        // Trade Partners
        if (meta.trade_partners && meta.trade_partners.length > 0) {{
            relHtml += `<details class="country-meta-card">
                <summary><span><svg width="14" height="14" viewBox="0 0 16 16" fill="none" style="vertical-align:-2px;margin-right:6px;"><path d="M2 12l4-4 3 3 5-7" stroke="#f1c40f" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/></svg>Ticaret Ortakları <span style="font-size:10px;opacity:0.5;">(${{meta.trade_partners.length}})</span></span></summary>
                <div class="country-meta-content">
                    <div style="display:flex;gap:5px;flex-wrap:wrap;">
                        ${{meta.trade_partners.map((t,i) => `<span style="padding:3px 10px;background:rgba(241,196,15,0.08);border:1px solid rgba(241,196,15,0.15);border-radius:12px;font-size:11px;color:#f1c40f;cursor:pointer;" onclick="highlightCountryWithFlag('${{t}}')">${{i+1}}. ${{t}}</span>`).join('')}}
                    </div>
                </div>
            </details>`;
        }}

        // Organizations
        const memberships = [];
        if (countryGroups.nato && countryGroups.nato.has(countryName)) memberships.push({{name:'NATO',color:'#3498db'}});
        if (countryGroups.g8 && countryGroups.g8.has(countryName)) memberships.push({{name:'G8',color:'#f1c40f'}});
        if (countryGroups.brics_plus && countryGroups.brics_plus.has(countryName)) memberships.push({{name:'BRICS+',color:'#5865f2'}});
        const orgs = meta.organizations || [];
        orgs.forEach(o => {{
            if (!memberships.find(m => m.name === o)) memberships.push({{name:o,color:'#95a5a6'}});
        }});
        if (memberships.length > 0) {{
            relHtml += `<details class="country-meta-card" open>
                <summary><span><svg width="14" height="14" viewBox="0 0 16 16" fill="none" style="vertical-align:-2px;margin-right:6px;"><circle cx="8" cy="8" r="5.5" stroke="#3498db" stroke-width="1.2"/><path d="M8 5v6M5 8h6" stroke="#3498db" stroke-width="1.2"/></svg>Üyelikler & Kuruluşlar <span style="font-size:10px;opacity:0.5;">(${{memberships.length}})</span></span></summary>
                <div class="country-meta-content">
                    <div style="display:flex;gap:5px;flex-wrap:wrap;">
                        ${{memberships.map(m => `<span class="group-badge" style="border-color:${{m.color}}40;color:${{m.color}};background:${{m.color}}15;">${{m.name}}</span>`).join('')}}
                    </div>
                </div>
            </details>`;
        }}

        // Territorial disputes
        if (meta.territorial_disputes && meta.territorial_disputes.length > 0) {{
            relHtml += `<details class="country-meta-card">
                <summary><span><svg width="14" height="14" viewBox="0 0 16 16" fill="none" style="vertical-align:-2px;margin-right:6px;"><path d="M8 1v14M1 8h14" stroke="#e67e22" stroke-width="1.5" stroke-linecap="round" opacity="0.7"/><circle cx="8" cy="8" r="5" stroke="#e67e22" stroke-width="1.2"/></svg>Toprak Uyuşmazlıkları <span style="font-size:10px;opacity:0.5;">(${{meta.territorial_disputes.length}})</span></span></summary>
                <div class="country-meta-content">
                    ${{meta.territorial_disputes.map(t => `<div style="padding:4px 0;font-size:11px;color:#e67e22;border-bottom:1px solid rgba(255,255,255,0.03);">⚠ ${{t}}</div>`).join('')}}
                </div>
            </details>`;
        }}

        // Active conflicts
        if (countryConflicts.length > 0) {{
            relHtml += conflictHtml;
        }}

        if (!relHtml) {{
            relHtml = '<div class="sidebar-empty">Bu ülke için ilişki verisi bulunamadı.</div>';
        }}
        relContainer.innerHTML = relHtml;
    }}
}}

function closeSidebar() {{
    if (sidebarRefreshTimer) {{
        clearTimeout(sidebarRefreshTimer);
        sidebarRefreshTimer = null;
    }}
    const sidebar = document.getElementById('countrySidebar');
    if (sidebar) sidebar.classList.remove('open');
}}
function toggleFilterPanel() {{
    const panel = document.getElementById('controlPanel');
    const fab = document.getElementById('panelFab');
    const btn = document.getElementById('panelToggle');
    const handle = document.getElementById('panelHandle');
    const handleIcon = document.getElementById('panelHandleIcon');
    if (!panel) return;
    const open = !panel.classList.contains('mobile-open');
    if (open) {{
        panel.classList.add('mobile-open');
    }} else {{
        panel.classList.remove('mobile-open');
    }}
    if (fab) {{
        fab.classList.toggle('hidden', open);
        fab.setAttribute('aria-expanded', open ? 'true' : 'false');
    }}
    if (btn) {{
        btn.textContent = open ? 'Kapat' : 'Filtreler';
        btn.setAttribute('aria-expanded', open ? 'true' : 'false');
    }}
    if (handle) {{
        handle.setAttribute('aria-expanded', open ? 'true' : 'false');
    }}
    if (handleIcon) {{
        // Show direction: when panel is open, arrow points right (close); when closed, left (open).
        handleIcon.textContent = open ? '›' : '‹';
    }}
}}
function toggleDecadeSection(header) {{
    const events = header.nextElementSibling;
    events.classList.toggle('open');
}}

// Country code mapping for flags (country_name -> ISO Alpha-2)
// Dynamically generated from master country_mappings.json
const countryCodeMap = {turkish_to_iso_json};

// Also add from events data (fallback for missing entries)
allEvents.forEach(e => {{
    if (e.country_code && e.country_name && !countryCodeMap[e.country_name]) {{
        countryCodeMap[e.country_name] = e.country_code.toLowerCase();
    }}
}});


// GeoJSON country boundaries - loaded async via loadAppData()
// Access via window.countriesGeoJSON (set by async loader before init)
let highlightLayers = []; // Changed to array for multiple layers

// Name mappings - loaded async (see loadAppData)
const geoJSONNameMap = window.geoJSONNameMap || {turkish_to_english_json};
const reverseNameMap = window.reverseNameMap || {english_to_turkish_json};

// Find country feature in GeoJSON by name or code
function findCountryFeature(countryName) {{
    if (!window.countriesGeoJSON) {{
        console.error('GeoJSON not loaded!');
        return null;
    }}

    const countryCode = countryCodeMap[countryName];
    const geoJSONName = geoJSONNameMap[countryName] || countryName;

    console.log('Looking for:', countryName, '-> GeoJSON name:', geoJSONName, '-> ISO:', countryCode);

    const found = window.countriesGeoJSON.features.find(f => {{
        const props = f.properties;
        const propName = props.name || '';
        const propISO = (props['ISO3166-1-Alpha-2'] || '').toLowerCase();

        // Match by mapped name first (exact)
        if (propName === geoJSONName) return true;
        // Match by original name (exact)
        if (propName === countryName) return true;
        // Match by ISO code (skip -99)
        if (countryCode && propISO && propISO !== '-99' && propISO === countryCode) return true;
        // Case-insensitive exact match
        if (propName.toLowerCase() === geoJSONName.toLowerCase()) return true;
        if (propName.toLowerCase() === countryName.toLowerCase()) return true;
        return false;
    }});

    if (found) {{
        console.log('Found country:', found.properties.name);
    }} else {{
        console.warn('Country not found in GeoJSON:', countryName, '(mapped:', geoJSONName, ')');
    }}

    return found;
}}

// Special flag URLs for territories not in flagcdn
const specialFlagUrls = {{
    'Northern Cyprus': 'https://upload.wikimedia.org/wikipedia/commons/thumb/1/1e/Flag_of_the_Turkish_Republic_of_Northern_Cyprus.svg/640px-Flag_of_the_Turkish_Republic_of_Northern_Cyprus.svg.png',
    'Kuzey Kıbrıs': 'https://upload.wikimedia.org/wikipedia/commons/thumb/1/1e/Flag_of_the_Turkish_Republic_of_Northern_Cyprus.svg/640px-Flag_of_the_Turkish_Republic_of_Northern_Cyprus.svg.png',
    'Kuzey Kibris': 'https://upload.wikimedia.org/wikipedia/commons/thumb/1/1e/Flag_of_the_Turkish_Republic_of_Northern_Cyprus.svg/640px-Flag_of_the_Turkish_Republic_of_Northern_Cyprus.svg.png',
    'KKTC': 'https://upload.wikimedia.org/wikipedia/commons/thumb/1/1e/Flag_of_the_Turkish_Republic_of_Northern_Cyprus.svg/640px-Flag_of_the_Turkish_Republic_of_Northern_Cyprus.svg.png',
    'Kuzey Kıbrıs Türk Cumhuriyeti': 'https://upload.wikimedia.org/wikipedia/commons/thumb/1/1e/Flag_of_the_Turkish_Republic_of_Northern_Cyprus.svg/640px-Flag_of_the_Turkish_Republic_of_Northern_Cyprus.svg.png',
    'Cyprus No Mans Area': 'https://upload.wikimedia.org/wikipedia/commons/thumb/d/d4/Flag_of_Cyprus.svg/640px-Flag_of_Cyprus.svg.png',
    'Kosovo': 'https://flagcdn.com/w640/xk.png'
}};



// Flag Highlight Logic


function clearCountryHighlight() {{
    // 1. Clear Vector Highlights
    if (typeof highlightLayers !== 'undefined' && highlightLayers.length > 0) {{
        highlightLayers.forEach(layer => {{
            if (layer._path && layer._originalFill) {{
                layer._path.setAttribute('fill', layer._originalFill);
                layer._path.setAttribute('fill-opacity', layer._originalOpacity || 0.2);
            }}
        }});
        highlightLayers = [];
    }}

    // 2. Clear Flag Overlay (Singleton) - Hide it
    if (window.flagOverlayLayer) {{
        window.flagOverlayLayer.style.opacity = 0;
        window.currentFlagCountry = null;
    }}
    
    // Legacy Cleanup (in case of old cache/reload issues)
    if (window.currentFlagOverlay && window.currentFlagOverlay.parentElement) {{
        window.currentFlagOverlay.parentElement.removeChild(window.currentFlagOverlay);
        window.currentFlagOverlay = null;
    }}
}}

// Initialize on load
document.addEventListener('DOMContentLoaded', function() {{
    initFilters();
    initAiSearch();
    updateFilterBadges();
    setTimeout(updateGroupCounts, 500);
}});

window.openSidebar = openSidebar;
window.getFilteredCountryEvents = getFilteredCountryEvents;
window.refreshOpenSidebarEvents = refreshOpenSidebarEvents;
window.highlightCountryWithFlag = highlightCountryWithFlag;
window.clearCountryHighlight = clearCountryHighlight;
window.findCountryFeature = findCountryFeature;

// Register markers after map loads
window.addEventListener('load', function() {{
    // Wait a bit for Folium to fully render markers
    setTimeout(function() {{
        // Get all marker icons
        const markers = document.querySelectorAll('.leaflet-marker-icon');
        
        // Match markers to countries by their tooltip
        markers.forEach(markerIcon => {{
            const parent = markerIcon.parentElement;
            if (parent && parent._leaflet_id) {{
                const leafletId = parent._leaflet_id;
                // Try to find the marker object in Leaflet
                document.querySelectorAll('.leaflet-marker-pane > *').forEach(markerDiv => {{
                    if (markerDiv._leaflet_id === leafletId && markerDiv._icon) {{
                        const tooltip = markerDiv._tooltip;
                        if (tooltip && tooltip._content) {{
                            // Extract country name from tooltip (format: "Country (X olay)")
                            const match = tooltip._content.match(/^(.+?)\\s*\\(/);
                            if (match) {{
                                const country = match[1].trim();
                                markersByCountry[country] = markerDiv;
                            }}
                        }}
                    }}
                }});
            }}
        }});
        
        // Initial visibility update
        updateMarkerVisibility();
    }}, 500);
}});

</script>
'''

    def _create_popup_content(self, country_name: str, country_events: List[dict]) -> str:
        """Create HTML popup content with 3 event preview."""
        total = len(country_events)
        preview_events = sorted(country_events, key=lambda x: -x['year'])[:3]

        events_html = ""
        for e in preview_events:
            cat = self.categories.get(e['category'], {})
            cat_color = cat.get('color', '#666')
            cat_label = cat.get('label', e['category'])
            events_html += f'''
            <div class="popup-event">
                <div class="popup-event-year">{e['year']}</div>
                <div class="popup-event-title">{e['title']}</div>
                <span class="popup-event-cat" style="background:{cat_color}">{cat_label}</span>
            </div>
            '''

        more_text = f"ve {total - 3} olay daha..." if total > 3 else ""

        return f'''
        <div class="popup-container">
            <div class="popup-header">
                <div class="popup-country">{country_name}</div>
                <div class="popup-count">{total} tarihi olay</div>
            </div>
            <div class="popup-preview">
                {events_html}
                {f'<div style="font-size:11px;color:#888;padding-top:5px;">{more_text}</div>' if more_text else ''}
            </div>
            <button class="popup-btn" onclick="openSidebar('{country_name}')">
                Tüm Olayları Gör →
            </button>
        </div>
        '''

    def _get_marker_icon(self, category: str) -> folium.Icon:
        """Get marker icon based on category."""
        cat = self.categories.get(category, {})
        icon = cat.get('icon', 'fa-info')
        color_map = {
            '#e74c3c': 'red',
            '#2c3e50': 'black',
            '#e67e22': 'orange',
            '#9b59b6': 'purple',
            '#3498db': 'blue',
            '#2ecc71': 'green',
            '#16a085': 'cadetblue',  # politics
            '#f1c40f': 'orange',  # time_100
            '#95a5a6': 'gray',  # cinema
            '#e84393': 'pink',  # music
        }
        color = color_map.get(cat.get('color', '#3498db'), 'blue')
        return folium.Icon(color=color, icon=icon, prefix='fa')

    def _write_data_assets(self, output_dir: Path) -> None:
        """Write large data objects as separate JSON files for async loading."""
        # 1. GeoJSON country boundaries (~14MB inline -> separate cacheable file)
        if self.geojson_data:
            geo_path = output_dir / "geo.json"
            with open(geo_path, "w", encoding="utf-8") as f:
                json.dump(self.geojson_data, f, ensure_ascii=False, separators=(",", ":"))
            print(f"  Data asset: geo.json ({geo_path.stat().st_size // 1024}KB)")

        # 2. Events data (~1.8MB inline -> separate cacheable file)
        events_path = output_dir / "events_data.json"
        with open(events_path, "w", encoding="utf-8") as f:
            json.dump(self.events, f, ensure_ascii=False, separators=(",", ":"))
        print(f"  Data asset: events_data.json ({events_path.stat().st_size // 1024}KB)")

        # 3. Meta bundle (metadata + indicators + strategic snapshots + mappings)
        meta_bundle = {
            "country_metadata": self.country_metadata if hasattr(self, "country_metadata") else {},
            "water_sources": self.water_sources if hasattr(self, "water_sources") else {"updated_at_utc": "", "countries": {}},
            "current_conflicts": self.current_conflicts if hasattr(self, "current_conflicts") else {"updated_at_utc": "", "source_note": "", "conflicts": []},
            "indicators": self.indicators if hasattr(self, "indicators") else {},
            "strategic_snapshots": self.strategic_snapshots if hasattr(self, "strategic_snapshots") else {"sanctions": {"countries": {}}, "weather": {"countries": {}}, "air_quality": {"countries": {}}, "fx": {"countries": {}}},
            "turkish_to_english": self.turkish_to_english,
            "english_to_turkish": self.english_to_turkish,
            "turkish_to_iso": self.turkish_to_iso,
        }
        meta_path = output_dir / "meta.json"
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta_bundle, f, ensure_ascii=False, separators=(",", ":"))
        print(f"  Data asset: meta.json ({meta_path.stat().st_size // 1024}KB)")

    def create_map(self, output_path: str = None) -> str:
        """Create the interactive geopolitical map."""
        output_path = output_path or self.output_dir / "geopolitical_map.html"
        import datetime

        build_time_utc = datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
        self.build_info = {
            "build_time_utc": build_time_utc,
            "events": len(self.events),
        }
        git_sha = os.environ.get("GIT_SHA") or os.environ.get("COMMIT_SHA")
        if not git_sha:
            head_path = self.base_dir / ".git" / "HEAD"
            if head_path.exists():
                head_ref = head_path.read_text().strip()
                if head_ref.startswith("ref:"):
                    ref_path = self.base_dir / ".git" / head_ref.split(" ", 1)[1]
                    if ref_path.exists():
                        git_sha = ref_path.read_text().strip()
                else:
                    git_sha = head_ref
        if git_sha:
            self.build_info["git_sha"] = git_sha[:12]

        m = folium.Map(
            location=[30, 20],
            zoom_start=3,
            tiles='CartoDB positron',
            prefer_canvas=True
        )

        # Add custom CSS and JS
        m.get_root().html.add_child(folium.Element(self._get_custom_css_js()))

        # Group events by country
        by_country = {}
        for event in self.events:
            country = event['country_name']
            if country not in by_country:
                by_country[country] = []
            by_country[country].append(event)

        # Add one marker per country (at the location of most recent event)
        for country, events in by_country.items():
            # Use the most recent event's location
            latest = max(events, key=lambda x: x['year'])

            # Determine dominant category for icon
            cat_counts = {}
            for e in events:
                cat_counts[e['category']] = cat_counts.get(e['category'], 0) + 1
            dominant_cat = max(cat_counts, key=cat_counts.get)

            popup_content = self._create_popup_content(country, events)
            icon = self._get_marker_icon(dominant_cat)

            marker = folium.Marker(
                location=[latest['lat'], latest['lon']],
                popup=folium.Popup(popup_content, max_width=350),
                tooltip=f"{country} ({len(events)} olay)",
                icon=icon
            )
            marker.add_to(m)

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        m.save(str(output_path))

        # Write data assets as separate files for async loading
        self._write_data_assets(Path(output_path).parent)

        # Post-process HTML to add marker tracking for filtering
        self._inject_marker_tracking(output_path, by_country)

        # Create robots.txt
        robots_path = Path(output_path).parent / "robots.txt"
        with open(robots_path, "w") as f:
            f.write("User-agent: *\nAllow: /\nSitemap: https://jeopolitik.com.tr/sitemap.xml")
            
        # Create expanded sitemap.xml (countries + decades)
        sitemap_path = Path(output_path).parent / "sitemap.xml"
        now = datetime.datetime.now().strftime("%Y-%m-%d")
        tr_chars = str.maketrans("çğıöşüÇĞİÖŞÜ ", "cgiosuCGIOSU-")
        with open(sitemap_path, "w") as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            f.write('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
            f.write(f'  <url>\n    <loc>https://jeopolitik.com.tr/</loc>\n    <lastmod>{now}</lastmod>\n    <changefreq>daily</changefreq>\n    <priority>1.0</priority>\n  </url>\n')
            for country in sorted(by_country.keys()):
                slug = country.lower().translate(tr_chars)
                f.write(f'  <url>\n    <loc>https://jeopolitik.com.tr/#{slug}</loc>\n    <lastmod>{now}</lastmod>\n    <changefreq>weekly</changefreq>\n    <priority>0.8</priority>\n  </url>\n')
            for dec in self.DECADES:
                f.write(f'  <url>\n    <loc>https://jeopolitik.com.tr/#decade-{dec}</loc>\n    <lastmod>{now}</lastmod>\n    <changefreq>monthly</changefreq>\n    <priority>0.6</priority>\n  </url>\n')
            f.write('</urlset>\n')

        # Build metadata and health check files
        self.build_info["countries"] = len(by_country)
        self.build_info["status"] = "ok"
        self.build_info["generated_at_utc"] = build_time_utc
        self.build_info["site"] = "https://jeopolitik.com.tr/"

        build_info_path = Path(output_path).parent / "build-info.json"
        with open(build_info_path, "w", encoding="utf-8") as f:
            json.dump(self.build_info, f, ensure_ascii=False, indent=2)

        health_path = Path(output_path).parent / "healthz.json"
        with open(health_path, "w", encoding="utf-8") as f:
            json.dump(self.build_info, f, ensure_ascii=False, indent=2)

        print(f"Harita oluşturuldu: {output_path}")
        print(f"SEO dosyaları oluşturuldu: robots.txt, sitemap.xml")
        print(f"Build info oluşturuldu: build-info.json, healthz.json")
        print(f"Toplam {len(self.events)} olay, {len(by_country)} ülke")
        return str(output_path)
    
    def _inject_marker_tracking(self, output_path: str, by_country: dict):
        """Inject JavaScript to track markers for filtering using robust Leaflet discovery."""
        with open(output_path, 'r', encoding='utf-8') as f:
            html = f.read()
            
        # Build marker data JSON
        marker_data = {}
        for country, events in by_country.items():
            decades = set(e['decade'] for e in events)
            categories = set(e['category'] for e in events)
            marker_data[country] = {
                'decades': list(decades),
                'categories': list(categories)
            }
        
        # Inject filtering logic
        inject_script = f'''
<script>
// Filter data
const countryFilterData = {json.dumps(marker_data, ensure_ascii=False)};

// Global storage
window.geoMap = null;
window.markerLayersByCountry = {{}};

// Initialize marker tracking - waits for async data load
window.addEventListener('load', async function() {{
    // Load data assets first
    if (typeof loadAppData === 'function') {{
        const loaded = await loadAppData();
        if (!loaded) return;
    }}

    // Failsafe: remove loading overlay after 15 seconds no matter what
    setTimeout(function() {{
        const ov = document.getElementById('loadingOverlay');
        if (ov) {{ ov.style.opacity = '0'; setTimeout(() => ov.remove(), 400); }}
    }}, 15000);

    function findMapInstance() {{
        for (let key in window) {{
            try {{
                if (window[key] && window[key] instanceof L.Map) {{
                    return key;
                }}
            }} catch(e) {{}}
        }}
        return null;
    }}

    let retries = 0;
    const maxRetries = 20;
    function tryInitMap() {{
        retries++;
        const mapKey = findMapInstance();
        if (mapKey) {{
            window.geoMap = window[mapKey];
            console.log("Found Leaflet Map instance:", mapKey, "(attempt " + retries + ")");
            initMapFeatures();
        }} else if (retries < maxRetries) {{
            console.log("Map instance not found yet, retrying... (" + retries + "/" + maxRetries + ")");
            setTimeout(tryInitMap, 500);
        }} else {{
            console.error("Map instance not found after " + maxRetries + " attempts!");
            const ov = document.getElementById('loadingOverlay');
            if (ov) {{ ov.style.opacity = '0'; setTimeout(() => ov.remove(), 400); }}
        }}
    }}

    setTimeout(tryInitMap, 300);

    function initMapFeatures() {{
        if (!window.geoMap) {{
            return;
        }}
        
        console.log("Analyzing map layers...");
        const markerLayers = {{}};
        
        // Iterate over all layers in the map
        window.geoMap.eachLayer(function(layer) {{
            // Check if it's a marker with a tooltip
            if (layer instanceof L.Marker && layer.getTooltip()) {{
                const content = layer.getTooltip().getContent();
                
                // Parse HTML content safely
                let textContent = content;
                if (typeof content === 'string') {{
                    // Remove HTML tags
                    textContent = content.replace(/<[^>]*>/g, '');
                    // Normalize whitespace (newlines become spaces, then trim)
                    textContent = textContent.replace(/\\s+/g, ' ').trim();
                }}
                
                // Match country name: "Turkey (55 events)" -> "Turkey"
                const match = textContent.match(/^(.+?)\\s*\\(/);
                
                if (match) {{
                    const country = match[1].trim();
                    if (!markerLayers[country]) {{
                        markerLayers[country] = [];
                    }}
                    markerLayers[country].push(layer);
                    
                    // Bind click to sidebar
                    layer.off('click'); // Remove existing clicks (e.g. popup)
                    layer.unbindPopup(); // Disable popup to prioritize sidebar
                    layer.on('click', function(e) {{
                        window.openSidebar(country);
                        L.DomEvent.stopPropagation(e);
                    }});
                }}
            }}
        }});
        
        window.markerLayersByCountry = markerLayers;
        console.log(`Mapped markers for ${{Object.keys(markerLayers).length}} countries.`);
        
        // Initialize HOI4-style arrow overlay layer
        window.hoi4Layer = new L.Hoi4Overlay();
        window.hoi4Layer.addTo(window.geoMap);
        console.log("HOI4 Arrow Overlay layer initialized.");
        
        // --- NEW: Add territory click handlers ---
        console.log("Adding territory click handlers...");
        // --- NEW: Add territory click handlers for ALL countries ---
        console.log("Adding territory click handlers for all countries...");
        
        // Use global reverseNameMap (generated from country_mappings.json)

        if (window.countriesGeoJSON) {{
            window.countriesGeoJSON.features.forEach(feature => {{
                const geoName = feature.properties.name || feature.properties.NAME;
                // Try to find Turkish name using global reverseNameMap, otherwise fallback to GeoJSON name
                let countryKey = reverseNameMap[geoName] || geoName;
                
                // reverseNameMap already normalizes to canonical Turkish names (e.g., Turkey -> Türkiye)
                if (geoName === 'China') {{
                    feature.properties['ISO3166-1-Alpha-2'] = 'cn';
                }}
                
                // Create a transparent clickable layer for every country
                L.geoJSON(feature, {{
                    style: {{
                        fillColor: '#ffffff', 
                        fillOpacity: 0,
                        color: 'transparent', 
                        weight: 0
                    }}
                }})
                .on('mouseover', function(e) {{
                    // Hover: Show Flag
                    console.log('Mouseover triggered for:', countryKey); // DEBUG
                    if (window.highlightCountryWithFlag) {{
                        window.highlightCountryWithFlag(countryKey);
                    }}
                    if (window.updateIndicatorHoverInfo) {{
                        window.updateIndicatorHoverInfo(countryKey);
                    }}
                    L.DomEvent.stopPropagation(e); // Ensure it stops here
                }})
                .on('mouseout', function(e) {{
                    // Out: Remove Flag
                    if (window.clearCountryHighlight) {{
                        window.clearCountryHighlight();
                    }}
                    if (window.clearIndicatorHoverInfo) {{
                        window.clearIndicatorHoverInfo();
                    }}
                }})
                .on('click', function(e) {{
                    console.log('Territory clicked:', countryKey);
                    
                    // 1. Draw arrows if rivalries exist
                    if (window.countryMeta && window.countryMeta[countryKey]) {{
                         const meta = window.countryMeta[countryKey];
                         if (meta.rivalries && meta.rivalries.length > 0) {{
                             if (window.drawRivalryArrows) {{
                                 window.drawRivalryArrows(countryKey, meta.rivalries);
                             }}
                         }} else {{
                             // Clear arrows if no rivalries
                             if (window.arrowLayers) {{
                                 window.arrowLayers.forEach(l => window.geoMap.removeLayer(l));
                                 window.arrowLayers = [];
                             }}
                         }}
                    }}

                    // 2. Open sidebar (keep existing behavior)
                    window.openSidebar(countryKey);
                    L.DomEvent.stopPropagation(e);
                }}).addTo(window.geoMap);
            }});
        }}

        // External overlays (G8/NATO highlights, economic indicators)
        if (window.initExternalOverlays) {{
            window.initExternalOverlays();
        }}

        // --- GLOBAL CONFLICTS INIT ---
        // (Disabled per user request - no global arrows on load)
        /*
        if (window.showConflictArrows && window.drawGlobalActiveArrows) {{
             console.log("Triggering initial global arrows...");
             window.drawGlobalActiveArrows();
        }}
        */
        
        // Map Click to Clear Selection
        if (window.geoMap) {{
            window.geoMap.on('click', function(e) {{
                // If we are currently focused on a country, clear it
                if (window.activeCountrySelection) {{
                    console.log("Map background clicked: Clearing Selection");
                    window.activeCountrySelection = null;
                    window._lastArrowCountry = null;
                    window._lastArrowRivalries = null;
                    
                    // Clear arrows (do NOT show global)
                    if (window.hoi4Layer) window.hoi4Layer.setArrows([]);
                    
                    if (window.closeSidebar) window.closeSidebar();
                }}
            }});
        }}

        // Update group counts and visible event count now that data is loaded
        if (typeof updateGroupCounts === 'function') updateGroupCounts();
        if (typeof updateVisibleCount === 'function') updateVisibleCount();

        // Dismiss loading overlay
        const overlay = document.getElementById('loadingOverlay');
        if (overlay) {{
            overlay.style.opacity = '0';
            setTimeout(() => overlay.remove(), 400);
        }}

    }} // end initMapFeatures
}});

// --- Performance: Debounce + rAF utilities ---
let _markerVisibilityRAF = null;
function _scheduleMarkerUpdate() {{
    if (_markerVisibilityRAF) cancelAnimationFrame(_markerVisibilityRAF);
    _markerVisibilityRAF = requestAnimationFrame(() => {{
        _markerVisibilityRAF = null;
        _doUpdateMarkerVisibility();
    }});
}}

// Debounced version for rapid filter changes (80ms)
let _filterDebounceTimer = null;
function updateMarkerVisibility() {{
    clearTimeout(_filterDebounceTimer);
    _filterDebounceTimer = setTimeout(_scheduleMarkerUpdate, 80);
}}

// Actual visibility update logic
function _doUpdateMarkerVisibility() {{
    if (!window.geoMap || !window.markerLayersByCountry) return;
    
    const groupKey = window.activeCountryGroup;
    const groupSet = (groupKey && window.countryGroups && window.countryGroups[groupKey]) ? window.countryGroups[groupKey] : null;

    const visibleCountries = new Set();
    Object.entries(countryFilterData).forEach(([country, data]) => {{
        if (groupSet && !groupSet.has(country)) return;
        const hasVisibleDecade = data.decades.some(d => selectedDecades.has(d));
        const hasVisibleCategory = data.categories.some(c => selectedCategories.has(c) || (showTime100 && c === 'time_100'));
        
        if (hasVisibleDecade && hasVisibleCategory) {{
            visibleCountries.add(country);
        }}
    }});
    
    // Update markers
    Object.entries(window.markerLayersByCountry).forEach(([country, layers]) => {{
        const isVisible = visibleCountries.has(country);
        layers.forEach(layer => {{
            if (isVisible) {{
                if (!window.geoMap.hasLayer(layer)) {{
                    window.geoMap.addLayer(layer);
                }}
                // Ensure opacity is reset if it was modified
                if (layer.setOpacity) layer.setOpacity(1);
            }} else {{
                if (window.geoMap.hasLayer(layer)) {{
                    window.geoMap.removeLayer(layer);
                }}
            }}
        }});
    }});
    
    console.log(`Updated visibility: ${{visibleCountries.size}} countries visible.`);
    if (window.refreshOpenSidebarEvents) {{
        window.refreshOpenSidebarEvents();
    }}
}}

    // --- Global Visual Centers (Moved out for reuse) ---
    const VISUAL_CENTERS = {{
        // Russia -> Moscow/West
        "Russia": [55.75, 37.61],
        "Rusya": [55.75, 37.61],
        // USA -> Central/East
        "United States": [39.8, -98.5],
        "ABD": [39.8, -98.5],
        // France
        "France": [46.6, 2.2],
        "Fransa": [46.6, 2.2],
        // UK
        "United Kingdom": [52.5, -1.0],
        "Birleşik Krallık": [52.5, -1.0],
        "Ingiltere": [52.5, -1.0],
        // China
        "China": [32.0, 110.0],
        "Çin": [32.0, 110.0],
        "Cin": [32.0, 110.0],
        // Canada
        "Canada": [50.0, -100.0],
        "Kanada": [50.0, -100.0],
        // Ukraine
        "Ukraine": [48.3794, 31.1656],
        "Ukrayna": [48.3794, 31.1656],
        // Non-State Actor / Internal Conflict Centers
        "Hızlı Destek Kuvvetleri": [13.5, 24.5], 
        "Hamas": [31.4, 34.4], 
        "Gazze": [31.4, 34.4],
        "Batı Şeria": [31.9, 35.2],
        "Filistin": [31.9, 35.2], 
        "Boko Haram": [11.8, 13.5], 
        "ISWAP": [12.5, 13.8],
        "M23": [-1.5, 29.3], 
        "Amhara": [11.5, 38.0], 
        "Oromia": [8.5, 40.0], 
        "Al-Shabaab": [2.5, 44.0], 
        "Suriye Muhalifleri": [36.0, 36.8], 
        "HTS": [35.9, 36.6], 
        "Husiler": [15.3, 44.2], 
        "Cihatçı Gruplar (Sahel)": [14.5, 0.5], 
        "JNIM": [14.5, -2.0], 
        "Meksika Kartelleri": [25.0, -107.5], 
        "Myanmar Direnişi": [22.0, 95.5], 
        "Haiti Çeteleri": [18.55, -72.3], 
        "Ekvador Çeteleri": [-2.2, -79.9], 
        "PCC": [-23.55, -46.63], 
        "ISKP": [34.2, 70.5], 
        "Hizbullah": [33.3, 35.4], 
        "Cabo Delgado İsyancıları": [-12.5, 39.5], 
        "ELN": [8.5, -73.0], 
        "ISIS": [35.0, 44.0], 
        "Libya Doğusu (Haftar)": [32.1, 20.1], 
        "Keşmir Militanları": [34.0, 74.5], 
        "Güney Tayland İsyancıları": [6.5, 101.3], 
        "NPA": [8.0, 125.0], 
        "Abu Sayyaf": [6.0, 121.0], 
        "Bangladeş Militanları": [23.5, 90.5], 
        "Papua Ayrılıkçıları": [-4.0, 138.0], 
        "Irak Direnişi": [33.3, 44.3]
    }};

    function findLayer(name) {{
        let found = null;
        if (window.geoMap) {{
            window.geoMap.eachLayer(function(layer) {{
                if (layer.feature && layer.feature.properties) {{
                    const props = layer.feature.properties;
                    if (props.NAME === name || props.NAME_LONG === name || 
                        (window.countryCodeMap && window.countryCodeMap[props.NAME] === name) ||
                        (window.countryMeta && window.countryMeta[name] && window.countryMeta[name].code === props.ISO_A3)) {{
                        found = layer;
                    }}
                }}
            }});
        }}
        return found;
    }}

    function getVisualCenter(name, layer) {{
        if (VISUAL_CENTERS[name]) {{
            return L.latLng(VISUAL_CENTERS[name]);
        }}
        if (layer) {{
            return layer.getBounds().getCenter();
        }}
        return null;
    }}

    function resolveConflictPoint(name, anchor) {{
        if (anchor && typeof anchor === 'object') {{
            const lat = Number(anchor.lat);
            const lon = Number(anchor.lon);
            if (Number.isFinite(lat) && Number.isFinite(lon)) {{
                return L.latLng(lat, lon);
            }}
        }}

        if (!name) return null;
        let layer = null;
        if (typeof window.findCountryFeature === 'function') {{
            const feature = window.findCountryFeature(name);
            if (feature) layer = L.geoJSON(feature);
        }}
        if (!layer) layer = findLayer(name);
        if (!layer && !VISUAL_CENTERS[name]) return null;
        return getVisualCenter(name, layer);
    }}

    function dedupeArrowData(rows) {{
        const out = [];
        const seen = new Set();
        (rows || []).forEach(row => {{
            if (!row || !row.start || !row.end) return;
            const key = [
                row.label || '',
                row.status || '',
                row.start.lat.toFixed(2),
                row.start.lng.toFixed(2),
                row.end.lat.toFixed(2),
                row.end.lng.toFixed(2)
            ].join('|');
            if (seen.has(key)) return;
            seen.add(key);
            out.push(row);
        }});
        return out;
    }}

    function getArrowsForCountry(sourceName, rivalries) {{
        if (!sourceName || !rivalries || rivalries.length === 0) return [];
        const sourceCenter = resolveConflictPoint(sourceName, null);
        if (!sourceCenter) return [];

        const arrowData = [];
        rivalries.forEach(rivalItem => {{
            const rivalName = (typeof rivalItem === 'object') ? rivalItem.rival : rivalItem;
            const conflictText = (typeof rivalItem === 'object') ? rivalItem.text : null;
            const status = (typeof rivalItem === 'object') ? (rivalItem.status || 'active') : 'active';
            const targetAnchor = (typeof rivalItem === 'object') ? rivalItem.target_anchor : null;
            const targetCenter = resolveConflictPoint(rivalName, targetAnchor);
            if (sourceCenter && targetCenter) {{
                arrowData.push({{
                    start: sourceCenter,
                    end: targetCenter,
                    label: conflictText,
                    status: status
                }});
            }}
        }});
        return dedupeArrowData(arrowData);
    }}

    function getArrowsForConflict(conflict, focusCountry = '') {{
        if (!conflict || !Array.isArray(conflict.links)) return [];
        const participants = Array.isArray(conflict.participants) ? conflict.participants : [];
        const arrows = [];
        conflict.links.forEach(link => {{
            if (!link || !link.source) return;
            if (focusCountry) {{
                const touchesFocus = [link.source, link.target].some(name => String(name || '').trim() === focusCountry);
                if (!touchesFocus && !participants.includes(focusCountry)) return;
            }}
            const start = resolveConflictPoint(link.source, link.source_anchor);
            const end = resolveConflictPoint(link.target, link.target_anchor);
            if (!start || !end) return;
            arrows.push({{
                start: start,
                end: end,
                label: link.label || conflict.label,
                status: link.status || conflict.status || 'active'
            }});
        }});
        return dedupeArrowData(arrows);
    }}

    function drawCountryConflicts(countryName, conflicts) {{
        if (!window.geoMap) return;
        window._lastArrowCountry = countryName;
        window._lastArrowRivalries = null;
        window._lastArrowConflictId = '';
        window.activeCountrySelection = countryName;

        if (!window.showConflictArrows) {{
            if (window.hoi4Layer) window.hoi4Layer.setArrows([]);
            return;
        }}

        let arrows = [];
        (conflicts || []).forEach(conflict => {{
            arrows = arrows.concat(getArrowsForConflict(conflict, countryName));
        }});
        if (window.hoi4Layer) window.hoi4Layer.setArrows(dedupeArrowData(arrows));
    }}

    function showConflictOnMap(conflictId, focusCountry = '') {{
        const conflict = activeConflicts.find(item => item.id === conflictId);
        if (!conflict || !window.hoi4Layer) return;
        window._lastArrowConflictId = conflictId;
        window._lastArrowCountry = focusCountry || '';
        window._lastArrowRivalries = null;
        if (!window.showConflictArrows) {{
            window.hoi4Layer.setArrows([]);
            return;
        }}
        const arrows = getArrowsForConflict(conflict, focusCountry || '');
        window.hoi4Layer.setArrows(dedupeArrowData(arrows));
    }}

    function drawRivalryArrows(sourceName, rivalries) {{
        if (!window.geoMap) return;
        if (!window.arrowLayers) window.arrowLayers = [];
        window.arrowLayers.forEach(l => window.geoMap.removeLayer(l));
        window.arrowLayers = [];
        
        window._lastArrowCountry = sourceName;
        window._lastArrowRivalries = rivalries;
        window._lastArrowConflictId = '';
        window.activeCountrySelection = sourceName;

        if (!window.showConflictArrows) {{
            if (window.hoi4Layer) window.hoi4Layer.setArrows([]);
            return;
        }}
        
        const data = getArrowsForCountry(sourceName, rivalries);
        window.hoi4Layer.setArrows(dedupeArrowData(data));
    }}

    function drawGlobalActiveArrows() {{
        if (!window.showConflictArrows) return;
        if (window.activeCountrySelection) return;

        let allArrows = [];
        if (activeConflicts.length > 0) {{
            activeConflicts.forEach(conflict => {{
                if ((conflict.status || 'active') !== 'historical') {{
                    allArrows = allArrows.concat(getArrowsForConflict(conflict));
                }}
            }});
        }} else if (window.countryMeta) {{
            Object.keys(window.countryMeta).forEach(country => {{
                 const meta = window.countryMeta[country];
                 if (meta.rivalries) {{
                     const active = meta.rivalries.filter(r => r.status !== 'historical');
                     if (active.length > 0) {{
                         allArrows = allArrows.concat(getArrowsForCountry(country, active));
                     }}
                 }}
            }});
        }}
        if (window.hoi4Layer) window.hoi4Layer.setArrows(dedupeArrowData(allArrows));
    }}
    window.drawGlobalActiveArrows = drawGlobalActiveArrows;
    window.showConflictOnMap = showConflictOnMap;



// --- Elegant Arrow Implementation ---

function drawElegantArrow(ctx, screenPts, opts) {{
  const {{
    color = "rgba(231, 76, 60, 0.85)",
    glowColor = "rgba(231, 76, 60, 0.3)",
    width = 3,
    label = "",
    isHistorical = false,
    dashPattern = null,
    pulsePhase = 0,
    curveOffset = 0,
  }} = opts;

  const startP = screenPts[0];
  const endP = screenPts[screenPts.length - 1];
  
  const dx = endP.x - startP.x, dy = endP.y - startP.y;
  const totalLen = Math.sqrt(dx*dx + dy*dy);
  if (totalLen < 20) return;
  const headSize = isHistorical ? 8 : 12;

  // Calculate control point for Bézier curve (perpendicular offset)
  const midX = (startP.x + endP.x) / 2;
  const midY = (startP.y + endP.y) / 2;
  const perpX = -dy / totalLen;
  const perpY = dx / totalLen;
  const cpX = midX + perpX * curveOffset;
  const cpY = midY + perpY * curveOffset;

  // Shorten end to leave room for arrowhead
  // For curves, compute the tangent at t=1 for arrowhead direction
  const t = 0.98;
  const nearEndX = (1-t)*(1-t)*startP.x + 2*(1-t)*t*cpX + t*t*endP.x;
  const nearEndY = (1-t)*(1-t)*startP.y + 2*(1-t)*t*cpY + t*t*endP.y;
  const tangentDx = endP.x - nearEndX;
  const tangentDy = endP.y - nearEndY;
  const tangentLen = Math.sqrt(tangentDx*tangentDx + tangentDy*tangentDy) || 1;
  const shortenedEnd = {{
    x: endP.x - (tangentDx / tangentLen) * headSize,
    y: endP.y - (tangentDy / tangentLen) * headSize
  }};
  // Adjusted control point for shortened curve
  const sCpX = cpX;
  const sCpY = cpY;

  ctx.save();
  ctx.lineJoin = "round";
  ctx.lineCap = "round";

  // Glow effect for active arrows
  if (!isHistorical) {{
    const glowIntensity = 0.25 + 0.15 * Math.sin(pulsePhase);
    ctx.shadowColor = glowColor;
    ctx.shadowBlur = 12 + 4 * Math.sin(pulsePhase);
    ctx.strokeStyle = color.replace(/[\d.]+\)$/, glowIntensity + ')');
    ctx.lineWidth = width + 6;
    ctx.beginPath();
    ctx.moveTo(startP.x, startP.y);
    ctx.quadraticCurveTo(sCpX, sCpY, shortenedEnd.x, shortenedEnd.y);
    ctx.stroke();
    ctx.shadowBlur = 0;
    ctx.shadowColor = 'transparent';
  }}

  // Main line
  ctx.strokeStyle = color;
  ctx.lineWidth = width;
  if (dashPattern) {{
    ctx.setLineDash(dashPattern);
  }} else {{
    ctx.setLineDash([]);
  }}
  ctx.beginPath();
  ctx.moveTo(startP.x, startP.y);
  ctx.quadraticCurveTo(sCpX, sCpY, shortenedEnd.x, shortenedEnd.y);
  ctx.stroke();
  ctx.setLineDash([]);

  // Arrowhead direction: use tangent at curve end
  const headFrom = {{ x: nearEndX, y: nearEndY }};
  drawElegantArrowHead(ctx, headFrom, endP, headSize, color, isHistorical);

  ctx.restore();

  // Label at curve midpoint (t=0.5 on the Bézier)
  if (label) {{
    const labelPt = {{
      x: 0.25*startP.x + 0.5*cpX + 0.25*endP.x,
      y: 0.25*startP.y + 0.5*cpY + 0.25*endP.y
    }};
    drawElegantLabel(ctx, screenPts, label, isHistorical, labelPt);
  }}
}}

function drawElegantArrowHead(ctx, a, b, size, color, isHistorical) {{
  const dx = b.x - a.x, dy = b.y - a.y;
  const ang = Math.atan2(dy, dx);
  const spread = isHistorical ? 0.35 : 0.4;

  const left = {{
    x: b.x - size * Math.cos(ang - spread),
    y: b.y - size * Math.sin(ang - spread),
  }};
  const right = {{
    x: b.x - size * Math.cos(ang + spread),
    y: b.y - size * Math.sin(ang + spread),
  }};

  ctx.beginPath();
  ctx.moveTo(b.x, b.y);
  ctx.lineTo(left.x, left.y);
  ctx.lineTo(right.x, right.y);
  ctx.closePath();

  ctx.fillStyle = color;
  ctx.fill();
}}

function drawElegantLabel(ctx, pts, text, isHistorical, customMid) {{
  const startP = pts[0];
  const endP = pts[pts.length - 1];
  const ang = Math.atan2(endP.y - startP.y, endP.x - startP.x);

  const trueMid = customMid || {{
    x: (startP.x + endP.x) / 2,
    y: (startP.y + endP.y) / 2
  }};

  let drawAngle = ang;
  if (drawAngle > Math.PI / 2 || drawAngle < -Math.PI / 2) {{
    drawAngle += Math.PI;
  }}

  ctx.save();
  ctx.translate(trueMid.x, trueMid.y);
  ctx.rotate(drawAngle);

  const fontSize = isHistorical ? 10 : 11;
  ctx.font = `${{isHistorical ? '500' : '600'}} ${{fontSize}}px 'Inter', 'Segoe UI', sans-serif`;
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";

  const metrics = ctx.measureText(text);
  const textW = metrics.width;
  const px = 6, py = 4;
  const yOff = -14;
  const radius = 4;

  // Rounded rect background
  const x = -textW / 2 - px;
  const y = yOff - fontSize / 2 - py;
  const w = textW + px * 2;
  const h = fontSize + py * 2;

  ctx.fillStyle = isHistorical ? "rgba(40, 44, 52, 0.8)" : "rgba(30, 39, 46, 0.92)";
  ctx.beginPath();
  ctx.moveTo(x + radius, y);
  ctx.lineTo(x + w - radius, y);
  ctx.quadraticCurveTo(x + w, y, x + w, y + radius);
  ctx.lineTo(x + w, y + h - radius);
  ctx.quadraticCurveTo(x + w, y + h, x + w - radius, y + h);
  ctx.lineTo(x + radius, y + h);
  ctx.quadraticCurveTo(x, y + h, x, y + h - radius);
  ctx.lineTo(x, y + radius);
  ctx.quadraticCurveTo(x, y, x + radius, y);
  ctx.closePath();
  ctx.fill();

  // Text
  ctx.fillStyle = isHistorical ? "rgba(190, 195, 200, 0.9)" : "#f1f2f6";
  ctx.fillText(text, 0, yOff);
  ctx.restore();
}}

// New Helper: Draw Single Arrow on Demand
function drawSingleArrow(sourceName, rivalName) {{
    console.log("Drawing single arrow:", sourceName, "->", rivalName);
    if (!window.countryMeta) return;
    const meta = window.countryMeta[sourceName];
    if (!meta || !meta.rivalries) return;
    
    const target = meta.rivalries.find(r => r.rival === rivalName);
    if (target) {{
        // Reset/Draw only this arrow
        drawRivalryArrows(sourceName, [target]);
    }}
}}

// --- Custom Overlay Layer with Smooth Animations ---
L.Hoi4Overlay = L.Layer.extend({{
    initialize: function() {{
        this._arrows = [];
        this._animationFrame = null;
        this._debounceTimer = null;
        this._isMoving = false;
        this._pulsePhase = 0;
        this._animating = false;
    }},
    
    onAdd: function(map) {{
        this._map = map;
        this._canvas = L.DomUtil.create('canvas', 'hoi4-canvas');
        this._canvas.style.position = 'absolute';
        this._canvas.style.top = 0;
        this._canvas.style.left = 0;
        this._canvas.style.pointerEvents = 'none';
        this._canvas.style.zIndex = 500;
        this._canvas.style.opacity = 0;
        this._canvas.style.transition = 'opacity 0.5s cubic-bezier(0.4, 0, 0.2, 1)';
        
        map.getPanes().overlayPane.appendChild(this._canvas);
        
        map.on('movestart zoomstart', this._onMoveStart, this);
        map.on('moveend zoomend viewreset', this._onMoveEnd, this);
        
        this._updateCanvas();
        this._drawArrows();
    }},
    
    onRemove: function(map) {{
        if (this._debounceTimer) clearTimeout(this._debounceTimer);
        this._stopPulse();
        map.getPanes().overlayPane.removeChild(this._canvas);
        map.off('movestart zoomstart', this._onMoveStart, this);
        map.off('moveend zoomend viewreset', this._onMoveEnd, this);
    }},
    
    setArrows: function(arrows) {{
        this._arrows = arrows;
        if (!this._isMoving) {{
            this._updateCanvas();
            this._drawArrows();
            this._canvas.style.opacity = 1;
            // Start pulse animation if there are active arrows
            const hasActive = arrows.some(a => a.status !== 'historical');
            if (hasActive) {{
                this._startPulse();
            }} else {{
                this._stopPulse();
            }}
        }}
    }},
    
    _onMoveStart: function() {{
        this._isMoving = true;
        this._canvas.style.opacity = 0;
        this._stopPulse();
        if (this._debounceTimer) {{
            clearTimeout(this._debounceTimer);
            this._debounceTimer = null;
        }}
    }},
    
    _onMoveEnd: function() {{
        if (this._debounceTimer) clearTimeout(this._debounceTimer);
        this._debounceTimer = setTimeout(() => {{
            this._isMoving = false;
            this._updateCanvas();
            this._drawArrows();
            this._canvas.style.opacity = 1;
            const hasActive = this._arrows.some(a => a.status !== 'historical');
            if (hasActive) this._startPulse();
        }}, 350);
    }},
    
    _startPulse: function() {{
        if (this._animating) return;
        this._animating = true;
        const self = this;
        function tick() {{
            if (!self._animating) return;
            self._pulsePhase += 0.04;
            self._drawArrows();
            self._animationFrame = requestAnimationFrame(tick);
        }}
        tick();
    }},
    
    _stopPulse: function() {{
        this._animating = false;
        if (this._animationFrame) {{
            cancelAnimationFrame(this._animationFrame);
            this._animationFrame = null;
        }}
    }},
    
    _updateCanvas: function() {{
        if (!this._map) return;
        const size = this._map.getSize();
        const dpr = window.devicePixelRatio || 1;
        
        this._canvas.width = size.x * dpr;
        this._canvas.height = size.y * dpr;
        this._canvas.style.width = size.x + 'px';
        this._canvas.style.height = size.y + 'px';
        
        const topLeft = this._map.containerPointToLayerPoint([0, 0]);
        L.DomUtil.setPosition(this._canvas, topLeft);
    }},
    
    _drawArrows: function() {{
        if (!this._map) return;
        const size = this._map.getSize();
        const dpr = window.devicePixelRatio || 1;
        
        const ctx = this._canvas.getContext('2d');
        ctx.setTransform(1, 0, 0, 1, 0, 0);
        ctx.scale(dpr, dpr);
        ctx.clearRect(0, 0, size.x, size.y);
        
        const phase = this._pulsePhase || 0;
        
        // Compute curve offsets for arrows sharing the same endpoints
        const pairCounts = {{}};
        const pairIndices = {{}};
        this._arrows.forEach((arrow, i) => {{
            // Create a consistent key for each pair (sort lat/lng)
            const sKey = arrow.start.lat.toFixed(4) + ',' + arrow.start.lng.toFixed(4);
            const eKey = arrow.end.lat.toFixed(4) + ',' + arrow.end.lng.toFixed(4);
            const pairKey = sKey < eKey ? sKey + '|' + eKey : eKey + '|' + sKey;
            if (!pairCounts[pairKey]) pairCounts[pairKey] = [];
            pairCounts[pairKey].push(i);
        }});
        // Assign offset: for N arrows in same pair, spread from -(N-1)/2 to +(N-1)/2
        const offsets = new Array(this._arrows.length).fill(0);
        Object.values(pairCounts).forEach(indices => {{
            if (indices.length <= 1) return;
            const n = indices.length;
            indices.forEach((idx, j) => {{
                offsets[idx] = (j - (n - 1) / 2) * 50;
            }});
        }});
        
        // Draw historical (passive) arrows first (behind)
        this._arrows.forEach((arrow, i) => {{
            if (arrow.status !== 'historical') return;
            const p1 = this._map.latLngToContainerPoint(arrow.start);
            const p2 = this._map.latLngToContainerPoint(arrow.end);
            drawElegantArrow(ctx, [p1, p2], {{
                color: "rgba(140, 150, 160, 0.35)",
                glowColor: "transparent",
                width: 2,
                label: arrow.label,
                isHistorical: true,
                dashPattern: [8, 6],
                pulsePhase: 0,
                curveOffset: offsets[i],
            }});
        }});
        
        // Draw active arrows on top
        this._arrows.forEach((arrow, i) => {{
            if (arrow.status === 'historical') return;
            const p1 = this._map.latLngToContainerPoint(arrow.start);
            const p2 = this._map.latLngToContainerPoint(arrow.end);
            drawElegantArrow(ctx, [p1, p2], {{
                color: "rgba(231, 76, 60, 0.9)",
                glowColor: "rgba(231, 76, 60, 0.35)",
                width: 3.5,
                label: arrow.label,
                isHistorical: false,
                dashPattern: null,
                pulsePhase: phase,
                curveOffset: offsets[i],
            }});
        }});
    }}
}});


</script>
'''
        
        # Injection of data
        inject_script += f'''
<script>
window.countryMeta = window.countryMeta || countryMeta;
window.countryIsoMap = {{
    "Turkiye": "tr", "Türkiye": "tr", "Almanya": "de", "Rusya": "ru", "Ukrayna": "ua", 
    "Fransa": "fr", "Birleşik Krallık": "gb", "ABD": "us", "Çin": "cn",
    "Misir": "eg", "Libya": "ly", "Tunus": "tn", "Cezayir": "dz", "Fas": "ma",
    "Yunanistan": "gr", "Bulgaristan": "bg", "Sırbistan": "rs", "Hırvatistan": "hr",
    "Bosna Hersek": "ba", "Karadağ": "me", "Kosova": "xk", "Makedonya": "mk",
    "Arnavutluk": "al", "Romanya": "ro", "Polonya": "pl", "İtalya": "it",
    "İspanya": "es", "Portekiz": "pt", "Hollanda": "nl", "Belçika": "be",
    "Avusturya": "at", "Macaristan": "hu", "Çekya": "cz", "Slovakya": "sk",
    "İsveç": "se", "Norveç": "no", "Danimarka": "dk", "Finlandiya": "fi",
    "İran": "ir", "Irak": "iq", "Suriye": "sy", "Lübnan": "lb", "Ürdün": "jo",
    "İsrail": "il", "Filistin": "ps", "Suudi Arabistan": "sa", "Yemen": "ye",
    "Umman": "om", "BAE": "ae", "Katar": "qa", "Kuveyt": "kw", "Bahreyn": "bh",
    "Azerbaycan": "az", "Ermenistan": "am", "Gürcistan": "ge",
    "Hindistan": "in", "Pakistan": "pk", "Japonya": "jp", "Güney Kore": "kr", "Kuzey Kore": "kp",
    "Malavi": "mw", "Benin": "bj", "Togo": "tg", "Gana": "gh", "Fildisi Sahili": "ci",
    "Liberya": "lr", "Sierra Leone": "sl", "Gine": "gn", "Gine-Bissau": "gw",
    "Gambiya": "gm", "Senegal": "sn", "Mali": "ml", "Moritanya": "mr",
    "Nijer": "ne", "Nijerya": "ng", "Çad": "td", "Kamerun": "cm",
    "Orta Afrika Cumhuriyeti": "cf", "Ekvator Ginesi": "gq", "Gabon": "ga",
    "Kongo": "cg", "Demokratik Kongo Cumhuriyeti": "cd", "Angola": "ao",
    "Namibya": "na", "Guney Afrika": "za", "Lesoto": "ls", "Esvatini": "sz",
    "Botsvana": "bw", "Zambiya": "zm", "Zimbabve": "zw", "Mozambik": "mz",
    "Madagaskar": "mg", "Komorlar": "km", "Seyseller": "sc", "Mauritius": "mu",
    "Cibuti": "dj", "Eritre": "er", "Etiyopya": "et", "Somali": "so",
    "Kenya": "ke", "Uganda": "ug", "Ruanda": "rw", "Burundi": "bi",
    "Tanzanya": "tz", "Guney Sudan": "ss", "Sudan": "sd", "Yesil Burun Adalari": "cv",
    "Sao Tome ve Principe": "st", "Burkina Faso": "bf",
    "Kanada": "ca", "Brezilya": "br", "Arjantin": "ar", "Meksika": "mx",
    "Kolombiya": "co", "Venezuela": "ve", "Sili": "cl", "Peru": "pe",
    "Ekvador": "ec", "Bolivya": "bo", "Kuba": "cu", "Jamaika": "jm",
    "Haiti": "ht", "Dominik Cumhuriyeti": "do", "Endonezya": "id",
    "Malezya": "my", "Filipinler": "ph", "Vietnam": "vn", "Tayland": "th",
    "Myanmar": "mm", "Kambocya": "kh", "Laos": "la", "Mogolistan": "mn",
    "Avustralya": "au", "Yeni Zelanda": "nz", "Isvicre": "ch", "Isvec": "se",
    "Norvec": "no", "Izlanda": "is", "Belcika": "be", "Avusturya": "at",
    "Surinam": "sr", "Guyana": "gy", "Uruguay": "uy", "Paraguay": "py"
}};
</script>
'''

        # -- Share FAB + Analytics + Service Worker --
        share_analytics_html = '''
<!-- Share FAB -->
<style>
.share-fab {
    position: fixed; bottom: 24px; right: 24px; z-index: 9500;
    display: flex; flex-direction: column-reverse; align-items: center; gap: 10px;
}
.share-fab-btn {
    width: 52px; height: 52px; border-radius: 50%; border: none; cursor: pointer;
    display: flex; align-items: center; justify-content: center;
    background: rgba(26,26,46,0.85); backdrop-filter: blur(12px);
    box-shadow: 0 4px 20px rgba(0,0,0,0.4); transition: all 0.3s;
    color: #fff; font-size: 20px;
}
.share-fab-btn:hover { transform: scale(1.12); background: rgba(52,152,219,0.9); }
.share-fab-btn.main-share { background: linear-gradient(135deg, #3498db, #2ecc71); width: 56px; height: 56px; font-size: 22px; }
.share-fab-options { display: none; flex-direction: column-reverse; gap: 8px; }
.share-fab.open .share-fab-options { display: flex; }
.share-fab-btn svg { width: 22px; height: 22px; fill: currentColor; }

/* Embed modal */
.embed-modal {
    display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%;
    z-index: 9999; background: rgba(0,0,0,0.7); align-items: center; justify-content: center;
}
.embed-modal.show { display: flex; }
.embed-modal-content {
    background: #1a1a2e; border: 1px solid rgba(255,255,255,0.1); border-radius: 12px;
    padding: 24px; max-width: 500px; width: 90%; color: #fff;
}
.embed-modal-content h3 { margin: 0 0 12px; font-size: 16px; }
.embed-modal-content textarea {
    width: 100%; height: 80px; background: #0d0d1a; color: #3498db; border: 1px solid rgba(255,255,255,0.1);
    border-radius: 8px; padding: 10px; font-family: monospace; font-size: 12px; resize: none;
}
.embed-modal-content button {
    margin-top: 10px; padding: 8px 20px; background: #3498db; color: #fff; border: none;
    border-radius: 6px; cursor: pointer; font-weight: 600;
}
.embed-modal-content .close-embed { background: transparent; color: #999; float: right; }
</style>

<div class="share-fab" id="shareFab">
    <button class="share-fab-btn main-share" onclick="document.getElementById('shareFab').classList.toggle('open')" title="Paylaş">
        <svg viewBox="0 0 24 24"><path d="M18 16.08c-.76 0-1.44.3-1.96.77L8.91 12.7c.05-.23.09-.46.09-.7s-.04-.47-.09-.7l7.05-4.11c.54.5 1.25.81 2.04.81 1.66 0 3-1.34 3-3s-1.34-3-3-3-3 1.34-3 3c0 .24.04.47.09.7L8.04 9.81C7.5 9.31 6.79 9 6 9c-1.66 0-3 1.34-3 3s1.34 3 3 3c.79 0 1.5-.31 2.04-.81l7.12 4.16c-.05.21-.08.43-.08.65 0 1.61 1.31 2.92 2.92 2.92s2.92-1.31 2.92-2.92-1.31-2.92-2.92-2.92z"/></svg>
    </button>
    <div class="share-fab-options">
        <button class="share-fab-btn" onclick="shareTwitter()" title="X/Twitter" style="background:rgba(0,0,0,0.8)">
            <svg viewBox="0 0 24 24"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>
        </button>
        <button class="share-fab-btn" onclick="shareWhatsApp()" title="WhatsApp" style="background:rgba(37,211,102,0.8)">
            <svg viewBox="0 0 24 24"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/></svg>
        </button>
        <button class="share-fab-btn" onclick="shareTelegram()" title="Telegram" style="background:rgba(38,166,224,0.8)">
            <svg viewBox="0 0 24 24"><path d="M11.944 0A12 12 0 000 12a12 12 0 0012 12 12 12 0 0012-12A12 12 0 0012 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 01.171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.479.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z"/></svg>
        </button>
        <button class="share-fab-btn" onclick="shareEmbed()" title="Embed Kodu" style="background:rgba(155,89,182,0.8)">
            <svg viewBox="0 0 24 24"><path d="M9.4 16.6L4.8 12l4.6-4.6L8 6l-6 6 6 6zm5.2 0L19.2 12l-4.6-4.6L16 6l6 6-6 6z"/></svg>
        </button>
    </div>
</div>

<!-- Embed Modal -->
<div class="embed-modal" id="embedModal">
    <div class="embed-modal-content">
        <button class="close-embed" onclick="document.getElementById('embedModal').classList.remove('show')">&times;</button>
        <h3>Siteye Göm</h3>
        <textarea id="embedCode" readonly>&lt;iframe src="https://jeopolitik.com.tr/" width="100%" height="600" frameborder="0" style="border-radius:12px;box-shadow:0 4px 24px rgba(0,0,0,0.3);" allowfullscreen&gt;&lt;/iframe&gt;</textarea>
        <button onclick="navigator.clipboard.writeText(document.getElementById('embedCode').value);this.textContent='Kopyalandı!'">Kopyala</button>
    </div>
</div>

<script>
const SITE_URL = "https://jeopolitik.com.tr/";
const SITE_TITLE = "Jeopolitik Tarih Haritası - Son 100 Yılın Dünya Olayları";
const SITE_DESC = "3900+ olay, 138 ülke, 13 gösterge ile interaktif jeopolitik harita.";

function shareTwitter() {
    window.open("https://x.com/intent/tweet?text=" + encodeURIComponent(SITE_TITLE) + "&url=" + encodeURIComponent(SITE_URL), "_blank");
}
function shareWhatsApp() {
    window.open("https://wa.me/?text=" + encodeURIComponent(SITE_TITLE + " " + SITE_URL), "_blank");
}
function shareTelegram() {
    window.open("https://t.me/share/url?url=" + encodeURIComponent(SITE_URL) + "&text=" + encodeURIComponent(SITE_TITLE), "_blank");
}
function shareEmbed() {
    document.getElementById("embedModal").classList.add("show");
    document.getElementById("shareFab").classList.remove("open");
}

// Service Worker Registration
if ("serviceWorker" in navigator) {
    navigator.serviceWorker.register("/sw.js").catch(function(){});
}
</script>

<!-- Plausible Analytics (privacy-friendly, no cookies) -->
<script defer data-domain="jeopolitik.com.tr" src="https://plausible.io/js/script.js"></script>
'''

        # Folium places </body> BEFORE its scripts. 
        # By removing Folium's original </body> and appending ours right before </html>, 
        # we ensure ALL script tags (both Folium's and ours) are inside the <body>.
        html = html.replace('</body>', inject_script + share_analytics_html)
        html = html.replace('</html>', '</body>\n</html>')

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Create geopolitical history map')
    parser.add_argument('--data', '-d', help='Path to events.json')
    parser.add_argument('--output', '-o', help='Output HTML file')
    args = parser.parse_args()

    geo_map = GeopoliticalMap(data_path=args.data)
    geo_map.create_map(output_path=args.output)


if __name__ == "__main__":
    main()
