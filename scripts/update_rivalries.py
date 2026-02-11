import json
import os

METADATA_PATH = 'data/country_metadata.json'

updates = {
    "Rusya": [
        {"rival": "Ukrayna", "text": "Rusya-Ukrayna Savaşı (~28,300 ölüm/yıl)", "year": "2022-Devam", "status": "active"},
        {"rival": "ABD", "text": "Soğuk Savaş (Miras)", "year": "1947-1991", "status": "historical"}
    ],
    "Ukrayna": [
        {"rival": "Rusya", "text": "Rusya-Ukrayna Savaşı (Varlık Mücadelesi)", "year": "2022-Devam", "status": "active"}
    ],
    "İsrail": [
        {"rival": "Hamas", "text": "İsrail-Gazze Savaşı (7,700+ ölüm)", "year": "2023-Devam", "status": "active"},
        {"rival": "Hizbullah", "text": "Kuzey Cephesi Çatışmaları", "year": "2023-Devam", "status": "active"},
        {"rival": "Filistin", "text": "Batı Şeria Gerilimi", "year": "1948-Devam", "status": "active"}
    ],
    "Filistin": [
         {"rival": "İsrail", "text": "Bağımsızlık ve Toprak Mücadelesi", "year": "1948-Devam", "status": "active"}
    ],
    "Sudan": [
        {"rival": "Hızlı Destek Kuvvetleri", "text": "Sudan İç Savaşı (SAF vs RSF)", "year": "2023-Devam", "status": "active"}
    ],
    "Pakistan": [
        {"rival": "Keşmir Militanları", "text": "Keşmir Sınır Gerilimi", "year": "1947-Devam", "status": "active"},
        {"rival": "ISKP", "text": "Terör Saldırıları", "year": "2015-Devam", "status": "active"}
    ],
    "Nijerya": [
        {"rival": "Boko Haram", "text": "Boko Haram İsyanı", "year": "2009-Devam", "status": "active"},
        {"rival": "ISWAP", "text": "IŞİD Batı Afrika Kolu", "year": "2015-Devam", "status": "active"}
    ],
    "Etiyopya": [
        {"rival": "Amhara", "text": "Fano Milisleri Çatışması", "year": "2023-Devam", "status": "active"},
        {"rival": "Oromia", "text": "OLA İsyanı", "year": "2018-Devam", "status": "active"}
    ],
    "Somali": [
        {"rival": "Al-Shabaab", "text": "El-Şebab ile İç Savaş", "year": "2006-Devam", "status": "active"}
    ],
    "Suriye": [
        {"rival": "Suriye Muhalifleri", "text": "Suriye İç Savaşı", "year": "2011-Devam", "status": "active"},
        {"rival": "HTS", "text": "İdlib Çatışmaları", "year": "2017-Devam", "status": "active"}
    ],
    "Yemen": [
        {"rival": "Husiler", "text": "Yemen İç Savaşı", "year": "2014-Devam", "status": "active"}
    ],
    "Burkina Faso": [
        {"rival": "Cihatçı Gruplar (Sahel)", "text": "Sahel İslamcı İsyanı", "year": "2015-Devam", "status": "active"}
    ],
    "Meksika": [
        {"rival": "Meksika Kartelleri", "text": "Meksika Uyuşturucu Savaşı", "year": "2006-Devam", "status": "active"}
    ],
    "Demokratik Kongo Cumhuriyeti": [
        {"rival": "M23", "text": "Kivu Çatışması (M23)", "year": "2012-Devam", "status": "active"}
    ],
    "Myanmar": [
        {"rival": "Myanmar Direnişi", "text": "Myanmar İç Savaşı", "year": "2021-Devam", "status": "active"}
    ],
    "Haiti": [
        {"rival": "Haiti Çeteleri", "text": "Çete Savaşları (G9)", "year": "2020-Devam", "status": "active"}
    ],
    "Ekvador": [
        {"rival": "Ekvador Çeteleri", "text": "Uyuşturucu Çeteleri Çatışması", "year": "2018-Devam", "status": "active"}
    ],
    "Mali": [
        {"rival": "JNIM", "text": "Mali Savaşı (Cihatçı Gruplar)", "year": "2012-Devam", "status": "active"}
    ],
    "Brezilya": [
        {"rival": "PCC", "text": "Çete Savaşları (PCC/CV)", "year": "2006-Devam", "status": "active"}
    ],
    "Afganistan": [
        {"rival": "ISKP", "text": "IŞİD-Horasan Çatışması", "year": "2015-Devam", "status": "active"}
    ],
    "Lübnan": [
        {"rival": "İsrail", "text": "Hizbullah-İsrail Çatışması", "year": "2023-Devam", "status": "active"}
    ],
    "Venezuela": [
        {"rival": "ABD", "text": "Siyasi Gerilim ve Yaptırımlar", "year": "2014-Devam", "status": "active"}
    ],
    "Mozambik": [
        {"rival": "Cabo Delgado İsyancıları", "text": "Cabo Delgado İsyanı", "year": "2017-Devam", "status": "active"}
    ],
    "Kolombiya": [
        {"rival": "ELN", "text": "Kolombiya Çatışması", "year": "1964-Devam", "status": "active"}
    ],
    "Irak": [
        {"rival": "ISIS", "text": "IŞİD Kalıntıları ile Mücadele", "year": "2014-Devam", "status": "active"}
    ],
    "Libya": [
        {"rival": "Libya Doğusu (Haftar)", "text": "Siyasi Bölünme ve Çatışmalar", "year": "2014-Devam", "status": "active"}
    ],
    "Hindistan": [
        {"rival": "Keşmir Militanları", "text": "Keşmir Çatışması", "year": "1989-Devam", "status": "active"}
    ],
    "Tayland": [
        {"rival": "Güney Tayland İsyancıları", "text": "Güney Tayland İsyanı", "year": "2004-Devam", "status": "active"}
    ],
    "Filipinler": [
        {"rival": "NPA", "text": "Komünist İsyan", "year": "1969-Devam", "status": "active"},
        {"rival": "Abu Sayyaf", "text": "Moro Çatışması", "year": "1991-Devam", "status": "active"}
    ],
    "Bangladeş": [
        {"rival": "Bangladeş Militanları", "text": "İç İstikrarsızlık", "year": "2013-Devam", "status": "active"}
    ],
    "Endonezya": [
        {"rival": "Papua Ayrılıkçıları", "text": "Papua Çatışması", "year": "1963-Devam", "status": "active"}
    ],
    "Nijer": [
        {"rival": "Cihatçı Gruplar (Sahel)", "text": "Sahel Krizi", "year": "2015-Devam", "status": "active"}
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
            # Preserve existing if any, but override same rivals
            existing = data[country].get('rivalries', [])
            # Map existing by rival name for easy update
            existing_map = {r['rival']: r for r in existing}
            
            for new_r in rivalries:
                existing_map[new_r['rival']] = new_r
                
            # Convert back to list
            data[country]['rivalries'] = list(existing_map.values())
            print(f"Updated {country} with {len(rivalries)} active rivalries.")
        else:
            print(f"Warning: Country '{country}' not found in metadata.")

    with open(METADATA_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
        
    print("Successfully updated metadata.")

if __name__ == "__main__":
    main()
