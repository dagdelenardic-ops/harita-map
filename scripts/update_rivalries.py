import json
import os

METADATA_PATH = '/Users/gurursonmez/Documents/Harita/data/country_metadata.json'

# Rivalry Data: Country -> List of (Rival Name, Label, Wikipedia URL)
RIVALRIES = {
    # Europe
    "Turkiye": [
        ("Yunanistan", "Ege ve Kıbrıs Sorunu", "https://tr.wikipedia.org/wiki/K%C4%B1br%C4%B1s_Sorunu"),
        ("Ermenistan", "Tarihsel Gerilim", "https://tr.wikipedia.org/wiki/Ermenistan-T%C3%BCrkiye_ili%C5%9Fkileri"),
        ("Suriye", "Sınır Güvenliği", "https://tr.wikipedia.org/wiki/T%C3%BCrkiye-Suriye_ili%C5%9Fkileri"),
        ("Rusya", "Bölgesel Rekabet", "https://tr.wikipedia.org/wiki/Rusya-T%C3%BCrkiye_ili%C5%9Fkileri")
    ],
    "Yunanistan": [
        ("Türkiye", "Ege ve Kıbrıs Sorunu", "https://tr.wikipedia.org/wiki/Ege_Sorunu")
    ],
    "Rusya": [
        ("Ukrayna", "Rusya-Ukrayna Savaşı", "https://tr.wikipedia.org/wiki/Rusya-Ukrayna_Sava%C5%9F%C4%B1"),
        ("ABD", "Soğuk Savaş / Küresel Güç", "https://tr.wikipedia.org/wiki/So%C4%9Fuk_Sava%C5%9F"),
        ("Polonya", "Tarihsel Gerilim", "https://tr.wikipedia.org/wiki/Polonya-Rusya_ili%C5%9Fkileri"),
        ("Türkiye", "Bölgesel Rekabet", "https://tr.wikipedia.org/wiki/Rusya-T%C3%BCrkiye_ili%C5%9Fkileri")
    ],
    "Ukrayna": [
        ("Rusya", "Bağımsızlık Savaşı", "https://tr.wikipedia.org/wiki/Rusya-Ukrayna_Sava%C5%9F%C4%B1")
    ],
    "Fransa": [
        ("Almanya", "II. Dünya Savaşı", "https://tr.wikipedia.org/wiki/II._D%C3%BCnya_Sava%C5%9F%C4%B1"),
        ("Ingiltere", "Yüzyıl Savaşları / Tarihsel", "https://tr.wikipedia.org/wiki/Fransa-Birle%C5%9Fik_Krall%C4%B1k_ili%C5%9Fkileri")
    ],
    "Almanya": [
        ("Fransa", "II. Dünya Savaşı", "https://tr.wikipedia.org/wiki/II._D%C3%BCnya_Sava%C5%9F%C4%B1"),
        ("Polonya", "II. Dünya Savaşı", "https://tr.wikipedia.org/wiki/II._D%C3%BCnya_Sava%C5%9F%C4%B1"),
        ("Rusya", "II. Dünya Savaşı", "https://tr.wikipedia.org/wiki/Do%C4%9Fu_Cephesi_(II._D%C3%BCnya_Sava%C5%9F%C4%B1)")
    ],
    "Ingiltere": [
        ("Fransa", "Tarihsel Rekabet", "https://tr.wikipedia.org/wiki/Fransa-Birle%C5%9Fik_Krall%C4%B1k_ili%C5%9Fkileri"),
        ("Arjantin", "Falkland Savaşı", "https://tr.wikipedia.org/wiki/Falkland_Sava%C5%9F%C4%B1"),
        ("Almanya", "II. Dünya Savaşı", "https://tr.wikipedia.org/wiki/II._D%C3%BCnya_Sava%C5%9F%C4%B1")
    ],
    
    # Americas
    "ABD": [
        ("Rusya", "Soğuk Savaş", "https://tr.wikipedia.org/wiki/So%C4%9Fuk_Sava%C5%9F"),
        ("Çin", "Ticaret / Tayvan", "https://tr.wikipedia.org/wiki/%C3%87in-AB_ili%C5%9Fkileri"),
        ("Kuzey Kore", "Nükleer Tehdit", "https://tr.wikipedia.org/wiki/Kuzey_Kore-ABD_ili%C5%9Fkileri"),
        ("Vietnam", "Vietnam Savaşı", "https://tr.wikipedia.org/wiki/Vietnam_Sava%C5%9F%C4%B1")
    ],
    "Brezilya": [
        ("Arjantin", "Bölgesel Liderlik", "https://en.wikipedia.org/wiki/Argentina%E2%80%93Brazil_relations")
    ],
    "Arjantin": [
        ("Ingiltere", "Falkland Savaşı", "https://tr.wikipedia.org/wiki/Falkland_Sava%C5%9F%C4%B1"),
        ("Brezilya", "Bölgesel Liderlik", "https://en.wikipedia.org/wiki/Argentina%E2%80%93Brazil_relations")
    ],
    
    # Asia
    "Cin": [
        ("ABD", "Tayvan / Pasifik", "https://tr.wikipedia.org/wiki/%C3%87in-Tayvan_ili%C5%9Fkileri"),
        ("Japonya", "II. Dünya Savaşı / Adalar", "https://tr.wikipedia.org/wiki/%C3%87in-Japonya_ili%C5%9Fkileri"),
        ("Hindistan", "Sınır Çatışmaları", "https://tr.wikipedia.org/wiki/%C3%87in-Hindistan_ili%C5%9Fkileri"),
        ("Tayvan", "Egemenlik Sorunu", "https://tr.wikipedia.org/wiki/Tayvan_Sorunu")
    ],
    "Japonya": [
        ("Çin", "Senkaku Adaları", "https://en.wikipedia.org/wiki/Senkaku_Islands_dispute"),
        ("Kuzey Kore", "Füze Tehdidi", "https://en.wikipedia.org/wiki/Japan%E2%80%93North_Korea_relations"),
        ("Rusya", "Kuril Adaları", "https://tr.wikipedia.org/wiki/Kuril_Adalar%C4%B1_anla%C5%9Fmazl%C4%B1%C4%9F%C4%B1"),
        ("ABD", "II. Dünya Savaşı", "https://tr.wikipedia.org/wiki/Pasifik_Cephesi_(II._D%C3%BCnya_Sava%C5%9F%C4%B1)")
    ],
    "Hindistan": [
        ("Pakistan", "Keşmir Sorunu", "https://tr.wikipedia.org/wiki/Ke%C5%9Fmir_Sorunu"),
        ("Çin", "Sınır Çatışmaları", "https://tr.wikipedia.org/wiki/%C3%87in-Hindistan_ili%C5%9Fkileri")
    ],
    "Pakistan": [
        ("Hindistan", "Keşmir Sorunu", "https://tr.wikipedia.org/wiki/Ke%C5%9Fmir_Sorunu")
    ],
    "Guney Kore": [
        ("Kuzey Kore", "Kore Savaşı", "https://tr.wikipedia.org/wiki/Kore_Sava%C5%9F%C4%B1"),
        ("Japonya", "Tarihsel Sorunlar", "https://en.wikipedia.org/wiki/Japan%E2%80%93South_Korea_relations")
    ],
    "Kuzey Kore": [
        ("Guney Kore", "Kore Savaşı", "https://tr.wikipedia.org/wiki/Kore_Sava%C5%9F%C4%B1"),
        ("ABD", "Kore Savaşı / Nükleer", "https://tr.wikipedia.org/wiki/Kore_Sava%C5%9F%C4%B1")
    ],
    
    # Middle East
    "Iran": [
        ("Suudi Arabistan", "Vekalet Savaşları", "https://tr.wikipedia.org/wiki/%C4%B0ran-Suudi_Arabistan_ili%C5%9Fkileri"),
        ("Israil", "Vekalet Savaşları", "https://tr.wikipedia.org/wiki/%C4%B0ran-%C4%B0srail_ili%C5%9Fkileri"),
        ("Irak", "İran-Irak Savaşı", "https://tr.wikipedia.org/wiki/%C4%B0ran-Irak_Sava%C5%9F%C4%B1"),
        ("ABD", "1979 Devrimi / Nükleer", "https://tr.wikipedia.org/wiki/ABD-%C4%B0ran_ili%C5%9Fkileri")
    ],
    "Suudi Arabistan": [
        ("Iran", "Vekalet Savaşları", "https://tr.wikipedia.org/wiki/%C4%B0ran-Suudi_Arabistan_ili%C5%9Fkileri")
    ],
    "Israil": [
        ("Filistin", "Toprak Sorunu", "https://tr.wikipedia.org/wiki/%C4%B0srail-Filistin_%C3%A7at%C4%B1%C5%9Fmas%C4%B1"),
        ("Iran", "Güvenlik Tehdidi", "https://tr.wikipedia.org/wiki/%C4%B0ran-%C4%B0srail_ili%C5%9Fkileri"),
        ("Suriye", "Golan Tepeleri", "https://tr.wikipedia.org/wiki/Alt%C4%B1_G%C3%BCn_Sava%C5%9F%C4%B1")
    ],
    
    # Others
    "Azerbaycan": [
        ("Ermenistan", "Karabağ Savaşı", "https://tr.wikipedia.org/wiki/Da%C4%9Fl%C4%B1k_Karaba%C4%9F_Sorunu")
    ],
    "Ermenistan": [
        ("Azerbaycan", "Karabağ Savaşı", "https://tr.wikipedia.org/wiki/Da%C4%9Fl%C4%B1k_Karaba%C4%9F_Sorunu"),
        ("Türkiye", "1915 ve Sınır", "https://tr.wikipedia.org/wiki/Ermenistan-T%C3%BCrkiye_ili%C5%9Fkileri")
    ],
    "Sirbistan": [
        ("Kosova", "Bağımsızlık Sorunu", "https://tr.wikipedia.org/wiki/Kosova_Sava%C5%9F%C4%B1"),
        ("Hırvatistan", "Yugoslav İç Savaşı", "https://tr.wikipedia.org/wiki/H%C4%B1rvatistan_Sava%C5%9F%C4%B1"),
        ("Bosna-Hersek", "Bosna Savaşı", "https://tr.wikipedia.org/wiki/Bosna_Sava%C5%9F%C4%B1")
    ],
    "Misir": [
        ("Etiyopya", "Nil Suları Krizi", "https://en.wikipedia.org/wiki/Grand_Ethiopian_Renaissance_Dam")
    ],
    "Etiyopya": [
        ("Misir", "Nil Suları Krizi", "https://en.wikipedia.org/wiki/Grand_Ethiopian_Renaissance_Dam"),
        ("Eritre", "Bağımsızlık Savaşı", "https://tr.wikipedia.org/wiki/Eritre-Etiyopya_Sava%C5%9F%C4%B1")
    ],
    
    # Duplicates/Alt Names for robust matching
    "Türkiye": [
        ("Yunanistan", "Ege ve Kıbrıs Sorunu", "https://tr.wikipedia.org/wiki/K%C4%B1br%C4%B1s_Sorunu"),
        ("Ermenistan", "Tarihsel Gerilim", "https://tr.wikipedia.org/wiki/Ermenistan-T%C3%BCrkiye_ili%C5%9Fkileri"),
        ("Suriye", "Sınır Güvenliği", "https://tr.wikipedia.org/wiki/T%C3%BCrkiye-Suriye_ili%C5%9Fkileri"),
        ("Rusya", "Bölgesel Rekabet", "https://tr.wikipedia.org/wiki/Rusya-T%C3%BCrkiye_ili%C5%9Fkileri")
    ],
    "Turkey": [("Greece", "Aegean/Cyprus", "https://en.wikipedia.org/wiki/Cyprus_problem")],
    "China": [("USA", "Trade/Taiwan", "https://en.wikipedia.org/wiki/China%E2%80%93United_States_relations")],
    "United States": [("Russia", "Cold War", "https://en.wikipedia.org/wiki/Cold_War"), ("China", "Trade/Taiwan", "https://en.wikipedia.org/wiki/China%E2%80%93United_States_relations")],
}

def update_metadata():
    if not os.path.exists(METADATA_PATH):
        print(f"Error: {METADATA_PATH} not found.")
        return

    with open(METADATA_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    count = 0
    # Normalize keys: check both exact match and lowercase match
    existing_keys_lower = {k.lower(): k for k in data.keys()}

    for country, conflicts in RIVALRIES.items():
        target_key = None
        
        # Try direct match
        if country in data:
            target_key = country
        # Try case-insensitive match
        elif country.lower() in existing_keys_lower:
            target_key = existing_keys_lower[country.lower()]
        
        if target_key:
            # Construct dictionary of rivalries
            rivalry_list = []
            for rival, label, url in conflicts:
                rivalry_list.append({
                    "rival": rival,
                    "text": label,
                    "url": url
                })
            
            data[target_key]['rivalries'] = rivalry_list
            count += 1
        else:
            # Create new if needed
            print(f"Creating metadata entry for: {country}")
            rivalry_list = []
            for rival, label, url in conflicts:
                rivalry_list.append({
                    "rival": rival,
                    "text": label,
                    "url": url
                })

            data[country] = {
                "rivalries": rivalry_list,
                "predecessor": "-",
                "demographics": "-"
            }
            count += 1

    with open(METADATA_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    print(f"Updated {count} countries with detailed rivalry data (list of objects).")

if __name__ == "__main__":
    update_metadata()
