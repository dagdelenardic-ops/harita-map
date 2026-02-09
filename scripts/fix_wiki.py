import json
import re
import urllib.parse
import requests
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

# Cache for URL statuses
url_cache = {}

def check_url(url):
    if url in url_cache:
        return url_cache[url]
    try:
        # Use a real User-Agent to avoid blocks
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.head(url, headers=headers, allow_redirects=True, timeout=5)
        url_cache[url] = (response.status_code == 200)
        return url_cache[url]
    except:
        url_cache[url] = False
        return False

def fix_wiki_links(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    events = data.get('events', [])
    changed = False
    
    # Regex to find [Wikipedia](url)
    wiki_re = re.compile(r'\[Wikipedia\]\((https?://tr\.wikipedia\.org/wiki/[^\)]+)\)')
    
    # First, collect all unique links to check
    all_links = set()
    for event in events:
        desc = event.get('description', '')
        matches = wiki_re.findall(desc)
        for url in matches:
            all_links.add(url)
    
    print(f"Found {len(all_links)} unique Wikipedia links. Validating...")
    
    # Check links in parallel
    with ThreadPoolExecutor(max_workers=10) as executor:
        list(executor.map(check_url, all_links))
    
    # Apply fixes
    for event in events:
        desc = event.get('description', '')
        matches = wiki_re.findall(desc)
        
        for url in matches:
            if not url_cache.get(url, True):
                # TR sayfası yok: aynı başlıkla İngilizce makaleye git, Google Translate ile TR'ye çevir
                page_name = url.split('/')[-1]
                if '?' in page_name:
                    page_name = page_name.split('?')[0]
                page_name = urllib.parse.unquote(page_name)
                en_wiki_url = f"https://en.wikipedia.org/wiki/{urllib.parse.quote(page_name.replace(' ', '_'))}"
                translated_url = f"https://translate.google.com/translate?sl=en&tl=tr&u={urllib.parse.quote(en_wiki_url)}"
                event['description'] = desc.replace(f"({url})", f"({translated_url})")
                changed = True
                # Update desc for current event case if multiple links (rare)
                desc = event['description']
    
    if changed:
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Updated {json_path}")
    else:
        print("No changes needed")

if __name__ == "__main__":
    fix_wiki_links('data/events.json')
