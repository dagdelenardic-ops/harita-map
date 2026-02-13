#!/usr/bin/env python3
"""
Merge user-provided Scandinavia + Baltic events into data/events.json.

Goals:
- Add missing events (especially 1900-1930 gaps) without creating near-duplicates.
- Prefer the more comprehensive description when an exact title match exists.
- Keep canonical country naming consistent with Admin/Map ("country_name" Turkish).
- Never overwrite existing youtube_video_id, wikipedia_url etc.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


BASE_DIR = Path(__file__).resolve().parent.parent
EVENTS_PATH = BASE_DIR / "data" / "events.json"

ALLOWED_COUNTRIES = {
    "Danimarka",
    "Norveç",
    "İsveç",
    "Finlandiya",
    "İzlanda",
    "Estonya",
    "Letonya",
    "Litvanya",
}


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip().casefold())


def _event_id(country: str, year: int, title: str) -> str:
    h = hashlib.md5(f"{country}|{year}|{_norm(title)}".encode("utf-8")).hexdigest()[:10]
    return f"ev_scand_{h}"


def _category_map(raw: str) -> str:
    s = _norm(raw)
    # tolerate common variants/typos
    s = (
        s.replace("savas", "savaş")
        .replace("catisma", "çatışma")
        .replace("degisikligi", "değişikliği")
        .replace("onemli", "önemli")
        .replace("kultur", "kültür")
        .replace("toplum", "toplum")
    )

    if any(k in s for k in ["savaş", "çatışma"]):
        return "war"
    if "soyk" in s:
        return "genocide"
    if any(k in s for k in ["rejim", "devrim", "darbe"]):
        return "revolution"
    if "ter" in s:
        return "terror"
    if any(k in s for k in ["lider", "başbakan", "kral", "cumhurbaşkanı"]):
        return "leader"
    if "diplom" in s or "nato" in s or "bm" in s or "birleşmiş" in s:
        return "diplomacy"
    if any(k in s for k in ["polit", "ekonomi"]):
        return "politics"
    if any(k in s for k in ["kültür", "toplum"]):
        return "culture"
    return "culture"


def _decade(year: int) -> str:
    return f"{(year // 10) * 10}s"


def _coords_index(events: List[Dict[str, Any]]) -> Dict[str, Tuple[float, float]]:
    out: Dict[str, Tuple[float, float]] = {}
    for e in events:
        cn = (e.get("country_name") or "").strip()
        if not cn:
            continue
        try:
            lat = float(e.get("lat") or 0)
            lon = float(e.get("lon") or 0)
        except Exception:
            continue
        if (lat == 0 and lon == 0) or cn in out:
            continue
        out[cn] = (lat, lon)
    return out


def _fallback_coords(country: str) -> Tuple[float, float]:
    # Used only if dataset has no coordinates for that country yet.
    centers = {
        "Danimarka": (55.6761, 12.5683),  # Copenhagen
        "Norveç": (59.9139, 10.7522),  # Oslo
        "İsveç": (59.3293, 18.0686),  # Stockholm
        "Finlandiya": (60.1699, 24.9384),  # Helsinki
        "İzlanda": (64.1466, -21.9426),  # Reykjavik
        "Estonya": (59.4370, 24.7536),  # Tallinn
        "Letonya": (56.9496, 24.1052),  # Riga
        "Litvanya": (54.6872, 25.2797),  # Vilnius
    }
    return centers.get(country, (0.0, 0.0))


def _merge_longer_description(target: Dict[str, Any], incoming_desc: str) -> bool:
    inc = (incoming_desc or "").strip()
    if not inc:
        return False
    cur = (target.get("description") or "").strip()
    if len(inc) > len(cur) + 20:
        target["description"] = inc
        return True
    return False


def _load_user_events() -> List[Dict[str, Any]]:
    """
    Hard-coded from the user's paste in chat.
    We intentionally filter to ALLOWED_COUNTRIES.
    """
    out: List[Dict[str, Any]] = []

    # Source 1 (markdown bullets) - 1900-1929 (selected)
    out.extend(
        [
            # 1900-1909
            {
                "country_name": "Norveç",
                "year": 1905,
                "category": "revolution",
                "title": "İsveç-Norveç Birliği'nin Sona Ermesi",
                "description": "1905'te Norveç, İsveç'le kişisel birliği referandumla sonlandırdı ve bağımsız bir monarşi olarak yeniden kuruldu; modern İskandinav ulus-devletleşmesinin dönüm noktalarındandır.",
                "key_figures": ["Haakon VII"],
            },
            # Finland: law 1906, first election 1907 (user paste had 1907; we keep the core but correct context)
            {
                "country_name": "Finlandiya",
                "year": 1906,
                "category": "revolution",
                "title": "Finlandiya'da Kadınlara Tam Oy Hakkı",
                "description": "Finlandiya, kadınlara tam oy hakkı tanıyan öncü ülkelerden biri oldu; 1907 seçimlerinde kadınlar ilk kez oy kullandı ve parlamentoya girdi.",
                "key_figures": [],
            },
            {
                "country_name": "Estonya",
                "year": 1905,
                "category": "revolution",
                "title": "1905 Devrimi'nin Baltık'ta Yankıları (Estonya)",
                "description": "1905 Rus Devrimi, Estonya'da milliyetçi ve toplumsal hareketleri tetikledi; Çarlık yönetiminin sert bastırması ulusal bilinci kalıcı biçimde güçlendirdi.",
                "key_figures": [],
            },
            {
                "country_name": "Letonya",
                "year": 1905,
                "category": "revolution",
                "title": "1905 Devrimi'nin Baltık'ta Yankıları (Letonya)",
                "description": "1905 Rus Devrimi, Letonya'da milliyetçi ve toplumsal hareketleri tetikledi; bastırma süreci buna rağmen ulusal mobilizasyonu büyüttü.",
                "key_figures": [],
            },
            {
                "country_name": "İzlanda",
                "year": 1908,
                "category": "revolution",
                "title": "İzlanda'da Özerklik Taleplerinin Yükselişi",
                "description": "20. yüzyıl başında özerklik talepleri hızla arttı; süreç 1918 Danimarka ile birlik anlaşmasına ve 1944'te cumhuriyete giden yolu açtı.",
                "key_figures": [],
            },
            # 1910-1919
            {
                "country_name": "Finlandiya",
                "year": 1917,
                "category": "revolution",
                "title": "Rusya'dan Bağımsızlık İlanı",
                "description": "1917'de Finlandiya Rusya'dan bağımsızlığını ilan etti; kısa iç savaş ve 1919 anayasal cumhuriyet, devletin kurumsal çerçevesini belirledi.",
                "key_figures": [],
            },
            {
                "country_name": "Estonya",
                "year": 1918,
                "category": "war",
                "title": "Bağımsızlık İlanı ve Kurtuluş Savaşı",
                "description": "1918 bağımsızlık ilanı sonrası Alman ve Bolşevik güçlere karşı savaş verildi; 1920'de bağımsızlık uluslararası olarak pekişti.",
                "key_figures": [],
            },
            {
                "country_name": "Letonya",
                "year": 1918,
                "category": "war",
                "title": "Bağımsızlık İlanı ve Bağımsızlık Savaşı",
                "description": "1918'de bağımsızlık ilanı sonrası Alman ve Bolşevik güçlere karşı yürütülen savaş, devletin kuruluşunu güvence altına aldı.",
                "key_figures": [],
            },
            {
                "country_name": "Litvanya",
                "year": 1918,
                "category": "revolution",
                "title": "Bağımsızlık İlanı (16 Şubat)",
                "description": "Litvanya 1918'de bağımsızlığını ilan etti; savaş sonrası düzen içinde devlet kurumları inşa edildi.",
                "key_figures": [],
            },
            # 1920-1929
            {
                "country_name": "Estonya",
                "year": 1920,
                "category": "diplomacy",
                "title": "Tartu Antlaşması",
                "description": "Tartu Antlaşması ile Sovyet Rusya Estonya'nın bağımsızlığını tanıdı; erken dönem uluslararası tanınma sürecinin temel belgesi oldu.",
                "key_figures": [],
            },
            {
                "country_name": "Letonya",
                "year": 1920,
                "category": "diplomacy",
                "title": "Sovyetlerle Barış Antlaşması",
                "description": "Letonya ile Sovyet Rusya arasındaki barış antlaşması, yeni devletin egemenlik çerçevesini pekiştirdi.",
                "key_figures": [],
            },
            {
                "country_name": "Litvanya",
                "year": 1920,
                "category": "diplomacy",
                "title": "Sovyetlerle Barış Antlaşması",
                "description": "Litvanya ile Sovyet Rusya arasındaki barış antlaşması, bağımsızlığın uluslararası düzeyde tanınmasını güçlendirdi.",
                "key_figures": [],
            },
            {
                "country_name": "Litvanya",
                "year": 1922,
                "category": "politics",
                "title": "İlk Demokratik Anayasa",
                "description": "Bağımsız Litvanya'da 1922 Anayasası kabul edilerek parlamenter kurumlar şekillendi.",
                "key_figures": [],
            },
            {
                "country_name": "Estonya",
                "year": 1924,
                "category": "terror",
                "title": "Sovyet Destekli Darbe Girişimi (Aralık 1924)",
                "description": "1924'te Sovyet destekli komünist darbe girişimi başarısız oldu; iç güvenlik politikaları sertleşti ve rejim konsolide edildi.",
                "key_figures": [],
            },
        ]
    )

    # Source 2 (JSON paste) - filter to allowed countries only
    src2 = [
        {
            "ulke": "İsveç",
            "onYil": "1920s",
            "yil": 1921,
            "kategori": "Politika",
            "baslik": "İsveç'te kadınlara oy hakkı ve ilk seçim",
            "aciklama": "1921 genel seçimlerinde İsveçli kadınlar ilk kez oy kullanarak parlamentoya temsilci gönderdi; bu adım ülkenin parlamenter demokrasisini toplumsal cinsiyet açısından dönüştüren bir eşik oldu.",
        },
        {
            "ulke": "Danimarka",
            "onYil": "1920s",
            "yil": 1920,
            "kategori": "Diplomasi",
            "baslik": "Schleswig plebisiti ve sınırın kalıcılaşması",
            "aciklama": "1920 plebisitiyle Kuzey Schleswig halkı yeniden Danimarka'ya katılmayı seçti; bugünkü Danimarka–Almanya sınırı bu referandumla fiilen netleşti.",
        },
        {
            "ulke": "Finlandiya",
            "onYil": "1920s",
            "yil": 1920,
            "kategori": "RejimDegisikligi",
            "baslik": "Cumhuriyet kurumlarının yerleşmesi",
            "aciklama": "1918 iç savaşının ardından 1920'ler boyunca Finlandiya çok partili parlamenter sistemi güçlendirerek genç cumhuriyetin istikrarını sağlamaya çalıştı.",
        },
        {
            "ulke": "Norveç",
            "onYil": "1930s",
            "yil": 1935,
            "kategori": "Politika",
            "baslik": "Norveç İşçi Partisi hükümeti",
            "aciklama": "1935'te İşçi Partisi hükümeti kurarak Norveç'te vergilendirme, işçi hakları ve sosyal politika alanında kapsamlı reformlara imza attı.",
        },
        {
            "ulke": "İsveç",
            "onYil": "1930s",
            "yil": 1932,
            "kategori": "Politika",
            "baslik": "Sosyal Demokratların uzun iktidar dönemi",
            "aciklama": "1932 seçimlerinden sonra İsveç Sosyal Demokrat Partisi iktidara gelerek işsizlikle mücadele ve sosyal güvenlik reformlarıyla modern refah devletini kurmaya başladı.",
        },
        {
            "ulke": "Norveç",
            "onYil": "1940s",
            "yil": 1940,
            "kategori": "SavasCatısma",
            "baslik": "Norveç'in Nazi Almanyası tarafından işgali",
            "aciklama": "Nisan 1940'ta Almanya, Norveç'i işgal etti; hükümet Londra'ya kaçarken içeride hem Quisling işbirlikçi rejimi hem de güçlü bir direniş hareketi ortaya çıktı.",
        },
        {
            "ulke": "Danimarka",
            "onYil": "1940s",
            "yil": 1940,
            "kategori": "SavasCatısma",
            "baslik": "Danimarka'nın işgali ve işbirliği politikası",
            "aciklama": "Alman işgali altındaki Danimarka, iç özerkliğini korumak için 'kontrollü işbirliği' stratejisi izledi; bu politika savaş sonrasında yoğun tartışmalara yol açtı.",
        },
        # Finland 1939-40 Winter War exists already; don't add a duplicate from this paste.
        {
            "ulke": "Norveç",
            "onYil": "1940s",
            "yil": 1949,
            "kategori": "Diplomasi",
            "baslik": "Norveç'in NATO'ya katılması",
            "aciklama": "Norveç 1949'da NATO'nun kurucu üyelerinden biri oldu ve Kuzey Atlantik savunma hattının kilit parçalarından biri hâline geldi.",
        },
        {
            "ulke": "İsveç",
            "onYil": "1950s",
            "yil": 1952,
            "kategori": "Diplomasi",
            "baslik": "İskandinav Konseyi'nin kuruluşu",
            "aciklama": "1952'de kurulan İskandinav Konseyi, bölge ülkeleri arasında pasaportsuz dolaşım ve ortak işgücü piyasası gibi uygulamalara giden kurumsal işbirliğini başlattı.",
        },
        {
            "ulke": "Finlandiya",
            "onYil": "1950s",
            "yil": 1955,
            "kategori": "Diplomasi",
            "baslik": "Finlandiya'nın Birleşmiş Milletler'e girişi",
            "aciklama": "Finlandiya 1955'te BM üyesi olarak uluslararası izolasyonu kırdı ve Sovyetler ile Batı arasında yürüttüğü denge politikasını küresel platforma taşıdı.",
        },
        {
            "ulke": "Norveç",
            "onYil": "1970s",
            "yil": 1970,
            "kategori": "Politika",
            "baslik": "Kuzey Denizi petrolünün keşfi",
            "aciklama": "1970'lerde Kuzey Denizi'nde bulunan petrol sahaları Norveç'i büyük bir enerji üreticisine dönüştürdü ve ileride devlet petrol fonunun temelini attı.",
        },
        {
            "ulke": "Norveç",
            "onYil": "1970s",
            "yil": 1972,
            "kategori": "Politika",
            "baslik": "Norveç'te AET referandumu",
            "aciklama": "1972 referandumunda Norveç halkı Avrupa Ekonomik Topluluğu'na üyeliğe hayır dedi; ülke ekonomik entegrasyonla siyasi mesafeyi birleştiren çizgiyi tercih etti.",
        },
        {
            "ulke": "İsveç",
            "onYil": "1980s",
            "yil": 1986,
            "kategori": "OnemliLider",
            "baslik": "Başbakan Olof Palme suikastı",
            "aciklama": "İsveç Başbakanı Olof Palme 1986'da Stockholm'de sokak ortasında öldürüldü; olay uzun süre çözülemeyen bir siyasi cinayet dosyasına dönüştü.",
        },
        {
            "ulke": "Norveç",
            "onYil": "2010s",
            "yil": 2011,
            "kategori": "TerorSaldirisi",
            "baslik": "Utøya ve Oslo'da aşırı sağcı terör",
            "aciklama": "2011'de Norveç'te gerçekleştirilen bombalı saldırı ve Utøya adasındaki katliam, ülkede aşırı sağ radikalleşme ve güvenlik politikalarını kökten tartıştırdı.",
        },
        {
            "ulke": "İsveç",
            "onYil": "2010s",
            "yil": 2018,
            "kategori": "KulturToplum",
            "baslik": "İklim aktivizminin yükselişi",
            "aciklama": "İsveçli öğrenci Greta Thunberg'in başlattığı okul grevleri, dünya çapında genç iklim hareketinin sembolü hâline geldi.",
        },
        {
            "ulke": "Finlandiya",
            "onYil": "2020s",
            "yil": 2022,
            "kategori": "Diplomasi",
            "baslik": "Finlandiya'nın NATO başvurusu",
            "aciklama": "Rusya'nın Ukrayna'yı işgali sonrası Finlandiya, askeri ittifaka katılma kararı alarak geleneksel tarafsızlık çizgisini terk etti.",
        },
        {
            "ulke": "İsveç",
            "onYil": "2020s",
            "yil": 2022,
            "kategori": "Diplomasi",
            "baslik": "İsveç'in NATO başvurusu",
            "aciklama": "İsveç 2022'de NATO üyeliği için başvurarak güvenlik doktrininde tarihsel bir değişime gitti.",
        },
    ]

    for e in src2:
        country = (e.get("ulke") or "").strip()
        if country not in ALLOWED_COUNTRIES:
            continue
        year = int(e["yil"])
        out.append(
            {
                "country_name": country,
                "year": year,
                "category": _category_map(str(e.get("kategori") or "")),
                "title": str(e.get("baslik") or "").strip(),
                "description": str(e.get("aciklama") or "").strip(),
                "key_figures": [],
            }
        )

    return out


def main() -> None:
    data = json.loads(EVENTS_PATH.read_text(encoding="utf-8"))
    events = data.get("events") or []
    if not isinstance(events, list):
        raise SystemExit("events.json: `events` must be a list")

    coords = _coords_index([e for e in events if isinstance(e, dict)])

    # Index existing events by (country, year, normalized title)
    idx: Dict[Tuple[str, int, str], Dict[str, Any]] = {}
    for e in events:
        if not isinstance(e, dict):
            continue
        country = (e.get("country_name") or "").strip()
        year = e.get("year")
        title = (e.get("title") or "").strip()
        if not country or not isinstance(year, int) or not title:
            continue
        idx[(country, year, _norm(title))] = e

    incoming = _load_user_events()
    added = 0
    updated = 0
    skipped = 0

    for inc in incoming:
        country = inc["country_name"]
        if country not in ALLOWED_COUNTRIES:
            continue
        year = int(inc["year"])
        title = str(inc["title"]).strip()
        key = (country, year, _norm(title))

        existing = idx.get(key)
        if existing:
            # Prefer longer description only (safe merge).
            if _merge_longer_description(existing, str(inc.get("description") or "")):
                updated += 1
            else:
                skipped += 1
            continue

        lat, lon = coords.get(country, _fallback_coords(country))
        ev = {
            "id": _event_id(country, year, title),
            "country_code": "",  # normalize_events.py will fill
            "country_name": country,
            "lat": lat,
            "lon": lon,
            "decade": _decade(year),
            "year": year,
            "category": str(inc.get("category") or "culture"),
            "title": title,
            "description": str(inc.get("description") or "").strip(),
            "wikipedia_url": "",
            "casualties": None,
            "key_figures": list(inc.get("key_figures") or []),
        }

        events.append(ev)
        idx[key] = ev
        added += 1

    if added or updated:
        data["events"] = events
        EVENTS_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print("Scandinavia + Baltics merge complete.")
    print(f"- incoming: {len(incoming)}")
    print(f"- added: {added}")
    print(f"- updated(desc): {updated}")
    print(f"- skipped: {skipped}")


if __name__ == "__main__":
    main()

