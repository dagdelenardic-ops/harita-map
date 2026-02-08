import csv
import json
import os
import urllib.parse
import re

METADATA_PATH = '/Users/gurursonmez/Documents/Harita/data/country_metadata.json'
CSV_PATH = '/Users/gurursonmez/Documents/Harita/data/wars_demo.csv' # Will look for all_countries_wars.csv later if available, but using demo for now as per instructions

def load_metadata():
    if not os.path.exists(METADATA_PATH):
        print(f"Error: {METADATA_PATH} not found.")
        return {}
    with open(METADATA_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_metadata(data):
    with open(METADATA_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def extract_primary_rival(opponents_text, valid_countries):
    """
    Attempts to find a valid country name within the opponents text.
    Returns the first match found in the valid_countries set.
    """
    if not opponents_text:
        return None
        
    # Normalize text for checking
    text_lower = opponents_text.lower()
    
    # Sort valid countries by length (descending) to match "United Kingdom" before "United" checking
    # Note: keys in valid_countries are Turkish names e.g. "Almanya", "Rusya" based on metadata
    sorted_countries = sorted(valid_countries, key=len, reverse=True)
    
    for country in sorted_countries:
        # Check if country name appears in the opponents text
        # Using simple substring check for now, can be improved with regex word boundaries
        if country.lower() in text_lower:
            return country
            
    # Fallback: If no known country found, return the text itself (truncated if too long)
    # or match comma separation
    parts = opponents_text.split(',')
    primary = parts[0].strip()
    
    # Clean up common suffix like " forces", " army" etc if needed, but keeping simple for now
    return primary

def import_wars():
    data = load_metadata()
    existing_countries = set(data.keys())
    
    # Try to find the full CSV first, fall back to demo
    csv_file = CSV_PATH
    full_csv = '/Users/gurursonmez/Documents/Harita/data/all_countries_wars.csv'
    if os.path.exists(full_csv):
        csv_file = full_csv
    elif not os.path.exists(csv_file):
        print(f"Error: CSV file not found at {csv_file}")
        return

    print(f"Reading from {csv_file}...")
    
    updated_count = 0
    rows_processed = 0
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        # Group by country first
        country_wars = {}
        
        for row in reader:
            country = row['country'].strip()
            if not country: continue
            
            if country not in country_wars:
                country_wars[country] = []
            country_wars[country].append(row)
            rows_processed += 1
            
        # Process each country
        for country_name, wars in country_wars.items():
            # Check if this country exists in metadata
            # The CSV `country` column is expected to be Turkish names matching metadata keys
            target_key = None
            if country_name in data:
                target_key = country_name
            else:
                # Try simple lookup or skip
                # Maybe case insensitive
                for k in existing_countries:
                    if k.lower() == country_name.lower():
                        target_key = k
                        break
            
            if not target_key:
                print(f"Warning: Country '{country_name}' from CSV not found in metadata. Creating new entry...")
                target_key = country_name
                data[target_key] = {"predecessor": "-", "demographics": "-", "rivalries": []}
            
            # Prepare new rivalry list
            new_rivalries = []
            
            for war in wars:
                war_name = war['war_name']
                opponents = war['opponents']
                arrow_label = war['arrow_label']
                summary = war.get('summary_1_2_sentences', '')
                
                # Determine rival for arrow
                rival_name = extract_primary_rival(opponents, existing_countries)
                if not rival_name:
                    rival_name = "Unknown"
                    
                # Generate Wikipedia Link
                # Using a search query is safest if we don't have exact URLs
                safe_war_name = urllib.parse.quote(war_name)
                url = f"https://tr.wikipedia.org/w/index.php?search={safe_war_name}"
                
                rivalry_entry = {
                    "rival": rival_name,
                    "text": arrow_label, # The short label for the arrow
                    "url": url,
                    "desc": summary, # Storing summary too in case we want to separate sidebar desc
                    "full_name": war_name
                }
                new_rivalries.append(rivalry_entry)
                
            # Update metadata
            data[target_key]['rivalries'] = new_rivalries
            updated_count += 1
            
    save_metadata(data)
    print(f"Processed {rows_processed} rows.")
    print(f"Updated metadata for {updated_count} countries.")

if __name__ == "__main__":
    import_wars()
