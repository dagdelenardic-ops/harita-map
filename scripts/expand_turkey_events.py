#!/usr/bin/env python3
"""
Add more Turkey (TR) events per decade into data/events.json.

User request (2026-02-09): For Turkey, add at least 5 additional events for each decade (1920s..2020s),
researched from the internet (Wikipedia API), and ensure events don't duplicate/overlap.

This script:
1) Normalizes a few legacy category names so all events use known keys.
2) Adds a 'diplomacy' category.
3) Removes a known duplicate Turkey event (12 Eylul coup duplicate entry).
4) Appends the curated Turkey events list (id-stable).
5) Fills missing Wikipedia links for Turkey events (TR preferred, EN fallback).
6) Regenerates offline admin embeds (admin/data.js, admin/country_mappings.js).
"""

from __future__ import annotations

import json
import time
import urllib.parse
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import requests


BASE_DIR = Path(__file__).resolve().parent.parent
EVENTS_PATH = BASE_DIR / "data" / "events.json"
COUNTRY_MAPPINGS_PATH = BASE_DIR / "data" / "country_mappings.json"
ADMIN_EVENTS_EMBED_PATH = BASE_DIR / "admin" / "data.js"
ADMIN_COUNTRY_MAPPINGS_EMBED_PATH = BASE_DIR / "admin" / "country_mappings.js"

USER_AGENT = "Mozilla/5.0 (HaritaBot/1.0; +https://jeopolitik.com.tr)"

TR_COUNTRY_CODE = "TR"
TR_COUNTRY_NAME = "Türkiye"
TR_LAT = 39.9334  # Ankara
TR_LON = 32.8597


# Curated additional Turkey events: 5 per decade (1920s..2020s).
# Keep titles specific so Wikipedia resolution is reliable.
NEW_TR_EVENTS: List[Dict[str, Any]] = [
    # 1920s
    {
        "id": "ev_tr_1920s_01",
        "decade": "1920s",
        "year": 1920,
        "category": "diplomacy",
        "title": "Sevr Antlaşması",
        "description": "Osmanlı Devleti ile İtilaf Devletleri arasında imzalanan antlaşma; Türkiye'de bağımsızlık mücadelesinin seyrini belirleyen kritik dönüm noktalarından biri.",
        "key_figures": ["Damat Ferid Paşa"],
    },
    {
        "id": "ev_tr_1920s_02",
        "decade": "1920s",
        "year": 1921,
        "category": "revolution",
        "title": "1921 Anayasası (Teşkilât-ı Esasiye Kanunu)",
        "description": "Kurtuluş Savaşı koşullarında kabul edilen 1921 Anayasası, egemenliğin millete ait olduğu ilkesini kurumsallaştırarak yeni devlet düzeninin temelini attı.",
        "key_figures": ["Mustafa Kemal Atatürk"],
    },
    {
        "id": "ev_tr_1920s_03",
        "decade": "1920s",
        "year": 1922,
        "category": "revolution",
        "title": "Saltanatın Kaldırılması",
        "description": "Osmanlı saltanatının kaldırılmasıyla monarşi sona erdi; Cumhuriyet'e giden siyasal dönüşüm hızlandı.",
        "key_figures": ["Mustafa Kemal Atatürk"],
    },
    {
        "id": "ev_tr_1920s_04",
        "decade": "1920s",
        "year": 1924,
        "category": "revolution",
        "title": "Halifeliğin Kaldırılması",
        "description": "Halifeliğin kaldırılması, laikleşme ve merkezî devlet inşası sürecinde köklü bir adım oldu.",
        "key_figures": ["Mustafa Kemal Atatürk", "İsmet İnönü"],
    },
    {
        "id": "ev_tr_1920s_05",
        "decade": "1920s",
        "year": 1925,
        "category": "war",
        "title": "Şeyh Said İsyanı",
        "description": "Doğu ve Güneydoğu Anadolu'da patlak veren isyan; erken Cumhuriyet döneminin güvenlik, idare ve siyaset yaklaşımını derinden etkiledi.",
        "key_figures": ["Şeyh Said"],
    },
    # 1930s
    {
        "id": "ev_tr_1930s_01",
        "decade": "1930s",
        "year": 1930,
        "category": "terror",
        "title": "Menemen Olayı",
        "description": "Menemen'de yaşanan ayaklanma ve Kubilay'ın öldürülmesi, laiklik tartışmalarını ve devletin güvenlik reflekslerini güçlendirdi.",
        "key_figures": ["Mustafa Fehmi Kubilay"],
    },
    {
        "id": "ev_tr_1930s_02",
        "decade": "1930s",
        "year": 1934,
        "category": "revolution",
        "title": "Soyadı Kanunu",
        "description": "Soyadı Kanunu ile modern kimlik kayıt sistemi güçlendirildi; toplumsal modernleşme reformlarının önemli bir halkası tamamlandı.",
        "key_figures": ["Mustafa Kemal Atatürk"],
    },
    {
        "id": "ev_tr_1930s_03",
        "decade": "1930s",
        "year": 1936,
        "category": "diplomacy",
        "title": "Montrö Boğazlar Sözleşmesi",
        "description": "Montrö Sözleşmesi, Boğazlar rejimini yeniden düzenleyerek Türkiye'nin egemenlik ve güvenlik kapasitesini artırdı.",
        "key_figures": [],
    },
    {
        "id": "ev_tr_1930s_04",
        "decade": "1930s",
        "year": 1938,
        "category": "leader",
        "title": "Atatürk'ün Ölümü",
        "description": "Cumhuriyet'in kurucu lideri Mustafa Kemal Atatürk'ün ölümü, Türkiye'de liderlik geçişi ve dönemin siyasal dengeleri açısından tarihsel bir kırılma yarattı.",
        "key_figures": ["Mustafa Kemal Atatürk"],
    },
    {
        "id": "ev_tr_1930s_05",
        "decade": "1930s",
        "year": 1939,
        "category": "diplomacy",
        "title": "Hatay'ın Türkiye'ye Katılması",
        "description": "Hatay Devleti'nin Türkiye'ye katılması, sınır ve egemenlik tartışmalarında diplomatik bir başarı olarak öne çıktı.",
        "key_figures": ["Tayfur Sökmen"],
    },
    # 1940s
    {
        "id": "ev_tr_1940s_01",
        "decade": "1940s",
        "year": 1942,
        "category": "revolution",
        "title": "Varlık Vergisi",
        "description": "Savaş ekonomisi koşullarında çıkarılan Varlık Vergisi, ekonomi ve toplumsal yapı üzerinde derin etkiler bıraktı; iç siyaset ve azınlık politikaları tartışmalarını şekillendirdi.",
        "key_figures": [],
    },
    {
        "id": "ev_tr_1940s_02",
        "decade": "1940s",
        "year": 1945,
        "category": "diplomacy",
        "title": "Birleşmiş Milletler'e Kurucu Üyelik",
        "description": "Türkiye, II. Dünya Savaşı sonrası uluslararası düzenin inşasında Birleşmiş Milletler'in kurucu üyeleri arasında yer aldı.",
        "key_figures": [],
    },
    {
        "id": "ev_tr_1940s_03",
        "decade": "1940s",
        "year": 1946,
        "category": "revolution",
        "title": "Çok Partili Hayata Geçiş (1946 Seçimleri)",
        "description": "1946 seçimleri, Türkiye'de çok partili siyasal hayata geçişin dönüm noktası oldu; demokratikleşme tartışmalarını ve siyasi rekabeti kalıcılaştırdı.",
        "key_figures": ["İsmet İnönü", "Celal Bayar"],
    },
    {
        "id": "ev_tr_1940s_04",
        "decade": "1940s",
        "year": 1947,
        "category": "diplomacy",
        "title": "Truman Doktrini",
        "description": "ABD'nin Truman Doktrini kapsamında Türkiye'ye sağladığı destek, Soğuk Savaş'ta Türkiye'nin güvenlik eksenini Batı'ya yaklaştırdı.",
        "key_figures": ["Harry S. Truman"],
    },
    {
        "id": "ev_tr_1940s_05",
        "decade": "1940s",
        "year": 1949,
        "category": "diplomacy",
        "title": "Avrupa Konseyi Üyeliği",
        "description": "Türkiye'nin Avrupa Konseyi'ne katılımı, insan hakları ve demokratik kurumlar ekseninde Avrupa ile kurumsal bağların güçlenmesinde önemli bir adım oldu.",
        "key_figures": [],
    },
    # 1950s
    {
        "id": "ev_tr_1950s_01",
        "decade": "1950s",
        "year": 1950,
        "category": "revolution",
        "title": "Demokrat Parti'nin İktidara Gelişi (1950 Seçimleri)",
        "description": "1950 seçimleriyle Demokrat Parti iktidara geldi; Türkiye'de siyasal rekabet, ekonomi politikaları ve dış ilişkiler yönünde yeni bir dönem başladı.",
        "key_figures": ["Adnan Menderes", "Celal Bayar"],
    },
    {
        "id": "ev_tr_1950s_02",
        "decade": "1950s",
        "year": 1950,
        "category": "war",
        "title": "Kore Savaşı'na Türk Tugayı Gönderilmesi",
        "description": "Türkiye'nin Kore Savaşı'na asker göndermesi, Soğuk Savaş'ta Batı ittifakına entegrasyonunu hızlandırdı ve NATO sürecine katkı sağladı.",
        "key_figures": [],
    },
    {
        "id": "ev_tr_1950s_03",
        "decade": "1950s",
        "year": 1955,
        "category": "diplomacy",
        "title": "Bağdat Paktı",
        "description": "Bağdat Paktı (sonrasında CENTO), Türkiye'nin Orta Doğu güvenlik mimarisinde Batı yanlısı blokla kurduğu ittifakların önemli örneklerinden biri oldu.",
        "key_figures": ["Adnan Menderes"],
    },
    {
        "id": "ev_tr_1950s_04",
        "decade": "1950s",
        "year": 1958,
        "category": "war",
        "title": "Türk Mukavemet Teşkilatı (TMT)",
        "description": "Kıbrıs'ta Türk toplumunu savunmak amacıyla kurulan TMT, adadaki çatışma dinamikleri ve Türkiye-Yunanistan geriliminde etkili bir unsur haline geldi.",
        "key_figures": ["Rauf Denktaş"],
    },
    {
        "id": "ev_tr_1950s_05",
        "decade": "1950s",
        "year": 1959,
        "category": "diplomacy",
        "title": "Zürih ve Londra Antlaşmaları",
        "description": "Zürih ve Londra Antlaşmaları, Kıbrıs Cumhuriyeti'nin kuruluş çerçevesini çizdi; Türkiye, Yunanistan ve Birleşik Krallık'ın garantörlük rolünü belirledi.",
        "key_figures": ["Adnan Menderes", "Fatin Rüştü Zorlu", "Makarios III"],
    },
    # 1960s
    {
        "id": "ev_tr_1960s_01",
        "decade": "1960s",
        "year": 1961,
        "category": "revolution",
        "title": "1961 Anayasası",
        "description": "1961 Anayasası, Türkiye'de kuvvetler ayrılığı ve temel haklar alanında yeni kurumlar oluşturdu; siyasal sistemin çerçevesini yeniden tanımladı.",
        "key_figures": [],
    },
    {
        "id": "ev_tr_1960s_02",
        "decade": "1960s",
        "year": 1962,
        "category": "revolution",
        "title": "Talat Aydemir Darbe Girişimi",
        "description": "1960 darbesi sonrasında yaşanan darbe girişimleri, sivil-asker ilişkilerinde kırılganlığı ve siyasi istikrarsızlığı görünür kıldı.",
        "key_figures": ["Talat Aydemir"],
    },
    {
        "id": "ev_tr_1960s_03",
        "decade": "1960s",
        "year": 1963,
        "category": "diplomacy",
        "title": "Ankara Anlaşması (AET Ortaklık Anlaşması)",
        "description": "Türkiye ile Avrupa Ekonomik Topluluğu arasında imzalanan Ankara Anlaşması, uzun vadeli Avrupa entegrasyonu hedefinin hukuki temelini attı.",
        "key_figures": [],
    },
    {
        "id": "ev_tr_1960s_04",
        "decade": "1960s",
        "year": 1964,
        "category": "diplomacy",
        "title": "Johnson Mektubu",
        "description": "ABD Başkanı Lyndon B. Johnson'ın Kıbrıs bağlamındaki mektubu, Türkiye'nin dış politika ve güvenlik algısında kalıcı etkiler yarattı.",
        "key_figures": ["Lyndon B. Johnson", "İsmet İnönü"],
    },
    {
        "id": "ev_tr_1960s_05",
        "decade": "1960s",
        "year": 1967,
        "category": "war",
        "title": "Kıbrıs Krizi (1967)",
        "description": "1967 Kıbrıs krizi, Türkiye'nin olası askerî müdahale hazırlıkları ve yoğun diplomasi trafiğiyle Türkiye-Yunanistan ilişkilerinde tansiyonu yükseltti.",
        "key_figures": ["Süleyman Demirel"],
    },
    # 1970s
    {
        "id": "ev_tr_1970s_01",
        "decade": "1970s",
        "year": 1971,
        "category": "revolution",
        "title": "12 Mart Muhtırası",
        "description": "1971 muhtırası, siyasi hayatı yeniden şekillendirdi; hükümet değişikliği ve sertleşen güvenlik politikalarıyla iç siyasal dengeyi dönüştürdü.",
        "key_figures": [],
    },
    {
        "id": "ev_tr_1970s_02",
        "decade": "1970s",
        "year": 1975,
        "category": "revolution",
        "title": "Kıbrıs Türk Federe Devleti'nin İlanı",
        "description": "1975'te ilan edilen Kıbrıs Türk Federe Devleti, Kıbrıs meselesinde yeni bir siyasi yapı oluşturdu; müzakere süreçlerini ve bölgesel dengeleri etkiledi.",
        "key_figures": ["Rauf Denktaş"],
    },
    {
        "id": "ev_tr_1970s_03",
        "decade": "1970s",
        "year": 1977,
        "category": "terror",
        "title": "Kanlı 1 Mayıs (Taksim, 1977)",
        "description": "1977 Taksim 1 Mayıs mitinginde yaşanan saldırı ve panik, 1970'ler boyunca tırmanan siyasal şiddetin sembol olaylarından biri oldu.",
        "key_figures": [],
    },
    {
        "id": "ev_tr_1970s_04",
        "decade": "1970s",
        "year": 1978,
        "category": "terror",
        "title": "PKK'nin Kuruluşu",
        "description": "PKK'nin kuruluşu, Türkiye'nin iç güvenlik gündemini ve bölgesel politikalarını uzun yıllar etkileyecek silahlı çatışma döneminin arka planını oluşturdu.",
        "key_figures": ["Abdullah Öcalan"],
    },
    {
        "id": "ev_tr_1970s_05",
        "decade": "1970s",
        "year": 1978,
        "category": "terror",
        "title": "Kahramanmaraş Olayları",
        "description": "Kahramanmaraş'ta yaşanan kitlesel şiddet, Türkiye'de toplumsal kutuplaşmayı derinleştirdi ve 1980'e giden süreçte güvenlik krizini ağırlaştırdı.",
        "key_figures": [],
    },
    # 1980s
    {
        "id": "ev_tr_1980s_01",
        "decade": "1980s",
        "year": 1982,
        "category": "revolution",
        "title": "1982 Anayasası Referandumu",
        "description": "1982 Anayasası, 12 Eylül sonrası dönemin kurumsal çerçevesini belirledi; siyasal rejim ve sivil-asker ilişkilerinde uzun süreli etkiler yarattı.",
        "key_figures": ["Kenan Evren"],
    },
    {
        "id": "ev_tr_1980s_02",
        "decade": "1980s",
        "year": 1983,
        "category": "revolution",
        "title": "1983 Genel Seçimleri ve Sivil Yönetime Geçiş",
        "description": "1983 seçimleriyle sivil yönetim yeniden kuruldu; ekonomi politikalarında liberal dönüşüm ve yeni bir siyasi denge ortaya çıktı.",
        "key_figures": ["Turgut Özal"],
    },
    {
        "id": "ev_tr_1980s_03",
        "decade": "1980s",
        "year": 1984,
        "category": "war",
        "title": "PKK Silahlı Eylemlerinin Başlaması",
        "description": "1984'te başlayan PKK'nin silahlı eylemleri, Türkiye'de uzun süreli düşük yoğunluklu çatışma ve güvenlik politikaları dönemini başlattı.",
        "key_figures": ["Abdullah Öcalan"],
    },
    {
        "id": "ev_tr_1980s_04",
        "decade": "1980s",
        "year": 1987,
        "category": "diplomacy",
        "title": "AET'ye Tam Üyelik Başvurusu",
        "description": "Türkiye'nin Avrupa Toplulukları'na tam üyelik başvurusu, AB ile ilişkilerde yeni bir müzakere ve reform gündemi başlattı.",
        "key_figures": ["Turgut Özal"],
    },
    {
        "id": "ev_tr_1980s_05",
        "decade": "1980s",
        "year": 1989,
        "category": "leader",
        "title": "Turgut Özal'ın Cumhurbaşkanı Seçilmesi",
        "description": "Özal'ın Cumhurbaşkanı olması, ekonomi ve dış politika önceliklerinde süreklilik ve yeni açılımlar tartışmalarını beraberinde getirdi.",
        "key_figures": ["Turgut Özal"],
    },
    # 1990s
    {
        "id": "ev_tr_1990s_01",
        "decade": "1990s",
        "year": 1991,
        "category": "war",
        "title": "Körfez Savaşı ve Türkiye",
        "description": "1991 Körfez Savaşı, Türkiye'nin güvenlik politikalarını ve Irak sınırı çevresindeki insani/siyasi dinamikleri (mülteci akınları, üs kullanımı) belirgin biçimde etkiledi.",
        "key_figures": ["Turgut Özal"],
    },
    {
        "id": "ev_tr_1990s_02",
        "decade": "1990s",
        "year": 1992,
        "category": "diplomacy",
        "title": "Karadeniz Ekonomik İşbirliği Örgütü (KEİ) Kuruluşu",
        "description": "KEİ'nin kurulması, Türkiye'nin Karadeniz havzasında ekonomik ve diplomatik işbirliği ağlarını kurumsallaştırma girişimlerinin merkezinde yer aldı.",
        "key_figures": [],
    },
    {
        "id": "ev_tr_1990s_03",
        "decade": "1990s",
        "year": 1994,
        "category": "revolution",
        "title": "1994 Ekonomik Krizi",
        "description": "1994 krizi, finansal istikrarı sarstı; kemer sıkma programları ve sosyal etkileriyle 1990'lar siyasetini ve ekonomisini dönüştürdü.",
        "key_figures": ["Tansu Çiller"],
    },
    {
        "id": "ev_tr_1990s_04",
        "decade": "1990s",
        "year": 1997,
        "category": "revolution",
        "title": "28 Şubat Süreci",
        "description": "1997'deki 28 Şubat süreci, sivil-asker ilişkileri ve laiklik eksenli iç siyasette uzun süreli etkiler yarattı; hükümet değişimine uzanan bir krize dönüştü.",
        "key_figures": ["Necmettin Erbakan"],
    },
    {
        "id": "ev_tr_1990s_05",
        "decade": "1990s",
        "year": 1999,
        "category": "terror",
        "title": "Abdullah Öcalan'ın Yakalanması",
        "description": "PKK lideri Abdullah Öcalan'ın yakalanması, iç güvenlik ve çatışma dinamiklerinde yeni bir faza geçişi tetikledi.",
        "key_figures": ["Abdullah Öcalan"],
    },
    # 2000s
    {
        "id": "ev_tr_2000s_01",
        "decade": "2000s",
        "year": 2003,
        "category": "diplomacy",
        "title": "1 Mart Tezkeresi (2003)",
        "description": "TBMM'de Irak Savaşı öncesi ABD askerlerinin Türkiye üzerinden geçişine ilişkin tezkerenin reddi, Türkiye-ABD ilişkilerinde ve bölgesel politikada önemli bir kırılma yarattı.",
        "key_figures": ["Abdullah Gül"],
    },
    {
        "id": "ev_tr_2000s_02",
        "decade": "2000s",
        "year": 2004,
        "category": "diplomacy",
        "title": "Annan Planı Referandumu",
        "description": "Kıbrıs'ta Annan Planı referandumu, ada sorununda çözüm arayışlarını ve Türkiye-AB ilişkilerinin seyrini etkileyen kritik bir eşik oldu.",
        "key_figures": ["Kofi Annan", "Rauf Denktaş"],
    },
    {
        "id": "ev_tr_2000s_03",
        "decade": "2000s",
        "year": 2007,
        "category": "revolution",
        "title": "27 Nisan e-Muhtırası ve 2007 Krizi",
        "description": "2007'deki e-muhtıra ve cumhurbaşkanlığı seçimi etrafında gelişen kriz, sivil-asker ilişkileri ve anayasal siyaset üzerinde kalıcı etkiler bıraktı.",
        "key_figures": [],
    },
    {
        "id": "ev_tr_2000s_04",
        "decade": "2000s",
        "year": 2008,
        "category": "revolution",
        "title": "AK Parti Kapatma Davası",
        "description": "Anayasa Mahkemesi'nde görülen kapatma davası, Türkiye'de parti sistemi ve yargı-siyaset ilişkileri açısından önemli bir kırılma olarak öne çıktı.",
        "key_figures": [],
    },
    {
        "id": "ev_tr_2000s_05",
        "decade": "2000s",
        "year": 2009,
        "category": "diplomacy",
        "title": "Türkiye-Ermenistan Protokolleri",
        "description": "İlişkilerin normalleşmesi amacıyla imzalanan protokoller, Kafkasya diplomasisi ve tarih-politika tartışmalarında güçlü yankı uyandırdı.",
        "key_figures": ["Ahmet Davutoğlu"],
    },
    # 2010s
    {
        "id": "ev_tr_2010s_01",
        "decade": "2010s",
        "year": 2011,
        "category": "war",
        "title": "Suriye İç Savaşı ve Mülteci Krizi",
        "description": "2011'de başlayan Suriye iç savaşı, Türkiye'nin güvenlik politikalarını ve demografik/sosyal yapısını etkileyen büyük bir mülteci akınına yol açtı.",
        "key_figures": [],
    },
    {
        "id": "ev_tr_2010s_02",
        "decade": "2010s",
        "year": 2015,
        "category": "terror",
        "title": "Suruç Saldırısı",
        "description": "Suruç'taki saldırı, Türkiye'de güvenlik gündemini ve Suriye merkezli tehdit algısını derinleştiren kritik bir terör eylemi olarak hafızaya kazındı.",
        "key_figures": [],
    },
    {
        "id": "ev_tr_2010s_03",
        "decade": "2010s",
        "year": 2015,
        "category": "terror",
        "title": "Ankara Garı Saldırısı",
        "description": "Ankara Garı'nda gerçekleşen saldırı, yakın dönem Türkiye tarihinin en ölümcül terör eylemlerinden biri olarak iç güvenlik ve siyasal iklimi etkiledi.",
        "key_figures": [],
    },
    {
        "id": "ev_tr_2010s_04",
        "decade": "2010s",
        "year": 2017,
        "category": "revolution",
        "title": "2017 Anayasa Referandumu",
        "description": "2017 referandumu ile yönetim sistemi ve güçler dengesi tartışmaları yeni bir evreye taşındı; yürütme yapısı köklü biçimde değişti.",
        "key_figures": ["Recep Tayyip Erdoğan"],
    },
    {
        "id": "ev_tr_2010s_05",
        "decade": "2010s",
        "year": 2018,
        "category": "war",
        "title": "Zeytin Dalı Harekâtı",
        "description": "Türkiye'nin Suriye'nin kuzeyinde yürüttüğü harekât, sınır güvenliği ve bölgesel güç dengeleri açısından önemli sonuçlar doğurdu.",
        "key_figures": [],
    },
    # 2020s
    {
        "id": "ev_tr_2020s_01",
        "decade": "2020s",
        "year": 2020,
        "category": "war",
        "title": "İkinci Dağlık Karabağ Savaşı ve Türkiye",
        "description": "2020 Dağlık Karabağ savaşı sürecinde Türkiye'nin Azerbaycan'a desteği, Güney Kafkasya'da askeri ve diplomatik dengeleri etkiledi.",
        "key_figures": [],
    },
    {
        "id": "ev_tr_2020s_02",
        "decade": "2020s",
        "year": 2020,
        "category": "culture",
        "title": "Ayasofya'nın Yeniden Cami Olarak Açılması",
        "description": "Ayasofya'nın statüsüne ilişkin karar, iç politikada ve uluslararası alanda geniş yankı uyandırdı; kimlik ve kültürel miras tartışmalarını canlandırdı.",
        "key_figures": [],
    },
    {
        "id": "ev_tr_2020s_03",
        "decade": "2020s",
        "year": 2022,
        "category": "diplomacy",
        "title": "Karadeniz Tahıl Koridoru Anlaşması",
        "description": "Rusya-Ukrayna savaşı sırasında Karadeniz üzerinden tahıl sevkiyatını mümkün kılan girişimde Türkiye'nin arabuluculuk rolü öne çıktı.",
        "key_figures": ["Recep Tayyip Erdoğan", "António Guterres"],
    },
    {
        "id": "ev_tr_2020s_04",
        "decade": "2020s",
        "year": 2023,
        "category": "culture",
        "title": "Kahramanmaraş Depremleri",
        "description": "2023 depremleri, Türkiye'nin afet yönetimi ve toplumsal dayanıklılığı açısından tarihsel bir sınav oldu; bölgesel insani yardım mobilizasyonunu tetikledi.",
        "key_figures": [],
    },
    {
        "id": "ev_tr_2020s_05",
        "decade": "2020s",
        "year": 2023,
        "category": "revolution",
        "title": "2023 Türkiye Genel Seçimleri",
        "description": "Cumhurbaşkanlığı ve parlamento seçimleri, Türkiye'nin iç siyasi dengeleri ve dış politika öncelikleri üzerinde belirleyici bir etki yarattı.",
        "key_figures": ["Recep Tayyip Erdoğan", "Kemal Kılıçdaroğlu"],
    },
]


CATEGORY_REMAP = {
    "Diplomasi": "diplomacy",
    "Barış/Diplomasi": "diplomacy",
    "Teknoloji": "culture",
    "Çevre": "culture",
    "Deniz Kazası": "culture",
}

# Some Turkey events are inherently ambiguous in Wikipedia search. Use explicit targets to
# avoid wrong pages (e.g., "14 Nisan", "2022'de Türkiye", etc).
#
# Format: event_id -> (lang, page_title)
TR_WIKI_OVERRIDES: Dict[str, Tuple[str, str]] = {
    # Existing (pre-script) TR entries
    "ev_gap_1952_0": ("tr", "NATO-Türkiye ilişkileri"),
    "ev_gap_2002_1": ("tr", "2002 Türkiye genel seçimleri"),
    # Curated additions
    "ev_tr_1940s_05": ("tr", "Avrupa Konseyi üyesi ülkeler"),
    "ev_tr_1950s_01": ("tr", "1950 Türkiye genel seçimleri"),
    "ev_tr_1950s_02": ("tr", "Türk Tugayı"),
    "ev_tr_1950s_03": ("tr", "Bağdat Paktı"),
    "ev_tr_1960s_05": ("tr", "Kıbrıs Sorunu"),
    "ev_tr_1980s_02": ("tr", "1983 Türkiye genel seçimleri"),
    "ev_tr_1980s_04": ("tr", "Türkiye'nin Avrupa Birliği üyelik süreci"),
    "ev_tr_1980s_05": ("tr", "1989 Türkiye cumhurbaşkanlığı seçimi"),
    "ev_tr_1990s_03": ("tr", "Türkiye'de ekonomik krizler"),
    "ev_tr_1990s_05": ("tr", "Abdullah Öcalan'ın yakalanması"),
    "ev_tr_2000s_03": ("tr", "27 Nisan Bildirisi"),
    "ev_tr_2010s_04": ("tr", "2017 Türkiye anayasa değişikliği referandumu"),
    "ev_tr_2020s_03": ("tr", "Karadeniz Tahıl Girişimi"),
}


def _wiki_url(lang: str, title: str) -> str:
    t = (title or "").strip().replace(" ", "_")
    return f"https://{lang}.wikipedia.org/wiki/{urllib.parse.quote(t)}" if t else ""


class WikiResolver:
    def __init__(self) -> None:
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})
        self.search_cache: Dict[Tuple[str, str], str] = {}
        self.langlink_cache: Dict[Tuple[str, str, str], str] = {}
        self._last_req = 0.0

    def _throttle(self) -> None:
        now = time.time()
        if now - self._last_req < 0.05:
            time.sleep(0.05 - (now - self._last_req))
        self._last_req = time.time()

    def search_title(self, query: str, lang: str) -> str:
        q = (query or "").strip()
        if not q:
            return ""
        key = (lang, q)
        if key in self.search_cache:
            return self.search_cache[key]
        self._throttle()
        try:
            r = self.session.get(
                f"https://{lang}.wikipedia.org/w/api.php",
                params={
                    "action": "query",
                    "list": "search",
                    "srsearch": q,
                    "srlimit": 1,
                    "format": "json",
                    "utf8": 1,
                },
                timeout=10,
            )
            if r.status_code != 200:
                self.search_cache[key] = ""
                return ""
            hits = (r.json().get("query") or {}).get("search") or []
            title = (hits[0].get("title") if hits else "") or ""
            self.search_cache[key] = title
            return title
        except Exception:
            self.search_cache[key] = ""
            return ""

    def langlink_title(self, from_title: str, from_lang: str, to_lang: str) -> str:
        title = (from_title or "").strip()
        if not title:
            return ""
        key = (from_lang, to_lang, title)
        if key in self.langlink_cache:
            return self.langlink_cache[key]
        self._throttle()
        try:
            r = self.session.get(
                f"https://{from_lang}.wikipedia.org/w/api.php",
                params={
                    "action": "query",
                    "prop": "langlinks",
                    "titles": title,
                    "redirects": 1,
                    "lllang": to_lang,
                    "format": "json",
                    "utf8": 1,
                },
                timeout=10,
            )
            if r.status_code != 200:
                self.langlink_cache[key] = ""
                return ""
            pages = (r.json().get("query") or {}).get("pages") or {}
            out = ""
            for page in pages.values():
                ll = page.get("langlinks") or []
                if ll:
                    out = (ll[0].get("*") or ll[0].get("title") or "").strip()
                    break
            self.langlink_cache[key] = out
            return out
        except Exception:
            self.langlink_cache[key] = ""
            return ""

    def resolve_prefer_tr(self, query: str) -> str:
        q = (query or "").strip()
        if not q:
            return ""

        # Try TR directly, with a couple of disambiguation attempts first.
        # (Without this, very generic queries can resolve to unrelated pages like dates.)
        tr_queries = [f"{TR_COUNTRY_NAME} {q}", q]
        for qq in tr_queries:
            t_tr = self.search_title(qq, "tr")
            if t_tr:
                # Heuristic: skip day pages like "14 Nisan"
                if " " in t_tr and t_tr.split(" ", 1)[0].isdigit():
                    continue
                # Heuristic: skip year pages like "2022'de Türkiye"
                if "de Türkiye" in t_tr or "da Türkiye" in t_tr:
                    continue
                return _wiki_url("tr", t_tr)

        # Fallback EN, then map to TR if possible
        en_queries = tr_queries + [f"{q} {TR_COUNTRY_NAME}"]
        t_en = ""
        for qq in en_queries:
            t_en = self.search_title(qq, "en")
            if t_en:
                break
        if t_en:
            tr_title = self.langlink_title(t_en, "en", "tr")
            return _wiki_url("tr", tr_title) if tr_title else _wiki_url("en", t_en)

        return ""


def _regen_admin_embeds(data: Dict[str, Any]) -> None:
    ADMIN_EVENTS_EMBED_PATH.write_text(
        "window.__EVENTS_DATA__ = " + json.dumps(data, ensure_ascii=False) + ";\n",
        encoding="utf-8",
    )
    mappings = json.loads(COUNTRY_MAPPINGS_PATH.read_text(encoding="utf-8"))
    ADMIN_COUNTRY_MAPPINGS_EMBED_PATH.write_text(
        "window.__COUNTRY_MAPPINGS__ = "
        + json.dumps(mappings.get("countries") or [], ensure_ascii=False)
        + ";\n",
        encoding="utf-8",
    )


def main() -> None:
    data = json.loads(EVENTS_PATH.read_text(encoding="utf-8"))
    events: List[Dict[str, Any]] = data.get("events") or []
    categories: Dict[str, Any] = data.get("categories") or {}

    # 1) Ensure 'diplomacy' category exists (used across dataset).
    categories.setdefault(
        "diplomacy",
        {
            "color": "#2ecc71",
            "icon": "fa-handshake",
            "label": "Diplomasi",
        },
    )

    # 2) Remap legacy categories to known keys.
    remapped = 0
    for ev in events:
        cat = (ev.get("category") or "").strip()
        if cat in CATEGORY_REMAP:
            ev["category"] = CATEGORY_REMAP[cat]
            remapped += 1

    # 3) Remove a known duplicate Turkey event (keep the richer one with wiki link).
    # Duplicate pair: ev029 vs ev_1980_31. Keep ev029; drop ev_1980_31.
    before = len(events)
    events = [e for e in events if e.get("id") != "ev_1980_31"]
    removed = before - len(events)

    # 4) Append new Turkey events if not already present.
    existing_ids: Set[str] = {str(e.get("id") or "") for e in events}
    existing_key: Set[Tuple[str, int, str]] = set()
    for e in events:
        cc = (e.get("country_code") or "").strip().upper()
        y = int(e.get("year") or 0)
        t = (e.get("title") or "").strip()
        if cc and y and t:
            existing_key.add((cc, y, t))

    added = 0
    for ev in NEW_TR_EVENTS:
        ev = dict(ev)  # copy
        ev.setdefault("country_code", TR_COUNTRY_CODE)
        ev.setdefault("country_name", TR_COUNTRY_NAME)
        ev.setdefault("lat", TR_LAT)
        ev.setdefault("lon", TR_LON)
        ev.setdefault("wikipedia_url", "")
        ev.setdefault("casualties", None)
        ev.setdefault("key_figures", [])

        # Basic validation
        ev_id = str(ev.get("id") or "").strip()
        if not ev_id:
            raise SystemExit("New event id is missing")
        if ev_id in existing_ids:
            # Already applied in a previous run.
            continue
        cc = (ev.get("country_code") or "").strip().upper()
        if cc != TR_COUNTRY_CODE:
            raise SystemExit(f"Unexpected country_code in new event {ev_id}: {cc}")
        key = (cc, int(ev.get("year") or 0), (ev.get("title") or "").strip())
        if key in existing_key:
            # Skip if already exists (id-stable behavior across reruns).
            continue
        events.append(ev)
        existing_ids.add(ev_id)
        existing_key.add(key)
        added += 1

    # Persist category changes
    data["categories"] = categories
    data["events"] = events

    # 5) Fix/Fill Wikipedia links for Turkey events (TR preferred, EN fallback).
    resolver = WikiResolver()
    tr_events = [e for e in events if (e.get("country_code") or "").strip().upper() == TR_COUNTRY_CODE]
    override_updates = 0
    for ev in tr_events:
        ev_id = str(ev.get("id") or "").strip()
        if not ev_id or ev_id not in TR_WIKI_OVERRIDES:
            continue
        lang, title = TR_WIKI_OVERRIDES[ev_id]
        url = _wiki_url(lang, title)
        if url and url != (ev.get("wikipedia_url") or ""):
            ev["wikipedia_url"] = url
            override_updates += 1

    filled_wiki = 0
    unresolved: List[str] = []
    for ev in tr_events:
        if (ev.get("wikipedia_url") or "").strip():
            continue
        title = (ev.get("title") or "").strip()
        if not title:
            continue
        url = resolver.resolve_prefer_tr(title)
        if url:
            ev["wikipedia_url"] = url
            filled_wiki += 1
        else:
            unresolved.append(f"{ev.get('year')} {title}")

    # Write back events.json
    EVENTS_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # Regenerate admin embeds
    _regen_admin_embeds(data)

    # Summary
    print("Turkey expansion complete.")
    print(f"- events (total): {len(events)}")
    print(f"- categories remapped: {remapped}")
    print(f"- removed known duplicate TR event(s): {removed}")
    print(f"- added new TR events: {added} (expected 55 unless already applied)")
    print(f"- filled TR wikipedia_url: {filled_wiki}")
    print(f"- override-updated TR wikipedia_url: {override_updates}")
    if unresolved:
        print(f"- unresolved TR wiki links: {len(unresolved)}")
        for s in unresolved[:20]:
            print('  -', s)


if __name__ == "__main__":
    main()
