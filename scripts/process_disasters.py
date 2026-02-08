import pandas as pd
import json
import os

# File paths
excel_path = '/Users/gurursonmez/Documents/Harita/data/public_emdat_2026-01-27.xlsx'
json_path = '/Users/gurursonmez/Documents/Harita/data/country_metadata.json'

# Significance Thresholds
MIN_DEATHS = 50
MIN_AFFECTED = 50000
MIN_DAMAGE_USD = 500000 # '000 USD -> 500,000 * 1000 = 500 Million USD

# Country Mapping (EMDAT Name -> JSON Key candidates)
# This is a manual map for common mismatches. 
# For others, we will try direct match or check if English name exists in keys.
COUNTRY_MAP = {
    "United States of America": ["ABD", "United States", "USA"],
    "United States": ["ABD", "United States", "USA"],
    "Turkey": ["Turkiye", "Türkiye", "Turkey"],
    "Türkiye": ["Turkiye", "Türkiye", "Turkey"],
    "Russian Federation": ["Rusya", "Russia"],
    "United Kingdom": ["Birlesik Krallik", "Birleşik Krallık", "United Kingdom"],
    "United Kingdom of Great Britain and Northern Ireland": ["Birlesik Krallik", "Birleşik Krallık", "United Kingdom"],
    "China": ["Cin", "Çin", "China"],
    "India": ["Hindistan", "India"],
    "Germany": ["Almanya", "Germany"],
    "France": ["Fransa", "France"],
    "Italy": ["Italya", "İtalya", "Italy"],
    "Japan": ["Japonya", "Japan"],
    "Brazil": ["Brezilya", "Brazil"],
    "Canada": ["Kanada", "Canada"],
    "Australia": ["Avustralya", "Australia"],
    "Spain": ["Ispanya", "İspanya", "Spain"],
    "Mexico": ["Meksika", "Mexico"],
    "Indonesia": ["Endonezya", "Indonesia"],
    "Netherlands": ["Hollanda", "Netherlands"],
    "Saudi Arabia": ["Suudi Arabistan", "Saudi Arabia"],
    "Switzerland": ["Isvicre", "İsviçre", "Switzerland"],
    "Argentina": ["Arjantin", "Argentina"],
    "Sweden": ["Isvec", "İsveç", "Sweden"],
    "Poland": ["Polonya", "Poland"],
    "Belgium": ["Belcika", "Belçika", "Belgium"],
    "Thailand": ["Tayland", "Thailand"],
    "Austria": ["Avusturya", "Austria"],
    "Norway": ["Norveç", "Norway"],
    "United Arab Emirates": ["BAE", "Birleşik Arap Emirlikleri", "United Arab Emirates"],
    "South Africa": ["Guney Afrika", "Güney Afrika", "South Africa"],
    "Greece": ["Yunanistan", "Greece"],
    "Denmark": ["Danimarka", "Denmark"],
    "Finland": ["Finlandiya", "Finland"],
    "Ukraine": ["Ukrayna", "Ukraine"],
    "South Korea": ["Guney Kore", "South Korea"],
    "Korea (the Republic of)": ["Guney Kore", "South Korea"],
    "Egypt": ["Misir", "Mısır", "Egypt"],
    "Portugal": ["Portekiz", "Portugal"],
    "Vietnam": ["Vietnam", "Viet Nam"],
    "Viet Nam": ["Vietnam"],
    "Hungary": ["Macaristan", "Hungary"],
    "Iran (Islamic Republic of)": ["Iran", "İran"],
    "Iran": ["Iran", "İran"],
    "Iraq": ["Irak", "Iraq"],
    "Ireland": ["Irlanda", "İrlanda", "Ireland"],
    "New Zealand": ["Yeni Zelanda", "New Zealand"],
    "Romania": ["Romanya", "Romania"],
    "Syrian Arab Republic": ["Suriye", "Syria"],
    "Syria": ["Suriye", "Syria"],
    "Morocco": ["Fas", "Morocco"],
    "Malaysia": ["Malezya", "Malaysia"],
    "Czech Republic": ["Çek Cumhuriyeti", "Czech Republic", "Cekoslovakya"], # Mapping to Cekoslovakya for legacy if needed, but mainly Cek Cumhuriyeti
    "Czechia": ["Çek Cumhuriyeti", "Czech Republic"],
    "Peru": ["Peru"],
    "Chile": ["Sili", "Şili", "Chile"],
    "Colombia": ["Kolombiya", "Colombia"],
    "Philippines": ["Filipinler", "Philippines"],
    "Pakistan": ["Pakistan"],
    "Bangladesh": ["Bangladeş", "Bangladesh"],
    "Nigeria": ["Nijerya", "Nigeria"],
    "Algeria": ["Cezayir", "Algeria"],
    "Israel": ["Israil", "İsrail", "Israel"],
    "Kuwait": ["Kuveyt", "Kuwait"],
    "Qatar": ["Katar", "Qatar"],
    "Kazakhstan": ["Kazakistan", "Kazakhstan"],
    "Azerbaijan": ["Azerbaycan", "Azerbaijan"],
    "Oman": ["Umman", "Oman"],
    "Luxembourg": ["Lüksemburg", "Luxembourg"],
    "Slovakia": ["Slovakya", "Slovakia"],
    "Bulgaria": ["Bulgaristan", "Bulgaria"],
    "Croatia": ["Hırvatistan", "Croatia"],
    "Serbia": ["Sırbistan", "Serbia"],
    "Slovenia": ["Slovenya", "Slovenia"],
    "Bosnia and Herzegovina": ["Bosna Hersek", "Bosnia and Herzegovina"],
    "Uzbekistan": ["Özbekistan", "Uzbekistan"],
    "Turkmenistan": ["Türkmenistan", "Turkmenistan"],
    "Kyrgyzstan": ["Kırgızistan", "Kyrgyzstan"],
    "Tajikistan": ["Tacikistan", "Tajikistan"],
    "Tunisia": ["Tunus", "Tunisia"],
    "Libya": ["Libya"],
    "Jordan": ["Ürdün", "Jordan"],
    "Lebanon": ["Lübnan", "Lebanon"],
    "Afghanistan": ["Afganistan", "Afghanistan"],
    "Georgia": ["Gurcistan", "Gürcistan", "Georgia"],
    "Armenia": ["Ermenistan", "Armenia"],
    "Mongolia": ["Moğolistan", "Mongolia"],
}

def load_data():
    print("Loading Excel data...")
    df = pd.read_excel(excel_path)
    
    print("Loading JSON metadata...")
    with open(json_path, 'r', encoding='utf-8') as f:
        metadata = json.load(f)
    return df, metadata

def process_disasters(df, metadata):
    print("Processing disasters...")
    
    # Filter for significant events
    # Criteria: Deaths >= 50 OR Affected >= 50k OR Damage >= 500k ('000 USD)
    sig_df = df[
        (df['Total Deaths'] >= MIN_DEATHS) |
        (df['Total Affected'] >= MIN_AFFECTED) |
        (df['Total Damage (\'000 US$)'] >= MIN_DAMAGE_USD)
    ].copy()
    
    print(f"Found {len(sig_df)} significant disasters out of {len(df)} total.")
    
    # Process each disaster
    matches_found = 0
    
    # Create normalized keys map for metadata
    # We want to match EMDAT country to Metadata keys.
    # Metadata keys are mixed (TR, EN).
    
    # Clear existing 'felaketler' data start fresh
    print("Clearing existing disaster data...")
    for key in metadata:
        if "felaketler" in metadata[key]:
            metadata[key]["felaketler"] = []

    # Iterate over significant disasters
    for _, row in sig_df.iterrows():
        country = row['Country']
        year = row['Start Year']
        dis_type = row['Disaster Type']
        dis_subtype = row['Disaster Subtype'] if pd.notna(row['Disaster Subtype']) else ""
        event_name = row['Event Name'] if pd.notna(row['Event Name']) else ""
        
        deaths = row['Total Deaths'] if pd.notna(row['Total Deaths']) else 0
        affected = row['Total Affected'] if pd.notna(row['Total Affected']) else 0
        damage = row['Total Damage (\'000 US$)'] if pd.notna(row['Total Damage (\'000 US$)']) else 0
        
        # Translation Map
        DISASTER_TRANSLATIONS = {
            "Flood": "Sel",
            "Flash flood": "Ani Sel",
            "Riverine flood": "Nehir Taşkını",
            "Coastal flood": "Kıyı Seli",
            "Earthquake": "Deprem",
            "Ground movement": "Yer Sarsıntısı",
            "Tsunami": "Tsunami",
            "Storm": "Fırtına",
            "Tropical cyclone": "Tropikal Kasırga",
            "Convective storm": "Konvektif Fırtına",
            "Extra-tropical storm": "Ekstra-tropikal Fırtına",
            "Tornado": "Hortum",
            "Drought": "Kuraklık",
            "Wildfire": "Orman Yangını",
            "Forest fire": "Orman Yangını",
            "Land fire (Brush, Bush, Pasture)": "Arazi Yangını",
            "Extreme temperature": "Aşırı Sıcaklık",
            "Heat wave": "Sıcak Hava Dalgası",
            "Cold wave": "Soğuk Hava Dalgası",
            "Severe winter conditions": "Ağır Kış Şartları",
            "Epidemic": "Salgın",
            "Viral disease": "Viral Hastalık",
            "Bacterial disease": "Bakteriyel Hastalık",
            "Parasitic disease": "Paraziter Hastalık",
            "Volcanic activity": "Volkanik Aktivite",
            "Ash fall": "Kül Yağmuru",
            "Lava flow": "Lav Akıntısı",
            "Mass movement (dry)": "Toprak Kayması (Kuru)",
            "Landslide": "Heyelan",
            "Rockfall": "Kaya Düşmesi",
            "Mass movement (wet)": "Toprak Kayması (Islak)",
            "Avalanche": "Çığ",
            "Insect infestation": "Böcek İstilası",
            "Locust": "Çekirge",
            "Animal accident": "Hayvan Kazası",
            "Impact": "Göktaşı/Çarpma",
            "Glacial lake outburst": "Buzul Gölü Taşkını",
            "Fog": "Sis",
            "Derecho": "Derecho Fırtınası",
            "Sandstorm": "Kum Fırtınası",
            "Mudslide": "Çamur Kayması",
            "Explosion": "Patlama",
            "Fire": "Yangın",
            "Transport accident": "Ulaşım Kazası",
            "Collapse": "Çökme",
            "Air": "Hava Kazası",
            "Road": "Trafik Kazası",
            "Water": "Deniz Kazası",
            "Rail": "Tren Kazası",
            "Fire (Miscellaneous)": "Yangın (Çeşitli)",
            "Explosion (Industrial)": "Patlama (Endüstriyel)",
            "Collapse (Miscellaneous)": "Çökme (Çeşitli)",
            "Collapse (Industrial)": "Çökme (Endüstriyel)",
            "Structure Collapse": "Yapı Çökmesi",
            "Miscellaneous accident": "Çeşitli Kazalar",
            "Wildfire (General)": "Orman Yangını",
            "Lightning/Thunderstorms": "Yıldırım/Fırtına",
            "Blizzard/Winter storm": "Kar Fırtınası",
            "Severe weather": "Şiddetli Hava Koşulları",
            "Flood (General)": "Sel",
            "Storm (General)": "Fırtına"
        }

        # Apply Translation
        dis_type = DISASTER_TRANSLATIONS.get(dis_type, dis_type)
        dis_subtype = DISASTER_TRANSLATIONS.get(dis_subtype, dis_subtype)
        
        # Build the disaster object
        disaster_obj = {
            "year": int(year),
            "type": dis_type,
            "subtype": dis_subtype,
            "name": event_name,
            "deaths": int(deaths),
            "affected": int(affected),
            "damage_usd_millions": float(damage) / 1000 if damage > 0 else 0
        }
        
        # Find matching keys in metadata
        target_keys = []
        
        # 1. Check Explicit Map
        if country in COUNTRY_MAP:
            candidates = COUNTRY_MAP[country]
            for cand in candidates:
                if cand in metadata:
                    target_keys.append(cand)
        
        # 2. Check Direct Match
        if country in metadata and country not in target_keys:
            target_keys.append(country)
            
        # 3. If no match yet, try simple fuzzy/lower check
        if not target_keys:
            for key in metadata.keys():
                if key.lower() == country.lower():
                    target_keys.append(key)
        
        if target_keys:
            matches_found += 1
            for key in target_keys:
                if "felaketler" not in metadata[key]:
                    metadata[key]["felaketler"] = []
                
                # Avoid duplicates? (Simple check based on year and type)
                exists = False
                for d in metadata[key]["felaketler"]:
                    if d['year'] == disaster_obj['year'] and d['type'] == disaster_obj['type'] and d['deaths'] == disaster_obj['deaths']:
                        exists = True
                        break
                
                if not exists:
                    metadata[key]["felaketler"].append(disaster_obj)
        else:
            # Uncomment to debug missing countries
            # print(f"Warning: No match for {country}")
            pass

    print(f"Processed events. Updated metadata for {matches_found} events (note: one event might update multiple keys).")
    return metadata

def save_data(metadata):
    print(f"Saving updated metadata to {json_path}...")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=4)
    print("Done.")

if __name__ == "__main__":
    df, metadata = load_data()
    updated_metadata = process_disasters(df, metadata)
    save_data(updated_metadata)
