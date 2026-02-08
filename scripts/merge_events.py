#!/usr/bin/env python3
"""
Merge geopolitical events from CSV file with existing events.json
"""

import json
import csv
import os
from pathlib import Path
from typing import Dict, List


# Category mapping from Turkish to English keys
CATEGORY_MAP = {
    "Savaş/Çatışma": "war",
    "Savas/Catisma": "war",
    "Soykırım": "genocide",
    "Soykirim": "genocide",
    "Devrim/Rejim Değişikliği": "revolution",
    "Devrim/Rejim Degisikligi": "revolution",
    "Terör Saldırısı": "terror",
    "Teror Saldirisi": "terror",
    "Önemli Lider": "leader",
    "Onemli Lider": "leader"
}

# Approximate coordinates for countries not in the existing dataset
COUNTRY_COORDS = {
    "Birleşik Arap Emirlikleri": (24.4539, 54.3773),
    "Cezayir": (36.7538, 3.0588),
    "Fas": (33.9716, -6.8498),
    "Sudan": (15.5007, 32.5599),
    "Suudi Arabistan": (24.7136, 46.6753),
    "Tunus": (36.8065, 10.1815),
    "Yemen": (15.5527, 48.5164),
    "Ürdün": (31.9454, 35.9284),
    "Avustralya": (-25.2744, 133.7751),
    "Danimarka": (56.2639, 9.5018),
    "Finlandiya": (61.9241, 25.7482),
    "Norveç": (60.4720, 8.4689),
    "İsveç": (60.1282, 18.6435),
    "İzlanda": (64.9631, -19.0208),
    "Katar": (25.3548, 51.1839),
    "Kuveyt": (29.3117, 47.4818),
    "Libya": (26.3351, 17.2283),
    "Lübnan": (33.8547, 35.8623),
    # Added mappings for new CSVs (using verified existing coords or new correct ones)
    "ABD": (40.7128, -74.006),
    "Hindistan": (28.6139, 77.209),
    "Almanya": (52.52, 13.405),
    "Fransa": (48.8566, 2.3522),
    "Rusya": (55.7558, 37.6173),
    "Polonya": (52.2297, 21.0122),
    "Birleşik Krallık": (55.3781, -3.4360),
    "İspanya": (40.4168, -3.7038),
    "Güney Afrika": (-30.5595, 22.9375),
    "Küba": (21.5218, -77.7812),
    "Jamaika": (18.1096, -77.2975),
    "Trinidad ve Tobago": (10.6918, -61.2225),
    "Uganda": (1.3733, 32.2903),
    "İsrail": (31.0461, 34.8516)
}

# Country name normalization (English -> Turkish)
COUNTRY_NAME_MAP = {
    "South Africa": "Güney Afrika",
    "Egypt": "Mısır",
    "Morocco": "Fas",
    "Algeria": "Cezayir",
    "Greece": "Yunanistan",
    "Saudi Arabia": "Suudi Arabistan",
    "Iraq": "Irak",
    "Iran": "İran",
    "Syria": "Suriye",
    "Jordan": "Ürdün",
    "Lebanon": "Lübnan",
    "Estonia": "Estonya",
    "Latvia": "Letonya",
    "Lithuania": "Litvanya",
    "Belarus": "Belarus",
    "Kuwait": "Kuveyt",
    "Qatar": "Katar",
    "United Arab Emirates": "Birleşik Arap Emirlikleri",
    "UAE": "Birleşik Arap Emirlikleri",
    "Denmark": "Danimarka",
    "Finland": "Finlandiya",
    "Iceland": "İzlanda",
    "Afghanistan": "Afganistan",
    "Vietnam": "Vietnam",
    "Philippines": "Filipinler",
    "Thailand": "Tayland",
    "Malaysia": "Malezya",
    "South Korea": "Güney Kore",
    "Nigeria": "Nijerya",
    "Kenya": "Kenya",
    "Ethiopia": "Etiyopya",
    "Tanzania": "Tanzanya",
    "Tunisia": "Tunus",
    "Libya": "Libya",
    "Canada": "Kanada",
    "Peru": "Peru",
    "Venezuela": "Venezüela",
    "Bolivia": "Bolivya",
    "Cuba": "Küba",
    "Haiti": "Haiti",
    "Italy": "İtalya",
    "Germany": "Almanya",
    "United Kingdom": "Birleşik Krallık",
    "UK": "Birleşik Krallık",
    "Pakistan": "Pakistan",
    "India": "Hindistan",
    "Russia": "Rusya",
    "Ukraine": "Ukrayna",
    "China": "Çin",
    "Japan": "Japonya",
    "Indonesia": "Endonezya",
    "New Zealand": "Yeni Zelanda",
    "Papua New Guinea": "Papua Yeni Gine",
    "Mongolia": "Moğolistan",
    "Mexico": "Meksika",
    "Brazil": "Brezilya",
    "Argentina": "Arjantin",
    "Chile": "Şili",
    "Colombia": "Kolombiya",
    "Spain": "İspanya",
    "Portugal": "Portekiz",
    "France": "Fransa",
    "Belgium": "Belçika",
    "Netherlands": "Hollanda",
    "Switzerland": "İsviçre",
    "Austria": "Avusturya",
    "Sweden": "İsveç",
    "Norway": "Norveç",
    "Poland": "Polonya",
    "Hungary": "Macaristan",
    "Romania": "Romanya",
    "Bulgaria": "Bulgaristan",
    "Ireland": "İrlanda",
    "Luxembourg": "Lüksemburg"
}


def load_csv_events(csv_path: str) -> List[dict]:
    """Load events from CSV file."""
    events = []
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Map category
            category = CATEGORY_MAP.get(row['category'], 'war')
            
            # Get coordinates (use default if not in dictionary)
            country_raw = row['country'].strip()
            country = COUNTRY_NAME_MAP.get(country_raw, country_raw)
            lat, lon = COUNTRY_COORDS.get(country, (0, 0))
            
            # Parse year
            try:
                year = int(row['year'])
            except (ValueError, TypeError):
                # Try year_start if year fails
                try:
                    year = int(row['year_start'])
                except (ValueError, TypeError):
                    continue  # Skip if we can't parse the year
            
            # Determine decade
            decade_base = (year // 10) * 10
            decade = f"{decade_base}s"
            
            event = {
                "country_code": "",  # CSV doesn't have country codes
                "country_name": country,
                "lat": lat,
                "lon": lon,
                "decade": decade,
                "year": year,
                "category": category,
                "title": row['event'],
                "description": row['summary'],
                "wikipedia_url": "",  # CSV doesn't have URLs
                "casualties": None,
                "key_figures": []
            }
            
            events.append(event)
    
    return events


def load_existing_events(json_path: str) -> tuple:
    """Load existing events.json and return categories and events."""
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return data.get('categories', {}), data.get('events', [])


def _normalize_existing_events(events: List[dict]):
    """Normalize country names in existing events list using global COUNTRY_NAME_MAP."""
    for event in events:
        c_raw = event.get('country_name', '').strip()
        if c_raw in COUNTRY_NAME_MAP:
            event['country_name'] = COUNTRY_NAME_MAP[c_raw]
            # Update ID? No, ID is independent of country usually, but better keep as is.



def merge_events(existing_events: List[dict], csv_events: List[dict]) -> List[dict]:
    """Merge CSV events with existing events, avoiding duplicates."""
    
    # Create a set of existing event signatures (country + year + title)
    existing_signatures = set()
    for event in existing_events:
        signature = (
            event['country_name'].lower(),
            event['year'],
            event['title'].lower()
        )
        existing_signatures.add(signature)
    
    # Filter out CSV events that already exist
    new_events = []
    for event in csv_events:
        signature = (
            event['country_name'].lower(),
            event['year'],
            event['title'].lower()
        )
        
        if signature not in existing_signatures:
            new_events.append(event)
    
    # Assign IDs to new events
    # Find the highest existing ID
    max_id = 0
    for event in existing_events:
        if 'id' in event:
            try:
                id_num = int(event['id'].replace('ev', ''))
                max_id = max(max_id, id_num)
            except (ValueError, AttributeError):
                pass
    
    # Assign new IDs
    for i, event in enumerate(new_events, start=max_id + 1):
        event['id'] = f"ev{i:03d}"
    
    # Merge and sort by year
    all_events = existing_events + new_events
    all_events.sort(key=lambda x: x['year'])
    
    return all_events


def normalize_title(title):
    """Normalize title for comparison (lowercase, remove punctuation)."""
    import re
    # Remove punctuation and extra spaces, convert to lowercase
    normalized = re.sub(r'[^\w\s]', ' ', title.lower())
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    return normalized


def load_all_csv_events(base_dir: Path, category_map: dict) -> List[dict]:
    """Load events from both CSV files, removing duplicates within CSVs."""
    csv_files = [
        base_dir / "data" / "geopolitik_olaylar_seed_1900_gunumuz.csv",
        base_dir / "data" / "jeopolitik_afrika_guney_amerika_events.csv",
        base_dir / "data" / "jeopolitik_orta_avrupa_events.csv",
        base_dir / "data" / "time_100_manual.csv",
        base_dir / "data" / "events1_translated.csv",
        base_dir / "data" / "israel_events_update.csv",
        base_dir / "data" / "western_europe_events.csv",
        base_dir / "data" / "central_europe_events.csv",
        base_dir / "data" / "gap_filler_events.csv",
        base_dir / "data" / "gap_filler_v2.csv",
        base_dir / "data" / "gap_filler_v3.csv",
        base_dir / "data" / "gap_filler_final.csv",
        base_dir / "data" / "gap_filler_europe_major.csv",
        base_dir / "data" / "gap_filler_baltics.csv",
        base_dir / "data" / "gap_filler_final_sweep.csv",
        base_dir / "data" / "gap_filler_sa_density.csv",
        base_dir / "data" / "gap_filler_missing_countries.csv"
    ]
    
    all_csv_events = []
    seen_signatures = set()
    csv_duplicate_count = 0
    
    for csv_path in csv_files:
        if not csv_path.exists():
            print(f"Warning: {csv_path} not found, skipping")
            continue
            
        print(f"Loading: {csv_path.name}")
        
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            file_events = 0
            file_duplicates = 0
            
            for row in reader:
                # Determine which format we're using
                if 'year' in row and 'summary' in row and 'event' in row: # time_100 format matches geopolitik mostly
                    title = row['event']
                    desc = row['summary']
                    year_str = row['year']
                    country = row['country']
                    cat_raw = row['category']
                    
                    if cat_raw == 'Time 100':
                        category = 'time_100'
                    else:
                        category = category_map.get(cat_raw, 'war')
                        
                elif 'event_title' in row:  # jeopolitik format
                    # ... existing logic ...
                    category = category_map.get(row['category'], 'war')
                    country = row['country']
                    title = row['event_title']
                    year_str = row.get('year_start', row.get('year', ''))
                    desc = row.get('description_tr', '')
                elif 'event' in row:  # geopolitik format  
                    category = category_map.get(row['category'], 'war')
                    country = row['country']
                    title = row['event']
                    year_str = row.get('year', '')
                    desc = row.get('summary', '')
                else:
                    continue
                
                # Parse year (same as before)
                try:
                    year = int(float(year_str))
                except (ValueError, TypeError):
                    continue
                
                # Create signature
                norm_title = normalize_title(title)
                signature = (country.lower().strip(), year, norm_title)
                
                if signature in seen_signatures:
                    file_duplicates += 1
                    csv_duplicate_count += 1
                    continue
                
                seen_signatures.add(signature)
                
                lat, lon = COUNTRY_COORDS.get(country, (0, 0))
                decade_base = (year // 10) * 10
                decade = f"{decade_base}s"
                
                event = {
                    "country_code": "",
                    "country_name": country,
                    "lat": lat,
                    "lon": lon,
                    "decade": decade,
                    "year": year,
                    "category": category,
                    "title": title,
                    "description": desc,
                    "wikipedia_url": "",
                    "casualties": None,
                    "key_figures": []
                }
                
                all_csv_events.append(event)
                file_events += 1
            
            print(f"  - Loaded {file_events} events ({file_duplicates} duplicates skipped)")
    
    print(f"\nTotal CSV events after deduplication: {len(all_csv_events)}")
    print(f"Total CSV duplicates removed: {csv_duplicate_count}")
    
    return all_csv_events


def main():
    base_dir = Path(__file__).parent.parent
    
    # Map raw categories to our main categories
    CATEGORY_MAP = {
        'Savas': 'war',
        'Catisma': 'war',
        'Isgal': 'war',
        'Soykirim': 'genocide',
        'Devrim': 'revolution',
        'Darbe': 'revolution',
        'Bagimsizlik': 'revolution',
        'Rejim Degisikligi': 'revolution',
        'Teror': 'terror',
        'Suikast': 'terror',
        'Lider': 'leader',
        'Time 100': 'time_100',
        # New mappings for events1
        'Protest': 'revolution',
        'Independence': 'revolution',
        'War': 'war',
        'Culture': 'culture',
        'Law': 'revolution',
        'Sports': 'culture',
        'Crime': 'culture'
    }

    print("="*60)
    print("MERGING GEOPOLITICAL EVENTS")
    print("="*60)
    
    print("\n1. Loading CSV events from both files...")
    csv_events = load_all_csv_events(base_dir, CATEGORY_MAP)
    
    print(f"\n2. Loading existing Wikipedia events from: {base_dir / 'data' / 'events.json'}")
    json_path = base_dir / "data" / "events.json"
    categories, existing_events = load_existing_events(str(json_path))
    _normalize_existing_events(existing_events)
    print(f"   Found {len(existing_events)} existing events")
    
    # Custom add Time 100 category
    categories['time_100'] = {
        "label": "Time 100: Yüzyılın En Önemli Kişileri",
        "color": "#f1c40f"  # Gold
    }
    
    # Custom add Culture category
    categories['culture'] = {
        "label": "Kültür & Toplum",
        "color": "#9b59b6"  # Purple
    }

    # Count by category before merge
    existing_by_cat = {}
    for e in existing_events:
        cat = e.get('category', 'unknown')
        existing_by_cat[cat] = existing_by_cat.get(cat, 0) + 1
    
    print("\n3. Merging events (Wikipedia has priority)...")
    merged_events = merge_events(existing_events, csv_events)
    
    new_count = len(merged_events) - len(existing_events)
    print(f"   Total events after merge: {len(merged_events)}")
    print(f"   New events added: {new_count}")
    
    # Count by category after merge
    merged_by_cat = {}
    for e in merged_events:
        cat = e.get('category', 'unknown')
        merged_by_cat[cat] = merged_by_cat.get(cat, 0) + 1
    
    print("\n4. Category breakdown:")
    for cat_key, cat_info in categories.items():
        before = existing_by_cat.get(cat_key, 0)
        after = merged_by_cat.get(cat_key, 0)
        added = after - before
        print(f"   {cat_info['label']:30s}: {before:3d} -> {after:3d} (+{added})")
    
    # Save merged data
    output_data = {
        "categories": categories,
        "events": merged_events
    }
    
    backup_path = str(json_path) + ".backup"
    print(f"\n5. Creating backup at: {backup_path}")
    with open(backup_path, 'w', encoding='utf-8') as f:
        json.dump({"categories": categories, "events": existing_events}, f, ensure_ascii=False, indent=2)
    
    print(f"6. Writing merged data to: {json_path}")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    # Print statistics
    countries = set(e['country_name'] for e in merged_events)
    print("\n" + "="*60)
    print("✅ MERGE COMPLETE!")
    print("="*60)
    print(f"Total events: {len(merged_events)}")
    print(f"Total countries: {len(countries)}")
    print(f"New events from CSV: {new_count}")
    print("="*60)


if __name__ == "__main__":
    main()

