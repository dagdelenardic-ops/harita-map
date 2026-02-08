
import csv
import json

CSV_PATH = '/Users/gurursonmez/Documents/Harita/data/gap_filler_africa_supplement.csv'
EVENTS_PATH = '/Users/gurursonmez/Documents/Harita/data/events.json'

def debug_merge():
    with open(EVENTS_PATH, 'r') as f:
        data = json.load(f)
    
    existing_events = []
    for ev in data['events']:
        existing_events.append((ev.get('country_name'), ev.get('year'), ev.get('title')))
    
    print(f"Loaded {len(existing_events)} existing events.")
    
    print(f"Reading {CSV_PATH}...")
    with open(CSV_PATH, 'r', encoding='utf-8') as f:
        # Check first line for BOM or weird chars
        first_line = f.readline()
        print(f"Header line: {repr(first_line)}")
        f.seek(0)
        
        reader = csv.DictReader(f)
        print(f"Fieldnames: {reader.fieldnames}")
        
        for i, row in enumerate(reader):
            if i >= 5: break
            
            country = row.get('country')
            year = row.get('year')
            title = row.get('event')
            
            print(f"Row {i}: Country='{country}', Year='{year}', Title='{title}'")
            
            if not (country and year and title):
                print(f"  -> SKIPPING: Missing fields. Keys: {list(row.keys())}")
                continue
                
            # Check existence
            try:
                y = int(year)
            except:
                print(f"  -> SKIPPING: Invalid year {year}")
                continue
                
            found = False
            for ex_c, ex_y, ex_t in existing_events:
                if ex_c == country and ex_y == y and ex_t == title:
                    found = True
                    break
            
            if found:
                print("  -> EXISTS in data")
            else:
                print("  -> NEW (Should be added)")

if __name__ == "__main__":
    debug_merge()
