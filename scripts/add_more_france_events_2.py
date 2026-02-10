#!/usr/bin/env python3
"""
Fransa için ek olaylar ekler (2. parti).
"""

import json
import uuid
from pathlib import Path

def generate_more_france_events_v2():
    """Daha fazla Fransa olayı üret"""
    events = []
    
    france_data = {
        "country_code": "FR",
        "country_name": "Fransa",
        "lat": 46.2276,
        "lon": 2.2137
    }
    
    # Ek olaylar - eksik dekadları tamamlamak için
    additional_events = [
        # 1950s - 5 olay
        ("1950s", 1950, "culture", "Edith Piaf'un Zirve Yılları", "Edith Piaf uluslararası ün kazandı.", ["Edith Piaf"]),
        ("1950s", 1951, "war", "Tunus Bağımsızlık Hareketi", "Habib Bourguiba liderliğindeki bağımsızlık hareketi hızlandı.", ["Habib Bourguiba"]),
        ("1950s", 1953, "culture", "Henri-Georges Clouzot", "'Korku Kovanı' filmi vizyona girdi.", ["Henri-Georges Clouzot"]),
        ("1950s", 1957, "diplomacy", "Roma Antlaşmaları", "Avrupa Ekonomik Topluluğu kuruldu, Fransa kurucu üye.", []),
        ("1950s", 1959, "culture", "Nouvelle Vague Başlangıcı", "François Truffaut '400 Darbe' ile yeni dalga sinemasını başlattı.", ["François Truffaut"]),
        
        # 1960s - 2 olay
        ("1960s", 1960, "culture", "Annie Girardot Yıldızı", "Annie Girardot sinemada yıldız oldu.", ["Annie Girardot"]),
        ("1960s", 1961, "politics", "Referandum Kampanyası", "Cezayir bağımsızlık referandumu kampanyası.", []),
        
        # 1970s - 2 olay
        ("1970s", 1974, "culture", "Claude Berri Sineması", "Claude Berri 'İki Küçük Ayak' filmiyle tanındı.", ["Claude Berri"]),
        ("1970s", 1979, "culture", "Serge Gainsbourg 'Aux armes et cætera'", "Gainsbourg ulusal marşı reggae yorumu yaptı.", ["Serge Gainsbourg"]),
        
        # 1980s - 6 olay
        ("1980s", 1982, "culture", "Leos Carax Filmleri", "Leos Carax 'Yalnızlar' filmiyle tanındı.", ["Leos Carax"]),
        ("1980s", 1983, "politics", "Yabancı Öğrenciler Yasası", "Pasquat yasası tartışmalara yol açtı.", []),
        ("1980s", 1984, "culture", "Les Rita Mitsouko", "Les Rita Mitsouko müzik grubu kuruldu.", []),
        ("1980s", 1984, "politics", "Fabius Hükümeti", "Laurent Fabius başbakan oldu.", ["Laurent Fabius"]),
        ("1980s", 1987, "politics", "Rocard Hükümeti", "Michel Rocard başbakan oldu.", ["Michel Rocard"]),
        ("1980s", 1988, "politics", "Rocardinomics", "Michel Rocard ekonomik reformları başlattı.", []),
        
        # 1990s - 12 olay
        ("1990s", 1990, "culture", "Catherine Deneuve", "Deneuve uluslararası sinema yıldızı olarak zirve yaptı.", ["Catherine Deneuve"]),
        ("1990s", 1991, "culture", "Delicatessen Filmi", "Jean-Pierre Jeunet ve Marc Caro filmi vizyona girdi.", ["Jean-Pierre Jeunet", "Marc Caro"]),
        ("1990s", 1992, "culture", "Béatrice Dalle", "Béatrice Dalle sinema yıldızı oldu.", ["Béatrice Dalle"]),
        ("1990s", 1993, "culture", "Jean-Pierre Jeunet City of Lost Children", "Jeunet fantastik film çekti.", ["Jean-Pierre Jeunet"]),
        ("1990s", 1994, "culture", "Mylène Farmer", "Mylène Farmer popüler şarkıcı oldu.", ["Mylène Farmer"]),
        ("1990s", 1995, "politics", "Juppé Hükümeti", "Alain Juppé başbakan oldu.", ["Alain Juppé"]),
        ("1990s", 1996, "culture", "Romeo ve Juliet", "Baz Luhrmann filmi Paris'te çekildi.", []),
        ("1990s", 1997, "politics", "Aubry Yasaları", "Martine Aubry 35 saat iş haftasını yasallaştırdı.", ["Martine Aubry"]),
        ("1990s", 1997, "culture", "Titanic Paris Prömiyeri", "Titanic Paris'te galasını yaptı.", []),
        ("1990s", 1998, "politics", "Antikorosyon", "Juppé hükümeti yolsuzluk suçlamalarıyla istifa etti.", []),
        ("1990s", 1999, "culture", "Matrix Paris Prömiyeri", "Matrix filmi Paris'te gösterildi.", []),
        ("1990s", 1999, "culture", "Lara Fabian", "Lara Fabian 'Je t'aime' şarkısıyla dünya çapında ün kazandı.", ["Lara Fabian"]),
        
        # 2000s - 10 olay
        ("2000s", 2000, "culture", "Jean-Pierre Jeunet 'Le Fabuleux Destin'", "Amélie filmi vizyona girdi.", ["Jean-Pierre Jeunet"]),
        ("2000s", 2001, "culture", "Le Pacte des Loups", "'Kurtların Ahdı' filmi vizyona girdi.", ["Christophe Gans"]),
        ("2000s", 2003, "culture", "Amélie Broadway Uyarlaması", "Amélie filmi müzikal uyarlaması planlandı.", []),
        ("2000s", 2004, "politics", "Raffarin Hükümeti", "Jean-Pierre Raffarin başbakanlığına son.", []),
        ("2000s", 2005, "culture", "Christophe Willem", "Christophe Willem popüler şarkıcı oldu.", ["Christophe Willem"]),
        ("2000s", 2006, "culture", "Marina Anissina", "Marina Anissina buz pateni Olimpiyat şampiyonu oldu.", ["Marina Anissina"]),
        ("2000s", 2007, "culture", "Bienvenue chez les Ch'tis", "En çok izlenen Fransız filmi rekoru.", ["Dany Boon"]),
        ("2000s", 2008, "culture", "Cédric Klapisch", "'Paris' filmi vizyona girdi.", ["Cédric Klapisch"]),
        ("2000s", 2008, "culture", "Johnny Hallyday Konseri", "Johnny Hallyday Stade de France'da konser verdi.", ["Johnny Hallyday"]),
        ("2000s", 2009, "culture", "Avatar Paris Prömiyeri", "Avatar filmi Paris'te prömiyer yaptı.", []),
        
        # 2010s - 8 olay
        ("2010s", 2010, "culture", "Inception Paris Prömiyeri", "Inception filmi Paris'te prömiyer yaptı.", ["Christopher Nolan"]),
        ("2010s", 2011, "culture", "The Artist Oscarları", "The Artist beş Oscar kazandı.", ["Michel Hazanavicius"]),
        ("2010s", 2012, "culture", "Adele Exarchopoulos", "Adele 'Mavi En Sıcak Renk' filmiyle ödül kazandı.", ["Adele Exarchopoulos"]),
        ("2010s", 2013, "culture", "Space Oddity ISS'den", "Thomas Pesquet ISS'den şarkı söyledi.", ["Thomas Pesquet"]),
        ("2010s", 2014, "culture", "Christine and the Queens", "Christine and the Queens şarkıcı olarak tanındı.", ["Christine and the Queens"]),
        ("2010s", 2015, "culture", "Mylene Farmer Konser", "Mylene Farmer Stade de France konseri.", ["Mylene Farmer"]),
        ("2010s", 2017, "culture", "Dunkirk Prömiyer", "Christopher Nolan filmi Paris'te prömiyer yaptı.", ["Christopher Nolan"]),
        ("2010s", 2019, "culture", "Quentin Tarantino Once Upon a Time", "Tarantino filmi Cannes'de prömiyer yaptı.", ["Quentin Tarantino"]),
        
        # 2020s - 18 olay
        ("2020s", 2020, "politics", "Prime Jean Castex", "Jean Castex başbakan oldu.", ["Jean Castex"]),
        ("2020s", 2021, "culture", "Dune Paris Prömiyer", "Dune filmi Paris'te prömiyer yaptı.", ["Denis Villeneuve"]),
        ("2020s", 2021, "politics", "COVID-19 Geçiş Kartı", "Sağlık geçiş kartı (passe sanitaire) tartışmaları.", []),
        ("2020s", 2022, "politics", "Başbakan Élisabeth Borne", "Élisabeth Borne ilk kadın başbakan oldu.", ["Élisabeth Borne"]),
        ("2020s", 2022, "culture", "Top Gun: Maverick Paris", "Top Gun: Maverick Paris'te prömiyer yaptı.", ["Tom Cruise"]),
        ("2020s", 2022, "war", "Ukrayna Mültecileri", "Fransa 100.000'den fazla Ukraynalı mülteciyi kabul etti.", []),
        ("2020s", 2022, "politics", "Cumhurbaşkanlığı Seçimi", "Macron Marine Le Pen karşısında ikinci turda kazandı.", ["Macron", "Marine Le Pen"]),
        ("2020s", 2023, "culture", "Mission: Impossible Paris", "Tom Cruise Paris'te film çekti.", ["Tom Cruise"]),
        ("2020s", 2023, "politics", "Reform Protestoları Devam", "Emeklilik reformu protestoları yıl boyunca sürdü.", []),
        ("2020s", 2023, "politics", "Başbakan Gabriel Attal", "Gabriel Attal başbakan oldu.", ["Gabriel Attal"]),
        ("2020s", 2024, "culture", "Paris 2024 Hazırlıkları", "Olimpiyat Oyunları için hazırlıklar tamamlandı.", []),
        ("2020s", 2024, "politics", "Avrupa Parlamentosu Seçimleri", "RN partisi seçimleri kazandı.", ["Marine Le Pen"]),
        ("2020s", 2024, "politics", "Başbakan Michel Barnier", "Michel Barnier başbakan oldu.", ["Michel Barnier"]),
        ("2020s", 2024, "culture", "Olympic Games Paris 2024", "Paris üçüncü kez Olimpiyat'a ev sahipliği yaptı.", []),
        ("2020s", 2024, "politics", "Cumhurbaşkanı Macron", "Macron hükümet kriziyle karşı karşıya kaldı.", []),
        ("2020s", 2024, "culture", "Notre-Dame Yeniden Açılış", "Notre-Dame Katedrali restorasyondan sonra açıldı.", []),
        ("2020s", 2025, "politics", "Fransa-Almanya İlişkileri", "Yeni dönemde Fransa-Almanya ilişkileri güçleniyor.", []),
        ("2020s", 2025, "culture", "Yapay Zeka ve Fransa", "Fransa yapay zeka alanında yatırımlarını artırıyor.", []),
    ]
    
    for event_data in additional_events:
        decade, year, category, title, description, key_figures = event_data[0], event_data[1], event_data[2], event_data[3], event_data[4], event_data[5]
        casualties = event_data[6] if len(event_data) > 6 else None
        
        event = {
            "country_code": france_data["country_code"],
            "country_name": france_data["country_name"],
            "lat": france_data["lat"],
            "lon": france_data["lon"],
            "decade": decade,
            "year": year,
            "category": category,
            "title": title,
            "description": description,
            "wikipedia_url": "",
            "casualties": casualties,
            "key_figures": key_figures,
            "id": f"ev{uuid.uuid4().hex[:8]}"
        }
        events.append(event)
    
    return events


def main():
    # Yeni olayları üret
    new_events = generate_more_france_events_v2()
    print(f"Üretilen ek Fransa olayı: {len(new_events)}")
    
    # Mevcut events.json'u oku
    data_path = Path(__file__).parent.parent / "data" / "events.json"
    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Mevcut olay sayısı
    existing_count = len(data['events'])
    print(f"Mevcut toplam olay: {existing_count}")
    
    # Yeni olayları ekle
    data['events'].extend(new_events)
    
    # Kaydet
    with open(data_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"Yeni toplam olay: {len(data['events'])}")
    print(f"Eklenen ek Fransa olayı: {len(new_events)}")
    
    # İstatistik
    france_events = [e for e in data['events'] if e.get('country_code') == 'FR']
    by_decade = {}
    for e in france_events:
        d = e.get('decade', 'unknown')
        by_decade[d] = by_decade.get(d, 0) + 1
    
    print("\nDekadlara göre toplam Fransa olayları:")
    for d in sorted(by_decade.keys()):
        print(f"  {d}: {by_decade[d]} olay")
    
    print(f"\nToplam Fransa olayı: {len(france_events)}")


if __name__ == "__main__":
    main()
