import json

EVENTS_PATH = '/Users/gurursonmez/Documents/Harita/data/events.json'

MAPPING = {
    # Africa
    "Egypt": "Misir",
    "Mısır": "Misir",
    "Misir": "Misir",
    "Libya": "Libya",
    "Tunisia": "Tunus",
    "Algeria": "Cezayir",
    "Morocco": "Fas",
    "Western Sahara": "Batı Sahra",
    "Mauritania": "Moritanya",
    "Mali": "Mali",
    "Senegal": "Senegal",
    "Gambia": "Gambiya",
    "The Gambia": "Gambiya",
    "Guinea": "Gine",
    "Guinea-Bissau": "Gine-Bissau",
    "Sierra Leone": "Sierra Leone",
    "Liberia": "Liberya",
    "Ivory Coast": "Fildisi Sahili",
    "Côte d'Ivoire": "Fildisi Sahili",
    "Côte d’Ivoire": "Fildisi Sahili",
    "Ghana": "Gana",
    "Togo": "Togo",
    "Benin": "Benin",
    "Niger": "Nijer",
    "Nigeria": "Nijerya",
    "Chad": "Çad",
    "Cameroon": "Kamerun",
    "Central African Republic": "Orta Afrika Cumhuriyeti",
    "CAR": "Orta Afrika Cumhuriyeti",
    "Equatorial Guinea": "Ekvator Ginesi",
    "Gabon": "Gabon",
    "Congo": "Kongo",
    "Republic of the Congo": "Kongo",
    "Democratic Republic of the Congo": "Demokratik Kongo Cumhuriyeti",
    "DRC": "Demokratik Kongo Cumhuriyeti",
    "Kongo DC": "Demokratik Kongo Cumhuriyeti",
    "Sao Tome and Principe": "Sao Tome ve Principe",
    "Sao Tome ve Principe": "Sao Tome ve Principe",
    "Angola": "Angola",
    "Namibia": "Namibya",
    "South Africa": "Guney Afrika",
    "South Africa Republic": "Guney Afrika",
    "Lesotho": "Lesoto",
    "Eswatini": "Esvatini",
    "Swaziland": "Esvatini",
    "Botswana": "Botsvana",
    "Zambia": "Zambiya",
    "Zimbabwe": "Zimbabve",
    "Malawi": "Malavi",
    "Mozambique": "Mozambik",
    "Madagascar": "Madagaskar",
    "Comoros": "Komorlar",
    "Seychelles": "Seyseller",
    "Mauritius": "Mauritius",
    "Djibouti": "Cibuti",
    "Eritrea": "Eritre",
    "Ethiopia": "Etiyopya",
    "Somalia": "Somali",
    "Kenya": "Kenya",
    "Uganda": "Uganda",
    "Rwanda": "Ruanda",
    "Burundi": "Burundi",
    "Tanzania": "Tanzanya",
    "South Sudan": "Guney Sudan",
    "Sudan": "Sudan",
    "Cape Verde": "Yesil Burun Adalari",
    "Cabo Verde": "Yesil Burun Adalari",

    # Other Global
    "Turkey": "Turkiye",
    "Türkiye": "Turkiye",
    "Greece": "Yunanistan",
    "Bulgaria": "Bulgaristan",
    "Serbia": "Sırbistan",
    "Croatia": "Hırvatistan",
    "Albania": "Arnavutluk",
    "Macedonia": "Makedonya",
    "North Macedonia": "Makedonya",
    "Bosnia and Herzegovina": "Bosna Hersek",
    "Bosnia": "Bosna Hersek",
    "Bosnia-Herzegovina": "Bosna Hersek",
    "Montenegro": "Karadağ",
    "Kosovo": "Kosova",
    "Slovenia": "Slovenya",
    "Romania": "Romanya",
    "Cyprus": "Kibris",
    "Kıbrıs": "Kibris",
    "Northern Cyprus": "Kuzey Kıbrıs",
    "Kuzey Kıbrıs": "Kuzey Kıbrıs",
    "Israel": "Israil",
    "Palestine": "Filistin",
    "Lebanon": "Lübnan",
    "Syria": "Suriye",
    "Jordan": "Ürdün",
    "Iraq": "Irak",
    "Iran": "Iran",
    "Saudi Arabia": "Suudi Arabistan",
    "Yemen": "Yemen",
    "Oman": "Umman",
    "UAE": "BAE",
    "United Arab Emirates": "BAE",
    "Qatar": "Katar",
    "Kuwait": "Kuveyt",
    "Bahrain": "Bahreyn",
    "Georgia": "Gurcistan",
    "Armenia": "Ermenistan",
    "Azerbaijan": "Azerbaycan",
    "Russia": "Rusya",
    "Ukraine": "Ukrayna",
    "Belarus": "Belarus",
    "Poland": "Polonya",
    "Germany": "Almanya",
    "France": "Fransa",
    "Italy": "Italya",
    "Spain": "Ispanya",
    "Portugal": "Portekiz",
    "United Kingdom": "Birlesik Krallik",
    "UK": "Birlesik Krallik",
    "Great Britain": "Birlesik Krallik",
    "England": "Birlesik Krallik",
    "Ireland": "Irlanda",
    "USA": "ABD",
    "United States": "ABD",
    "Canada": "Kanada",
    "Brazil": "Brezilya",
    "Argentina": "Arjantin",
    "Mexico": "Meksika",
    "Colombia": "Kolombiya",
    "Venezuela": "Venezuela",
    "Chile": "Sili",
    "Peru": "Peru",
    "Ecuador": "Ekvador",
    "Bolivia": "Bolivya",
    "Cuba": "Kuba",
    "Jamaica": "Jamaika",
    "Haiti": "Haiti",
    "Dominican Republic": "Dominik Cumhuriyeti",
    "China": "Cin",
    "Japan": "Japonya",
    "South Korea": "Guney Kore",
    "North Korea": "Kuzey Kore",
    "India": "Hindistan",
    "Pakistan": "Pakistan",
    "Bangladesh": "Bangladeş",
    "Indonesia": "Endonezya",
    "Malaysia": "Malezya",
    "Philippines": "Filipinler",
    "Vietnam": "Vietnam",
    "Thailand": "Tayland",
    "Myanmar": "Myanmar",
    "Cambodia": "Kambocya",
    "Laos": "Laos",
    "Mongolia": "Mogolistan",
    "Australia": "Avustralya",
    "New Zealand": "Yeni Zelanda",
    "Switzerland": "Isvicre",
    "Sweden": "Isvec",
    "Norway": "Norvec",
    "Denmark": "Danimarka",
    "Finland": "Finlandiya",
    "Iceland": "Izlanda",
    "İzlanda": "Izlanda",
    "Netherlands": "Hollanda",
    "Belgium": "Belcika",
    "Austria": "Avusturya",
    "Hungary": "Macaristan",
    "Czech Republic": "Cekya",
    "Czechia": "Cekya",
    "Slovakia": "Slovakya",
    "Suriname": "Surinam",
    "Guyana": "Guyana",
    "Uruguay": "Uruguay",
    "Paraguay": "Paraguay"
}

def normalize():
    with open(EVENTS_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    changed_count = 0
    counts = {}
    
    for ev in data['events']:
        c = ev.get('country_name')
        if not c: continue
        
        # Strip whitespace
        c = c.strip()
        
        # Check mapping
        if c in MAPPING:
            new_c = MAPPING[c]
            if c != new_c:
                ev['country_name'] = new_c
                changed_count += 1
                c = new_c
            
        counts[c] = counts.get(c, 0) + 1
        
    print(f"Normalized {changed_count} events.")
    
    print("Countries with < 10 events:")
    sorted_counts = sorted(counts.items(), key=lambda x: x[1])
    low_counts = 0
    for k, v in sorted_counts:
        if v < 10:
            print(f"{k}: {v}")
            low_counts += 1
    
    if low_counts == 0:
        print("All countries have >= 10 events!")

    with open(EVENTS_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    normalize()
