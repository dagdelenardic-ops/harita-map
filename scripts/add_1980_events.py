import json
import os

events_path = '/Users/gurursonmez/Documents/Harita/data/events.json'

# Manual list of 1980 events (Translated)
# Format: Country, Year, Category (mapped), Title, Description
new_events_data = [
    ("Birlesik Krallik", 1980, "culture", "Çelik İşçileri Grevi", "İngiliz çelik işçileri 1926'dan beri ilk kez ulusal greve gitti."),
    ("Hindistan", 1980, "leader", "Indira Gandhi'nin Dönüşü", "Indira Gandhi'nin Kongre Partisi seçimleri kazandı."),
    ("ABD", 1980, "culture", "Chrysler Kurtarma Paketi", "Başkan Carter, Chrysler için 1.5 milyar dolarlık kurtarma paketini onayladı."),
    ("Japonya", 1980, "culture", "Paul McCartney Tutuklandı", "Tokyo havaalanında uyuşturucu bulundurmaktan tutuklandı ve sınır dışı edildi."),
    ("ABD", 1980, "war", "Moskova Olimpiyatları Boykotu", "Başkan Carter, ABD'nin Moskova Olimpiyatlarını boykot edeceğini açıkladı."),
    ("Guatemala", 1980, "terror", "İspanyol Büyükelçiliği Yangını", "Büyükelçilik işgal edildi ve ateşe verildi, 36 kişi öldü."),
    ("Iran", 1980, "leader", "Beni Sadr İlk Başkan", "Ebu'l-Hasan Beni Sadr, İran'ın ilk cumhurbaşkanı olarak yemin etti."),
    ("ABD", 1980, "culture", "Buz Üzerinde Mucize (Miracle on Ice)", "Kış Olimpiyatları'nda ABD buz hokeyi takımı favori SSCB'yi yendi."),
    ("Kolombiya", 1980, "terror", "Dominik Büyükelçiliği Kuşatması", "M-19 gerillaları büyükelçiliği kuşattı ve rehineler aldı."),
    ("Zimbabve", 1980, "leader", "Mugabe Başbakan Seçildi", "Robert Mugabe Zimbabve başbakanı seçildi."),
    ("El Salvador", 1980, "leader", "Başpiskopos Romero Suikastı", "Başpiskopos Óscar Romero ayin sırasında öldürüldü."),
    ("Norveç", 1980, "war", "Petrol Platformu Faciası", "Alexander L. Kielland platformu Kuzey Denizi'nde çöktü, 123 kişi öldü."),
    ("Israil", 1980, "culture", "Talpiot Mezarı Bulundu", "Kudüs'te Talpiot Mezarı keşfedildi."),
    ("Liberia", 1980, "revolution", "Samuel Doe Darbesi", "Samuel K. Doe kanlı bir darbe ile yönetimi ele geçirdi."),
    ("Kanada", 1980, "culture", "Umudun Maratonu (Marathon of Hope)", "Terry Fox kanser araştırmaları için Kanada'yı koşarak geçmeye başladı."),
    ("Zimbabve", 1980, "revolution", "Bağımsızlık", "Zimbabve Birleşik Krallık'tan bağımsızlığını kazandı."),
    ("Ispanya", 1980, "war", "Dan-Air Uçak Kazası", "Tenerife'de Dan-Air Flight 1008 düştü, 146 kişi öldü."),
    ("Hollanda", 1980, "leader", "Kraliçe Beatrix", "Kraliçe Juliana tahttan çekildi, kızı Beatrix tahta geçti."),
    ("Sırbistan", 1980, "leader", "Tito'nun Ölümü", "Yugoslavya lideri Josip Broz Tito hayatını kaybetti."), # Mapping Yugoslavia to Serbia (Sırbistan) for coordinate reference usually
    ("Turkiye", 1980, "culture", "Nihat Erim Suikastı", "Eski Başbakan Nihat Erim İstanbul'da öldürüldü."),
    ("ABD", 1980, "culture", "St. Helens Yanardağı Patlaması", "Washington eyaletinde yanardağ patladı, 57 kişi öldü."),
    ("Birlesik Krallik", 1980, "culture", "Ian Curtis'in Ölümü", "Joy Division solisti Ian Curtis hayatını kaybetti."),
    ("Guney Kore", 1980, "revolution", "Gwangju Ayaklanması", "Demokratik reform talebiyle öğrenci gösterileri başladı."),
    ("Japonya", 1980, "culture", "Pac-Man Çıktı", "Efsanevi video oyunu Pac-Man Japonya'da piyasaya sürüldü."),
    ("ABD", 1980, "culture", "CNN Yayına Başladı", "İlk 24 saatlik haber kanalı CNN yayına girdi."),
    ("Italya", 1980, "war", "Ustica Katliamı (Itavia Flight 870)", "Yolcu uçağı denize düştü/düşürüldü, 81 kişi öldü."),
    ("Izlanda", 1980, "leader", "Vigdís Finnbogadóttir", "Dünyanın demokratik yolla seçilen ilk kadın devlet başkanı oldu."),
    ("Rusya", 1980, "culture", "1980 Moskova Olimpiyatları", "Birçok batılı ülkenin boykot ettiği olimpiyatlar yapıldı."),
    ("Cin", 1980, "culture", "Nüfus 1 Milyar", "Çin nüfusu 1 milyara ulaştı."),
    ("Italya", 1980, "terror", "Bologna İstasyonu Saldırısı", "Tren istasyonundaki bombalı saldırıda 85 kişi öldü."),
    ("Polonya", 1980, "revolution", "Gdansk Anlaşması ve Dayanışma", "Lech Walesa önderliğinde Dayanışma (Solidarity) sendikası kuruldu."),
    ("Turkiye", 1980, "revolution", "12 Eylül Darbesi", "Kenan Evren liderliğinde ordu yönetime el koydu."),
    ("Irak", 1980, "war", "İran-Irak Savaşı", "Irak'ın saldırısıyla 8 yıl sürecek savaş başladı."),
    ("Almanya", 1980, "terror", "Oktoberfest Saldırısı", "Münih'teki saldırıda 13 kişi öldü."),
    ("ABD", 1980, "culture", "John Lennon'ın Ölümü", "Efsanevi müzisyen New York'ta vurularak öldürüldü.")
]

# Country name map (My Turkish naming to Events.json country_name)
# Trying to match existing names in events.json
COUNTRY_NAME_FIX = {
    "Turkiye": "Turkiye", # Or "Türkiye" depending on file. Will normalize.
    "ABD": "ABD",
    "Birlesik Krallik": "Birlesik Krallik",
    "Japonya": "Japonya",
    "Japonya": "Japonya",
    "Japonya": "Japonya",
    "Guney Kore": "Guney Kore",
    "Izlanda": "İzlanda", # Check capitalization
    "Ispanya": "Ispanya",
    "Sırbistan": "Sırbistan", # For Yugoslavia events if needed, checking file content for mapped names
}

def load_events():
    with open(events_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_coords(events_data, country_name):
    # Try to find a lat/lon for this country from existing events
    for ev in events_data['events']:
        if ev.get('country_name') == country_name and ev.get('lat') != 0:
            return ev['lat'], ev['lon']
        # Also try similar names
        if country_name == "Sırbistan" and ev.get('country_name') in ["Sırbistan", "Yugoslavya", "Serbia"]:
             return ev['lat'], ev['lon']
        if country_name == "Izlanda" and ev.get('country_name') in ["İzlanda", "Iceland"]:
             return ev['lat'], ev['lon']
             
    return 0, 0

def add_events():
    data = load_events()
    existing_ids = set(ev['id'] for ev in data['events'])
    
    cnt = 0
    for c_name, year, cat, title, desc in new_events_data:
        # Generate ID
        new_id = f"ev_1980_{cnt}"
        while new_id in existing_ids:
            cnt += 1
            new_id = f"ev_1980_{cnt}"
        
        # Get coords
        lat, lon = get_coords(data, c_name)
        
        # Specialized fix if coords not found (generic centers)
        if lat == 0 and lon == 0:
            if c_name == "Turkiye": lat, lon = 39.0, 35.0
            elif c_name == "ABD": lat, lon = 37.09, -95.71
            elif c_name == "Birlesik Krallik": lat, lon = 55.0, -3.0
            elif c_name == "Japonya": lat, lon = 36.0, 138.0
            elif c_name == "Hindistan": lat, lon = 20.0, 77.0
            elif c_name == "Guatemala": lat, lon = 15.7, -90.2
            elif c_name == "Iran": lat, lon = 32.0, 53.0
            elif c_name == "Kolombiya": lat, lon = 4.0, -72.0
            elif c_name == "Zimbabve": lat, lon = -19.0, 29.0
            elif c_name == "El Salvador": lat, lon = 13.7, -88.9
            elif c_name == "Norveç": lat, lon = 60.0, 8.0
            elif c_name == "Israil": lat, lon = 31.0, 35.0
            elif c_name == "Liberia": lat, lon = 6.4, -9.4
            elif c_name == "Kanada": lat, lon = 56.0, -106.0
            elif c_name == "Ispanya": lat, lon = 40.0, -3.7
            elif c_name == "Hollanda": lat, lon = 52.0, 5.0
            elif c_name == "Sırbistan": lat, lon = 44.0, 21.0
            elif c_name == "Guney Kore": lat, lon = 35.9, 127.7
            elif c_name == "Italya": lat, lon = 41.8, 12.5
            elif c_name == "Izlanda": lat, lon = 64.9, -19.0
            elif c_name == "Rusya": lat, lon = 61.0, 105.0
            elif c_name == "Cin": lat, lon = 35.0, 105.0
            elif c_name == "Polonya": lat, lon = 52.0, 19.0
            elif c_name == "Irak": lat, lon = 33.0, 43.0
            elif c_name == "Almanya": lat, lon = 51.0, 10.0

        new_event = {
            "country_code": "", 
            "country_name": c_name,
            "lat": lat,
            "lon": lon,
            "decade": "1980s",
            "year": year,
            "category": cat,
            "title": title,
            "description": desc,
            "wikipedia_url": "",
            "casualties": None,
            "key_figures": [],
            "id": new_id
        }
        
        data['events'].append(new_event)
        existing_ids.add(new_id)
        cnt += 1

    print(f"Added {cnt} new events.")
    
    with open(events_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    add_events()
