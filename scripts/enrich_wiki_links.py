import json
import requests
import time
import urllib.parse

events_path = '/Users/gurursonmez/Documents/Harita/data/events.json'

def load_events():
    with open(events_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_events(data):
    with open(events_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def search_wikipedia(query, lang='tr'):
    # Try to find a Wikipedia page for the query
    # Using Wikipedia API
    base_url = f"https://{lang}.wikipedia.org/w/api.php"
    params = {
        "action": "opensearch",
        "search": query,
        "limit": 1,
        "namespace": 0,
        "format": "json"
    }
    
    try:
        response = requests.get(base_url, params=params, timeout=5)
        if response.status_code == 200:
            data = response.json()
            # data structure: [search_term, [titles], [descriptions], [urls]]
            if data[3]:
                return data[3][0]
    except Exception as e:
        print(f"Error searching for {query}: {e}")
    
    return ""

def enrich_links():
    data = load_events()
    events = data['events']
    
    updated_count = 0
    
    print(f"Total events: {len(events)}")
    
    for ev in events:
        # Check if URL is missing or empty
        if not ev.get('wikipedia_url'):
            title = ev.get('title')
            desc = ev.get('description')
            
            # Construct a search query
            # Prefer title. If title is short, maybe combine with country?
            # Start with title.
            if not title:
                continue
                
            print(f"Searching for: {title}")
            url = search_wikipedia(title)
            
            # If no result for title, maybe try English title if we can guess it? 
            # Or try appending "tarihi" or something?
            # For now, simple title search.
            
            if url:
                ev['wikipedia_url'] = url
                updated_count += 1
                print(f"Found: {url}")
            else:
                # Fallback: simple google search url meant for user manual check? 
                # User asked to "put relevant link from internet".
                # If wiki fails, maybe we rely on google search string?
                # No, user specifically said "wikipedia_url" mostly but "internetten arayarak ilgili linki koy" 
                # (search internet and put relevant link).
                # Current schema has "wikipedia_url". I'll put the wiki link if found.
                print(f"No result for {title}")
            
            # Rate limiting
            time.sleep(0.5)
            
    print(f"Updated {updated_count} events.")
    save_events(data)

if __name__ == "__main__":
    enrich_links()
