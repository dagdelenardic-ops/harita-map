#!/usr/bin/env python3
"""
Enrich country relations data in meta.json.
Adds allies, trade partners, rivalries, territorial disputes, and diplomatic ties.
"""

import json
from pathlib import Path

BASE = Path(__file__).parent.parent

# Comprehensive relations database
# Format: country -> { allies, rivals, trade_partners, territorial_disputes, diplomatic_notes }
RELATIONS_DB = {
    "ABD": {
        "allies": ["Birleşik Krallık", "Kanada", "Japonya", "Güney Kore", "Almanya", "Fransa", "Avustralya", "İsrail", "Polonya", "İtalya"],
        "rivalries": [
            {"rival": "Rusya", "text": "Soğuk Savaş mirası, Ukrayna, nükleer silahlar", "status": "active"},
            {"rival": "Çin", "text": "Ticaret savaşı, Tayvan, teknoloji rekabeti", "status": "active"},
            {"rival": "İran", "text": "Nükleer program, Ortadoğu nüfuzu", "status": "active"},
            {"rival": "Kuzey Kore", "text": "Nükleer tehdit, Kore yarımadası", "status": "active"}
        ],
        "trade_partners": ["Çin", "Kanada", "Meksika", "Japonya", "Almanya"],
        "territorial_disputes": [],
        "organizations": ["NATO", "G7", "BM Güvenlik Konseyi (P5)", "AUKUS", "Five Eyes", "USMCA"]
    },
    "Türkiye": {
        "allies": ["Azerbaycan", "Katar", "Pakistan", "Somali", "Libya"],
        "rivalries": [
            {"rival": "Yunanistan", "text": "Ege adaları, Kıbrıs sorunu, kıta sahanlığı", "status": "active"},
            {"rival": "Ermenistan", "text": "1915 olayları, Karabağ, sınır kapısı", "status": "active"},
            {"rival": "Suriye", "text": "Kuzey Suriye operasyonları, mülteci krizi", "status": "active"},
            {"rival": "İsrail", "text": "Filistin meselesi, Mavi Marmara", "status": "tension"},
            {"rival": "Mısır", "text": "Doğu Akdeniz, Libya politikası", "status": "tension"}
        ],
        "trade_partners": ["Almanya", "Rusya", "Çin", "Birleşik Krallık", "İtalya"],
        "territorial_disputes": ["Kıbrıs (KKTC)", "Ege Adaları (Yunanistan ile)"],
        "organizations": ["NATO", "G20", "Türk Devletleri Teşkilatı", "İslam İşbirliği Teşkilatı", "Karadeniz Ekonomik İşbirliği"]
    },
    "Rusya": {
        "allies": ["Çin", "Belarus", "İran", "Suriye", "Kuzey Kore", "Küba"],
        "rivalries": [
            {"rival": "ABD", "text": "NATO genişlemesi, nükleer denge, Ukrayna", "status": "active"},
            {"rival": "Ukrayna", "text": "Kırım ilhakı, Donbas, 2022 işgali", "status": "war"},
            {"rival": "Birleşik Krallık", "text": "Casusluk, Skripal olayı, yaptırımlar", "status": "active"},
            {"rival": "Polonya", "text": "Tarihsel gerilim, NATO sınırı", "status": "tension"},
            {"rival": "Japonya", "text": "Kuril Adaları uyuşmazlığı", "status": "frozen"}
        ],
        "trade_partners": ["Çin", "Almanya", "Hollanda", "Türkiye", "Hindistan"],
        "territorial_disputes": ["Kırım (Ukrayna ile)", "Kuril Adaları (Japonya ile)", "Güney Osetya ve Abhazya (Gürcistan ile)"],
        "organizations": ["BM Güvenlik Konseyi (P5)", "BRICS+", "ŞİÖ", "KGAÖ", "BDT"]
    },
    "Çin": {
        "allies": ["Rusya", "Pakistan", "Kuzey Kore", "Kamboçya", "Myanmar"],
        "rivalries": [
            {"rival": "ABD", "text": "Ticaret savaşı, Tayvan, Güney Çin Denizi", "status": "active"},
            {"rival": "Hindistan", "text": "Sınır çatışmaları (Ladakh), Tibet sorunu", "status": "active"},
            {"rival": "Japonya", "text": "Senkaku/Diaoyu Adaları, tarihsel husumet", "status": "active"},
            {"rival": "Tayvan", "text": "'Bir Çin' politikası, askeri gerilim", "status": "active"},
            {"rival": "Filipinler", "text": "Güney Çin Denizi, resif iddiaları", "status": "active"},
            {"rival": "Vietnam", "text": "Güney Çin Denizi, Paracel/Spratly adaları", "status": "tension"}
        ],
        "trade_partners": ["ABD", "Japonya", "Güney Kore", "Almanya", "Avustralya"],
        "territorial_disputes": ["Tayvan", "Güney Çin Denizi (birçok ülke ile)", "Aksai Chin / Arunachal Pradesh (Hindistan ile)"],
        "organizations": ["BM Güvenlik Konseyi (P5)", "BRICS+", "ŞİÖ", "G20", "RCEP"]
    },
    "Almanya": {
        "allies": ["Fransa", "ABD", "Hollanda", "Polonya", "İtalya", "Avusturya", "İspanya"],
        "rivalries": [
            {"rival": "Rusya", "text": "Enerji bağımlılığı, Ukrayna politikası", "status": "active"}
        ],
        "trade_partners": ["ABD", "Fransa", "Çin", "Hollanda", "Polonya"],
        "territorial_disputes": [],
        "organizations": ["NATO", "AB", "G7", "G20", "Schengen"]
    },
    "Fransa": {
        "allies": ["Almanya", "ABD", "Birleşik Krallık", "İtalya", "İspanya", "Belçika"],
        "rivalries": [
            {"rival": "Rusya", "text": "Ukrayna krizi, Avrupa güvenliği", "status": "active"},
            {"rival": "Türkiye", "text": "Libya, Doğu Akdeniz, Ermeni diasporası", "status": "tension"},
            {"rival": "Çin", "text": "Indo-Pasifik stratejisi", "status": "competition"}
        ],
        "trade_partners": ["Almanya", "ABD", "İtalya", "İspanya", "Belçika"],
        "territorial_disputes": [],
        "organizations": ["NATO", "AB", "G7", "BM Güvenlik Konseyi (P5)", "Frankofoni"]
    },
    "Birleşik Krallık": {
        "allies": ["ABD", "Fransa", "Kanada", "Avustralya", "Japonya", "Polonya"],
        "rivalries": [
            {"rival": "Rusya", "text": "Casusluk, Skripal, Ukrayna desteği", "status": "active"},
            {"rival": "İran", "text": "Nükleer anlaşma, Basra Körfezi", "status": "tension"},
            {"rival": "Arjantin", "text": "Falkland/Malvinas Adaları", "status": "frozen"}
        ],
        "trade_partners": ["ABD", "Almanya", "Hollanda", "Fransa", "Çin"],
        "territorial_disputes": ["Falkland Adaları (Arjantin ile)", "Cebelitarık (İspanya ile)"],
        "organizations": ["NATO", "G7", "BM Güvenlik Konseyi (P5)", "AUKUS", "Five Eyes", "Commonwealth"]
    },
    "Hindistan": {
        "allies": ["ABD", "Fransa", "Japonya", "Avustralya", "İsrail"],
        "rivalries": [
            {"rival": "Pakistan", "text": "Keşmir sorunu, terörizm, nükleer yarış", "status": "active"},
            {"rival": "Çin", "text": "Ladakh sınır çatışmaları, Hint Okyanusu", "status": "active"}
        ],
        "trade_partners": ["ABD", "Çin", "Birleşik Arap Emirlikleri", "Suudi Arabistan", "Irak"],
        "territorial_disputes": ["Keşmir (Pakistan ile)", "Aksai Chin (Çin ile)", "Arunachal Pradesh (Çin ile)"],
        "organizations": ["BRICS+", "G20", "Quad", "ŞİÖ", "Bağlantısızlar Hareketi"]
    },
    "Pakistan": {
        "allies": ["Çin", "Türkiye", "Suudi Arabistan"],
        "rivalries": [
            {"rival": "Hindistan", "text": "Keşmir, nükleer gerilim, su paylaşımı", "status": "active"},
            {"rival": "Afganistan", "text": "Durand Hattı, Taliban ilişkileri", "status": "tension"}
        ],
        "trade_partners": ["Çin", "Birleşik Arap Emirlikleri", "ABD", "Suudi Arabistan"],
        "territorial_disputes": ["Keşmir (Hindistan ile)"],
        "organizations": ["ŞİÖ", "İslam İşbirliği Teşkilatı", "CPEC"]
    },
    "İsrail": {
        "allies": ["ABD", "Almanya", "Hindistan"],
        "rivalries": [
            {"rival": "İran", "text": "Nükleer program, vekalet savaşları, Hizbullah", "status": "active"},
            {"rival": "Filistin", "text": "İşgal, Gazze ablukası, yerleşimler", "status": "war"},
            {"rival": "Suriye", "text": "Golan Tepeleri, İran varlığı", "status": "active"},
            {"rival": "Lübnan", "text": "Hizbullah, sınır gerilimi", "status": "active"},
            {"rival": "Türkiye", "text": "Filistin politikası, diplomatik gerilim", "status": "tension"}
        ],
        "trade_partners": ["ABD", "Çin", "Birleşik Krallık", "Hindistan", "Hollanda"],
        "territorial_disputes": ["Batı Şeria", "Gazze", "Golan Tepeleri (Suriye ile)", "Şebaa Çiftlikleri (Lübnan ile)"],
        "organizations": ["Abraham Anlaşmaları"]
    },
    "İran": {
        "allies": ["Rusya", "Çin", "Suriye", "Irak (Şii milisler)"],
        "rivalries": [
            {"rival": "ABD", "text": "Nükleer yaptırımlar, rejim değişikliği baskısı", "status": "active"},
            {"rival": "İsrail", "text": "Varoluşsal tehdit algısı, vekalet savaşları", "status": "active"},
            {"rival": "Suudi Arabistan", "text": "Mezhepsel rekabet, Yemen, bölgesel hakimiyet", "status": "active"}
        ],
        "trade_partners": ["Çin", "Türkiye", "Birleşik Arap Emirlikleri", "Hindistan"],
        "territorial_disputes": [],
        "organizations": ["BRICS+ (2024 üye)", "ŞİÖ", "İslam İşbirliği Teşkilatı"]
    },
    "Suudi Arabistan": {
        "allies": ["ABD", "Mısır", "Birleşik Arap Emirlikleri", "Bahreyn"],
        "rivalries": [
            {"rival": "İran", "text": "Yemen vekalet savaşı, Şii-Sünni gerilimi", "status": "active"},
            {"rival": "Katar", "text": "Diplomatik kriz (2017-21), Müslüman Kardeşler", "status": "normalized"},
            {"rival": "Türkiye", "text": "Bölgesel liderlik, Kaşıkçı olayı", "status": "tension"}
        ],
        "trade_partners": ["Çin", "Hindistan", "Japonya", "Güney Kore", "ABD"],
        "territorial_disputes": [],
        "organizations": ["G20", "OPEC+", "Körfez İşbirliği Konseyi", "İslam İşbirliği Teşkilatı"]
    },
    "Mısır": {
        "allies": ["Suudi Arabistan", "Birleşik Arap Emirlikleri", "ABD", "Fransa"],
        "rivalries": [
            {"rival": "Türkiye", "text": "Müslüman Kardeşler, Libya politikası", "status": "normalized"},
            {"rival": "Etiyopya", "text": "Hedasi Barajı, Nil suyu paylaşımı", "status": "active"},
            {"rival": "İsrail", "text": "Gazze sınırı, Filistin meselesi (soğuk barış)", "status": "cold_peace"}
        ],
        "trade_partners": ["Çin", "ABD", "Suudi Arabistan", "İtalya", "Almanya"],
        "territorial_disputes": ["Halayib Üçgeni (Sudan ile)"],
        "organizations": ["Arap Birliği", "Afrika Birliği", "İslam İşbirliği Teşkilatı"]
    },
    "Japonya": {
        "allies": ["ABD", "Avustralya", "Hindistan", "Güney Kore", "Filipinler"],
        "rivalries": [
            {"rival": "Çin", "text": "Senkaku Adaları, tarihsel husumet, Güney Çin Denizi", "status": "active"},
            {"rival": "Kuzey Kore", "text": "Füze tehdidi, kaçırılan vatandaşlar", "status": "active"},
            {"rival": "Rusya", "text": "Kuril Adaları uyuşmazlığı", "status": "frozen"}
        ],
        "trade_partners": ["Çin", "ABD", "Güney Kore", "Tayvan", "Avustralya"],
        "territorial_disputes": ["Senkaku/Diaoyu Adaları (Çin ile)", "Kuril Adaları (Rusya ile)", "Dokdo/Takeshima (Güney Kore ile)"],
        "organizations": ["G7", "G20", "Quad", "RCEP", "CPTPP"]
    },
    "Güney Kore": {
        "allies": ["ABD", "Japonya", "Avustralya"],
        "rivalries": [
            {"rival": "Kuzey Kore", "text": "Nükleer tehdit, birleşme sorunu, 38. paralel", "status": "active"},
            {"rival": "Çin", "text": "THAAD krizi, Kore Savaşı mirası", "status": "tension"}
        ],
        "trade_partners": ["Çin", "ABD", "Japonya", "Vietnam", "Tayvan"],
        "territorial_disputes": ["Dokdo/Takeshima (Japonya ile)"],
        "organizations": ["G20", "RCEP", "MIKTA"]
    },
    "Kuzey Kore": {
        "allies": ["Çin", "Rusya"],
        "rivalries": [
            {"rival": "ABD", "text": "Nükleer kriz, yaptırımlar, askeri tatbikatlar", "status": "active"},
            {"rival": "Güney Kore", "text": "Bölünmüş ulus, nükleer tehdit", "status": "active"},
            {"rival": "Japonya", "text": "Füze testleri, kaçırma olayları", "status": "active"}
        ],
        "trade_partners": ["Çin", "Rusya"],
        "territorial_disputes": ["Kore yarımadası birleşme sorunu"],
        "organizations": ["Bağlantısızlar Hareketi"]
    },
    "Ukrayna": {
        "allies": ["ABD", "Birleşik Krallık", "Polonya", "Almanya", "Fransa", "Kanada"],
        "rivalries": [
            {"rival": "Rusya", "text": "2022 işgali, Kırım ilhakı, Donbas savaşı", "status": "war"}
        ],
        "trade_partners": ["Çin", "Polonya", "Almanya", "Türkiye", "İtalya"],
        "territorial_disputes": ["Kırım (Rusya işgalinde)", "Donbas (Rusya işgalinde)"],
        "organizations": ["AB aday", "NATO aday"]
    },
    "Polonya": {
        "allies": ["ABD", "Ukrayna", "Birleşik Krallık", "Litvanya", "Romanya"],
        "rivalries": [
            {"rival": "Rusya", "text": "Tarihsel husumet, Ukrayna savaşı sınır tehdidi", "status": "active"},
            {"rival": "Belarus", "text": "Göçmen krizi, sınır provokasyonları", "status": "active"}
        ],
        "trade_partners": ["Almanya", "Çin", "İtalya", "Fransa", "Çek Cumhuriyeti"],
        "territorial_disputes": [],
        "organizations": ["NATO", "AB", "Vişegrad Grubu"]
    },
    "Arjantin": {
        "allies": ["Brezilya", "Şili", "Uruguay"],
        "rivalries": [
            {"rival": "Birleşik Krallık", "text": "Falkland/Malvinas Adaları egemenliği", "status": "frozen"}
        ],
        "trade_partners": ["Brezilya", "Çin", "ABD", "Şili", "Hindistan"],
        "territorial_disputes": ["Falkland/Malvinas Adaları (Birleşik Krallık ile)"],
        "organizations": ["G20", "Mercosur", "CELAC"]
    },
    "Brezilya": {
        "allies": ["Arjantin", "Güney Afrika", "Hindistan"],
        "rivalries": [
            {"rival": "Venezuela", "text": "Mülteci krizi, sınır gerilimi", "status": "tension"}
        ],
        "trade_partners": ["Çin", "ABD", "Arjantin", "Hollanda", "Almanya"],
        "territorial_disputes": [],
        "organizations": ["BRICS+", "G20", "Mercosur", "CELAC"]
    },
    "Meksika": {
        "allies": ["ABD", "Kanada", "Kolombiya"],
        "rivalries": [],
        "trade_partners": ["ABD", "Çin", "Kanada", "Almanya", "Japonya"],
        "territorial_disputes": [],
        "organizations": ["G20", "USMCA", "CELAC", "Pasifik İttifakı"]
    },
    "Kanada": {
        "allies": ["ABD", "Birleşik Krallık", "Fransa", "Avustralya"],
        "rivalries": [
            {"rival": "Çin", "text": "Meng Wanzhou krizi, Hong Kong, insan hakları", "status": "tension"},
            {"rival": "Rusya", "text": "Arktika egemenlik iddiaları", "status": "tension"}
        ],
        "trade_partners": ["ABD", "Çin", "Birleşik Krallık", "Japonya", "Meksika"],
        "territorial_disputes": ["Arktika (Rusya, Danimarka ile)"],
        "organizations": ["NATO", "G7", "USMCA", "Five Eyes", "Commonwealth"]
    },
    "Avustralya": {
        "allies": ["ABD", "Birleşik Krallık", "Japonya", "Hindistan", "Yeni Zelanda"],
        "rivalries": [
            {"rival": "Çin", "text": "Ticaret savaşı, Solomon Adaları, casusluk", "status": "active"}
        ],
        "trade_partners": ["Çin", "Japonya", "Güney Kore", "ABD", "Hindistan"],
        "territorial_disputes": [],
        "organizations": ["AUKUS", "Quad", "Five Eyes", "G20", "RCEP"]
    },
    "İtalya": {
        "allies": ["ABD", "Fransa", "Almanya", "İspanya"],
        "rivalries": [],
        "trade_partners": ["Almanya", "Fransa", "ABD", "Çin", "İspanya"],
        "territorial_disputes": [],
        "organizations": ["NATO", "AB", "G7", "G20"]
    },
    "İspanya": {
        "allies": ["Fransa", "ABD", "İtalya", "Portekiz"],
        "rivalries": [
            {"rival": "Fas", "text": "Ceuta ve Melilla, Batı Sahra", "status": "tension"}
        ],
        "trade_partners": ["Fransa", "Almanya", "İtalya", "Portekiz", "Çin"],
        "territorial_disputes": ["Ceuta ve Melilla (Fas ile)", "Cebelitarık (Birleşik Krallık ile)"],
        "organizations": ["NATO", "AB", "G20"]
    },
    "Portekiz": {
        "allies": ["İspanya", "Birleşik Krallık", "Brezilya", "ABD"],
        "rivalries": [],
        "trade_partners": ["İspanya", "Fransa", "Almanya", "Birleşik Krallık"],
        "territorial_disputes": [],
        "organizations": ["NATO", "AB", "Portekizce Konuşan Ülkeler Topluluğu"]
    },
    "Yunanistan": {
        "allies": ["Fransa", "ABD", "Mısır", "Kıbrıs", "İsrail"],
        "rivalries": [
            {"rival": "Türkiye", "text": "Ege adaları, Kıbrıs, kıta sahanlığı", "status": "active"}
        ],
        "trade_partners": ["İtalya", "Almanya", "Türkiye", "Bulgaristan", "Çin"],
        "territorial_disputes": ["Ege kıta sahanlığı (Türkiye ile)"],
        "organizations": ["NATO", "AB"]
    },
    "İsveç": {
        "allies": ["Finlandiya", "Norveç", "Danimarka", "ABD"],
        "rivalries": [],
        "trade_partners": ["Almanya", "Norveç", "Finlandiya", "Danimarka", "ABD"],
        "territorial_disputes": [],
        "organizations": ["NATO (2024 üye)", "AB", "Nordik Konseyi"]
    },
    "Norveç": {
        "allies": ["ABD", "Birleşik Krallık", "İsveç", "Danimarka"],
        "rivalries": [
            {"rival": "Rusya", "text": "Arktika sınırı, Svalbard", "status": "tension"}
        ],
        "trade_partners": ["Birleşik Krallık", "Almanya", "İsveç", "Hollanda", "ABD"],
        "territorial_disputes": [],
        "organizations": ["NATO", "Nordik Konseyi", "EEA"]
    },
    "Finlandiya": {
        "allies": ["İsveç", "ABD", "Estonya", "Norveç"],
        "rivalries": [
            {"rival": "Rusya", "text": "1340 km sınır, NATO üyeliği sonrası gerilim", "status": "tension"}
        ],
        "trade_partners": ["Almanya", "İsveç", "Rusya", "Hollanda", "ABD"],
        "territorial_disputes": [],
        "organizations": ["NATO (2023 üye)", "AB", "Nordik Konseyi"]
    },
    "Hollanda": {
        "allies": ["ABD", "Belçika", "Almanya", "Birleşik Krallık"],
        "rivalries": [
            {"rival": "Rusya", "text": "MH17 uçağı, yaptırımlar", "status": "active"}
        ],
        "trade_partners": ["Almanya", "Belçika", "ABD", "Çin", "Birleşik Krallık"],
        "territorial_disputes": [],
        "organizations": ["NATO", "AB", "Benelüks"]
    },
    "Belçika": {
        "allies": ["Fransa", "Hollanda", "ABD", "Almanya"],
        "rivalries": [],
        "trade_partners": ["Almanya", "Hollanda", "Fransa", "ABD", "Birleşik Krallık"],
        "territorial_disputes": [],
        "organizations": ["NATO (merkez)", "AB (merkez)", "Benelüks"]
    },
    "İsviçre": {
        "allies": [],
        "rivalries": [],
        "trade_partners": ["Almanya", "ABD", "İtalya", "Fransa", "Birleşik Krallık"],
        "territorial_disputes": [],
        "organizations": ["Tarafsız", "BM (2002 üye)", "EFTA"]
    },
    "Avusturya": {
        "allies": ["Almanya", "İsviçre", "İtalya"],
        "rivalries": [],
        "trade_partners": ["Almanya", "İtalya", "ABD", "İsviçre", "Çin"],
        "territorial_disputes": [],
        "organizations": ["AB", "Tarafsızlık politikası"]
    },
    "Romanya": {
        "allies": ["ABD", "Polonya", "Birleşik Krallık", "Moldova"],
        "rivalries": [
            {"rival": "Rusya", "text": "Karadeniz güvenliği, Moldova/Transdinyester", "status": "tension"}
        ],
        "trade_partners": ["Almanya", "İtalya", "Macaristan", "Fransa", "Türkiye"],
        "territorial_disputes": [],
        "organizations": ["NATO", "AB"]
    },
    "Macaristan": {
        "allies": ["Sırbistan", "Türkiye"],
        "rivalries": [
            {"rival": "Ukrayna", "text": "Macar azınlık hakları, AB-Rusya politikası", "status": "tension"}
        ],
        "trade_partners": ["Almanya", "Avusturya", "İtalya", "Çin", "Polonya"],
        "territorial_disputes": [],
        "organizations": ["NATO", "AB", "Vişegrad Grubu"]
    },
    "Çek Cumhuriyeti": {
        "allies": ["Slovakya", "Polonya", "Almanya", "ABD"],
        "rivalries": [],
        "trade_partners": ["Almanya", "Slovakya", "Polonya", "Çin", "Fransa"],
        "territorial_disputes": [],
        "organizations": ["NATO", "AB", "Vişegrad Grubu"]
    },
    "Sırbistan": {
        "allies": ["Rusya", "Çin", "Macaristan"],
        "rivalries": [
            {"rival": "Kosova", "text": "Bağımsızlık tanınması, Kuzey Kosova gerilimi", "status": "active"},
            {"rival": "Hırvatistan", "text": "90'lar savaşı mirası", "status": "cold"}
        ],
        "trade_partners": ["Almanya", "Çin", "İtalya", "Rusya", "Bosna Hersek"],
        "territorial_disputes": ["Kosova"],
        "organizations": ["AB aday", "BRICS+ gözlemci"]
    },
    "Gürcistan": {
        "allies": ["Ukrayna", "ABD", "Türkiye"],
        "rivalries": [
            {"rival": "Rusya", "text": "2008 savaşı, Güney Osetya ve Abhazya işgali", "status": "active"}
        ],
        "trade_partners": ["Türkiye", "Çin", "Rusya", "Azerbaycan", "ABD"],
        "territorial_disputes": ["Güney Osetya (Rusya işgalinde)", "Abhazya (Rusya işgalinde)"],
        "organizations": ["AB aday", "NATO ortağı"]
    },
    "Azerbaycan": {
        "allies": ["Türkiye", "İsrail", "Pakistan"],
        "rivalries": [
            {"rival": "Ermenistan", "text": "Karabağ savaşları (2020, 2023), etnik gerginlik", "status": "post-war"}
        ],
        "trade_partners": ["İtalya", "Türkiye", "İsrail", "Hindistan", "Gürcistan"],
        "territorial_disputes": ["Karabağ bölgesi (2023'te geri alındı)"],
        "organizations": ["Türk Devletleri Teşkilatı", "BDT", "Bağlantısızlar Hareketi"]
    },
    "Ermenistan": {
        "allies": ["Fransa", "Hindistan", "Yunanistan"],
        "rivalries": [
            {"rival": "Azerbaycan", "text": "Karabağ kaybı, sınır güvenliği", "status": "post-war"},
            {"rival": "Türkiye", "text": "1915 soykırımı tanınması, sınır kapısı", "status": "frozen"}
        ],
        "trade_partners": ["Rusya", "Çin", "İran", "Birleşik Arap Emirlikleri", "Almanya"],
        "territorial_disputes": ["Karabağ (kaybedildi)"],
        "organizations": ["KGAÖ (askıda)", "BDT", "Avrasya Ekonomik Birliği"]
    },
    "Suriye": {
        "allies": ["İran", "Rusya"],
        "rivalries": [
            {"rival": "İsrail", "text": "Golan Tepeleri, İran varlığına saldırılar", "status": "active"},
            {"rival": "Türkiye", "text": "Kuzey Suriye operasyonları, Kürt meselesi", "status": "active"}
        ],
        "trade_partners": ["Rusya", "İran", "Çin", "Irak", "Lübnan"],
        "territorial_disputes": ["Golan Tepeleri (İsrail işgalinde)"],
        "organizations": ["Arap Birliği (2023 geri dönüş)"]
    },
    "Irak": {
        "allies": ["İran", "ABD"],
        "rivalries": [
            {"rival": "Türkiye", "text": "PKK operasyonları, Kuzey Irak", "status": "tension"}
        ],
        "trade_partners": ["Çin", "Hindistan", "ABD", "Güney Kore", "Türkiye"],
        "territorial_disputes": ["Kerkük (Kürt-Arap gerilimi)"],
        "organizations": ["Arap Birliği", "OPEC"]
    },
    "Lübnan": {
        "allies": ["İran (Hizbullah)", "Suriye"],
        "rivalries": [
            {"rival": "İsrail", "text": "Hizbullah çatışmaları, sınır gerilimi", "status": "active"}
        ],
        "trade_partners": ["Birleşik Arap Emirlikleri", "Çin", "ABD", "Türkiye"],
        "territorial_disputes": ["Şebaa Çiftlikleri (İsrail ile)"],
        "organizations": ["Arap Birliği"]
    },
    "Etiyopya": {
        "allies": ["Çin", "Birleşik Arap Emirlikleri"],
        "rivalries": [
            {"rival": "Mısır", "text": "Hedasi Barajı, Nil suyu paylaşımı", "status": "active"},
            {"rival": "Eritre", "text": "Sınır savaşı mirası, Tigray çatışması", "status": "tension"},
            {"rival": "Somali", "text": "Somaliland tanınması, denize erişim", "status": "active"}
        ],
        "trade_partners": ["Çin", "ABD", "Suudi Arabistan", "Hindistan", "Almanya"],
        "territorial_disputes": ["Somaliland deniz anlaşması"],
        "organizations": ["Afrika Birliği (merkez)", "IGAD"]
    },
    "Güney Afrika": {
        "allies": ["Brezilya", "Hindistan", "Çin", "Rusya"],
        "rivalries": [],
        "trade_partners": ["Çin", "ABD", "Almanya", "Birleşik Krallık", "Hindistan"],
        "territorial_disputes": [],
        "organizations": ["BRICS+ (ev sahibi 2023)", "G20", "Afrika Birliği", "SADC"]
    },
    "Nijerya": {
        "allies": ["ABD", "Birleşik Krallık", "Fransa"],
        "rivalries": [
            {"rival": "Kamerun", "text": "Bakassi Yarımadası mirası, sınır çatışmaları", "status": "tension"}
        ],
        "trade_partners": ["Hindistan", "İspanya", "ABD", "Hollanda", "Fransa"],
        "territorial_disputes": [],
        "organizations": ["OPEC", "Afrika Birliği", "ECOWAS"]
    },
    "Kenya": {
        "allies": ["ABD", "Birleşik Krallık"],
        "rivalries": [
            {"rival": "Somali", "text": "Deniz sınırı, El-Şebab tehdidi", "status": "tension"}
        ],
        "trade_partners": ["Çin", "Hindistan", "ABD", "Birleşik Arap Emirlikleri", "Uganda"],
        "territorial_disputes": ["Deniz sınırı (Somali ile - UCM kararı)"],
        "organizations": ["Afrika Birliği", "Doğu Afrika Topluluğu"]
    },
    "Fas": {
        "allies": ["ABD", "Fransa", "İsrail", "Suudi Arabistan"],
        "rivalries": [
            {"rival": "Cezayir", "text": "Batı Sahra, sınır kapanması, bölgesel rekabet", "status": "active"},
            {"rival": "İspanya", "text": "Ceuta/Melilla, göç sorunu", "status": "tension"}
        ],
        "trade_partners": ["İspanya", "Fransa", "ABD", "İtalya", "Çin"],
        "territorial_disputes": ["Batı Sahra", "Ceuta ve Melilla (İspanya ile)"],
        "organizations": ["Abraham Anlaşmaları", "Afrika Birliği (geri dönüş)"]
    },
    "Cezayir": {
        "allies": ["Rusya", "Çin", "Filistin"],
        "rivalries": [
            {"rival": "Fas", "text": "Batı Sahra sorunu, diplomatik ilişki kesintisi", "status": "active"},
            {"rival": "Fransa", "text": "Sömürge mirası, hafıza savaşları", "status": "tension"}
        ],
        "trade_partners": ["İtalya", "Fransa", "İspanya", "Çin", "Türkiye"],
        "territorial_disputes": ["Batı Sahra (Fas ile)"],
        "organizations": ["OPEC", "Afrika Birliği", "Arap Birliği"]
    },
    "Kolombiya": {
        "allies": ["ABD", "Birleşik Krallık"],
        "rivalries": [
            {"rival": "Venezuela", "text": "Mülteci krizi, sınır gerilimi, ideolojik farklılık", "status": "tension"}
        ],
        "trade_partners": ["ABD", "Çin", "Meksika", "Brezilya", "Ekvador"],
        "territorial_disputes": [],
        "organizations": ["OECD", "Pasifik İttifakı"]
    },
    "Venezuela": {
        "allies": ["Küba", "Rusya", "İran", "Çin"],
        "rivalries": [
            {"rival": "ABD", "text": "Yaptırımlar, rejim değişikliği baskısı", "status": "active"},
            {"rival": "Guyana", "text": "Essequibo bölgesi egemenlik iddiası", "status": "active"},
            {"rival": "Kolombiya", "text": "Sınır gerilimi, mülteci krizi", "status": "tension"}
        ],
        "trade_partners": ["Çin", "Hindistan", "ABD", "Türkiye"],
        "territorial_disputes": ["Essequibo (Guyana ile)"],
        "organizations": ["OPEC", "CELAC"]
    },
    "Küba": {
        "allies": ["Venezuela", "Rusya", "Çin"],
        "rivalries": [
            {"rival": "ABD", "text": "Ambargo, Guantanamo, rejim karşıtlığı", "status": "active"}
        ],
        "trade_partners": ["Çin", "İspanya", "Kanada", "Rusya"],
        "territorial_disputes": ["Guantanamo Körfezi (ABD üssü)"],
        "organizations": ["CELAC", "Bağlantısızlar Hareketi"]
    },
    "Endonezya": {
        "allies": ["Avustralya", "Japonya", "ABD"],
        "rivalries": [
            {"rival": "Çin", "text": "Natuna Denizi, Güney Çin Denizi iddiaları", "status": "tension"}
        ],
        "trade_partners": ["Çin", "ABD", "Japonya", "Hindistan", "Malezya"],
        "territorial_disputes": ["Natuna Denizi (Çin ile)"],
        "organizations": ["ASEAN", "G20", "RCEP"]
    },
    "Filipinler": {
        "allies": ["ABD", "Japonya", "Avustralya"],
        "rivalries": [
            {"rival": "Çin", "text": "Güney Çin Denizi, resif işgalleri, balıkçılık hakları", "status": "active"}
        ],
        "trade_partners": ["Çin", "ABD", "Japonya", "Güney Kore", "Singapur"],
        "territorial_disputes": ["Güney Çin Denizi (Çin ile)"],
        "organizations": ["ASEAN", "RCEP"]
    },
    "Vietnam": {
        "allies": ["Rusya", "Hindistan"],
        "rivalries": [
            {"rival": "Çin", "text": "Güney Çin Denizi, Paracel/Spratly adaları", "status": "active"}
        ],
        "trade_partners": ["ABD", "Çin", "Güney Kore", "Japonya", "Tayvan"],
        "territorial_disputes": ["Paracel ve Spratly Adaları (Çin ile)"],
        "organizations": ["ASEAN", "RCEP", "CPTPP"]
    },
    "Tayland": {
        "allies": ["ABD", "Çin", "Japonya"],
        "rivalries": [
            {"rival": "Kamboçya", "text": "Preah Vihear tapınağı sınır anlaşmazlığı", "status": "frozen"}
        ],
        "trade_partners": ["Çin", "ABD", "Japonya", "Malezya", "Vietnam"],
        "territorial_disputes": [],
        "organizations": ["ASEAN", "RCEP"]
    },
    "Myanmar": {
        "allies": ["Çin", "Rusya"],
        "rivalries": [],
        "trade_partners": ["Çin", "Tayland", "Japonya", "Hindistan"],
        "territorial_disputes": ["Rohingya sorunu (Bangladeş ile sınır)"],
        "organizations": ["ASEAN (askıda)"]
    },
    "Bangladeş": {
        "allies": ["Çin", "Japonya", "Hindistan"],
        "rivalries": [
            {"rival": "Myanmar", "text": "Rohingya mülteci krizi", "status": "active"}
        ],
        "trade_partners": ["Çin", "Hindistan", "ABD", "Almanya", "Birleşik Krallık"],
        "territorial_disputes": [],
        "organizations": ["BRICS+ (2024 ortağı)", "Bağlantısızlar Hareketi"]
    },
    "Sri Lanka": {
        "allies": ["Hindistan", "Çin"],
        "rivalries": [],
        "trade_partners": ["Çin", "Hindistan", "ABD", "Birleşik Krallık", "Almanya"],
        "territorial_disputes": [],
        "organizations": ["BRICS+ ortağı", "Bağlantısızlar Hareketi"]
    },
    "Afganistan": {
        "allies": ["Pakistan (Taliban)", "Katar"],
        "rivalries": [
            {"rival": "ABD", "text": "20 yıllık işgal mirası, varlık dondurma", "status": "frozen"},
            {"rival": "İran", "text": "Su paylaşımı (Helmand), sınır çatışmaları", "status": "tension"}
        ],
        "trade_partners": ["Pakistan", "İran", "Çin", "Hindistan"],
        "territorial_disputes": ["Durand Hattı (Pakistan ile)"],
        "organizations": ["İslam İşbirliği Teşkilatı (askıda)"]
    },
    "Demokratik Kongo Cumhuriyeti": {
        "allies": ["Angola", "Güney Afrika"],
        "rivalries": [
            {"rival": "Ruanda", "text": "M23 isyanı desteği, kaynak savaşları", "status": "active"},
            {"rival": "Uganda", "text": "Doğu Kongo müdahaleleri", "status": "tension"}
        ],
        "trade_partners": ["Çin", "Güney Afrika", "Belçika", "Hindistan"],
        "territorial_disputes": [],
        "organizations": ["Afrika Birliği", "SADC"]
    },
    "Ruanda": {
        "allies": ["Birleşik Krallık", "ABD"],
        "rivalries": [
            {"rival": "Demokratik Kongo Cumhuriyeti", "text": "M23 desteği suçlaması, maden kaynakları", "status": "active"}
        ],
        "trade_partners": ["Birleşik Arap Emirlikleri", "Çin", "Hindistan", "Kenya"],
        "territorial_disputes": [],
        "organizations": ["Afrika Birliği", "Commonwealth", "Doğu Afrika Topluluğu"]
    },
    "Somali": {
        "allies": ["Türkiye", "Mısır"],
        "rivalries": [
            {"rival": "Etiyopya", "text": "Somaliland tanınması, deniz anlaşması", "status": "active"},
            {"rival": "Kenya", "text": "Deniz sınırı uyuşmazlığı, El-Şebab", "status": "tension"}
        ],
        "trade_partners": ["Birleşik Arap Emirlikleri", "Türkiye", "Çin", "Hindistan"],
        "territorial_disputes": ["Somaliland bağımsızlık talebi"],
        "organizations": ["Afrika Birliği", "Arap Birliği"]
    },
    "Sudan": {
        "allies": ["Mısır", "Suudi Arabistan"],
        "rivalries": [
            {"rival": "Güney Sudan", "text": "Abyei bölgesi, petrol geliri paylaşımı", "status": "active"},
            {"rival": "Etiyopya", "text": "El-Fashaga sınır çatışması", "status": "active"}
        ],
        "trade_partners": ["Çin", "Suudi Arabistan", "Birleşik Arap Emirlikleri"],
        "territorial_disputes": ["Abyei (Güney Sudan ile)", "Halayib (Mısır ile)"],
        "organizations": ["Arap Birliği", "Afrika Birliği"]
    },
    "Güney Sudan": {
        "allies": ["Uganda", "Kenya"],
        "rivalries": [
            {"rival": "Sudan", "text": "Petrol transit hakları, Abyei", "status": "active"}
        ],
        "trade_partners": ["Çin", "Japonya", "Hindistan"],
        "territorial_disputes": ["Abyei (Sudan ile)"],
        "organizations": ["Afrika Birliği", "IGAD"]
    },
    "Libya": {
        "allies": ["Türkiye (Trablus)", "Rusya/Mısır/BAE (Tobruk)"],
        "rivalries": [],
        "trade_partners": ["İtalya", "Türkiye", "Çin", "İspanya"],
        "territorial_disputes": [],
        "organizations": ["Arap Birliği", "OPEC", "Afrika Birliği"]
    },
    "Birleşik Arap Emirlikleri": {
        "allies": ["ABD", "Suudi Arabistan", "İsrail", "Hindistan", "Fransa"],
        "rivalries": [
            {"rival": "İran", "text": "Abu Musa adaları, bölgesel rekabet", "status": "tension"},
            {"rival": "Türkiye", "text": "Bölgesel nüfuz rekabeti", "status": "competition"}
        ],
        "trade_partners": ["Çin", "Hindistan", "Japonya", "ABD", "Suudi Arabistan"],
        "territorial_disputes": ["Abu Musa ve Tunb Adaları (İran ile)"],
        "organizations": ["Körfez İşbirliği Konseyi", "Abraham Anlaşmaları", "OPEC+"]
    },
    "Katar": {
        "allies": ["Türkiye", "ABD"],
        "rivalries": [
            {"rival": "Suudi Arabistan", "text": "2017 ablukası mirası, Al Jazeera", "status": "normalized"}
        ],
        "trade_partners": ["Japonya", "Güney Kore", "Hindistan", "Çin", "Birleşik Krallık"],
        "territorial_disputes": [],
        "organizations": ["Körfez İşbirliği Konseyi", "OPEC"]
    },
    "Belarus": {
        "allies": ["Rusya"],
        "rivalries": [
            {"rival": "Polonya", "text": "Göçmen krizi, sınır provokasyonları", "status": "active"},
            {"rival": "Litvanya", "text": "Göçmen silahı, diplomatik gerilim", "status": "active"}
        ],
        "trade_partners": ["Rusya", "Çin", "Ukrayna", "Almanya", "Polonya"],
        "territorial_disputes": [],
        "organizations": ["BDT", "KGAÖ", "Avrasya Ekonomik Birliği"]
    },
    "Moldova": {
        "allies": ["Romanya", "Ukrayna", "ABD"],
        "rivalries": [
            {"rival": "Rusya", "text": "Transdinyester işgali, enerji bağımlılığı", "status": "active"}
        ],
        "trade_partners": ["Romanya", "Almanya", "İtalya", "Türkiye", "Rusya"],
        "territorial_disputes": ["Transdinyester (Rusya kontrolünde)"],
        "organizations": ["AB aday", "BDT (çekilme sürecinde)"]
    },
    "Kosova": {
        "allies": ["ABD", "Birleşik Krallık", "Almanya", "Türkiye"],
        "rivalries": [
            {"rival": "Sırbistan", "text": "Bağımsızlık tanınması, Kuzey Kosova", "status": "active"}
        ],
        "trade_partners": ["Almanya", "İtalya", "Türkiye", "Çin", "Sırbistan"],
        "territorial_disputes": ["Kuzey Kosova (Sırbistan ile)"],
        "organizations": ["AB aday (potansiyel)", "NATO (KFOR koruma)"]
    },
    "Hırvatistan": {
        "allies": ["ABD", "Almanya", "Slovenya"],
        "rivalries": [
            {"rival": "Sırbistan", "text": "90'lar savaşı mirası, azınlık hakları", "status": "cold"}
        ],
        "trade_partners": ["İtalya", "Almanya", "Slovenya", "Avusturya", "Bosna Hersek"],
        "territorial_disputes": [],
        "organizations": ["NATO", "AB", "Euro bölgesi (2023)"]
    },
    "Bosna Hersek": {
        "allies": ["Türkiye", "ABD"],
        "rivalries": [],
        "trade_partners": ["Almanya", "İtalya", "Hırvatistan", "Sırbistan", "Avusturya"],
        "territorial_disputes": [],
        "organizations": ["NATO ortağı", "AB aday"]
    },
    "Kamerun": {
        "allies": ["Fransa"],
        "rivalries": [
            {"rival": "Nijerya", "text": "Bakassi Yarımadası mirası", "status": "resolved"}
        ],
        "trade_partners": ["Çin", "Hollanda", "İtalya", "Fransa", "Hindistan"],
        "territorial_disputes": [],
        "organizations": ["Afrika Birliği", "Frankofoni"]
    },
    "Şili": {
        "allies": ["ABD", "Birleşik Krallık", "Japonya"],
        "rivalries": [
            {"rival": "Bolivya", "text": "Denize çıkış sorunu, Atacama Çölü", "status": "frozen"}
        ],
        "trade_partners": ["Çin", "ABD", "Japonya", "Güney Kore", "Brezilya"],
        "territorial_disputes": [],
        "organizations": ["OECD", "Pasifik İttifakı", "CPTPP"]
    },
    "Bolivya": {
        "allies": ["Venezuela", "Küba"],
        "rivalries": [
            {"rival": "Şili", "text": "Denize çıkış talebi, Pasifik Savaşı mirası", "status": "frozen"}
        ],
        "trade_partners": ["Brezilya", "Arjantin", "ABD", "Kolombiya", "Çin"],
        "territorial_disputes": ["Denize erişim (Şili ile)"],
        "organizations": ["CELAC", "Mercosur ortağı"]
    },
    "Peru": {
        "allies": ["ABD", "Brezilya"],
        "rivalries": [
            {"rival": "Şili", "text": "Deniz sınırı (UCM ile çözüldü)", "status": "resolved"}
        ],
        "trade_partners": ["Çin", "ABD", "Brezilya", "Güney Kore", "Kanada"],
        "territorial_disputes": [],
        "organizations": ["Pasifik İttifakı", "CPTPP"]
    },
    "Ekvador": {
        "allies": ["ABD", "Kolombiya"],
        "rivalries": [],
        "trade_partners": ["ABD", "Çin", "Panama", "Kolombiya", "Şili"],
        "territorial_disputes": [],
        "organizations": ["OPEC (ayrıldı)", "CELAC"]
    },
    "Angola": {
        "allies": ["Çin", "Brezilya", "Portekiz"],
        "rivalries": [],
        "trade_partners": ["Çin", "Hindistan", "ABD", "Güney Afrika", "Portekiz"],
        "territorial_disputes": ["Cabinda (iç ayrılıkçılık)"],
        "organizations": ["OPEC", "Afrika Birliği", "SADC"]
    },
    "Mozambik": {
        "allies": ["Portekiz", "ABD", "Hindistan"],
        "rivalries": [],
        "trade_partners": ["Güney Afrika", "Hindistan", "Hollanda", "Çin"],
        "territorial_disputes": [],
        "organizations": ["Afrika Birliği", "SADC", "Commonwealth"]
    },
    "Tanzanya": {
        "allies": ["Çin", "Hindistan"],
        "rivalries": [],
        "trade_partners": ["Hindistan", "Çin", "Güney Afrika", "Japonya", "Almanya"],
        "territorial_disputes": [],
        "organizations": ["Afrika Birliği", "Doğu Afrika Topluluğu"]
    },
    "Uganda": {
        "allies": ["ABD", "Birleşik Krallık"],
        "rivalries": [
            {"rival": "Demokratik Kongo Cumhuriyeti", "text": "Doğu Kongo müdahaleleri, kaynak çatışması", "status": "tension"}
        ],
        "trade_partners": ["Kenya", "Birleşik Arap Emirlikleri", "Çin", "Hindistan"],
        "territorial_disputes": [],
        "organizations": ["Afrika Birliği", "Doğu Afrika Topluluğu"]
    },
    "Gana": {
        "allies": ["ABD", "Birleşik Krallık"],
        "rivalries": [],
        "trade_partners": ["Çin", "Hindistan", "ABD", "İsviçre", "Birleşik Arap Emirlikleri"],
        "territorial_disputes": [],
        "organizations": ["Afrika Birliği", "ECOWAS", "Commonwealth"]
    },
    "Filistin": {
        "allies": ["İran", "Türkiye", "Katar", "Cezayir"],
        "rivalries": [
            {"rival": "İsrail", "text": "İşgal, yerleşimler, Gazze ablukası", "status": "war"}
        ],
        "trade_partners": ["İsrail (zoraki)", "Türkiye"],
        "territorial_disputes": ["Batı Şeria", "Gazze", "Doğu Kudüs"],
        "organizations": ["BM gözlemci devlet", "Arap Birliği", "İslam İşbirliği Teşkilatı"]
    },
    "Gazze": {
        "allies": ["Türkiye", "Katar", "İran"],
        "rivalries": [
            {"rival": "İsrail", "text": "Abluka, 2023 savaşı, insani kriz", "status": "war"}
        ],
        "trade_partners": [],
        "territorial_disputes": ["Gazze Şeridi (İsrail ablukası)"],
        "organizations": []
    },
    "Danimarka": {
        "allies": ["ABD", "Norveç", "İsveç", "Almanya"],
        "rivalries": [],
        "trade_partners": ["Almanya", "İsveç", "ABD", "Norveç", "Hollanda"],
        "territorial_disputes": ["Grönland (ABD ilgisi, 2025)"],
        "organizations": ["NATO", "AB", "Nordik Konseyi"]
    },
    "Gronland": {
        "allies": ["Danimarka"],
        "rivalries": [],
        "trade_partners": ["Danimarka", "ABD"],
        "territorial_disputes": ["Özerklik/bağımsızlık tartışması", "ABD satın alma ilgisi"],
        "organizations": ["Danimarka Krallığı (özerk)"]
    },
    "Bulgaristan": {
        "allies": ["Romanya", "Yunanistan", "ABD"],
        "rivalries": [
            {"rival": "Rusya", "text": "Enerji bağımlılığı, casusluk", "status": "tension"}
        ],
        "trade_partners": ["Almanya", "Romanya", "İtalya", "Türkiye", "Yunanistan"],
        "territorial_disputes": [],
        "organizations": ["NATO", "AB"]
    },
    "Estonya": {
        "allies": ["ABD", "Finlandiya", "Birleşik Krallık"],
        "rivalries": [
            {"rival": "Rusya", "text": "Siber saldırılar, Rus azınlık, sınır güvenliği", "status": "active"}
        ],
        "trade_partners": ["Finlandiya", "Almanya", "Litvanya", "Letonya", "İsveç"],
        "territorial_disputes": [],
        "organizations": ["NATO", "AB", "Dijital liderlik"]
    },
    "Guyana": {
        "allies": ["ABD", "Birleşik Krallık", "Brezilya"],
        "rivalries": [
            {"rival": "Venezuela", "text": "Essequibo bölgesi egemenlik iddiası", "status": "active"}
        ],
        "trade_partners": ["ABD", "Singapur", "Birleşik Krallık", "Trinidad-Tobago"],
        "territorial_disputes": ["Essequibo (Venezuela ile)"],
        "organizations": ["CARICOM", "Commonwealth"]
    },
    "Haiti": {
        "allies": ["ABD", "Kanada"],
        "rivalries": [],
        "trade_partners": ["ABD", "Dominik Cumhuriyeti", "Çin"],
        "territorial_disputes": [],
        "organizations": ["CARICOM"]
    },
    "El Salvador": {
        "allies": ["ABD", "Çin"],
        "rivalries": [],
        "trade_partners": ["ABD", "Guatemala", "Honduras", "Çin"],
        "territorial_disputes": [],
        "organizations": ["SICA"]
    },
    "Guatemala": {
        "allies": ["ABD"],
        "rivalries": [],
        "trade_partners": ["ABD", "Meksika", "El Salvador", "Çin", "Honduras"],
        "territorial_disputes": ["Belize sınır anlaşmazlığı"],
        "organizations": ["SICA"]
    },
    "Eritre": {
        "allies": ["Rusya", "Çin"],
        "rivalries": [
            {"rival": "Etiyopya", "text": "Sınır savaşı mirası, Tigray müdahalesi", "status": "complex"}
        ],
        "trade_partners": ["Çin", "Suudi Arabistan", "Birleşik Arap Emirlikleri"],
        "territorial_disputes": [],
        "organizations": ["Afrika Birliği"]
    },
    "Burkina Faso": {
        "allies": ["Rusya (Wagner)", "Mali", "Nijer"],
        "rivalries": [
            {"rival": "Fransa", "text": "Askeri üs kapanması, neo-sömürgecilik suçlaması", "status": "severed"}
        ],
        "trade_partners": ["İsviçre", "Hindistan", "Güney Afrika", "Çin"],
        "territorial_disputes": [],
        "organizations": ["Sahel İttifakı (AES)", "Afrika Birliği"]
    },
    "Mali": {
        "allies": ["Rusya (Wagner)", "Burkina Faso", "Nijer"],
        "rivalries": [
            {"rival": "Fransa", "text": "Barkhane operasyonu sonu, diplomatik kopuş", "status": "severed"}
        ],
        "trade_partners": ["Senegal", "İsviçre", "Çin", "Birleşik Arap Emirlikleri"],
        "territorial_disputes": [],
        "organizations": ["Sahel İttifakı (AES)", "Afrika Birliği"]
    },
    "Nijer": {
        "allies": ["Rusya", "Mali", "Burkina Faso"],
        "rivalries": [
            {"rival": "Fransa", "text": "2023 darbe sonrası askeri çekilme", "status": "severed"},
            {"rival": "ECOWAS", "text": "Darbe sonrası yaptırım tehdidi", "status": "tension"}
        ],
        "trade_partners": ["Fransa", "Çin", "Nijerya", "Hindistan"],
        "territorial_disputes": [],
        "organizations": ["Sahel İttifakı (AES)"]
    },
    "Singapur": {
        "allies": ["ABD", "Avustralya", "Hindistan"],
        "rivalries": [
            {"rival": "Malezya", "text": "Su temini, hava sahası, tarihsel gerilim", "status": "managed"}
        ],
        "trade_partners": ["Çin", "ABD", "Malezya", "Tayvan", "Japonya"],
        "territorial_disputes": ["Pedra Branca (çözüldü)"],
        "organizations": ["ASEAN", "RCEP", "CPTPP"]
    },
    "Malezya": {
        "allies": ["Çin", "Japonya", "Türkiye"],
        "rivalries": [
            {"rival": "Çin", "text": "Güney Çin Denizi iddiaları", "status": "tension"},
            {"rival": "Singapur", "text": "Su ve hava sahası anlaşmazlıkları", "status": "managed"}
        ],
        "trade_partners": ["Çin", "Singapur", "ABD", "Japonya", "Tayland"],
        "territorial_disputes": ["Güney Çin Denizi (Çin ile)"],
        "organizations": ["ASEAN", "İslam İşbirliği Teşkilatı", "RCEP"]
    },
    "Kamboçya": {
        "allies": ["Çin"],
        "rivalries": [
            {"rival": "Vietnam", "text": "Tarihsel husumet, Khmer Kızılları mirası", "status": "managed"}
        ],
        "trade_partners": ["ABD", "Çin", "Japonya", "Tayland", "Vietnam"],
        "territorial_disputes": [],
        "organizations": ["ASEAN", "RCEP"]
    }
}


def enrich():
    meta_path = BASE / "output" / "meta.json"
    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    cm = meta.get("country_metadata", {})
    updated = 0
    added_new = 0

    for country_name, rel_data in RELATIONS_DB.items():
        if country_name not in cm:
            continue

        entry = cm[country_name]

        # Update allies (always overwrite with richer data)
        if rel_data.get("allies"):
            entry["allies"] = rel_data["allies"]

        # Update rivalries (merge with existing, avoid duplicates)
        existing_rivals = {r.get("rival", r) if isinstance(r, dict) else r for r in entry.get("rivalries", [])}
        new_rivalries = []
        for r in rel_data.get("rivalries", []):
            rival_name = r["rival"] if isinstance(r, dict) else r
            new_rivalries.append(r)

        if new_rivalries:
            entry["rivalries"] = new_rivalries

        # Add trade partners
        if rel_data.get("trade_partners"):
            entry["trade_partners"] = rel_data["trade_partners"]

        # Add territorial disputes
        if rel_data.get("territorial_disputes"):
            entry["territorial_disputes"] = rel_data["territorial_disputes"]

        # Add organizations
        if rel_data.get("organizations"):
            entry["organizations"] = rel_data["organizations"]

        cm[country_name] = entry
        updated += 1

    meta["country_metadata"] = cm
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    print(f"Enriched {updated} countries with relations data")
    print(f"Total countries in DB: {len(RELATIONS_DB)}")

    # Stats
    has_allies = sum(1 for v in cm.values() if v.get("allies"))
    has_rivals = sum(1 for v in cm.values() if v.get("rivalries"))
    has_trade = sum(1 for v in cm.values() if v.get("trade_partners"))
    has_orgs = sum(1 for v in cm.values() if v.get("organizations"))
    print(f"Coverage: allies={has_allies}, rivals={has_rivals}, trade={has_trade}, orgs={has_orgs} / {len(cm)}")


if __name__ == "__main__":
    enrich()
