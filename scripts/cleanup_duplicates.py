
import json
import csv
from pathlib import Path

def normalize(text):
    return text.strip()

def main():
    base_dir = Path(__file__).parent.parent
    events_json_path = base_dir / "data" / "events.json"
    
    # helper to load CSV map
    title_country_map = {}
    
    csv_files = [
        base_dir / "data" / "time_100_manual.csv",
        base_dir / "data" / "events1_translated.csv"
    ]
    
    print("Building target map from CSVs...")
    for p in csv_files:
        with open(p, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # time_100 keys
                if 'event' in row:
                    title = normalize(row['event'])
                elif 'event_title' in row:
                    title = normalize(row['event_title'])
                else:
                    continue
                
                country = normalize(row['country'])
                title_country_map[title] = country
                
    print(f"Tracking {len(title_country_map)} unique titles for cleanup.")
    
    # Load JSON
    with open(events_json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    events = data.get('events', [])
    initial_count = len(events)
    
    kept_events = []
    removed_count = 0
    
    for e in events:
        title = normalize(e.get('title', ''))
        country = normalize(e.get('country_name', ''))
        
        if title in title_country_map:
            expected_country = title_country_map[title]
            if country != expected_country:
                print(f"Removing duplicate/old: '{title}' in '{country}' (Expected: '{expected_country}')")
                removed_count += 1
                continue
        
        kept_events.append(e)
        
    data['events'] = kept_events
    
    # Save
    with open(events_json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        
    print(f"Cleanup complete. Removed {removed_count} events. Count: {initial_count} -> {len(kept_events)}")

if __name__ == "__main__":
    main()
