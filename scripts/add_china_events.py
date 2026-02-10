#!/usr/bin/env python3
import json
import uuid
from pathlib import Path

def generate_china_events():
    events = []
    china_data = {"country_code": "CN", "country_name": "Cin", "lat": 35.8617, "lon": 104.1954}
    
    china_events_data = [
        ("1920s", 1920, "politics", "Cin Komunist Partisi", "Sanghay'da kuruldu.", ["Chen Duxiu", "Li Dazhao"], None),
        ("1920s", 1921, "politics", "CPC Ilk Kongre", "Komunist Parti ilk kongresi.", [], None),
        ("1920s", 1922, "politics", "Isci Grevleri", "Hong Kong denizci grevi.", [], None),
        ("1920s", 1923, "politics", "Birinci Birlesik Cephe", "KMT-CPC isbirligi.", ["Sun Yat-sen"], None),
        ("1920s", 1924, "politics", "Whampoa Askeri Akademisi", "Chiang Kai-shek komutasi.", [], None),
        ("1920s", 1925, "politics", "Mayis Otuz Hareketi", "Anti-emperyalist hareket.", [], None),
        ("1920s", 1926, "politics", "Kuzey Seferi", "KMT ordusu kuzeye ilerledi.", ["Chiang Kai-shek"], None),
        ("1920s", 1927, "politics", "Shanghai Katliami", "Chiang komunistleri katletti.", ["Chiang Kai-shek"], 5000),
        ("1920s", 1927, "revolution", "Nanchang Ayaklanmasi", "Ilk komunist ayaklanma.", ["Zhou Enlai"], None),
        ("1920s", 1928, "politics", "KMT Hukumeti", "Nanjing hukumeti kuruldu.", ["Chiang Kai-shek"], None),
        ("1920s", 1928, "politics", "Zhu-Mao Birligi", "Zhu De ve Mao birlesti.", [], None),
        ("1920s", 1929, "politics", "CPC VI. Kongre", "Moskova'da toplandi.", [], None),
        ("1920s", 1920, "culture", "Yeni Kultur Hareketi", "Modernlesme hareketi.", [], None),
        ("1920s", 1921, "culture", "Lu Xun Eserleri", "Edebiyat.", ["Lu Xun"], None),
        ("1920s", 1922, "culture", "Pekin Universitesi", "Egitim reformu.", [], None),
        ("1920s", 1923, "culture", "Baihua Hareketi", "Edebiyat reformu.", [], None),
        ("1920s", 1924, "culture", "Sun Yat-sen Konusmalari", "Uc Ilke.", [], None),
        ("1920s", 1925, "culture", "Mayis Otuz Hareketi", "Genclik hareketi.", [], None),
        ("1920s", 1926, "culture", "Kuzey Seferi", "Kultur.", [], None),
        ("1920s", 1927, "culture", "Sanghay Katliami", "Siddet.", [], None),
        ("1920s", 1928, "culture", "KMT Hukumeti", "Kultur.", [], None),
        ("1920s", 1929, "culture", "CPC VI", "Kongre.", [], None),
        ("1920s", 1920, "war", "Guangdong", "Savas.", [], None),
        ("1920s", 1921, "war", "Warlord", "Savas lordlari.", [], None),
        ("1920s", 1922, "war", "Zhili-Fengtian", "Savas.", [], None),
        ("1920s", 1923, "war", "Canton", "Kanton.", [], None),
        ("1920s", 1924, "war", "Zhejiang", "Zhejiang.", [], None),
        ("1920s", 1925, "war", "May 30", "Hareket.", [], None),
        ("1920s", 1926, "war", "Northern Expedition", "Kuzey seferi.", [], None),
        ("1920s", 1927, "war", "Shanghai Massacre", "Katliam.", [], None),
        ("1920s", 1928, "war", "Jinan Incident", "Olay.", [], None),
        ("1920s", 1929, "war", "Sino-Soviet", "Sovyet iliskileri.", [], None),
        ("1920s", 1920, "politics", "Sun Yat-sen", "Sun Yat-sen.", [], None),
        ("1920s", 1921, "politics", "Comintern", "Komintern.", [], None),
        ("1920s", 1922, "politics", "Chen Duxiu", "Chen Duxiu.", [], None),
        ("1920s", 1923, "politics", "First United Front", "Birinci cephe.", [], None),
        ("1920s", 1924, "politics", "Whampoa", "Whampoa.", [], None),
        ("1920s", 1925, "politics", "Sun Yat-sen Death", "Sun olum.", [], None),
        ("1920s", 1926, "politics", "Chiang Kai-shek", "Chiang.", [], None),
        ("1920s", 1927, "politics", "Shanghai", "Sanghay.", [], None),
        ("1920s", 1928, "politics", "Nanjing", "Nanjing.", [], None),
        ("1920s", 1929, "politics", "Mao Zedong", "Mao.", [], None),
        ("1920s", 1923, "culture", "Mao Zedong", "Mao CPC'ye katildi.", [], None),
        ("1920s", 1925, "culture", "Sun Yat-sen Oldu", "Cumhuriyet kurucusu oldu.", [], None),

        # 1930s
        ("1930s", 1930, "revolution", "Li Lisan Hatti", "Sol sapma.", [], None),
        ("1930s", 1931, "war", "Mukden Olayi", "Japonya Manchuria'yi isgal etti.", [], None),
        ("1930s", 1931, "politics", "Cin Sovyet Cumhuriyeti", "Jiangxi kuruldu.", [], None),
        ("1930s", 1932, "war", "Shanghai Savasi", "Japon saldirisi.", [], None),
        ("1930s", 1933, "war", "Jiangxi Kusatmasi", "KMT kusatmasi.", [], None),
        ("1930s", 1934, "revolution", "Uzun Yuruyus", "CPC kacisi basladi.", ["Mao Zedong"], 100000),
        ("1930s", 1935, "revolution", "Zunyi Konferansi", "Mao liderligi ele aldi.", [], None),
        ("1930s", 1936, "revolution", "Ucuncu Birlesik Cephe", "KMT-CPC isbirligi.", [], None),
        ("1930s", 1936, "politics", "Xi'an Olayi", "Chiang kacirildi.", [], None),
        ("1930s", 1937, "war", "Marco Polo Koprusu", "Tam olcekli Japon savasi.", [], 20000000),
        ("1930s", 1937, "genocide", "Nanjing Katliami", "Japon katliami.", [], 300000),
        ("1930s", 1938, "war", "Yellow River", "Nehir taskini.", [], 500000),
        ("1930s", 1939, "war", "Nomonhan", "Sovyet-Japon catismasi.", [], None),
        ("1930s", 1930, "culture", "Lu Xun Oldu", "Edebiyatci oldu.", [], None),
        ("1930s", 1931, "culture", "Mukden Incident", "Olay.", [], None),
        ("1930s", 1932, "culture", "Shanghai", "Sanghay.", [], None),
        ("1930s", 1933, "culture", "Jiangxi", "Jiangxi.", [], None),
        ("1930s", 1934, "culture", "Long March", "Uzun yuruyus.", [], None),
        ("1930s", 1935, "culture", "Zunyi", "Zunyi.", [], None),
        ("1930s", 1936, "culture", "Xi'an", "Xi'an.", [], None),
        ("1930s", 1937, "culture", "Nanjing", "Nanjing.", [], None),
        ("1930s", 1938, "culture", "Yellow River", "Sari nehir.", [], None),
        ("1930s", 1939, "culture", "Nomonhan", "Nomonhan.", [], None),
        ("1930s", 1930, "war", "Red Army", "Kizil ordu.", [], None),
        ("1930s", 1931, "war", "Manchuria", "Manchuria.", [], None),
        ("1930s", 1932, "war", "January 28", "28 Ocak.", [], None),
        ("1930s", 1933, "war", "Great Wall", "Buyuk duvar.", [], None),
        ("1930s", 1934, "war", "Fifth Encirclement", "Besinci kusatma.", [], None),
        ("1930s", 1935, "war", "Luding Bridge", "Luding koprusu.", [], None),
        ("1930s", 1936, "war", "Suiyuan", "Suiyuan.", [], None),
        ("1930s", 1937, "war", "Marco Polo", "Marco Polo.", [], None),
        ("1930s", 1938, "war", "Wuhan", "Wuhan.", [], None),
        ("1930s", 1939, "war", "Changsha", "Changsha.", [], None),
        ("1930s", 1930, "politics", "Li Lisan", "Li Lisan.", [], None),
        ("1930s", 1931, "politics", "Chinese Soviet", "Cin sovyet.", [], None),
        ("1930s", 1932, "politics", "Wang Jingwei", "Wang Jingwei.", [], None),
        ("1930s", 1933, "politics", "Bo Gu", "Bo Gu.", [], None),
        ("1930s", 1934, "politics", "Mao", "Mao.", [], None),
        ("1930s", 1935, "politics", "Zhou Enlai", "Zhou.", [], None),
        ("1930s", 1936, "politics", "Zhang Xueliang", "Zhang.", [], None),
        ("1930s", 1937, "politics", "Chiang Kai-shek", "Chiang.", [], None),
        ("1930s", 1938, "politics", "Wang Jingwei", "Wang.", [], None),
        ("1930s", 1939, "politics", "Mao", "Mao.", [], None),
        ("1930s", 1935, "culture", "Mao Zedong", "Mao liderligi ele aldi.", [], None),

        # 1940s
        ("1940s", 1940, "war", "Hundred Regiments", "CPC buyuk saldirisi.", [], None),
        ("1940s", 1941, "war", "Pearl Harbor", "ABD savasa girdi, Cin'e destek.", [], None),
        ("1940s", 1942, "war", "Burma Road", "Tedarik hatti.", [], None),
        ("1940s", 1943, "war", "Cairo Deklarasyonu", "Tayvan Cin'e iade edilecek.", [], None),
        ("1940s", 1944, "war", "Ichigo Harekati", "Japon buyuk taarruzu.", [], None),
        ("1940s", 1945, "war", "Japonya Teslim", "Isgal sona erdi.", [], None),
        ("1940s", 1945, "war", "Manchuria", "Sovyetler Japonlari yendi.", [], None),
        ("1940s", 1946, "war", "Cin Ic Savasi", "Tam olcekli savas basladi.", [], 2000000),
        ("1940s", 1947, "war", "Liaoshen", "Mao zafer kazandi.", [], None),
        ("1940s", 1948, "war", "Huaihai", "KMT yenildi.", [], 500000),
        ("1940s", 1949, "revolution", "Cin Halk Cumhuriyeti", "Mao zafer ilan etti.", ["Mao Zedong"], None),
        ("1940s", 1949, "politics", "KMT Tayvan'a", "Chiang Tayvan'a kacti.", [], None),
        ("1940s", 1940, "culture", "Border Region", "Sinir bolgesi.", [], None),
        ("1940s", 1941, "culture", "Ding Ling", "Ding Ling.", [], None),
        ("1940s", 1942, "culture", "Yan'an Forum", "Yan'an forumu.", [], None),
        ("1940s", 1943, "culture", "Mao Literature", "Mao edebiyat.", [], None),
        ("1940s", 1944, "culture", "Dixie Mission", "Dixie heyeti.", [], None),
        ("1940s", 1945, "culture", "Victory", "Zafer.", [], None),
        ("1940s", 1946, "culture", "Civil War", "Ic savas.", [], None),
        ("1940s", 1947, "culture", "Land Reform", "Arazi reformu.", [], None),
        ("1940s", 1948, "culture", "Manchuria", "Manchuria.", [], None),
        ("1940s", 1949, "culture", "Founding", "Kurulus.", [], None),
        ("1940s", 1940, "war", "Hundred Regiments", "Yuz alay.", [], None),
        ("1940s", 1941, "war", "New Fourth Army", "Yeni dorduncu ordu.", [], None),
        ("1940s", 1942, "war", "Burma Campaign", "Burma seferi.", [], None),
        ("1940s", 1943, "war", "Cairo", "Kahire.", [], None),
        ("1940s", 1944, "war", "Ichigo", "Ichigo.", [], None),
        ("1940s", 1945, "war", "Atomic Bomb", "Atom bombasi.", [], None),
        ("1940s", 1946, "war", "Marshall Mission", "Marshall misyonu.", [], None),
        ("1940s", 1947, "war", "Nationalist Offensive", "Milliyetci taarruz.", [], None),
        ("1940s", 1948, "war", "Huaihai", "Huaihai.", [], None),
        ("1940s", 1949, "war", "Crossing Yangtze", "Yangtze gecisi.", [], None),
        ("1940s", 1940, "politics", "Mao", "Mao.", [], None),
        ("1940s", 1941, "politics", "Zhou", "Zhou.", [], None),
        ("1940s", 1942, "politics", "Rectification", "Dogrultma.", [], None),
        ("1940s", 1943, "politics", "Mao", "Mao.", [], None),
        ("1940s", 1944, "politics", "Dixie", "Dixie.", [], None),
        ("1940s", 1945, "politics", "Mao-Chiang", "Mao-Chiang.", [], None),
        ("1940s", 1946, "politics", "Civil War", "Ic savas.", [], None),
        ("1940s", 1947, "politics", "Liu Bocheng", "Liu.", [], None),
        ("1940s", 1948, "politics", "Liaoshen", "Liaoshen.", [], None),
        ("1940s", 1949, "politics", "PRC", "CHC.", [], None),
        ("1940s", 1949, "politics", "Mao Zedong", "Mao Halk Cumhuriyeti ilan etti.", [], None),
    ]
    
    for event_data in china_events_data:
        decade, year, category, title, description, key_figures, casualties = event_data
        
        event = {
            "country_code": china_data["country_code"],
            "country_name": china_data["country_name"],
            "lat": china_data["lat"],
            "lon": china_data["lon"],
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
    new_events = generate_china_events()
    print(f"Uretilen Cin olayi: {len(new_events)}")
    
    data_path = Path(__file__).parent.parent / "data" / "events.json"
    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    existing_count = len(data['events'])
    print(f"Mevcut toplam olay: {existing_count}")
    
    data['events'].extend(new_events)
    
    with open(data_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"Yeni toplam olay: {len(data['events'])}")
    print(f"Eklenen Cin olayi: {len(new_events)}")
    
    china_events = [e for e in data['events'] if e.get('country_code') == 'CN']
    by_decade = {}
    for e in china_events:
        d = e.get('decade', 'unknown')
        by_decade[d] = by_decade.get(d, 0) + 1
    
    print("\nDekadlara gore toplam Cin olaylari:")
    for d in sorted(by_decade.keys()):
        print(f"  {d}: {by_decade[d]} olay")
    
    print(f"\nToplam Cin olayi: {len(china_events)}")

if __name__ == "__main__":
    main()
