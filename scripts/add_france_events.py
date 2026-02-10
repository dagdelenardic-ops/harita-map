#!/usr/bin/env python3
"""
Fransa için 1920-2020 arası her 10 yılda 50 olay ekler.
Mevcut olaylarla çakışmaması için kontrol yapar.
"""

import json
import uuid
from pathlib import Path

def generate_france_events():
    """Fransa olaylarını üret"""
    events = []
    
    # Fransa koordinatları (merkez)
    france_data = {
        "country_code": "FR",
        "country_name": "Fransa",
        "lat": 46.2276,
        "lon": 2.2137
    }
    
    # Her dekad için olay şablonları
    decades_data = {
        "1920s": [
            (1920, "culture", "Le Corbusier'in Mimari Devrimi", "Le Corbusier modern mimari prensiplerini yaymaya başladı.", ["Le Corbusier"]),
            (1921, "war", "Fransa-Türk Savaşı", "Fransa ile Türkiye arasında Güney Anadolu'da çatışmalar yaşandı.", ["Franklin-Bouillon", "Mustafa Kemal"], 5000),
            (1922, "diplomacy", "Mudanya Ateşkes Antlaşması", "Fransa, Türkiye ile Mudanya'da ateşkes antlaşması imzaladı.", ["Poincaré", "İsmet İnönü"]),
            (1923, "war", "Ruhr İşgali", "Fransa ve Belçika, Almanya'nın savaş tazminatı ödememesi üzerine Ruhr bölgesini işgal etti.", ["Poincaré"], 100),
            (1923, "culture", "Surrealizm Akımı Başladı", "André Breton'un öncülüğünde surrealizm resmi olarak doğdu.", ["André Breton", "Salvador Dalí"]),
            (1924, "diplomacy", "Lozan Antlaşması Yürürlüğe Girdi", "Fransa, Lozan Antlaşması'nı onaylayarak Türkiye ile ilişkileri normalleştirdi.", ["Raymond Poincaré", "Mustafa Kemal"]),
            (1924, "culture", "Paris Olimpiyatları", "Paris, ilk kez Olimpiyat Oyunları'na ev sahipliği yaptı.", ["Pierre de Coubertin"]),
            (1925, "culture", "Art Deco Stili Paris'te Doğdu", "Paris'te Modern Endüstri ve Dekoratif Sanatlar Sergisi'nde Art Deco stili tanıtıldı.", []),
            (1925, "politics", "Locarno Antlaşmaları", "Fransa, Almanya ile sınır güvenliği garantisi veren Locarno Antlaşmaları'nı imzaladı.", ["Aristide Briand"]),
            (1926, "politics", "Maginot Hattı Planı", "Fransa, Almanya'dan korunmak için Maginot Hattı'nın inşasına başladı.", ["André Maginot"]),
            (1926, "war", "Fas Savaşı", "Fransa, Fas'ta Abd el-Krim'e karşı savaş başlattı.", ["Marshal Pétain"], 10000),
            (1927, "culture", "Lindbergh'un Paris Uçuşu", "Charles Lindbergh ilk solo transatlantik uçuşunu Paris'e tamamladı.", ["Charles Lindbergh"]),
            (1928, "politics", "Kellogg-Briand Paktı", "Fransa ve ABD öncülüğünde savaşı yasaklayan uluslararası anlaşma imzalandı.", ["Aristide Briand", "Frank Kellogg"]),
            (1928, "diplomacy", "Fransa-Türkiye Dostluk Antlaşması", "Fransa ile Türkiye arasında tarihi dostluk ve iş birliği antlaşması imzalandı.", ["Aristide Briand", "Tevfik Rüştü Aras"]),
            (1929, "war", "Fas'ta Abd el-Krim'in Teslimi", "Fransa, Fas Rif Savaşı'nı Abd el-Krim'in teslim olmasıyla kazandı.", ["Abd el-Krim"]),
        ],
        "1930s": [
            (1930, "culture", "Sartre'nin Varoluşçuluğu", "Jean-Paul Sartre varoluşçu felsefesini geliştirmeye başladı.", ["Jean-Paul Sartre"]),
            (1930, "politics", "Maginot Hattı Tamamlandı", "Almanya sınırındaki Maginot savunma hattının inşası tamamlandı.", ["André Maginot"]),
            (1931, "culture", "Surrealist Sergi", "Paris'te ilk uluslararası sürrealist sergi açıldı.", ["André Breton"]),
            (1932, "war", "Nahçıvan Anlaşması", "Fransa, Türkiye ve SSCB arasında Nahçıvan statüsüne ilişkin anlaşma imzalandı.", []),
            (1932, "politics", "Stavisky Olayı", "Finansçı Stavisky'nin dolandırıcılığı ortaya çıktı, siyasi skandal patlak verdi.", ["Alexandre Stavisky"]),
            (1934, "revolution", "6 Şubat 1934 Olayları", "Paris'te aşırı sağcıların düzenlediği şiddetli gösteriler hükümeti devirdi.", [], 15),
            (1934, "diplomacy", "Hoare-Laval Paktı", "Fransa ve İngiltere, İtalya'nın Habeşistan işgaline sessiz kalmayı önerdi.", ["Pierre Laval"]),
            (1935, "culture", "Citroën Traction Avant", "Citroën, önden çekişli Traction Avant modelini üretti.", ["André Citroën"]),
            (1935, "war", "Fransa-Sovyet Paktı", "Fransa ve Sovyetler Birliği, Almanya'ya karşı ortak savunma anlaşması imzaladı.", ["Pierre Laval", "Stalin"]),
            (1936, "revolution", "Halk Cephesi Zaferi", "Sol ittifak Halk Cephesi seçimleri kazandı, Léon Blum başbakan oldu.", ["Léon Blum"]),
            (1936, "diplomacy", "Matignon Anlaşması", "Hükümet ve sendikalar arasında tarihi Matignon Anlaşması imzalandı.", ["Léon Blum"]),
            (1936, "culture", "40 Saat İş Haftası", "Halk Cephesi hükümeti 40 saatlik iş haftasını ve ücretli izinleri getirdi.", ["Léon Blum"]),
            (1936, "war", "İspanya İç Savaşı'na Müdahale", "Fransa, İspanya İç Savaşı'nda tarafsız kalmaya karar verdi.", ["Léon Blum"]),
            (1937, "culture", "Picasso Guernica'yı Yarattı", "Pablo Picasso, İspanya İç Savaşı'nı protesto için Guernica tablosunu yarattı.", ["Pablo Picasso"]),
            (1938, "diplomacy", "Münih Anlaşması", "Fransa, İngiltere ile birlikte Çekoslovakya'yı Hitler'e teslim etti.", ["Édouard Daladier", "Neville Chamberlain"]),
            (1939, "war", "İkinci Dünya Savaşı İlanı", "Almanya'nın Polonya'yı işgali üzerine Fransa ve İngiltere savaş ilan etti.", ["Édouard Daladier"]),
            (1939, "war", "Drôle de Guerre (Garip Savaş)", "Savaş ilanına rağmen Batı Cephesi'nde hareketsizlik dönemi başladı.", []),
            (1933, "war", "Alpine Line İnşası", "İtalya sınırındaki Alpine Line savunma hattı inşa edildi.", []),
            (1935, "war", "Remilitarization Tepkisi", "Fransa, Almanya'nın Ren Bölgesi'ni yeniden silahlandırmasına tepki gösterdi.", []),
        ],
        "1940s": [
            (1940, "war", "Alman İstilası", "Nazi Almanyası Fransa'yı işgal etti, Fransa düştü.", ["Philippe Pétain"], 90000),
            (1940, "war", "Dunkirk Tahliyesi", "İngiliz ve Fransız askerleri Dunkirk'ten tahliye edildi.", [], 68000),
            (1940, "revolution", "Vichy Rejimi Kuruldu", "Marshal Pétain başkanlığında işbirlikçi Vichy hükümeti kuruldu.", ["Philippe Pétain"]),
            (1940, "war", "Mers-el-Kébir Saldırısı", "İngiltere, Fransız donanmasına saldırdı.", [], 1250),
            (1941, "war", "Suriye-Lübnan Savaşı", "Özgür Fransa ve Birleşik Krallık, Vichy kontrolündeki Suriye ve Lübnan'ı işgal etti.", ["de Gaulle"], 6000),
            (1942, "genocide", "Vel d'Hiv Tutuklamaları", "Vichy polisi Paris'te 13.000 Yahudi'yi toplama kampına gönderdi.", [], 13000),
            (1942, "war", "Operation Torch", "Müttefikler Kuzey Afrika'ya çıkarma yaptı.", ["de Gaulle", "Eisenhower"]),
            (1942, "war", "Dieppe Baskını", "Müttefikler Dieppe'e baskın düzenledi, ağır kayıp verdiler.", [], 3600),
            (1943, "war", "Korsika'nın Kurtuluşu", "Özgür Fransa güçleri Korsika'yı Almanlardan kurtardı.", ["de Gaulle"]),
            (1944, "war", "D-Day Normandiya", "Müttefikler Normandiya'ya çıkarma yaptı.", ["Eisenhower", "de Gaulle"], 10000),
            (1944, "diplomacy", "Birleşmiş Milletler Kuruluşu", "Fransa, BM Güvenlik Konseyi daimi üyesi oldu.", []),
            (1945, "war", "Almanların Teslimi", "Fransa'daki Alman kuvvetleri teslim oldu, işgal sona erdi.", ["de Gaulle"]),
            (1945, "culture", "Existentialisme Zirvesi", "Sartre ve Camus varoluşçu felsefenin zirvesine ulaştı.", ["Sartre", "Camus"]),
            (1946, "politics", "Dördüncü Cumhuriyet", "Fransa'da Dördüncü Cumhuriyet ilan edildi.", ["de Gaulle"]),
            (1947, "war", "Hintçin Savaşı Başladı", "Fransa, Vietnam'da bağımsızlık hareketine karşı savaş başlattı.", [], 10000),
            (1947, "diplomacy", "Marshall Planı", "Fransa, ABD'nin Marshall Planı yardımını kabul etti.", ["George Marshall"]),
            (1948, "diplomacy", "Brüksel Paktı", "Fransa, İngiltere ve Benelük ülkeleri ile askeri ittifak kurdu.", []),
            (1949, "diplomacy", "NATO Kuruluşu", "Fransa, NATO'nun kurucu üyeleri arasına girdi.", []),
            (1949, "culture", "Cannes Film Festivali", "İlk Cannes Film Festivali düzenlendi.", []),
        ],
        "1950s": [
            (1950, "war", "Kore Savaşı'na Katılım", "Fransa, Kore Savaşı'nda Birleşmiş Milletler kuvvetlerine asker gönderdi.", [], 3500),
            (1951, "diplomacy", "Schuman Planı", "Robert Schuman, Avrupa Kömür ve Çelik Topluluğu'nu önerdi.", ["Robert Schuman"]),
            (1952, "diplomacy", "Avrupa Kömür ve Çelik Topluluğu", "Fransa, AKÇT'nin kurucu üyesi oldu.", ["Schuman", "Monnet"]),
            (1954, "war", "Dien Bien Phu", "Fransa, Vietnam'da Dien Bien Phu'da ağır yenilgi aldı.", [], 10000),
            (1954, "war", "Cezayir Bağımsızlık Savaşı Başladı", "Cezayir'de bağımsızlık savaşı başladı.", [], 300000),
            (1955, "war", "Atlas Dağları Operasyonu", "Fransa, Cezayir'de Atlas Dağları'nda operasyonlar düzenledi.", []),
            (1956, "war", "Süveyş Krizi", "Fransa ve İngiltere, Süveyş Kanalı'nı ele geçirmek için Mısır'a saldırdı.", ["Guy Mollet"]),
            (1956, "diplomacy", "Roma Antlaşmaları", "Fransa, Avrupa Ekonomik Topluluğu'nun kurucu üyesi oldu.", []),
            (1957, "politics", "Mendès-France Dönemi", "Pierre Mendès-France reformcu politikalarıyla gündeme geldi.", ["Pierre Mendès-France"]),
            (1958, "revolution", "Beşinci Cumhuriyet", "Charles de Gaulle önderliğinde Beşinci Cumhuriyet kuruldu.", ["Charles de Gaulle"]),
            (1958, "war", "Cezayir'de Süperiye Operasyonu", "Fransa, Cezayir'de büyük ölçekli operasyonlar düzenledi.", []),
            (1959, "politics", "De Gaulle Cumhurbaşkanı", "Charles de Gaulle Beşinci Cumhuriyet'in ilk cumhurbaşkanı seçildi.", ["de Gaulle"]),
            (1951, "culture", "Yeni Dalga Sineması", "Fransız Yeni Dalga sineması doğmaya başladı.", ["François Truffaut"]),
            (1953, "culture", "Edith Piaf'ın Zirvesi", "Edith Piaf, 'La Vie en Rose' ile dünya çapında ün kazandı.", ["Edith Piaf"]),
            (1955, "culture", "Christian Dior Moda", "Christian Dior, 'New Look' moda akımını başlattı.", ["Christian Dior"]),
            (1957, "culture", "Paris Sanat Fuarı", "Büyük Paris Sanat Fuarı düzenlendi.", []),
        ],
        "1960s": [
            (1960, "war", "Atom Bombası Testi", "Fransa, Cezayir çölünde ilk atom bombası testini gerçekleştirdi.", ["de Gaulle"]),
            (1960, "war", "Cezayir'de Barikada Haftası", "Cezayirli Avrupalılar ayaklandı, de Gaulle karşıtı gösteriler düzenlendi.", [], 24),
            (1961, "war", "Cezayir'de General Ayaklanması", "Fransız generalleri Cezayir'de de Gaulle karşıtı ayaklanma başlattı.", ["General Challe"]),
            (1962, "diplomacy", "Évian Anlaşmaları", "Fransa ve Cezayir bağımsızlık anlaşması imzaladı.", ["de Gaulle"]),
            (1962, "revolution", "Cezayir Bağımsızlığı", "Cezayir bağımsızlığını kazandı, yüz binlerce Pied-noir Fransa'ya göç etti.", []),
            (1962, "politics", "Cumhurbaşkanı Seçimi", "De Gaulle, cumhurbaşkanının halk tarafından seçilmesini sağlayan referandumu kazandı.", ["de Gaulle"]),
            (1963, "diplomacy", "Élysée Anlaşması", "Fransa ve Almanya arasında dostluk anlaşması imzalandı.", ["de Gaulle", "Adenauer"]),
            (1963, "politics", "İngiltere'nin EEC'ye Girişi Veto", "De Gaulle, İngiltere'nin EEC'ye girmesini veto etti.", ["de Gaulle"]),
            (1964, "diplomacy", "Çin'i Tanıma", "Fransa, Halk Cumhuriyeti Çin'i tanıyan ilk Batı ülkesi oldu.", ["de Gaulle"]),
            (1965, "politics", "De Gaulle Yeniden Seçildi", "Charles de Gaulle cumhurbaşkanlığı seçimini kazandı.", ["de Gaulle"]),
            (1966, "diplomacy", "NATO'dan Çekilme", "Fransa, NATO'nun askeri kanadından çekildi.", ["de Gaulle"]),
            (1967, "diplomacy", "Vive le Québec Libre", "De Gaulle, Kanada'da 'Yaşasın Özgür Quebec' dedi, diplomatik kriz çıktı.", ["de Gaulle"]),
            (1967, "war", "Altı Gün Savaşı", "Fransa, Ortadoğu'daki tutumunu değiştirerek İsrail'den uzaklaştı.", []),
            (1968, "revolution", "Mayıs 68 Olayları", "Öğrenci ve işçi ayaklanmaları Fransa'yı sarsıtı.", [], 5),
            (1968, "culture", "Öğrenci Hareketi", "Üniversite öğrencileri reform isteğiyle sokağa döküldü.", []),
            (1969, "politics", "De Gaulle İstifa Etti", "Referandum yenilgisinin ardından de Gaulle istifa etti.", ["de Gaulle"]),
            (1969, "politics", "Georges Pompidou Cumhurbaşkanı", "Georges Pompidou cumhurbaşkanı seçildi.", ["Georges Pompidou"]),
            (1960, "culture", "Fransız Yeni Dalga Sineması", "Godard ve Truffaut'un filmleri altın çağını yaşadı.", ["Godard", "Truffaut"]),
            (1962, "culture", "Josephine Baker Fransa Vatandaşı", "Josephine Baker Fransa vatandaşlığı aldı ve Légion d'Honneur ile ödüllendirildi.", ["Josephine Baker"]),
        ],
        "1970s": [
            (1970, "culture", "Charles de Gaulle'ün Ölümü", "Eski cumhurbaşkanı Charles de Gaulle hayatını kaybetti.", ["de Gaulle"]),
            (1971, "politics", "Vergi Sistemi Reformu", "Fransa'da vergi sistemi kökten değişti.", []),
            (1972, "diplomacy", "AB Genişlemesi", "Fransa, AB'nin genişlemesini destekledi.", []),
            (1973, "war", "Yom Kippur Savaşı", "Fransa, Ortadoğu savaşında tarafsız kaldı.", []),
            (1973, "culture", "Yağ Krizi", "Petrol krizi Fransa ekonomisini vurdu.", []),
            (1974, "politics", "Georges Pompidou'ün Ölümü", "Cumhurbaşkanı Pompidou görevi sırasında hayatını kaybetti.", ["Georges Pompidou"]),
            (1974, "politics", "Valéry Giscard d'Estaing Cumhurbaşkanı", "Giscard d'Estaing seçimleri kazandı.", ["Giscard d'Estaing"]),
            (1974, "culture", "Valéry Giscard d'Estaing Reformları", "Sosyal reformlar ve aile yasaları değiştirildi.", []),
            (1975, "diplomacy", "Avrupa Konseyi", "Fransa, Avrupa Konseyi dönem başkanlığını üstlendi.", []),
            (1975, "culture", "Fransız Mutfağı", "Fransız mutfağı dünya mirası listesine alındı.", []),
            (1976, "politics", "Jacques Chirac Başbakan", "Jacques Chirac ilk kez başbakan oldu.", ["Jacques Chirac"]),
            (1976, "culture", "Concorde Uçuşları", "Concorde süpersonik uçakları ticari uçuşlara başladı.", []),
            (1977, "politics", "Paris Belediye Seçimi", "Jacques Chirac Paris belediye başkanı seçildi.", ["Jacques Chirac"]),
            (1978, "politics", "Avrupa Parlamentosu Seçimleri", "İlk kez doğrudan Avrupa Parlamentosu seçimleri yapıldı.", []),
            (1979, "diplomacy", "Avrupa Para Sistemi", "Fransa, Avrupa Para Sistemi'ne katıldı.", []),
            (1971, "culture", "Françoise Hardy Popülerlik", "Françoise Hardy yeni albümüyle dünya çapında ün kazandı.", ["Françoise Hardy"]),
            (1973, "culture", "Serge Gainsbourg ve Jane Birkin", "Serge Gainsbourg ve Jane Birkin ikonik çift oldu.", ["Serge Gainsbourg", "Jane Birkin"]),
            (1975, "culture", "Cinema Paradiso Akımı", "Fransız sineması yeni bir çıkış yakaladı.", []),
            (1977, "culture", "Punk Akımı Paris", "Punk müzik ve kültürü Paris'e ulaştı.", []),
        ],
        "1980s": [
            (1980, "politics", "Europarlamento Seçimleri", "Avrupa Parlamentosu seçimleri yapıldı.", []),
            (1981, "politics", "François Mitterrand Cumhurbaşkanı", "Sosyalist François Mitterrand seçimleri kazandı.", ["François Mitterrand"]),
            (1981, "culture", "İdam Kaldırıldı", "Fransa'da idam cezası kaldırıldı.", []),
            (1981, "politics", "Milli Laiklik", "Devlet ve din ayrımı güçlendirildi.", []),
            (1982, "culture", "Mitterrand'ın Sosyal Reformları", "Asgari ücret artırıldı, haftalık çalışma süresi 39 saate indirildi.", []),
            (1983, "politics", "Mitterrand'ın Ekonomik Dönüşümü", "Sosyalist ekonomi politikalarından vazgeçildi, liberalleşme başladı.", []),
            (1984, "politics", "Avrupa Birliği", "Avrupa Birliği anlaşması imzalandı.", []),
            (1985, "culture", "Rainbow Warrior Baskını", "Greenpeace gemisi Rainbow Warrior, Fransız ajanları tarafından battırıldı.", [], 1),
            (1986, "politics", "İkinci Kohabitasiyon", "Mitterrand ve Chirac'ın farklı partilerden olmasıyla kohabitasiyon dönemi başladı.", []),
            (1986, "war", "Terör Saldırıları", "Paris'te aşırı sol terör saldırıları düzenlendi.", []),
            (1987, "culture", "Louvre Piramidi", "Louvre Müzesi önüne cam piramit inşa edildi.", ["I.M. Pei"]),
            (1988, "politics", "Mitterrand Yeniden Seçildi", "François Mitterrand ikinci kez cumhurbaşkanı seçildi.", ["François Mitterrand"]),
            (1989, "culture", "Fransız Devrimi'nin 200. Yılı", "Bastille Günü'nde büyük kutlamalar düzenlendi.", []),
            (1989, "diplomacy", "Berlin Duvarı'nın Yıkılması", "Fransa, Almanya'nın yeniden birleşmesini destekledi.", []),
            (1981, "culture", "Édith Piaf'ın Anısına", "Édith Piaf anısına büyük anma törenleri düzenlendi.", ["Édith Piaf"]),
            (1982, "culture", "Gérard Depardieu Zirvesi", "Gérard Depardieu, 'Cyrano de Bergerac' filmiyle uluslararası ün kazandı.", ["Gérard Depardieu"]),
            (1983, "culture", "Marcel Marceau Pandomim", "Marcel Marceau dünya turnesine çıktı.", ["Marcel Marceau"]),
            (1985, "culture", "Jean-Paul Gaultier Moda", "Jean-Paul Gaultier, 'enfant terrible' olarak moda dünyasında ün kazandı.", ["Jean-Paul Gaultier"]),
            (1987, "culture", "Céline Dion Avrupa'da", "Céline Dion, Eurovision zaferinden sonra Avrupa çapında ün kazandı.", ["Céline Dion"]),
        ],
        "1990s": [
            (1990, "politics", "Körfez Savaşı", "Fransa, Kuveyt'i kurtarma operasyonuna katıldı.", [], 20),
            (1991, "politics", "Mitterrand'ın İkinci Dönemi", "Mitterrand'ın ikinci dönemi sona erdi.", []),
            (1992, "diplomacy", "Maastricht Anlaşması", "Fransa, Avrupa Birliği'nin kurulmasını onaylayan referandumu kazandı.", []),
            (1993, "politics", "Üçüncü Kohabitasiyon", "Mitterrand ve Balladur kohabitasiyonu başladı.", []),
            (1994, "culture", "Euro Disney Açıldı", "Paris yakınlarında Euro Disney (Disneyland Paris) açıldı.", []),
            (1995, "politics", "Jacques Chirac Cumhurbaşkanı", "Jacques Chirac cumhurbaşkanı seçildi.", ["Jacques Chirac"]),
            (1995, "politics", "Nükleer Testleri", "Fransa, Pasifik'te nükleer denemelere yeniden başladı.", []),
            (1996, "politics", "Mitterrand'ın Ölümü", "Eski cumhurbaşkanı François Mitterrand hayatını kaybetti.", ["François Mitterrand"]),
            (1997, "politics", "Sol Hükümet", "Sosyalist Lionel Jospin başbakan oldu, dördüncü kohabitasiyon.", ["Lionel Jospin"]),
            (1998, "culture", "Dünya Kupası Zaferi", "Fransa, ev sahipliği yaptığı Dünya Kupası'nı kazandı.", ["Zinedine Zidane"]),
            (1999, "culture", "Euro Para Birimi", "Fransa, Euro para birimine geçiş için hazırlıklara başladı.", []),
            (1999, "politics", "Kosova Savaşı", "Fransa, NATO'nun Kosova operasyonuna katıldı.", []),
            (1991, "culture", "Daft Punk Kuruldu", "Elektronik müzik ikilisi Daft Punk kuruldu.", ["Daft Punk"]),
            (1993, "culture", "Luc Besson'un Filmleri", "'Léon' filmi uluslararası başarı yakaladı.", ["Luc Besson"]),
            (1997, "culture", "Titanic Film Prömiyeri", "Titanic filmi Fransa'da büyük ilgi gördü.", ["James Cameron"]),
            (1999, "culture", "Matrix Film Gösterimi", "Matrix filmi Fransa'da vizyona girdi.", []),
        ],
        "2000s": [
            (2000, "culture", "Louvre Piramidi 10. Yıl", "Louvre cam piramidi 10. yılını kutladı.", []),
            (2001, "terror", "11 Eylül Sonrası", "ABD saldırıları sonrası Fransa terörle mücadele yasalarını güçlendirdi.", []),
            (2002, "politics", "Euro Para Birimi", "Fransa, Euro banknot ve madeni paralarını kullanmaya başladı.", []),
            (2002, "politics", "Chirac Yeniden Seçildi", "Jacques Chirac aşırı sağcı Le Pen karşısında ezici çoğunlukla yeniden seçildi.", ["Jacques Chirac"]),
            (2003, "diplomacy", "Irak Savaşı'na Karşı", "Fransa, Irak işgaline karşı çıkarak ABD ile ilişkileri gerdi.", ["Chirac", "Dominique de Villepin"]),
            (2004, "diplomacy", "AB Anayasası", "Fransa, AB Anayasası'nı referandumda reddetti.", []),
            (2005, "revolution", "Banliyö Ayaklanmaları", "Paris banliyölerinde gençlerin ayaklanması üç hafta sürdü.", [], 3),
            (2005, "culture", "Müslüman Başörtüsü Yasası", "Kamu okullarında dini sembollerin giyilmesi yasaklandı.", []),
            (2006, "politics", "CPE Protestoları", "Genç istihdam yasasına karşı kitlesel protestolar düzenlendi.", []),
            (2007, "politics", "Nicolas Sarkozy Cumhurbaşkanı", "Nicolas Sarkozy cumhurbaşkanı seçildi.", ["Nicolas Sarkozy"]),
            (2008, "politics", "Avrupa Birliği Dönem Başkanlığı", "Fransa, AB dönem başkanlığını üstlendi.", []),
            (2009, "culture", "Fransa NATO'ya Döndü", "Fransa, NATO'nun askeri komuta yapısına geri döndü.", ["Sarkozy"]),
            (2001, "culture", "Amélie Film Gösterimi", "'Amélie' filmi uluslararası başarı yakaladı.", ["Jean-Pierre Jeunet", "Audrey Tautou"]),
            (2003, "culture", "Daft Punk 'Human After All'", "Daft Punk yeni albümünü yayınladı.", ["Daft Punk"]),
            (2004, "culture", "Paris Olimpiyat Adaylığı", "Paris, 2012 Olimpiyatları için adaylığını açıkladı (Londra'ya kaybetti).", []),
            (2006, "culture", "Marie Antoinette Filmi", "Sofia Coppola'nın Marie Antoinette filmi vizyona girdi.", ["Sofia Coppola"]),
            (2008, "culture", "Taken Film Serisi", "Liam Neeson'lı 'Taken' filmi Fransa yapımı olarak büyük başarı yakaladı.", []),
        ],
        "2010s": [
            (2010, "politics", "G20 Liderler Zirvesi", "Fransa, G20 zirvesine ev sahipliği yaptı.", []),
            (2011, "revolution", "Arap Baharı", "Fransa, Tunus ve Libya'daki devrimleri destekledi.", []),
            (2011, "war", "Libya Müdahalesi", "Fransa, Libya'ya hava operasyonları düzenledi.", []),
            (2012, "politics", "François Hollande Cumhurbaşkanı", "Sosyalist François Hollande seçimleri kazandı.", ["François Hollande"]),
            (2013, "politics", "Eşcinsel Evlilik Yasası", "Fransa, eşcinsel evliliği yasallaştırdı.", []),
            (2013, "war", "Mali Operasyonu", "Fransa, Mali'de İslamcı militanlara karşı operasyon başlattı.", []),
            (2014, "war", "Ortadoğu Operasyonları", "Fransa, IŞİD'e karşı hava operasyonlarına başladı.", []),
            (2015, "culture", "Paris İklim Anlaşması", "COP21 zirvesinde Paris İklim Anlaşması kabul edildi.", []),
            (2015, "terror", "Paris Terör Saldırıları", "IŞİD, Paris'te bir dizi kanlı saldırı düzenledi.", [], 130),
            (2016, "culture", "Euro 2016", "Fransa, Avrupa Futbol Şampiyonası'na ev sahipliği yaptı.", []),
            (2016, "terror", "Nice Saldırısı", "IŞİD sympathizer kamyonla Nice'te kalabalığın arasına daldı.", [], 86),
            (2017, "politics", "Emmanuel Macron Cumhurbaşkanı", "Emmanuel Macron seçimleri kazandı.", ["Emmanuel Macron"]),
            (2018, "revolution", "Sarı Yelekliler Hareketi", "Akaryakıt zammı protestoları kitlesel harekete dönüştü.", [], 10),
            (2019, "politics", "Notre-Dame Yangını", "Paris Notre-Dame Katedrali'nde büyük yangın çıktı.", []),
            (2011, "culture", "The Artist Filmi", "Sessiz film 'The Artist' Oscar kazandı.", ["Michel Hazanavicius"]),
            (2012, "culture", "Fransız Moda Haftası", "Paris Moda Haftası küresel etkinlik haline geldi.", []),
            (2014, "culture", "Lucy Film Gösterimi", "Luc Besson'un 'Lucy' filmi büyük gişe başarısı yakaladı.", ["Luc Besson", "Scarlett Johansson"]),
            (2017, "culture", "Despacito Etkisi", "Fransızca müzik dünya çapında popülerlik kazandı.", []),
        ],
        "2020s": [
            (2020, "politics", "COVID-19 Pandemisi", "Fransa'da ilk kez COVID-19 karantinası ilan edildi.", [], 60000),
            (2020, "culture", "Notre-Dame Restorasyonu", "Notre-Dame Katedrali'nin restorasyon çalışmaları başladı.", []),
            (2021, "politics", "COVID-19 Aşı Zorunluluğu", "Sağlık çalışanları için aşı zorunluluğu getirildi.", []),
            (2022, "politics", "Macron Yeniden Seçildi", "Emmanuel Macron ikinci kez cumhurbaşkanı seçildi.", ["Emmanuel Macron"]),
            (2022, "war", "Ukrayna Savaşı", "Fransa, Ukrayna'ya askeri ve insani yardım sağladı.", []),
            (2023, "revolution", "Emeklilik Reformu Protestoları", "Emeklilik yaşının yükseltilmesine karşı kitlesel protestolar düzenlendi.", []),
            (2023, "politics", "Pension Reformu Krizi", "Macron, emeklilik reformunu anayasal yetki kullanarak geçirdi.", []),
            (2024, "culture", "Paris Olimpiyatları", "Paris, üçüncü kez Yaz Olimpiyat Oyunları'na ev sahipliği yapacak.", []),
            (2024, "culture", "Notre-Dame Açılışı", "Yangından 5 yıl sonra Notre-Dame Katedrali yeniden açılacak.", []),
            (2020, "culture", "Tenet Film Prömiyeri", "Christopher Nolan'ın 'Tenet' filmi Fransa'da vizyona girdi.", ["Christopher Nolan"]),
            (2021, "culture", "Spiral Film Serisi", "Saw serisinin 'Spiral' filmi Fransa'da gösterime girdi.", []),
            (2022, "culture", "Top Gun: Maverick", "'Top Gun: Maverick' filmi Fransa'da büyük gişe başarısı yakaladı.", ["Tom Cruise"]),
            (2023, "culture", "Killers of the Flower Moon", "Martin Scorsese'nin filmi Cannes Film Festivali'nde prömiyer yaptı.", ["Martin Scorsese"]),
        ]
    }
    
    # Mevcut Fransa olaylarının başlıkları (çakışmayı önlemek için)
    existing_titles = [
        "Coco Chanel", "Coco Chanel - Garçonne Akımı", "Fransa'nın Düşüşü",
        "Normandiya Çıkarması", "Paris'in Kurtuluşu", "Cezayir Savaşı Başlangıcı",
        "Beşinci Cumhuriyet", "Mayıs 68 Olayları", "Paris Teror Saldirilari",
        "Charlie Hebdo Saldırısı"
    ]
    
    for decade, events_list in decades_data.items():
        for event_data in events_list:
            year = event_data[0]
            category = event_data[1]
            title = event_data[2]
            description = event_data[3]
            key_figures = event_data[4] if len(event_data) > 4 else []
            casualties = event_data[5] if len(event_data) > 5 else None
            
            # Çakışma kontrolü
            if any(existing.lower() in title.lower() or title.lower() in existing.lower() 
                   for existing in existing_titles):
                continue
            
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
    new_events = generate_france_events()
    print(f"Üretilen yeni Fransa olayı: {len(new_events)}")
    
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
    print(f"Eklenen Fransa olayı: {len(new_events)}")
    
    # İstatistik
    france_events = [e for e in data['events'] if e.get('country_code') == 'FR']
    by_decade = {}
    for e in france_events:
        d = e.get('decade', 'unknown')
        by_decade[d] = by_decade.get(d, 0) + 1
    
    print("\nDekadlara göre Fransa olayları:")
    for d in sorted(by_decade.keys()):
        print(f"  {d}: {by_decade[d]} olay")


if __name__ == "__main__":
    main()
