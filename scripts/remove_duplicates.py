import json
from collections import defaultdict

EVENTS_PATH = '/Users/gurursonmez/Documents/Harita/data/events.json'

def remove_duplicates():
    with open(EVENTS_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    initial_count = len(data['events'])
    
    # Group by unique key
    grouped_events = defaultdict(list)
    
    for ev in data['events']:
        # Key: Country + Year + Title (normalized)
        key = (
            ev.get('country_name', '').strip(), 
            ev.get('year'), 
            ev.get('title', '').strip()
        )
        grouped_events[key].append(ev)
        
    unique_events = []
    
    for key, group in grouped_events.items():
        if len(group) == 1:
            unique_events.append(group[0])
        else:
            # If multiple, keep the one with the longest description
            # If descriptions are same length, pick the one with a valid ID (if any difference) or just first
            best_event = max(group, key=lambda x: len(x.get('description', '') or ''))
            unique_events.append(best_event)
            
    final_count = len(unique_events)
    removed_count = initial_count - final_count
    
    print(f"Initial event count: {initial_count}")
    print(f"Final event count:   {final_count}")
    print(f"Removed duplicates:  {removed_count}")
    
    data['events'] = unique_events
    
    with open(EVENTS_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    remove_duplicates()
