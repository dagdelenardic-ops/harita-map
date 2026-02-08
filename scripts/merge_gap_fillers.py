
import json
import os
import csv
import glob

EVENTS_PATH = '/Users/gurursonmez/Documents/Harita/data/events.json'
DATA_DIR = '/Users/gurursonmez/Documents/Harita/data'

# Files to merge
CSV_FILES = [
    'gap_filler_balkans.csv',
    'gap_filler_missing.csv',
    'gap_filler_missing_v2.csv',
    'gap_filler_final_fix.csv',
    'gap_filler_final.csv',
    'gap_filler_europe_major.csv',
    'gap_filler_baltics.csv',
    'western_europe_events.csv',
    'jeopolitik_afrika_guney_amerika_events.csv',
    'jeopolitik_orta_avrupa_events.csv',
    'gap_filler_sa_density.csv',
    'gap_filler_africa_central.csv',
    'gap_filler_africa_west.csv',
    'gap_filler_africa_east_south.csv',
    'gap_filler_africa_supplement.csv',
    'gap_filler_africa_final.csv',
    'gap_filler_africa_final_supplement.csv'
]

COUNTRY_NAME_FIX = {
    "Egypt": "Misir",
    "Mısır": "Misir",
    "Mozambique": "Mozambik",
    "Tanzania": "Tanzanya",
    "Niger": "Nijer",
    "Chad": "Çad",
    "Cameroon": "Kamerun",
    "Ivory Coast": "Fildisi Sahili",
    "Gabon": "Gabon",
    "Ghana": "Gana",
    "Guinea": "Gine",
    "South Africa": "Guney Afrika",
    "Namibia": "Namibya",
    "Zambia": "Zambiya",
    "Zimbabwe": "Zimbabve",
    "Botswana": "Botsvana",
    "Lesotho": "Lesoto",
    "Swaziland": "Esvatini",
    "Eswatini": "Esvatini",
    "Angola": "Angola",
    "Malawi": "Malavi",
    "Democratic Republic of the Congo": "Demokratik Kongo Cumhuriyeti",
    "DRC": "Demokratik Kongo Cumhuriyeti",
    "Congo": "Kongo",
    "Central African Republic": "Orta Afrika Cumhuriyeti",
    "Somalia": "Somali",
    "Djibouti": "Cibuti",
    "Eritrea": "Eritre",
    "Uganda": "Uganda",
    "Burundi": "Burundi",
    "Rwanda": "Ruanda",
    "Western Sahara": "Batı Sahra",
    "Mauritania": "Moritanya",
    "Mali": "Mali",
    "Senegal": "Senegal",
    "Gambia": "Gambiya",
    "Liberia": "Liberya",
    "Sierra Leone": "Sierra Leone",
    "Güney Sudan": "Guney Sudan",
    "Güney Afrika": "Guney Afrika",
    "Fildişi Sahili": "Fildisi Sahili",
    "Yeşil Burun Adalari": "Yesil Burun Adalari",
    "Yeşil Burun": "Yesil Burun Adalari",
    "Cabo Verde": "Yesil Burun Adalari", 
    "São Tomé ve Príncipe": "Sao Tome ve Principe",
    "Sao Tome": "Sao Tome ve Principe"
}

def load_events():
    with open(EVENTS_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_coords(events_data, country_name):
    # Try to find a lat/lon for this country from existing events
    for ev in events_data['events']:
        if ev.get('country_name') == country_name and ev.get('lat') != 0:
            return ev['lat'], ev['lon']
    
    # Fallback centers (approximate)
    centers = {
        "Sırbistan": (44.0, 21.0),
        "Hırvatistan": (45.1, 15.2),
        "Bosna Hersek": (43.9, 17.6),
        "Arnavutluk": (41.1, 20.1),
        "Makedonya": (41.6, 21.7),
        "Karadağ": (42.7, 19.3),
        "Kosova": (42.6, 20.9),
        "Bulgaristan": (42.7, 25.4),
        "Romanya": (45.9, 24.9),
        "Yunanistan": (39.0, 21.8),
        "Slovenya": (46.1, 14.9),
        "Estonya": (58.5, 25.0),
        "Letonya": (56.8, 24.6),
        "Litvanya": (55.1, 23.8),
        "Suudi Arabistan": (23.8, 45.0),
        "Almanya": (51.1, 10.4),
        "Avusturya": (47.5, 14.5)
    }
    return centers.get(country_name, (0, 0))

def merge_csvs():
    data = load_events()
    existing_events = {(ev['country_name'], ev['year'], ev['title']) for ev in data['events']}
    existing_ids = set(ev['id'] for ev in data['events'])
    
    total_added = 0
    
    for csv_file in CSV_FILES:
        path = os.path.join(DATA_DIR, csv_file)
        if not os.path.exists(path):
            print(f"Skipping missing file: {csv_file}")
            continue
            
        print(f"Processing {csv_file}...")
        
        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            file_added = 0
            forrow = 0
            for row in reader:
                # Handle different column names across files
                country = row.get('country') or row.get('Country')
                
                # Year handling
                year_str = row.get('year') or row.get('Year') or row.get('year_start')
                
                # Title handling
                title = row.get('event') or row.get('Event') or row.get('Title') or row.get('event_title')
                
                # Description handling
                desc = row.get('summary') or row.get('Summary') or row.get('Description') or row.get('description_tr')
                
                # Category handling
                raw_category = row.get('category') or row.get('Category')
                
                # Category Mapping
                CATEGORY_MAPPING = {
                    "Savaş/Çatışma": "war",
                    "Savas/Catisma": "war",
                    "Soykırım": "genocide",
                    "Soykirim": "genocide",
                    "Devrim/Rejim Değişikliği": "revolution",
                    "Devrim/Rejim Degisikligi": "revolution",
                    "Terör Saldırısı": "terror",
                    "Teror Saldirisi": "terror",
                    "Önemli Lider": "leader",
                    "Onemli Lider": "leader",
                    "Kültür/Bilim": "culture",
                    "Kultur/Bilim": "culture",
                    "Kültür & Toplum": "culture",
                    "Doğal Afet": "culture", # Map disasters to culture or a general category for now
                    "Ekonomi": "revolution"  # Map economy to revolution (often regime changing) or keep distinct if system supports
                }
                
                category = CATEGORY_MAPPING.get(raw_category, raw_category)

                if not (country and year_str and title):
                    if file_added == 0 and forrow < 5:
                        print(f"Skipping row {forrow} in {csv_file}: missing key fields. Row keys: {list(row.keys())}")
                    continue
                    
                # Fix country name
                if country in COUNTRY_NAME_FIX:
                    country = COUNTRY_NAME_FIX[country]
                
                try:
                    year = int(float(year_str))
                except:
                    if file_added == 0 and forrow < 5:
                         print(f"Skipping row {forrow} in {csv_file}: invalid year '{year_str}'")
                    continue
                    
                # Deduplication check
                key = (country, year, title)
                
                # Check if exists and update category if needed
                found_existing = False
                for ev in data['events']:
                    if ev.get('country_name') == country and ev.get('year') == year and ev.get('title') == title:
                        found_existing = True
                        # If category is mapped and different, update it
                        if ev.get('category') != category:
                            print(f"Updating category for {title}: {ev.get('category')} -> {category}")
                            ev['category'] = category
                            total_added += 1 # Count as an update
                        break
                
                if found_existing:
                    continue
                
                # Generate ID
                cnt = 0
                new_id = f"ev_gap_{year}_{cnt}"
                while new_id in existing_ids:
                    cnt += 1
                    new_id = f"ev_gap_{year}_{cnt}"
                
                lat, lon = get_coords(data, country)
                if lat == 0 and lon == 0:
                    # If still 0, try to print/log but continue
                    pass

                new_event = {
                    "country_code": "", 
                    "country_name": country,
                    "lat": lat,
                    "lon": lon,
                    "decade": f"{str(year)[:3]}0s",
                    "year": year,
                    "category": category if category else "Genel",
                    "title": title,
                    "description": desc if desc else title,
                    "wikipedia_url": "",
                    "casualties": None,
                    "key_figures": [],
                    "id": new_id
                }
                
                data['events'].append(new_event)
                existing_events.add((country, year, title))
                existing_ids.add(new_id)
                file_added += 1
                total_added += 1
                
        print(f"  Added {file_added} events from {csv_file}")

    print(f"Total new events added: {total_added}")
    
    with open(EVENTS_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    merge_csvs()
