#!/usr/bin/env python3
"""
Ensure UK has at least 10 events per decade from 1920s to 2020s.

Rules:
- Country naming follows current canonical form in Admin/Map:
  country_code=GB, country_name='Birleşik Krallık'
- Do not duplicate an existing event with same (year, normalized title) for UK.
- Add only as many events as needed to reach 10 for each decade.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List


BASE_DIR = Path(__file__).resolve().parent.parent
EVENTS_PATH = BASE_DIR / "data" / "events.json"

UK_COUNTRY_CODE = "GB"
UK_COUNTRY_NAME = "Birleşik Krallık"
UK_LAT = 51.5074
UK_LON = -0.1278

TARGET_DECADES = [f"{y}s" for y in range(1920, 2030, 10)]
TARGET_PER_DECADE = 10


def normalize_title(value: str) -> str:
    s = (value or "").strip().lower()
    s = re.sub(r"\s+", " ", s)
    return s


def make_event_id(year: int, title: str) -> str:
    base = f"gb|{year}|{normalize_title(title)}".encode("utf-8")
    return "ev_gb_" + hashlib.md5(base).hexdigest()[:10]


UK_EVENTS_CATALOG: Dict[str, List[Dict[str, object]]] = {
    "1920s": [
        {"year": 1920, "category": "war", "title": "İrlanda Bağımsızlık Savaşı'nın Tırmanışı", "description": "İrlanda'daki çatışmalar Londra'nın güvenlik ve anayasal çözüm arayışını hızlandırdı.", "key_figures": ["David Lloyd George", "Michael Collins"]},
        {"year": 1921, "category": "diplomacy", "title": "Anglo-İrlanda Antlaşması", "description": "Londra ile Dublin arasında imzalanan anlaşma İrlanda Serbest Devleti'nin yolunu açtı.", "key_figures": ["David Lloyd George", "Arthur Griffith"]},
        {"year": 1922, "category": "revolution", "title": "İrlanda Serbest Devleti'nin Kuruluşu", "description": "Birleşik Krallık içindeki anayasal yapı köklü biçimde değişti; ada siyasetinde yeni dönem başladı.", "key_figures": ["Michael Collins"]},
        {"year": 1922, "category": "culture", "title": "BBC'nin Kuruluşu", "description": "British Broadcasting Company'nin kuruluşu, kamusal yayıncılık modelinin temelini attı.", "key_figures": ["John Reith"]},
        {"year": 1924, "category": "politics", "title": "İlk İşçi Partisi Hükümeti", "description": "Ramsay MacDonald liderliğinde İşçi Partisi ilk kez iktidara gelerek iki partili sistemin dengesini değiştirdi.", "key_figures": ["Ramsay MacDonald"]},
        {"year": 1925, "category": "diplomacy", "title": "Locarno Sürecinde İngiltere'nin Güvenlik Rolü", "description": "Londra, kıta Avrupa'sında statükoyu korumaya dönük diplomatik mimarinin garantörlerinden biri oldu.", "key_figures": ["Austen Chamberlain"]},
        {"year": 1926, "category": "diplomacy", "title": "Balfour Deklarasyonu (Dominyon Eşitliği)", "description": "İmparatorluk Konferansı, dominyonları Birleşik Krallık ile eşit statülü topluluklar olarak tanımladı.", "key_figures": ["Stanley Baldwin"]},
        {"year": 1928, "category": "revolution", "title": "Equal Franchise Act ile Eşit Oy Hakkı", "description": "21 yaş üstü kadınlara erkeklerle eşit oy hakkı tanınarak temsil rejimi genişletildi.", "key_figures": ["Stanley Baldwin"]},
        {"year": 1929, "category": "politics", "title": "Büyük Buhran'ın İngiltere'ye Yansıması", "description": "Küresel kriz işsizlik ve kamu maliyesi baskısı yaratarak siyasal kutuplaşmayı artırdı.", "key_figures": ["Ramsay MacDonald"]},
        {"year": 1929, "category": "politics", "title": "İkinci İşçi Partisi Hükümeti", "description": "MacDonald'ın yeniden başbakan oluşu, kriz döneminde koalisyon ve kemer sıkma tartışmalarını tetikledi.", "key_figures": ["Ramsay MacDonald"]},
    ],
    "1930s": [
        {"year": 1931, "category": "revolution", "title": "Westminster Statüsü", "description": "Dominyonların yasama bağımsızlığını tanıyan statü, İngiliz İmparatorluğu'nun Commonwealth'e evrimini hızlandırdı.", "key_figures": ["George V"]},
        {"year": 1931, "category": "politics", "title": "Ulusal Hükümetin Kurulması", "description": "Ekonomik kriz karşısında kurulan geniş tabanlı hükümet, parti sisteminde uzun süreli etki bıraktı.", "key_figures": ["Ramsay MacDonald"]},
        {"year": 1932, "category": "diplomacy", "title": "Ottawa Konferansı ve İmparatorluk Tercih Sistemi", "description": "İmparatorluk içi ticareti önceleyen gümrük rejimi kabul edildi.", "key_figures": ["Neville Chamberlain"]},
        {"year": 1935, "category": "diplomacy", "title": "Hindistan Yönetim Yasası", "description": "Britanya-Hindistan idaresini yeniden düzenleyen yasa, sömürge sonrası dönüşümün ön adımlarından biri oldu.", "key_figures": ["Stanley Baldwin"]},
        {"year": 1936, "category": "revolution", "title": "Jarrow Yürüyüşü", "description": "İşsizliğe karşı kitlesel yürüyüş, sosyal politika tartışmalarında sembolik dönüm noktasına dönüştü.", "key_figures": ["Ellen Wilkinson"]},
        {"year": 1937, "category": "leader", "title": "Kral VI. George'un Taç Giymesi", "description": "Abdication krizinin ardından monarşi kurumsal meşruiyetini yeniden tesis etti.", "key_figures": ["George VI"]},
        {"year": 1938, "category": "diplomacy", "title": "Münih Anlaşması", "description": "Yatıştırma politikası Avrupa güvenlik düzeninde kısa vadeli sakinlik, uzun vadeli kırılganlık yarattı.", "key_figures": ["Neville Chamberlain"]},
        {"year": 1939, "category": "diplomacy", "title": "Polonya'ya Güvence Politikası", "description": "Londra'nın güvenlik garantisi, kıta savaşına doğrudan angajmanın çerçevesini belirledi.", "key_figures": ["Neville Chamberlain"]},
        {"year": 1939, "category": "war", "title": "Almanya'ya Savaş İlanı", "description": "Polonya'nın işgali sonrasında Birleşik Krallık II. Dünya Savaşı'na girdi.", "key_figures": ["Neville Chamberlain"]},
        {"year": 1939, "category": "politics", "title": "Operation Pied Piper Tahliyeleri", "description": "Sivil savunma planı kapsamında milyonlarca çocuk ve sivil büyük şehirlerden tahliye edildi.", "key_figures": ["Samuel Hoare"]},
    ],
    "1940s": [
        {"year": 1941, "category": "diplomacy", "title": "Atlantik Bildirisi", "description": "İngiltere-ABD ortak vizyonu savaş sonrası düzenin normatif çerçevesini şekillendirdi.", "key_figures": ["Winston Churchill", "Franklin D. Roosevelt"]},
        {"year": 1942, "category": "politics", "title": "Beveridge Raporu", "description": "Refah devleti mimarisinin ana ilkelerini belirleyen rapor, savaş sonrası sosyal reformları yönlendirdi.", "key_figures": ["William Beveridge"]},
        {"year": 1943, "category": "war", "title": "Akdeniz Stratejisinde İngiliz Ağırlığı", "description": "Müttefiklerin Sicilya ve İtalya hattına yönelişinde Londra belirleyici bir planlama rolü üstlendi.", "key_figures": ["Winston Churchill"]},
        {"year": 1944, "category": "war", "title": "Normandiya Çıkarmasında Komuta ve Lojistik Rol", "description": "Birleşik Krallık, D-Day operasyonlarının komuta, ikmal ve üs kapasitesinde merkezi işlev gördü.", "key_figures": ["Bernard Montgomery"]},
        {"year": 1945, "category": "politics", "title": "Attlee Hükümeti ve Refah Devleti Programı", "description": "Savaş sonrası dönemde kapsamlı kamusal sağlık, konut ve sosyal güvenlik reformları başlatıldı.", "key_figures": ["Clement Attlee"]},
        {"year": 1945, "category": "diplomacy", "title": "BM Güvenlik Konseyi Daimi Üyeliği", "description": "Birleşik Krallık, savaş sonrası uluslararası düzenin kurucu güçlerinden biri olarak daimi üyelik elde etti.", "key_figures": ["Clement Attlee"]},
        {"year": 1947, "category": "revolution", "title": "Hindistan ve Pakistan'ın Bağımsızlığı", "description": "Sömürge imparatorluğunun çözülmesini hızlandıran kritik eşik geçildi.", "key_figures": ["Louis Mountbatten"]},
        {"year": 1948, "category": "politics", "title": "NHS'nin Kuruluşu", "description": "Ulusal Sağlık Sistemi ile evrensel sağlık hizmeti modeline geçildi.", "key_figures": ["Aneurin Bevan"]},
        {"year": 1948, "category": "war", "title": "Berlin Hava Köprüsü'ne Katılım", "description": "Sovyet ablukasına karşı Batı Berlin'e hava ikmali operasyonunda aktif görev alındı.", "key_figures": ["Ernest Bevin"]},
        {"year": 1949, "category": "diplomacy", "title": "NATO'nun Kuruluşunda Kurucu Üyelik", "description": "Atlantik güvenlik mimarisinde transatlantik caydırıcılığın temel kurucularından biri oldu.", "key_figures": ["Ernest Bevin"]},
    ],
    "1950s": [
        {"year": 1950, "category": "war", "title": "Kore Savaşı'na İngiliz Katılımı", "description": "Birleşik Krallık, BM komutası altında Kore Savaşı'na kuvvet gönderdi.", "key_figures": ["Clement Attlee"]},
        {"year": 1951, "category": "culture", "title": "Festival of Britain", "description": "Savaş sonrası yeniden yapılanma ve bilim-teknoloji vizyonunu kamusal alana taşıyan ulusal sergi düzenlendi.", "key_figures": ["Herbert Morrison"]},
        {"year": 1952, "category": "leader", "title": "Kraliçe II. Elizabeth'in Tahta Çıkışı", "description": "Monarşide kuşak değişimi, Soğuk Savaş döneminde sembolik süreklilik sağladı.", "key_figures": ["Elizabeth II"]},
        {"year": 1952, "category": "war", "title": "Operation Hurricane: İlk İngiliz Nükleer Testi", "description": "Birleşik Krallık bağımsız nükleer caydırıcılık kapasitesini fiilen devreye aldı.", "key_figures": ["Winston Churchill"]},
        {"year": 1953, "category": "leader", "title": "II. Elizabeth'in Taç Giyme Töreni", "description": "Canlı yayınla geniş kitlelere ulaşan tören, modern monarşi iletişiminin dönüm noktası oldu.", "key_figures": ["Elizabeth II"]},
        {"year": 1954, "category": "politics", "title": "Karne Uygulamasının Sona Ermesi", "description": "Savaş dönemi kıtlık ekonomisinin kapanışı ve tüketim toplumuna geçiş hızlandı.", "key_figures": ["Winston Churchill"]},
        {"year": 1956, "category": "war", "title": "Süveyş Krizi", "description": "Mısır müdahalesi sonrasında geri adım, Birleşik Krallık'ın küresel güç statüsünün sınırlarını görünür kıldı.", "key_figures": ["Anthony Eden"]},
        {"year": 1957, "category": "politics", "title": "Windscale Nükleer Kazası", "description": "Nükleer güvenlik standartları ve devlet şeffaflığı tartışmalarını kalıcı biçimde etkiledi.", "key_figures": ["Harold Macmillan"]},
        {"year": 1958, "category": "terror", "title": "Notting Hill Irk Çatışmaları", "description": "Göç, entegrasyon ve polislik pratikleri etrafında uzun vadeli toplumsal gerilimler görünür hale geldi.", "key_figures": []},
        {"year": 1959, "category": "politics", "title": "Macmillan Dönemi Muhafazakar Seçim Zaferi", "description": "Refah ve büyüme söylemi, iç politikada muhafazakar hegemonyayı pekiştirdi.", "key_figures": ["Harold Macmillan"]},
    ],
    "1960s": [
        {"year": 1960, "category": "diplomacy", "title": "Wind of Change Konuşması", "description": "Dekolonizasyonun hızlanacağını ilan eden çizgi, Afrika politikasında stratejik yön değişimi yarattı.", "key_figures": ["Harold Macmillan"]},
        {"year": 1961, "category": "diplomacy", "title": "Berlin Krizi ve NATO Alarm Düzeyi", "description": "Soğuk Savaş geriliminde Londra, ittifak caydırıcılığını güçlendiren askeri-siyasi koordinasyon yürüttü.", "key_figures": ["Harold Macmillan"]},
        {"year": 1963, "category": "politics", "title": "Profumo Skandalı", "description": "Hükümet güvenilirliğini sarsan skandal, siyasal elit ve güvenlik kurumları tartışmasını derinleştirdi.", "key_figures": ["John Profumo"]},
        {"year": 1964, "category": "politics", "title": "Harold Wilson Hükümeti", "description": "Teknolojik modernizasyon ve planlama söylemiyle İşçi Partisi yeniden iktidara geldi.", "key_figures": ["Harold Wilson"]},
        {"year": 1966, "category": "culture", "title": "İngiltere'nin Dünya Kupası Zaferi", "description": "1966 FIFA Dünya Kupası zaferi ulusal kimlik anlatısında merkezi bir referans haline geldi.", "key_figures": ["Alf Ramsey"]},
        {"year": 1967, "category": "politics", "title": "Sterlin Devalüasyonu", "description": "Ödemeler dengesi baskıları karşısında alınan karar ekonomik yönetim tartışmalarını keskinleştirdi.", "key_figures": ["Harold Wilson"]},
        {"year": 1968, "category": "politics", "title": "Rivers of Blood Krizi", "description": "Göç ve kimlik tartışmaları etrafında siyasal söylem sert biçimde kutuplaştı.", "key_figures": ["Enoch Powell"]},
        {"year": 1968, "category": "revolution", "title": "Kuzey İrlanda Sivil Haklar Yürüyüşleri", "description": "Sivil haklar protestoları, The Troubles dönemine uzanan şiddet döngüsünü hızlandırdı.", "key_figures": ["Bernadette Devlin"]},
        {"year": 1969, "category": "war", "title": "Operation Banner", "description": "Birleşik Krallık ordusunun Kuzey İrlanda'ya konuşlandırılması uzun süreli iç güvenlik dönemini başlattı.", "key_figures": []},
        {"year": 1969, "category": "leader", "title": "Prens Charles'ın Galler Prensi Olarak Yatırımı", "description": "Monarşi, ulus-altı kimliklerle ilişkisini yeniden çerçevelemeye çalıştı.", "key_figures": ["Charles III"]},
    ],
    "1970s": [
        {"year": 1971, "category": "politics", "title": "Decimal Day: Ondalık Para Sistemine Geçiş", "description": "Sterlin sistemi modernize edilerek ekonomik işlemlerde standardizasyon sağlandı.", "key_figures": ["Edward Heath"]},
        {"year": 1972, "category": "war", "title": "Bloody Sunday", "description": "Derry'deki olay, Kuzey İrlanda çatışmasını uluslararası kamuoyunun merkezine taşıdı.", "key_figures": []},
        {"year": 1972, "category": "politics", "title": "Kuzey İrlanda'da Doğrudan Yönetim", "description": "Stormont'un askıya alınmasıyla Londra, güvenlik ve yönetimde doğrudan sorumluluk üstlendi.", "key_figures": ["Edward Heath"]},
        {"year": 1973, "category": "diplomacy", "title": "AET'ye Katılım", "description": "Birleşik Krallık Avrupa Ekonomik Topluluğu'na girerek ticaret ve hukuk düzenini yeniden konumlandırdı.", "key_figures": ["Edward Heath"]},
        {"year": 1974, "category": "revolution", "title": "Madenciler Grevi ve Üç Günlük Çalışma Haftası", "description": "Enerji krizi ve endüstriyel çatışma, hükümetin meşruiyetini ve ekonomik yönetişimi sarstı.", "key_figures": ["Edward Heath"]},
        {"year": 1974, "category": "diplomacy", "title": "Sunningdale Düzeninin Çöküşü", "description": "Kuzey İrlanda'da güç paylaşımı girişiminin başarısızlığı, çatışmanın uzamasına yol açtı.", "key_figures": ["Merlyn Rees"]},
        {"year": 1975, "category": "revolution", "title": "AET Üyelik Referandumu", "description": "Halkoylamasıyla Avrupa entegrasyonu onaylandı ve dış politika hattı kısa vadede netleşti.", "key_figures": ["Harold Wilson"]},
        {"year": 1976, "category": "politics", "title": "IMF Kurtarma Kredisi", "description": "Makroekonomik kriz döneminde dış finansmana başvuru, mali disiplin ve sosyal harcama dengesini yeniden tanımladı.", "key_figures": ["James Callaghan"]},
        {"year": 1978, "category": "revolution", "title": "Winter of Discontent", "description": "Yaygın grevler kamu hizmetlerini aksatarak siyasal iktidar değişimini hızlandırdı.", "key_figures": ["James Callaghan"]},
        {"year": 1979, "category": "revolution", "title": "İskoçya ve Galler Yetki Devri Referandumları", "description": "Yetki devri girişimleri eşik altında kalarak anayasal reform sürecini geçici olarak durdurdu.", "key_figures": []},
    ],
    "1980s": [
        {"year": 1981, "category": "revolution", "title": "Brixton Ayaklanmaları", "description": "Polis-toplum ilişkileri ve kentsel eşitsizlikler etrafında kapsamlı reform tartışmaları doğdu.", "key_figures": []},
        {"year": 1981, "category": "revolution", "title": "Toxteth Ayaklanmaları", "description": "Kent içi işsizlik ve dışlanma dinamikleri ulusal güvenlik ve sosyal politika gündemine taşındı.", "key_figures": []},
        {"year": 1983, "category": "politics", "title": "Falkland Sonrası Seçim Zaferi", "description": "Dış politika başarısının etkisiyle Thatcher hükümeti güçlü bir parlamento çoğunluğu elde etti.", "key_figures": ["Margaret Thatcher"]},
        {"year": 1984, "category": "revolution", "title": "Madenci Grevi (1984-85)", "description": "Sendikal güç dengesi ve sanayi politikasını kalıcı biçimde değiştiren uzun bir endüstriyel çatışma yaşandı.", "key_figures": ["Arthur Scargill", "Margaret Thatcher"]},
        {"year": 1985, "category": "diplomacy", "title": "Anglo-İrlanda Anlaşması", "description": "Dublin'e danışma rolü tanıyan anlaşma, Kuzey İrlanda sürecinde diplomatik çerçeveyi güncelledi.", "key_figures": ["Margaret Thatcher", "Garret FitzGerald"]},
        {"year": 1986, "category": "politics", "title": "Big Bang Finansal Serbestleşmesi", "description": "City of London'da düzenleme reformları finans sektörünün küresel ölçeğini hızla büyüttü.", "key_figures": ["Nigel Lawson"]},
        {"year": 1987, "category": "politics", "title": "Black Monday Sonrası Piyasa Müdahaleleri", "description": "1987 küresel borsa şokunun ardından finansal istikrar araçları güçlendirildi.", "key_figures": ["Nigel Lawson"]},
        {"year": 1988, "category": "terror", "title": "Lockerbie Saldırısı", "description": "Pan Am 103 saldırısı Birleşik Krallık güvenlik mimarisinde terörle mücadele önceliklerini değiştirdi.", "key_figures": []},
        {"year": 1989, "category": "politics", "title": "Poll Tax Uygulamasının Başlatılması", "description": "Yerel vergi reformu ciddi toplumsal tepki yaratarak hükümet meşruiyetini aşındırdı.", "key_figures": ["Margaret Thatcher"]},
        {"year": 1989, "category": "diplomacy", "title": "Soğuk Savaş Sonunda Avrupa Güvenliği Yeniden Konumlanması", "description": "Doğu Bloku çözülürken Londra, NATO merkezli güvenlik düzeninin korunmasını savundu.", "key_figures": ["Margaret Thatcher"]},
    ],
    "1990s": [
        {"year": 1990, "category": "revolution", "title": "Poll Tax İsyanları", "description": "Londra merkezli kitlesel protestolar vergi reformunu sürdürülemez hale getirdi.", "key_figures": []},
        {"year": 1990, "category": "leader", "title": "Thatcher'ın İstifası ve Major Dönemi", "description": "Parti içi liderlik krizi sonucunda başbakanlık el değiştirdi.", "key_figures": ["Margaret Thatcher", "John Major"]},
        {"year": 1991, "category": "war", "title": "Körfez Savaşı'nda Operasyon Granby", "description": "Birleşik Krallık, Irak'a karşı koalisyonda geniş askeri kuvvetle yer aldı.", "key_figures": ["John Major"]},
        {"year": 1992, "category": "politics", "title": "Black Wednesday", "description": "ERM'den çıkış, para politikası ve merkez bankacılığı rejimini kalıcı biçimde değiştirdi.", "key_figures": ["Norman Lamont"]},
        {"year": 1993, "category": "diplomacy", "title": "Maastricht Antlaşması'nın Onayı", "description": "AB ile ilişkilerde egemenlik tartışmaları iç siyasetin merkezine yerleşti.", "key_figures": ["John Major"]},
        {"year": 1997, "category": "leader", "title": "Tony Blair'in Seçim Zaferi", "description": "New Labour dönemiyle kamu hizmetleri, dış politika ve anayasal reform gündemi yenilendi.", "key_figures": ["Tony Blair"]},
        {"year": 1997, "category": "diplomacy", "title": "Hong Kong'un Çin'e Devri", "description": "Asya'daki sömürge mirasının en kritik dosyalarından biri resmen kapandı.", "key_figures": ["Chris Patten"]},
        {"year": 1998, "category": "revolution", "title": "Good Friday Referandumu", "description": "Kuzey İrlanda'da güç paylaşımı modeline toplumsal onay verilerek barış süreci kurumsallaştı.", "key_figures": ["Tony Blair", "Bertie Ahern"]},
        {"year": 1999, "category": "revolution", "title": "İskoç Parlamentosu'nun Yeniden Açılması", "description": "Yetki devri reformu ile çok katmanlı yönetişim modeline geçiş güçlendi.", "key_figures": ["Donald Dewar"]},
        {"year": 1999, "category": "war", "title": "Kosova Operasyonuna Katılım", "description": "NATO hava harekâtına aktif destek, Londra'nın müdahaleci güvenlik doktrinini pekiştirdi.", "key_figures": ["Tony Blair"]},
    ],
    "2000s": [
        {"year": 2001, "category": "war", "title": "11 Eylül Sonrası Afganistan Operasyonları", "description": "Birleşik Krallık, ABD öncülüğündeki askeri operasyona erken ve kapsamlı destek verdi.", "key_figures": ["Tony Blair"]},
        {"year": 2001, "category": "politics", "title": "Şap Hastalığı Krizi", "description": "Tarım ve kırsal ekonomiyi etkileyen salgın, olağanüstü kamu müdahalesini zorunlu kıldı.", "key_figures": ["Tony Blair"]},
        {"year": 2003, "category": "war", "title": "Irak Savaşı'na Katılım", "description": "Müdahale kararı iç siyasette meşruiyet, istihbarat ve hukuk tartışmalarını kalıcılaştırdı.", "key_figures": ["Tony Blair"]},
        {"year": 2005, "category": "culture", "title": "Londra'nın 2012 Olimpiyatlarını Alması", "description": "Mega etkinlik stratejisi kentsel dönüşüm ve uluslararası görünürlük hedefleriyle birleştirildi.", "key_figures": ["Sebastian Coe"]},
        {"year": 2005, "category": "politics", "title": "Terörle Mücadele Yasalarının Genişletilmesi", "description": "7/7 sonrası güvenlik mevzuatındaki sertleşme, özgürlük-güvenlik dengesini tartışmalı hale getirdi.", "key_figures": ["Tony Blair"]},
        {"year": 2007, "category": "politics", "title": "Northern Rock Krizi", "description": "Bankacılık sistemindeki kırılganlık ilk büyük mevduat paniğiyle görünür hale geldi.", "key_figures": ["Gordon Brown"]},
        {"year": 2007, "category": "politics", "title": "İskoçya'da SNP Hükümeti", "description": "Edinburgh'da milliyetçi iktidarın yükselişi, birlik tartışmalarına yeni ivme verdi.", "key_figures": ["Alex Salmond"]},
        {"year": 2008, "category": "politics", "title": "Küresel Krizde Banka Kurtarma Programı", "description": "Kamu sermaye enjeksiyonu ve garanti mekanizmaları finansal sistemi ayakta tuttu.", "key_figures": ["Gordon Brown"]},
        {"year": 2009, "category": "politics", "title": "Milletvekili Harcamaları Skandalı", "description": "Şeffaflık krizi parlamentoya güveni zedeledi ve kurumsal etik reformlarını hızlandırdı.", "key_figures": []},
        {"year": 2009, "category": "war", "title": "Helmand'da Askeri Yoğunlaşma", "description": "Afganistan'da artan kayıplar, dış müdahalelerin siyasi sürdürülebilirliği tartışmasını büyüttü.", "key_figures": ["Gordon Brown"]},
    ],
    "2010s": [
        {"year": 2010, "category": "politics", "title": "Muhafazakar-Liberal Demokrat Koalisyonu", "description": "Asılı parlamento sonrası kurulan koalisyon, kemer sıkma ve anayasal reform gündemini öne çıkardı.", "key_figures": ["David Cameron", "Nick Clegg"]},
        {"year": 2011, "category": "revolution", "title": "Londra Ayaklanmaları", "description": "Kısa sürede ülke geneline yayılan olaylar polislik, genç işsizliği ve sosyal eşitsizlik tartışmalarını derinleştirdi.", "key_figures": []},
        {"year": 2013, "category": "revolution", "title": "Eşcinsel Evlilik Yasası (İngiltere ve Galler)", "description": "Aile hukuku reformu ile medeni haklar alanında genişleme sağlandı.", "key_figures": ["David Cameron"]},
        {"year": 2014, "category": "revolution", "title": "İskoçya Bağımsızlık Referandumu", "description": "Birlik sürse de anayasal düzen ve mali yetkiler yeniden müzakere edildi.", "key_figures": ["Alex Salmond", "David Cameron"]},
        {"year": 2015, "category": "war", "title": "Suriye Hava Operasyonları Kararı", "description": "Parlamento kararıyla Birleşik Krallık'ın IŞİD hedeflerine yönelik askeri angajmanı genişledi.", "key_figures": ["David Cameron"]},
        {"year": 2017, "category": "terror", "title": "Manchester Arena Saldırısı", "description": "Saldırı, şehir güvenliği ve radikalleşme karşıtı stratejilerin yeniden yapılandırılmasına yol açtı.", "key_figures": []},
        {"year": 2017, "category": "terror", "title": "Grenfell Tower Yangını", "description": "Konut güvenliği, denetim rejimi ve sosyal adalet tartışmaları ulusal gündemin merkezine taşındı.", "key_figures": []},
        {"year": 2018, "category": "terror", "title": "Salisbury Zehirlenmesi Krizi", "description": "Kimyasal saldırı iddiaları Rusya ile ilişkilerde keskin diplomatik gerilim yarattı.", "key_figures": ["Theresa May"]},
        {"year": 2019, "category": "leader", "title": "Boris Johnson'ın Erken Seçim Zaferi", "description": "Net parlamento çoğunluğu, Brexit yasama sürecinin tamamlanmasını hızlandırdı.", "key_figures": ["Boris Johnson"]},
        {"year": 2019, "category": "politics", "title": "Brexit Parlamento Kilidi ve Anayasal Kriz", "description": "Hükümet-parlamento çekişmesi, yürütme yetkileri ve teamül hukuku sınırlarını test etti.", "key_figures": ["Boris Johnson"]},
    ],
    "2020s": [
        {"year": 2020, "category": "politics", "title": "COVID-19 Ulusal Kapanmaları", "description": "Salgın yönetimi sağlık sistemi kapasitesi, ekonomik destek paketleri ve özgürlük-güvenlik dengesi üzerinde belirleyici oldu.", "key_figures": ["Boris Johnson"]},
        {"year": 2020, "category": "revolution", "title": "AB'den Resmi Ayrılık ve Geçiş Süreci", "description": "31 Ocak 2020'de AB'den ayrılık ve yıl sonundaki yeni ticaret rejimi, dış ekonomik konumlanmayı yeniden tanımladı.", "key_figures": ["Boris Johnson"]},
        {"year": 2021, "category": "diplomacy", "title": "AUKUS Güvenlik Ortaklığı", "description": "İngiltere, Hint-Pasifik denklemi içinde ABD ve Avustralya ile uzun vadeli savunma işbirliği başlattı.", "key_figures": ["Boris Johnson"]},
        {"year": 2021, "category": "diplomacy", "title": "COP26 Glasgow Zirvesi", "description": "İklim diplomasisinde finansman ve emisyon hedefleri etrafında yüksek yoğunluklu müzakere trafiği yürütüldü.", "key_figures": ["Boris Johnson"]},
        {"year": 2022, "category": "leader", "title": "Kral III. Charles'ın Tahta Çıkışı", "description": "II. Elizabeth'in vefatı sonrası monarşide yeni dönem başladı.", "key_figures": ["Charles III"]},
        {"year": 2022, "category": "politics", "title": "Liz Truss Mini-Bütçe Krizi", "description": "Piyasa şoku sonrası maliye politikası geri çekildi ve hükümetin ömrü kısa sürdü.", "key_figures": ["Liz Truss"]},
        {"year": 2022, "category": "politics", "title": "Yaşam Maliyeti ve Enerji Krizi", "description": "Enerji fiyatlarındaki sert artış hane gelirleri ve ücret pazarlıkları üzerinde sistemik baskı yarattı.", "key_figures": ["Rishi Sunak"]},
        {"year": 2023, "category": "diplomacy", "title": "Windsor Çerçeve Anlaşması", "description": "Kuzey İrlanda Protokolü üzerindeki anlaşmazlıklar, AB ile yeni uygulama çerçevesiyle yumuşatıldı.", "key_figures": ["Rishi Sunak"]},
        {"year": 2024, "category": "politics", "title": "Genel Seçim: İşçi Partisi'nin İktidara Dönüşü", "description": "Uzun muhafazakar dönem sonrası hükümet değişimi iç politika önceliklerini yeniden tanımladı.", "key_figures": ["Keir Starmer"]},
        {"year": 2024, "category": "leader", "title": "Sunak'tan Starmer'a Başbakanlık Devri", "description": "Seçim sonucu yürütme erki el değiştirerek yeni kabine ve program dönemine geçildi.", "key_figures": ["Rishi Sunak", "Keir Starmer"]},
    ],
}


def build_event(year: int, category: str, title: str, description: str, key_figures: List[str]) -> Dict[str, object]:
    return {
        "id": make_event_id(year, title),
        "country_code": UK_COUNTRY_CODE,
        "country_name": UK_COUNTRY_NAME,
        "lat": UK_LAT,
        "lon": UK_LON,
        "decade": f"{(year // 10) * 10}s",
        "year": year,
        "category": category,
        "title": title,
        "description": description,
        "wikipedia_url": "",
        "casualties": None,
        "key_figures": key_figures,
    }


def main() -> None:
    data = json.loads(EVENTS_PATH.read_text(encoding="utf-8"))
    events = data.get("events") or []
    if not isinstance(events, list):
        raise SystemExit("events.json: `events` must be a list")

    by_decade_count: Counter = Counter()
    existing_keys = set()
    existing_ids = set()

    for ev in events:
        if not isinstance(ev, dict):
            continue
        event_id = str(ev.get("id") or "")
        if event_id:
            existing_ids.add(event_id)

        if str(ev.get("country_code") or "").upper() != UK_COUNTRY_CODE:
            continue
        year = ev.get("year")
        if not isinstance(year, int) or year < 1920:
            continue
        dec = f"{(year // 10) * 10}s"
        if dec not in TARGET_DECADES:
            continue
        by_decade_count[dec] += 1
        title_key = normalize_title(str(ev.get("title") or ""))
        existing_keys.add((dec, year, title_key))

    added_events: List[Dict[str, object]] = []
    added_by_decade = defaultdict(int)

    for decade in TARGET_DECADES:
        candidates = UK_EVENTS_CATALOG.get(decade, [])
        for item in candidates:
            if by_decade_count[decade] >= TARGET_PER_DECADE:
                break
            year = int(item["year"])
            title = str(item["title"])
            key = (decade, year, normalize_title(title))
            if key in existing_keys:
                continue

            event = build_event(
                year=year,
                category=str(item["category"]),
                title=title,
                description=str(item["description"]),
                key_figures=list(item.get("key_figures") or []),
            )

            # Keep deterministic IDs, but avoid collisions if an unrelated event already has it.
            if event["id"] in existing_ids:
                suffix = 2
                base = str(event["id"])
                while f"{base}_{suffix}" in existing_ids:
                    suffix += 1
                event["id"] = f"{base}_{suffix}"

            events.append(event)
            added_events.append(event)
            added_by_decade[decade] += 1
            by_decade_count[decade] += 1
            existing_ids.add(str(event["id"]))
            existing_keys.add(key)

    if not added_events:
        print("No new UK events were added.")
    else:
        data["events"] = events
        EVENTS_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Added UK events: {len(added_events)}")
        for dec in TARGET_DECADES:
            print(f"- {dec}: +{added_by_decade.get(dec, 0)} (total={by_decade_count.get(dec, 0)})")

    missing = [dec for dec in TARGET_DECADES if by_decade_count.get(dec, 0) < TARGET_PER_DECADE]
    if missing:
        print("WARNING: Could not reach target for decades:", ", ".join(missing))


if __name__ == "__main__":
    main()

