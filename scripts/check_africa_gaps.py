import json

AFRICAN_COUNTRIES = [
    "Mısır", "Libya", "Tunus", "Cezayir", "Fas", 
    "Sudan", "Guney Sudan", "Eritre", "Cibuti", "Somali", 
    "Etiyopya", "Kenya", "Uganda", "Ruanda", "Burundi", 
    "Tanzanya", "Kongo", "Demokratik Kongo Cumhuriyeti", "Orta Afrika Cumhuriyeti", 
    "Gabon", "Ekvator Ginesi", "Kamerun", "Çad", "Nijer", 
    "Nijerya", "Benin", "Togo", "Gana", "Fildisi Sahili", 
    "Liberya", "Sierra Leone", "Gine", "Gine-Bissau", "Senegal", 
    "Gambiya", "Moritanya", "Mali", "Burkina Faso", "Yesil Burun Adalari", 
    "Sao Tome ve Principe", "Angola", "Namibya", "Guney Afrika", "Lesoto", 
    "Esvatini", "Botsvana", "Zimbabve", "Zambiya", "Malavi", 
    "Mozambik", "Madagaskar", "Komorlar", "Seyseller", "Mauritius",
    "Batı Sahra"
]

# Normalization map to match json country names if they differ slighty
NORM_MAP = {
    "Misir": "Mısır",
    "Egypt": "Mısır",
    "Morocco": "Fas",
    "Algeria": "Cezayir",
    "Tunisia": "Tunus",
    "Libya": "Libya",
    "Sudan": "Sudan",
    "South Sudan": "Guney Sudan",
    "Eritrea": "Eritre",
    "Djibouti": "Cibuti",
    "Somalia": "Somali",
    "Ethiopia": "Etiyopya",
    "Kenya": "Kenya",
    "Uganda": "Uganda",
    "Rwanda": "Ruanda",
    "Burundi": "Burundi",
    "Tanzania": "Tanzanya",
    "Congo": "Kongo",
    "DRC": "Demokratik Kongo Cumhuriyeti",
    "Democratic Republic of the Congo": "Demokratik Kongo Cumhuriyeti",
    "Central African Republic": "Orta Afrika Cumhuriyeti",
    "Gabon": "Gabon",
    "Equatorial Guinea": "Ekvator Ginesi",
    "Cameroon": "Kamerun",
    "Chad": "Çad",
    "Niger": "Nijer",
    "Nigeria": "Nijerya",
    "Benin": "Benin",
    "Togo": "Togo",
    "Ghana": "Gana",
    "Ivory Coast": "Fildisi Sahili",
    "Liberia": "Liberya",
    "Sierra Leone": "Sierra Leone",
    "Guinea": "Gine",
    "Guinea-Bissau": "Gine-Bissau",
    "Senegal": "Senegal",
    "Gambia": "Gambiya",
    "Mauritania": "Moritanya",
    "Mali": "Mali",
    "Burkina Faso": "Burkina Faso",
    "Cape Verde": "Yesil Burun Adalari",
    "Sao Tome and Principe": "Sao Tome ve Principe",
    "Angola": "Angola",
    "Namibia": "Namibya",
    "South Africa": "Guney Afrika",
    "Lesotho": "Lesoto",
    "Eswatini": "Esvatini",
    "Swaziland": "Esvatini",
    "Botswana": "Botsvana",
    "Zimbabwe": "Zimbabve",
    "Zambia": "Zambiya",
    "Malawi": "Malavi",
    "Mozambique": "Mozambik",
    "Madagascar": "Madagaskar",
    "Comoros": "Komorlar",
    "Seychelles": "Seyseller",
    "Mauritius": "Mauritius",
    "Western Sahara": "Batı Sahra"
    
}

def check_africa():
    with open('data/events.json', 'r') as f:
        data = json.load(f)
    
    country_counts = {}
    for ev in data['events']:
        c_name = ev.get('country_name')
        # Normalize using NORM_MAP
        norm_name = NORM_MAP.get(c_name, c_name)
        country_counts[norm_name] = country_counts.get(norm_name, 0) + 1

    print("African Countries with < 10 events:")
    low_count_countries = []
    
    # Reverse NORM_MAP to check possible keys in JSON
    # actually let's just iterate our target list
    
    for tr_name in AFRICAN_COUNTRIES:
        # Check direct match
        count = country_counts.get(tr_name, 0)
        
        # Check variations
        if count == 0:
            # Try to find if it exists under a different name in json
            # e.g. json "South Africa" vs list "Guney Afrika"
            # We normalized strictly in previous steps but let's check
            pass

        if count < 10:
            print(f"{tr_name}: {count}")
            low_count_countries.append(tr_name)
            
    return low_count_countries

if __name__ == "__main__":
    check_africa()
