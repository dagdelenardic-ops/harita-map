import json
import os

METADATA_PATH = 'data/country_metadata.json'

updates = {
    "Democratic Republic of the Congo": [
        {"rival": "M23", "text": "Kivu Çatışması (M23)", "year": "2012-Devam", "status": "active"}
    ],
    "Ecuador": [
        {"rival": "Ekvador Çeteleri", "text": "Uyuşturucu Çeteleri Çatışması", "year": "2018-Devam", "status": "active"}
    ],
    "Niger": [
        {"rival": "Cihatçı Gruplar (Sahel)", "text": "Sahel Krizi", "year": "2015-Devam", "status": "active"}
    ],
    "Thailand": [
        {"rival": "Güney Tayland İsyancıları", "text": "Güney Tayland İsyanı", "year": "2004-Devam", "status": "active"}
    ]
}

def main():
    if not os.path.exists(METADATA_PATH):
        print(f"Error: {METADATA_PATH} not found.")
        return

    with open(METADATA_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    for country, rivalries in updates.items():
        if country in data:
            existing = data[country].get('rivalries', [])
            existing_map = {r['rival']: r for r in existing}
            for new_r in rivalries:
                existing_map[new_r['rival']] = new_r
            data[country]['rivalries'] = list(existing_map.values())
            print(f"Updated {country} with {len(rivalries)} active rivalries.")
        else:
            print(f"Key '{country}' not found. Creating new minimal entry.")
            data[country] = {
                "predecessor": "Kingdom of Siam", # minimal filler
                "demographics": "Thai", # minimal filler
                "felaketler": [],
                "rivalries": rivalries
            }

    with open(METADATA_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
        
    print("Successfully updated missing metadata.")

if __name__ == "__main__":
    main()
