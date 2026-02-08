#!/usr/bin/env python3
"""
Geopolitical History Map - Interactive world map showing major events from the last 100 years.
"""

import json
import os
from pathlib import Path
from typing import Dict, List

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

        # Load GeoJSON for country boundaries
        geojson_path = self.base_dir / "data" / "countries.geojson"
        self.geojson_data = None
        if geojson_path.exists():
            with open(geojson_path, 'r', encoding='utf-8') as f:
                self.geojson_data = json.load(f)
        if geojson_path.exists():
            with open(geojson_path, 'r', encoding='utf-8') as f:
                self.geojson_data = json.load(f)

        # Load Country Metadata
        metadata_path = self.base_dir / "data" / "country_metadata.json"
        self.country_metadata = {}
        if metadata_path.exists():
            with open(metadata_path, 'r', encoding='utf-8') as f:
                self.country_metadata = json.load(f)

        # Load Master Country Mappings
        mappings_path = self.base_dir / "data" / "country_mappings.json"
        self.country_mappings = []
        self.turkish_to_english = {}
        self.english_to_turkish = {}
        self.turkish_to_iso = {}
        if mappings_path.exists():
            with open(mappings_path, 'r', encoding='utf-8') as f:
                mappings_data = json.load(f)
                self.country_mappings = mappings_data.get('countries', [])
                # Build lookup dictionaries
                for c in self.country_mappings:
                    tr = c.get('turkish', '')
                    en = c.get('english', '')
                    iso = c.get('iso2', '')
                    aliases = c.get('aliases', [])
                    
                    if tr and en:
                        self.turkish_to_english[tr] = en
                        self.english_to_turkish[en] = tr
                    if tr and iso:
                        self.turkish_to_iso[tr] = iso
                    # Handle aliases
                    for alias in aliases:
                        if alias and en:
                            self.english_to_turkish[alias] = tr
                            self.turkish_to_english[alias] = en
                        if alias and iso:
                            self.turkish_to_iso[alias] = iso

        # Enrich events with video links
        for event in self.events:
            title = event.get('title', '')
            vid_id = self.VIDEO_MAPPINGS.get(title)
            
            if not vid_id:
                # Try substring matching (case insensitive)
                title_lower = title.lower()
                for key, vid in self.VIDEO_MAPPINGS.items():
                    if key.lower() in title_lower:
                        vid_id = vid
                        break
            
            if vid_id:
                event['youtube_video_id'] = vid_id

    def _get_custom_css_js(self) -> str:
        """Get custom CSS and JavaScript for the map."""
        events_json = json.dumps(self.events, ensure_ascii=False)
        categories_json = json.dumps(self.categories, ensure_ascii=False)
        geojson_json = json.dumps(self.geojson_data, ensure_ascii=False) if self.geojson_data else 'null'
        
        # Safe serialization for metadata
        country_metadata_json = json.dumps(self.country_metadata, ensure_ascii=False) if hasattr(self, 'country_metadata') else '{}'
        
        # Serialize master mappings for JavaScript
        turkish_to_english_json = json.dumps(self.turkish_to_english, ensure_ascii=False)
        english_to_turkish_json = json.dumps(self.english_to_turkish, ensure_ascii=False)
        turkish_to_iso_json = json.dumps(self.turkish_to_iso, ensure_ascii=False)

        return f'''
<meta charset="UTF-8">
<meta charset="UTF-8">
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

    /* Control Panel */
    .control-panel {{
        position: fixed;
        top: 10px;
        right: 10px;
        z-index: 1000;
        background: white;
        padding: 15px;
        border-radius: 12px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.15);
        max-height: 90vh;
        overflow-y: auto;
        width: 280px;
    }}
    .control-panel h3 {{
        margin: 0 0 12px 0;
        font-size: 16px;
        font-weight: 600;
        color: #2c3e50;
        border-bottom: 2px solid #3498db;
        padding-bottom: 8px;
    }}
    .control-section {{
        margin-bottom: 15px;
    }}
    .control-section h4 {{
        margin: 0 0 8px 0;
        font-size: 13px;
        font-weight: 500;
        color: #666;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }}
    .select-btns {{
        display: flex;
        gap: 5px;
    }}
    .select-btns button {{
        padding: 2px 8px;
        font-size: 10px;
        border: 1px solid #ddd;
        background: #f5f5f5;
        border-radius: 3px;
        cursor: pointer;
    }}
    .select-btns button:hover {{
        background: #e0e0e0;
    }}

    /* Decade checkboxes */
    .decade-grid {{
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 5px;
    }}
    .decade-item {{
        display: flex;
        align-items: center;
        gap: 4px;
        font-size: 12px;
        padding: 4px 6px;
        background: #f8f9fa;
        border-radius: 4px;
        cursor: pointer;
    }}
    .decade-item:hover {{
        background: #e9ecef;
    }}
    .decade-item input {{
        margin: 0;
    }}

    /* Category checkboxes */
    .category-list {{
        display: flex;
        flex-direction: column;
        gap: 5px;
    }}
    .category-item {{
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 12px;
        padding: 6px 8px;
        background: #f8f9fa;
        border-radius: 4px;
        cursor: pointer;
    }}
    .category-item:hover {{
        background: #e9ecef;
    }}
    .category-item input {{
        margin: 0;
    }}
    .category-color {{
        width: 14px;
        height: 14px;
        border-radius: 50%;
        flex-shrink: 0;
    }}

    /* Stats */
    .stats-box {{
        background: #f8f9fa;
        padding: 10px;
        border-radius: 8px;
        text-align: center;
    }}
    .stats-box .count {{
        font-size: 24px;
        font-weight: 700;
        color: #2c3e50;
    }}
    .stats-box .label {{
        font-size: 11px;
        color: #666;
    }}

    /* Country Sidebar */
    /* Country Sidebar - Left Side Slide-in */
    .country-sidebar {{
        position: fixed;
        top: 0;
        left: -420px; /* Hidden off-screen left */
        width: 420px;
        height: 100vh;
        background: #1e272e; /* Dark Military Grey */
        color: #ecf0f1;
        box-shadow: 2px 0 15px rgba(0,0,0,0.5);
        overflow-y: auto;
        z-index: 2000;
        transform: translateX(0); 
        transition: transform 0.35s cubic-bezier(0.175, 0.885, 0.32, 1.275); /* Smooth ease out back */
    }}
    .country-sidebar.open {{
        transform: translateX(420px);
    }}
    .sidebar-header {{
        padding: 20px;
        background: #2c3e50;
        color: white;
    }}
    .sidebar-header h2 {{
        margin: 0;
        font-size: 20px;
        font-weight: 600;
    }}
    .sidebar-header .event-count {{
        font-size: 13px;
        opacity: 0.8;
        margin-top: 5px;
    }}
    .close-sidebar {{
        /* Hidden - sidebar always open */
        display: none;
    }}
    .close-sidebar:hover {{
        opacity: 1;
    }}
    .sidebar-content {{
        flex: 1;
        overflow-y: auto;
        padding: 0;
    }}

    /* Timeline in sidebar */
    .decade-section {{
        border-bottom: 1px solid #333;
    }}
    .decade-header {{
        padding: 12px 20px;
        background: #2d3436;
        font-weight: 600;
        font-size: 14px;
        color: #ecf0f1;
        cursor: pointer;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-left: 3px solid #636e72;
    }}
    .decade-header:hover {{
        background: #353b48;
        border-left-color: #00cec9;
    }}
    .decade-header .count {{
        background: #0984e3;
        color: white;
        padding: 2px 8px;
        border-radius: 10px;
        font-size: 11px;
    }}
    .decade-events {{
        display: none;
        background: #1e272e;
    }}
    .decade-events.open {{
        display: block;
    }}
    .event-item {{
        padding: 15px 20px;
        border-bottom: 1px solid #333;
    }}
    .event-item:last-child {{
        border-bottom: none;
    }}
    .event-year {{
        font-size: 12px;
        color: #b2bec3;
        margin-bottom: 4px;
    }}
    .event-title {{
        font-weight: 600;
        font-size: 14px;
        color: #dfe6e9;
        margin-bottom: 6px;
    }}
    .event-category {{
        display: inline-block;
        padding: 2px 8px;
        border-radius: 10px;
        font-size: 10px;
        color: white;
        margin-bottom: 8px;
    }}
    .event-desc {{
        font-size: 12px;
        color: #bdc3c7;
        line-height: 1.5;
        margin-bottom: 8px;
    }}
    
    /* Metadata Card - Dark Theme */
    .country-meta-card {{
        margin: 15px;
        background: #2d3436;
        border-radius: 0;
        border: 1px solid #444;
        overflow: hidden;
    }}
    .country-meta-card summary {{
        padding: 10px 15px;
        cursor: pointer;
        font-weight: 600;
        color: #ced6e0;
        user-select: none;
        display: flex;
        align-items: center;
        justify-content: space-between;
        background: #353b48;
    }}
    .country-meta-card summary:hover {{ background: #3d4653; }}
    .country-meta-content {{
        padding: 15px;
        border-top: 1px solid #444;
        font-size: 13px;
        line-height: 1.5;
        color: #b2bec3;
    }}
    .meta-row {{ margin-bottom: 8px; }}
    .meta-label {{ color: #636e72; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; display: block; margin-bottom: 2px; }}

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
</style>

<!-- Sidebar always visible -->
<div class="country-sidebar" id="countrySidebar">
    <div class="sidebar-header">
        <h2 id="sidebarCountryName">Ülke</h2>
        <div class="event-count" id="sidebarEventCount">0 olay</div>
        <button class="close-sidebar" onclick="closeSidebar()">×</button>
    </div>
    <div id="countryMetaContainer"></div>
    <div class="sidebar-content" id="sidebarContent"></div>
</div>

<div class="control-panel">
    <h3>Jeopolitik Tarih Haritası</h3>

    <div class="instructions">
        Ülkeye tıklayın veya marker'a basın. Filtreleri kullanarak olayları daraltabilirsiniz.
    </div>

    <div class="control-section">
        <h4>
            Zaman Dilimi
            <div class="select-btns">
                <button onclick="selectAllDecades()">Tümü</button>
                <button onclick="selectNoDecades()">Hiçbiri</button>
            </div>
        </h4>
        <div class="decade-grid" id="decadeFilters"></div>
    </div>

    <div class="control-section">
        <h4>
            Kategoriler
            <div class="select-btns">
                <button onclick="selectAllCategories()">Tümü</button>
                <button onclick="selectNoCategories()">Hiçbiri</button>
            </div>
        </h4>
        <div class="category-list" id="categoryFilters"></div>
    </div>

    <div class="control-section">
        <h4>Özel Listeler</h4>
        <div class="category-list">
             <label class="category-item" style="background: #fffbe6; border: 1px solid #ffe58f;">
                <input type="checkbox" checked onchange="toggleSpecial('time_100')" id="special-time_100">
                <span class="category-color" style="background: #f1c40f; box-shadow: 0 0 5px #f1c40f;"></span>
                Time 100: Yüzyılın Kişileri
            </label>
        </div>
    </div>

    <div class="stats-box">
        <div class="count" id="visibleCount">0</div>
        <div class="label">görünen olay</div>
    </div>
</div>

<script>
// Data
const allEvents = {events_json};
const countryMeta = {country_metadata_json};
// Filter out special categories from standard list if needed, or handle in toggleCategory
const categories = {categories_json};
const decades = ['1920s', '1930s', '1940s', '1950s', '1960s', '1970s', '1980s', '1990s', '2000s', '2010s', '2020s'];

// State
let selectedDecades = new Set(decades);
// Initialize special list state
let showTime100 = true;
// Remove 'time_100' from standard categories set to avoid double toggle issues if it's there
let selectedCategories = new Set(Object.keys(categories).filter(c => c !== 'time_100'));

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

    const catContainer = document.getElementById('categoryFilters');
    Object.entries(categories).forEach(([key, cat]) => {{
        if (key === 'time_100') return; // Skip Time 100 in standard list
        const item = document.createElement('label');
        item.className = 'category-item';
        item.innerHTML = `
            <input type="checkbox" checked onchange="toggleCategory('${{key}}')" id="cat-${{key}}">
            <span class="category-color" style="background: ${{cat.color}}"></span>
            ${{cat.label}}
        `;
        catContainer.appendChild(item);
    }});

    updateVisibleCount();
}}

function toggleSpecial(type) {{
    if (type === 'time_100') {{
        showTime100 = !showTime100;
        updateVisibleCount();
        updateMarkerVisibility();
    }}
}}

function toggleDecade(decade) {{
    if (selectedDecades.has(decade)) {{
        selectedDecades.delete(decade);
    }} else {{
        selectedDecades.add(decade);
    }}
    updateVisibleCount();
    updateMarkerVisibility();
}}

function toggleCategory(category) {{
    if (selectedCategories.has(category)) {{
        selectedCategories.delete(category);
    }} else {{
        selectedCategories.add(category);
    }}
    updateVisibleCount();
    updateMarkerVisibility();
}}

function selectAllDecades() {{
    selectedDecades = new Set(decades);
    decades.forEach(d => document.getElementById('decade-' + d).checked = true);
    updateVisibleCount();
    updateMarkerVisibility();
}}

function selectNoDecades() {{
    selectedDecades.clear();
    decades.forEach(d => document.getElementById('decade-' + d).checked = false);
    updateVisibleCount();
    updateMarkerVisibility();
}}

function selectAllCategories() {{
    // Only select standard categories
    const standardCats = Object.keys(categories).filter(c => c !== 'time_100');
    selectedCategories = new Set(standardCats);
    standardCats.forEach(c => {{
        const el = document.getElementById('cat-' + c);
        if (el) el.checked = true;
    }});
    updateVisibleCount();
    updateMarkerVisibility();
}}

function selectNoCategories() {{
    selectedCategories.clear();
    Object.keys(categories).forEach(c => {{
        const el = document.getElementById('cat-' + c);
        if (el) el.checked = false;
    }});
    updateVisibleCount();
    updateMarkerVisibility();
}}

function updateVisibleCount() {{
    const count = allEvents.filter(e => {{
        // Special category handling
        if (e.category === 'time_100') {{
            return showTime100 && selectedDecades.has(e.decade);
        }}
        return selectedDecades.has(e.decade) && selectedCategories.has(e.category);
    }}).length;
    document.getElementById('visibleCount').textContent = count;
}}

// Track markers by country for filtering
const markersByCountry = {{}};

function updateMarkerVisibility() {{
    // Get filtered events by country
    const visibleCountries = new Set();
    
    allEvents.forEach(e => {{
        let isVisible = false;
        if (e.category === 'time_100') {{
            isVisible = showTime100 && selectedDecades.has(e.decade);
        }} else {{
            isVisible = selectedDecades.has(e.decade) && selectedCategories.has(e.category);
        }}
        
        if (isVisible) {{
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
    return allEvents.filter(e => {{
        const matchesCountry = e.country_name === countryName;
        let isVisible = false;
        if (e.category === 'time_100') {{
            isVisible = showTime100 && selectedDecades.has(e.decade);
        }} else {{
            isVisible = selectedDecades.has(e.decade) && selectedCategories.has(e.category);
        }}
        return matchesCountry && isVisible;
    }}).sort((a, b) => b.year - a.year);
}}

// Sidebar functions
// --- HELPER FUNCTIONS ---

function findCountryFeature(countryName) {{
    if (!window.geoMap) return null;
    let found = null;
    
    // 1. Try L.geoJSON layers if we have them accessibly
    // We didn't store them globally easily, but we have countriesGeoJSON data
    if (typeof countriesGeoJSON !== 'undefined' && countriesGeoJSON) {{
        countriesGeoJSON.features.forEach(f => {{
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

    // Special Case: Manual Overrides / Special Territories
    if (specialFlagUrls[countryName]) {{
        flagUrl = specialFlagUrls[countryName];
    }} 
    // Strategy A: Check countryCodeMap (name -> iso) which is the source of truth for this project
    else if (window.countryCodeMap && window.countryCodeMap[countryName]) {{
        flagCode = window.countryCodeMap[countryName];
    }}
    // Strategy B: Check Meta (if available) - converting 3-char code if needed
    else if (countryMeta[countryName] && countryMeta[countryName].code) {{
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
    else if (feature.properties && feature.properties['ISO3166-1-Alpha-2']) {{
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
function openSidebar(countryName) {{
    console.log("Opening sidebar for:", countryName);
    const countryEvents = getFilteredCountryEvents(countryName);
    console.log(`Found ${{countryEvents.length}} events for ${{countryName}}`); // DEBUG

    if (countryEvents.length === 0) {{
        console.log("No events found for", countryName);
    }}
    
    // Update Header
    const titleElem = document.getElementById('sidebarCountryName');
    if (titleElem) titleElem.innerText = countryName === 'Turkiye' ? 'Türkiye' : countryName;

    // 1. Highlight
    highlightCountryWithFlag(countryName);

    // 2. Open Sidebar UI
    const sidebar = document.getElementById('countrySidebar');
    sidebar.classList.add('open'); // Slide in
    
    document.getElementById('sidebarCountryName').textContent = countryName;
    document.getElementById('sidebarEventCount').textContent = countryEvents.length + ' olay';

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
    if (metaContainer && metaResult) {{
        const meta = metaResult.meta;
        const countryKey = metaResult.key; // Use the key that matched for arrow drawing
        metaContainer.innerHTML = `
            <details class="country-meta-card" open>
                <summary>
                    <span>▼ İstihbarat Raporu</span>
                </summary>
                <div class="country-meta-content">
                    <div class="meta-row">
                        <span class="meta-label">Önceki Rejim</span>
                        <div>${{meta.predecessor || '-'}}</div>
                    </div>
                     ${{
                        (meta.rivalries && meta.rivalries.length > 0)
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
                        <div class="meta-row" style="align-items:flex-start; margin-top:10px; border-top:1px dashed #444; padding-top:10px;">
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
        
        // 4. Draw Arrows
        if (meta.rivalries) {{
            drawRivalryArrows(countryKey, meta.rivalries);
        }} else if (window.hoi4Layer) {{
             window.hoi4Layer.setArrows([]);
        }}
    }} else {{
        if (metaContainer) metaContainer.innerHTML = '';
        if (window.hoi4Layer) window.hoi4Layer.setArrows([]);
    }}

    // 5. Render Events List
    const byDecade = {{}};
    countryEvents.forEach(e => {{
        if (!byDecade[e.decade]) byDecade[e.decade] = [];
        byDecade[e.decade].push(e);
    }});

    let html = '';
    decades.forEach(decade => {{
        if (byDecade[decade] && byDecade[decade].length > 0) {{
            // Render decade section...
            const events = byDecade[decade].sort((a, b) => a.year - b.year);
            html += `
                <div class="decade-section">
                    <div class="decade-header" onclick="toggleDecadeSection(this)">
                        ${{decade}}
                        <span class="count">${{events.length}}</span>
                    </div>
                    <div class="decade-events open">
            `;
            events.forEach(e => {{
                // Render event item...
                 const cat = categories[e.category] || {{}};
                 const videoHtml = e.youtube_video_id ? 
                    `<div class="video-container"><iframe src="https://www.youtube.com/embed/${{e.youtube_video_id}}?rel=0" allowfullscreen></iframe></div>` : '';
                 
                 html += `
                    <div class="event-item">
                        <div class="event-year">${{e.year}}</div>
                        <div class="event-title">${{e.title}}</div>
                        <div class="event-desc">${{e.description}}</div>
                         ${{videoHtml}}
                    </div>
                 `;
            }});
            html += '</div></div>';
        }}
    }});

    const sidebarContent = document.getElementById('sidebarContent');
    sidebarContent.innerHTML = html;
}}

// No closeSidebar function - sidebar always open
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


// GeoJSON country boundaries - inline embedded
const countriesGeoJSON = {geojson_json};
let highlightLayers = []; // Changed to array for multiple layers

// Log GeoJSON status
if (countriesGeoJSON) {{
    console.log('GeoJSON loaded inline:', countriesGeoJSON.features.length + ' countries');
}} else {{
    console.error('GeoJSON data not available');
}}

// GeoJSON name mapping (Turkish names -> English GeoJSON names)
// Dynamically generated from master country_mappings.json
const geoJSONNameMap = {turkish_to_english_json};

// Reverse mapping (English GeoJSON names -> Turkish canonical names)
// Also dynamically generated from master country_mappings.json
const reverseNameMap = {english_to_turkish_json};

// Find country feature in GeoJSON by name or code
function findCountryFeature(countryName) {{
    if (!countriesGeoJSON) {{
        console.error('GeoJSON not loaded!');
        return null;
    }}

    const countryCode = countryCodeMap[countryName];
    const geoJSONName = geoJSONNameMap[countryName] || countryName;

    console.log('Looking for:', countryName, '-> GeoJSON name:', geoJSONName, '-> ISO:', countryCode);

    const found = countriesGeoJSON.features.find(f => {{
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
}});

window.openSidebar = openSidebar;
window.getFilteredCountryEvents = getFilteredCountryEvents;
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
            '#3498db': 'blue'
        }
        color = color_map.get(cat.get('color', '#3498db'), 'blue')
        return folium.Icon(color=color, icon=icon, prefix='fa')

    def create_map(self, output_path: str = None) -> str:
        """Create the interactive geopolitical map."""
        output_path = output_path or self.output_dir / "geopolitical_map.html"

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
        
        # Post-process HTML to add marker tracking for filtering        
        self._inject_marker_tracking(output_path, by_country)

        print(f"Harita oluşturuldu: {output_path}")
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

// Initialize marker tracking
window.addEventListener('load', function() {{
    setTimeout(function() {{
        // Robustly find Leaflet map instance
        for (let key in window) {{
            if (window[key] && window[key] instanceof L.Map) {{
                window.geoMap = window[key];
                console.log("Found Leaflet Map instance:", key);
                break;
            }}
        }}

        if (!window.geoMap) {{
            console.error("Map instance not found in window properties!");
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

        if (typeof countriesGeoJSON !== 'undefined' && countriesGeoJSON) {{
            countriesGeoJSON.features.forEach(feature => {{
                const geoName = feature.properties.name || feature.properties.NAME;
                // Try to find Turkish name using global reverseNameMap, otherwise fallback to GeoJSON name
                let countryKey = reverseNameMap[geoName] || geoName;
                
                // Emergency Fix for Turkey/Romania mismatch & China ISO
                if (geoName === 'Turkey' || geoName === 'Republic of Turkey' || geoName === 'Türkiye') {{
                     countryKey = 'Turkiye'; // Match events.json exact spelling
                }}
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
                    L.DomEvent.stopPropagation(e); // Ensure it stops here
                }})
                .on('mouseout', function(e) {{
                    // Out: Remove Flag
                    if (window.clearCountryHighlight) {{
                        window.clearCountryHighlight();
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

    }}, 1500); // Wait for Folium to finish initialization
}});

// Visibility function directly using Leaflet API
function updateMarkerVisibility() {{
    if (!window.geoMap || !window.markerLayersByCountry) return;
    
    const visibleCountries = new Set();
    Object.entries(countryFilterData).forEach(([country, data]) => {{
        const hasVisibleDecade = data.decades.some(d => selectedDecades.has(d));
        const hasVisibleCategory = data.categories.some(c => selectedCategories.has(c));
        
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
}}

function drawRivalryArrows(sourceName, rivalries) {{
    if (!window.geoMap) return;
    if (!window.arrowLayers) window.arrowLayers = [];
    
    // Clear existing
    window.arrowLayers.forEach(l => window.geoMap.removeLayer(l));
    window.arrowLayers = [];

    // Valid inputs: expecting array of objects or strings (backward compat)
    if (!sourceName || !rivalries || rivalries.length === 0) return;

    // --- VISUAL CENTERS OVERRIDE ---
    // Fixes issues where centroid is far from the "action" (e.g. Russia -> Siberia)
    const VISUAL_CENTERS = {{
        // Russia -> Moscow/West
        "Russia": [55.75, 37.61],
        "Rusya": [55.75, 37.61],
        // USA -> Central/East (Kansas geographic center approx)
        "United States": [39.8, -98.5],
        "ABD": [39.8, -98.5],
        // France -> Metro
        "France": [46.6, 2.2],
        "Fransa": [46.6, 2.2],
        // UK
        "United Kingdom": [52.5, -1.0],
        "Birleşik Krallık": [52.5, -1.0],
        "Ingiltere": [52.5, -1.0],
        // China -> East/Populated
        "China": [32.0, 110.0],
        "Çin": [32.0, 110.0],
        "Cin": [32.0, 110.0],
        // Canada -> South
        "Canada": [50.0, -100.0],
        "Kanada": [50.0, -100.0],
        // Ukraine -> Central
        "Ukraine": [48.3794, 31.1656],
        "Ukrayna": [48.3794, 31.1656]
    }};

    // Helper to find layer
    function findLayer(name) {{
        let found = null;
        window.geoMap.eachLayer(function(layer) {{
            if (layer.feature && layer.feature.properties) {{
                const props = layer.feature.properties;
                // Check name matches
                if (props.NAME === name || props.NAME_LONG === name || 
                    (window.countryCodeMap && window.countryCodeMap[props.NAME] === name) ||
                    (window.countryMeta && window.countryMeta[name] && window.countryMeta[name].code === props.ISO_A3)) {{
                    found = layer;
                }}
            }}
        }});
        return found;
    }}

    // Helper to get Best Center
    function getVisualCenter(name, layer) {{
        // 1. Check override
        if (VISUAL_CENTERS[name]) {{
            return L.latLng(VISUAL_CENTERS[name]);
        }}
        // 2. Check override by finding key in VISUAL_CENTERS that matches
        // (Case insensitive check or mapped name check)
        // ... simplistic check:
        
        // 3. Fallback to bounds center
        if (layer) {{
            return layer.getBounds().getCenter();
        }}
        return null;
    }}

    // Find Source
    let sourceLayer = null;
    if (typeof window.findCountryFeature === 'function') {{
        const feature = window.findCountryFeature(sourceName);
        if (feature) sourceLayer = L.geoJSON(feature);
    }}
    if (!sourceLayer) sourceLayer = findLayer(sourceName);

    if (!sourceLayer && !VISUAL_CENTERS[sourceName]) {{
        console.warn("Source country layer not found for arrow:", sourceName);
        return;
    }}

    const sourceCenter = getVisualCenter(sourceName, sourceLayer);
    

    // Initialize arrow data
    const arrowData = [];
    
    // Loop through rivalries
    rivalries.forEach(rivalItem => {{
        // Handle both object and string format
        const rivalName = (typeof rivalItem === 'object') ? rivalItem.rival : rivalItem;
        const conflictText = (typeof rivalItem === 'object') ? rivalItem.text : null;

        let targetLayer = null;
        if (typeof window.findCountryFeature === 'function') {{
            const feature = window.findCountryFeature(rivalName);
            if (feature) targetLayer = L.geoJSON(feature);
        }}
        if (!targetLayer) targetLayer = findLayer(rivalName);

        // We can draw if we have a layer OR a visual center override
        const targetCenter = getVisualCenter(rivalName, targetLayer);

        if (sourceCenter && targetCenter) {{
            

            arrowData.push({{
                start: sourceCenter,
                end: targetCenter,
                label: conflictText
            }});
        }}
    }});
    
    // Update Draw Layer
    window.hoi4Layer.setArrows(arrowData);
}}

// --- HOI4 Canvas Arrow Implementation ---

function drawHoi4Arrow(ctx, screenPts, opts) {{
  const {{
    baseColor = "rgba(76,175,80,0.55)",
    stripeColor = "rgba(20,60,20,0.35)",
    outlineColor = "rgba(20,60,20,0.85)",
    width = 22,
    label = "",
  }} = opts;

  // 1) Outline
  ctx.lineJoin = "round";
  ctx.lineCap = "round";
  ctx.strokeStyle = outlineColor;
  ctx.lineWidth = width + 6;
  strokePolyline(ctx, screenPts);

  // 2) Base
  ctx.strokeStyle = baseColor;
  ctx.lineWidth = width;
  strokePolyline(ctx, screenPts);

  // 3) Stripes pattern
  const patternCanvas = document.createElement("canvas");
  patternCanvas.width = 24; patternCanvas.height = 24;
  const pctx = patternCanvas.getContext("2d");

  // diagonal stripes
  pctx.strokeStyle = stripeColor;
  pctx.lineWidth = 6;
  for (let i=-24; i<48; i+=12) {{
    pctx.beginPath();
    pctx.moveTo(i, 24);
    pctx.lineTo(i+24, 0);
    pctx.stroke();
  }}
  const pat = ctx.createPattern(patternCanvas, "repeat");
  ctx.strokeStyle = pat;
  ctx.lineWidth = width;
  strokePolyline(ctx, screenPts);

  // 4) Arrowhead at end
  const n = screenPts.length;
  if (n >= 2) {{
      const a = screenPts[n-2], b = screenPts[n-1];
      drawArrowHead(ctx, a, b, width, baseColor, outlineColor);
  }}

  // 5) Label at mid
  if (label) drawLabelOnPath(ctx, screenPts, label);
}}

function strokePolyline(ctx, pts) {{
  if (pts.length < 2) return;
  ctx.beginPath();
  ctx.moveTo(pts[0].x, pts[0].y);
  for (let i=1; i<pts.length; i++) ctx.lineTo(pts[i].x, pts[i].y);
  ctx.stroke();
}}

function drawArrowHead(ctx, a, b, width, fill, stroke) {{
  const dx = b.x - a.x, dy = b.y - a.y;
  const ang = Math.atan2(dy, dx);
  const len = Math.max(18, width * 1.5);

  const left = {{
    x: b.x - len*Math.cos(ang) + (len*0.6)*Math.cos(ang + Math.PI/2),
    y: b.y - len*Math.sin(ang) + (len*0.6)*Math.sin(ang + Math.PI/2),
  }};
  const right = {{
    x: b.x - len*Math.cos(ang) + (len*0.6)*Math.cos(ang - Math.PI/2),
    y: b.y - len*Math.sin(ang) + (len*0.6)*Math.sin(ang - Math.PI/2),
  }};

  ctx.beginPath();
  ctx.moveTo(b.x, b.y);
  ctx.lineTo(left.x, left.y);
  ctx.lineTo(right.x, right.y);
  ctx.closePath();

  ctx.fillStyle = fill;
  ctx.fill();
  ctx.strokeStyle = stroke;
  ctx.lineWidth = 2;
  ctx.stroke();
}}

function drawLabelOnPath(ctx, pts, text) {{
  const midIndex = Math.floor(pts.length * 0.5);
  const startP = pts[0];
  const endP = pts[pts.length-1];
  const ang = Math.atan2(endP.y - startP.y, endP.x - startP.x);
  
  const trueMid = {{
      x: (startP.x + endP.x) / 2,
      y: (startP.y + endP.y) / 2
  }};

  // Readability Flip
  let drawAngle = ang;
  if (drawAngle > Math.PI/2 || drawAngle < -Math.PI/2) {{
      drawAngle += Math.PI;
  }}

  ctx.save();
  ctx.translate(trueMid.x, trueMid.y);
  ctx.rotate(drawAngle);
  ctx.font = "bold 13px 'Oswald', sans-serif"; 
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";

  // Measure text for Ribbon
  const metrics = ctx.measureText(text);
  const textW = metrics.width;
  const padding = 8;
  const boxH = 22;
  const yOffset = -22;

  // Ribbon Background
  ctx.fillStyle = "rgba(30, 39, 46, 0.95)"; // Dark Military Grey
  ctx.fillRect(-textW/2 - padding, yOffset - boxH/2, textW + padding*2, boxH);
  
  // Ribbon Border
  ctx.lineWidth = 1;
  ctx.strokeStyle = "rgba(120, 140, 150, 0.8)";
  ctx.strokeRect(-textW/2 - padding, yOffset - boxH/2, textW + padding*2, boxH);

  // Text
  ctx.fillStyle = "#ecf0f1"; // Light Text
  ctx.fillText(text, 0, yOffset);
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
        this._opacity = 0;
        this._targetOpacity = 1;
        this._animationFrame = null;
        this._debounceTimer = null;
        this._isMoving = false;
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
        this._canvas.style.transition = 'opacity 0.4s ease-in-out';
        
        map.getPanes().overlayPane.appendChild(this._canvas);
        
        // Listen to movement events
        map.on('movestart zoomstart', this._onMoveStart, this);
        map.on('moveend zoomend viewreset', this._onMoveEnd, this);
        
        this._updateCanvas();
        this._drawArrows();
    }},
    
    onRemove: function(map) {{
        if (this._debounceTimer) clearTimeout(this._debounceTimer);
        if (this._animationFrame) cancelAnimationFrame(this._animationFrame);
        map.getPanes().overlayPane.removeChild(this._canvas);
        map.off('movestart zoomstart', this._onMoveStart, this);
        map.off('moveend zoomend viewreset', this._onMoveEnd, this);
    }},
    
    setArrows: function(arrows) {{
        this._arrows = arrows;
        // If not moving, draw and show immediately with fade
        if (!this._isMoving) {{
            this._updateCanvas();
            this._drawArrows();
            this._fadeInArrows();
        }}
    }},
    
    _onMoveStart: function() {{
        this._isMoving = true;
        // Hide arrows during movement for cleaner UX
        this._canvas.style.opacity = 0;
        if (this._debounceTimer) {{
            clearTimeout(this._debounceTimer);
            this._debounceTimer = null;
        }}
    }},
    
    _onMoveEnd: function() {{
        // Debounce: wait 400ms after movement stops before redrawing
        if (this._debounceTimer) clearTimeout(this._debounceTimer);
        
        this._debounceTimer = setTimeout(() => {{
            this._isMoving = false;
            this._updateCanvas();
            this._drawArrows();
            this._fadeInArrows();
        }}, 400);
    }},
    
    _fadeInArrows: function() {{
        // CSS transition handles the fade
        this._canvas.style.opacity = 1;
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
        ctx.setTransform(1, 0, 0, 1, 0, 0); // Reset transform
        ctx.scale(dpr, dpr);
        
        // Clear
        ctx.clearRect(0, 0, size.x, size.y);
        
        // Draw Arrows
        this._arrows.forEach(arrow => {{
            const p1 = this._map.latLngToContainerPoint(arrow.start);
            const p2 = this._map.latLngToContainerPoint(arrow.end);
            
            // Hoi4 Style Options based on status
            const isHistorical = arrow.status === 'historical';
            const opts = {{
                baseColor: isHistorical ? "rgba(120, 120, 120, 0.4)" : "rgba(60, 180, 75, 0.5)", 
                stripeColor: isHistorical ? "rgba(80, 80, 80, 0.3)" : "rgba(30, 90, 40, 0.4)",
                outlineColor: isHistorical ? "rgba(60, 60, 60, 0.8)" : "rgba(20, 60, 20, 0.9)",
                width: 14,
                label: arrow.label,
                glow: !isHistorical,
                dashed: isHistorical
            }};
            
            drawHoi4Arrow(ctx, [p1, p2], opts);
        }});
    }}
}});


</script>
'''
        
        # Injection of data
        inject_script += f'''
<script>
window.countryMeta = {json.dumps(self.country_metadata, ensure_ascii=False)};
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
        
        html = html.replace('</body>', inject_script + '</body>')
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)


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
