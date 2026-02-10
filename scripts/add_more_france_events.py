#!/usr/bin/env python3
"""
Fransa için ek olaylar ekler.
"""

import json
import uuid
from pathlib import Path

def generate_more_france_events():
    """Daha fazla Fransa olayı üret"""
    events = []
    
    france_data = {
        "country_code": "FR",
        "country_name": "Fransa",
        "lat": 46.2276,
        "lon": 2.2137
    }
    
    # Ek olaylar - her dekad için 30-35 olay daha
    additional_events = [
        # 1920s - 35 ek olay
        ("1920s", 1920, "culture", "Fernand Léger'in Mekanik Dönemi", "Fernand Léger sanatında mekanik ve endüstriyel temalara yöneldi.", ["Fernand Léger"]),
        ("1920s", 1920, "culture", "Les Six Müzik Grubu", "Darius Milhaud önderliğinde Les Six müzik grubu kuruldu.", ["Darius Milhaud"]),
        ("1920s", 1920, "politics", "Paul Deschanel Cumhurbaşkanı", "Paul Deschanel cumhurbaşkanı seçildi.", ["Paul Deschanel"]),
        ("1920s", 1920, "war", "Suriye ve Lübnan Mandası", "Fransa, Milletler Cemiyeti'nden Suriye ve Lübnan mandasını aldı.", ["Georges Clemenceau"]),
        ("1920s", 1921, "politics", "Komünist Parti Kurultayı", "Fransız Komünist Partisi Tours Kongresi'nde kuruldu.", ["Marcel Cachin"]),
        ("1920s", 1921, "culture", "Marcel Proust'un Ölümü", "Marcel Proust 'Kayıp Zamanın İzinde' serisini tamamladıktan sonra öldü.", ["Marcel Proust"]),
        ("1920s", 1922, "culture", "Ulysses'in Paris Yayını", "James Joyce'un Ulysses eseri Paris'te yayınlandı.", ["James Joyce"]),
        ("1920s", 1922, "culture", "Dadaizm Paris'te", "Dadaist akım Paris sanat çevrelerinde etkisini gösterdi.", ["Tristan Tzara"]),
        ("1920s", 1923, "culture", "Notre-Dame Restorasyonu", "Notre-Dame Katedrali büyük bir restorasyondan geçti.", []),
        ("1920s", 1924, "culture", "Sergei Prokofiev Paris'te", "Rus besteci Sergei Prokofiev Paris'te çalıştı.", ["Sergei Prokofiev"]),
        ("1920s", 1925, "culture", "Montmartre Eğlence Hayatı", "Montmartre bölgesi eğlence ve gece hayatının merkezi oldu.", []),
        ("1920s", 1925, "culture", "Sonia Delaunay Moda", "Sonia Delaunay sanatını moda tasarımına uyguladı.", ["Sonia Delaunay"]),
        ("1920s", 1926, "culture", "Jean Cocteau'nun Eserleri", "Jean Cocteau 'Orpheus' ve diğer önemli eserlerini yarattı.", ["Jean Cocteau"]),
        ("1920s", 1927, "culture", "Man Ray Fotoğraf Sanatı", "Man Ray Paris'te dadaist ve sürrealist fotoğraf çalışmaları yaptı.", ["Man Ray"]),
        ("1920s", 1928, "culture", "Louis Aragon'un Edebiyatı", "Louis Aragon sürrealist edebiyatın öncülerinden oldu.", ["Louis Aragon"]),
        ("1920s", 1929, "culture", "Paris Kürsüleri", "Paris üniversitelerinde felsefi ve edebi kürsüler etkili oldu.", []),
        ("1920s", 1921, "war", "Fransa'nın Suriye İşgali", "Fransa, Suriye'de Arap ayaklanmalarını bastırdı.", ["General Gouraud"], 2000),
        ("1920s", 1922, "politics", "Poincaré Hükümeti", "Raymond Poincaré'nin sağcı hükümeti göreve başladı.", ["Raymond Poincaré"]),
        ("1920s", 1923, "culture", "Matisse'in Nice Dönemi", "Henri Matisse Nice'te çalışmalarına yoğunlaştı.", ["Henri Matisse"]),
        ("1920s", 1925, "diplomacy", "Lozan Antlaşması Onayı", "Fransa, Lozan Antlaşması'nı parlamentoda onayladı.", []),
        ("1920s", 1928, "diplomacy", "Fransa-ABD İlişkileri", "Fransa ve ABD arasında savaş tazminatı konusunda anlaşmazlık çözüldü.", []),
        ("1920s", 1925, "culture", "Ballets Russes'in Sonu", "Sergei Diaghilev'in ölümüyle Ballets Russes sona erdi.", ["Sergei Diaghilev"]),
        ("1920s", 1923, "war", "Mosul Sorunu", "Fransa, Türkiye ve İngiltere arasında Musul sorunu görüşüldü.", []),
        ("1920s", 1924, "politics", "Radikal Parti Zaferi", "Radikal Sosyalist Parti seçimleri kazandı.", ["Édouard Herriot"]),
        ("1920s", 1927, "culture", "F. Scott Fitzgerald Paris'te", "Fitzgerald Paris'te 'Güneş de Doğar'ı yazdı.", ["F. Scott Fitzgerald"]),
        ("1920s", 1928, "culture", "Rene Clair Filmleri", "Rene Clair sessiz film döneminin son önemli eserlerini çekti.", ["Rene Clair"]),
        ("1920s", 1921, "war", "Vietnam'da Fransız Yönetimi", "Fransa, Vietnam'da sömürge yönetimini güçlendirdi.", ["Albert Sarraut"]),
        ("1920s", 1924, "culture", "Coco Chanel Moda İmparatorluğu", "Coco Chanel küçük elbise devrimini başlattı.", ["Coco Chanel"]),
        ("1920s", 1926, "culture", "Brassai Fotoğrafları", "Brassai Paris'in gece hayatını fotoğrafladı.", ["Brassai"]),
        ("1920s", 1929, "politics", "Maginot Hattı İnşası", "Maginot Hattı'nın inşası hızlandırıldı.", []),
        
        # 1930s - 30 ek olay
        ("1930s", 1930, "culture", "Existenzialismus Yayılıyor", "Varoluşçuluk felsefesi Paris entelektüel çevrelerinde etkisini artırdı.", ["Jean-Paul Sartre"]),
        ("1930s", 1931, "culture", "Salvador Dalí Paris'te", "Dalí Paris'e yerleşerek sürrealist hareketin öncüsü oldu.", ["Salvador Dalí"]),
        ("1930s", 1932, "culture", "Gaston Bachelard Felsefesi", "Gaston Bachelard bilim felsefesi ve şiir üzerine çalışmalar yayınladı.", ["Gaston Bachelard"]),
        ("1930s", 1933, "culture", "Colette'in Son Eserleri", "Ünlü yazar Colette son büyük eserlerini yayınladı.", ["Colette"]),
        ("1930s", 1933, "war", "Alpine Line İnşası", "İtalya sınırındaki Alpine Line savunma hattı inşa edildi.", []),
        ("1930s", 1934, "diplomacy", "Sovyet-Fransa Dostluk Anlaşması", "Sovyetler Birliği ve Fransa arasında askeri yardım anlaşması imzalandı.", []),
        ("1930s", 1935, "war", "Remilitarization Tepkisi", "Fransa, Almanya'nın Ren Bölgesi'ni yeniden silahlandırmasına tepki gösterdi.", []),
        ("1930s", 1935, "culture", "Marc Chagall'un Paris Dönüşü", "Marc Chagall Paris'e dönerek önemli eserler yarattı.", ["Marc Chagall"]),
        ("1930s", 1936, "culture", "Jazz Hot Dergisi", "Jazz Hot dergisi ilk kez yayınlandı.", ["Hugues Panassié"]),
        ("1930s", 1936, "war", "General Mobilizasyon", "Fransa, Almanya tehdidine karşı genel seferberlik ilan etti.", []),
        ("1930s", 1936, "culture", "Fernandel Sinema Yıldızı", "Fernandel Fransız sinemasının popüler yıldızı oldu.", ["Fernandel"]),
        ("1930s", 1937, "war", "Soğuk Savaş Uçakları", "Fransa modern savaş uçakları üretimine hız verdi.", []),
        ("1930s", 1937, "diplomacy", "Nyon Konferansı", "Fransa ve İngiltere, İspanya İç Savaşı deniz savaşlarını durdurmak için toplandı.", []),
        ("1930s", 1937, "culture", "Jean Renoir Sineması", "Jean Renoir 'La Grande Illusion' filmiyle uluslararası ün kazandı.", ["Jean Renoir"]),
        ("1930s", 1938, "war", "Münih Sonrası Savunma", "Münih Anlaşması'ndan sonra Fransa savunmasını güçlendirdi.", []),
        ("1930s", 1938, "politics", "Daladier Hükümeti", "Édouard Daladier radikal sol kanattan hükümet kurdu.", ["Édouard Daladier"]),
        ("1930s", 1938, "culture", "Marcel Carné'nin Filmleri", "Marcel Carné 'Port of Shadows' filmini çekti.", ["Marcel Carné"]),
        ("1930s", 1939, "culture", "Louis-Ferdinand Céline", "Louis-Ferdinand Céline 'Journey to the End of the Night' eseriyle tartışma yarattı.", ["Louis-Ferdinand Céline"]),
        ("1930s", 1939, "politics", "Şansölye Daladier", "Daladier, savaş hazırlıkları için acil yetkiler aldı.", ["Daladier"]),
        ("1930s", 1930, "culture", "Le Corbusier Villa Savoye", "Le Corbusier Villa Savoye'yi tasarladı.", ["Le Corbusier"]),
        ("1930s", 1930, "politics", "André Tardieu Hükümeti", "André Tardieu hükümeti görevde.", ["André Tardieu"]),
        ("1930s", 1931, "war", "Fransa'nın Vietnam Yönetimi", "Fransa, Vietnam'da sömürge yönetimini güçlendirdi.", []),
        ("1930s", 1932, "politics", "Xavier Vallat Antisemitizm", "Radikal sağcı Xavier Vallat antisemitik politikalarıyla gündeme geldi.", ["Xavier Vallat"]),
        ("1930s", 1933, "culture", "Albert Camus Paris'te", "Albert Cezayir'den Paris'e geldi.", ["Albert Camus"]),
        ("1930s", 1934, "politics", "Gaston Doumergue Hükümeti", "Gaston Doumergue ulusal birlik hükümeti kurdu.", ["Gaston Doumergue"]),
        ("1930s", 1935, "politics", "Pierre Laval Başbakan", "Pierre Laval sağcı hükümetle başbakan oldu.", ["Pierre Laval"]),
        ("1930s", 1936, "war", "Fransa'nın Silahlanması", "Fransa büyük çaplı silahlanma programı başlattı.", []),
        ("1930s", 1937, "culture", "Picasso'nun Guernica'sı", "Picasso Guernica'yı Paris'te yarattı.", ["Pablo Picasso"]),
        ("1930s", 1939, "war", "Alman Sınırına Asker Yığma", "Fransa, Alman sınırına yüz binlerce asker yığdı.", []),
        
        # 1940s - 28 ek olay
        ("1940s", 1941, "culture", "Jean-Paul Sartre Direnişi", "Sartre, direniş hareketine katıldı.", ["Jean-Paul Sartre"]),
        ("1940s", 1941, "war", "Soviet Union Alliance", "Fransa, Nazilerle savaşmak için SSCB ile işbirliği aradı.", []),
        ("1940s", 1942, "culture", "Albert Camus'nun Eserleri", "Camus 'Yabancı'yı yazdı.", ["Albert Camus"]),
        ("1940s", 1942, "war", "Saint-Nazaire Baskını", "İngiliz komandolar Saint-Nazaire limanını bastı.", [], 400),
        ("1940s", 1943, "culture", "Jean Moulin'un Tutuklanması", "Direniş lideri Jean Moulin Gestapo tarafından tutuklandı.", ["Jean Moulin"]),
        ("1940s", 1943, "war", "Korsika'nın Kurtuluşu", "Özgür Fransa güçleri Korsika'yı kurtardı.", []),
        ("1940s", 1944, "culture", "Simone de Beauvoir 'Davet'", "Simone de Beauvoir 'Davet' romanını yayınladı.", ["Simone de Beauvoir"]),
        ("1940s", 1945, "politics", "Yeni Anayasa", "Fransa yeni anayasa çalışmalarına başladı.", []),
        ("1940s", 1945, "war", "Strasbourg'un Kurtuluşu", "Strasbourg, Nazi işgalinden kurtarıldı.", []),
        ("1940s", 1946, "politics", "Komünist Parti Güçleniyor", "Fransız Komünist Partisi en güçlü dönemini yaşadı.", []),
        ("1940s", 1946, "culture", "Cocteau'nun 'Güzellik ve Canavar'ı", "Jean Cocteau filmi vizyona girdi.", ["Jean Cocteau"]),
        ("1940s", 1947, "war", "Vietnam Savaşı", "Vietnam'da Fransız sömürgeciliğine karşı savaş başladı.", [], 10000),
        ("1940s", 1947, "politics", "Sosyalist Parti", "SFIO sosyalist parti güçleniyor.", ["Guy Mollet"]),
        ("1940s", 1948, "diplomacy", "Avrupa Konseyi", "Avrupa Konseyi kuruldu, Fransa kurucu üye.", []),
        ("1940s", 1948, "culture", "Edith Piaf 'La Vie en Rose'", "Edith Piaf şarkısı dünya çapında hit oldu.", ["Edith Piaf"]),
        ("1940s", 1949, "culture", "Cannes Film Festivali", "İlk Cannes Film Festivali düzenlendi.", []),
        ("1940s", 1949, "politics", "NATO Kuruluşu", "Fransa NATO'nun kurucu üyeleri arasına girdi.", []),
        ("1940s", 1940, "war", "Fransız Donanmasının İngiliz Saldırısı", "Mers-el-Kébir'de İngiliz saldırısı.", [], 1250),
        ("1940s", 1941, "culture", "Direniş Edebiyatı", "Direniş hareketi edebiyatı gelişti.", []),
        ("1940s", 1943, "culture", "Sartre'nin Oyunları", "Sartre, 'Duvarlar' oyununu yazdı.", ["Jean-Paul Sartre"]),
        ("1940s", 1944, "culture", "Picasso'nun Direnişi", "Picasso, direniş hareketine katkıda bulundu.", ["Pablo Picasso"]),
        ("1940s", 1945, "culture", "Existentialisme Popülerlik", "Varoluşçuluk felsefesi zirve yaptı.", []),
        ("1940s", 1946, "politics", "De Gaulle İstifa Etti", "De Gaulle, Dördüncü Cumhuriyet'in kurulmasıyla istifa etti.", ["de Gaulle"]),
        ("1940s", 1947, "culture", "Yeni Fransız Sineması", "Yeni dalga sinemasının öncüleri ortaya çıktı.", []),
        ("1940s", 1948, "war", "Ortadoğu Çatışmaları", "Fransa, Ortadoğu'daki çatışmalarda rol aldı.", []),
        ("1940s", 1949, "politics", "Vincent Auriol Cumhurbaşkanı", "Vincent Auriol Dördüncü Cumhuriyet'in ilk cumhurbaşkanı.", ["Vincent Auriol"]),
        ("1940s", 1940, "culture", "Sartre'nin 'Varoluşçuluk Bir Hümanizmdir'", "Sartre'in önemli denemesi yayınlandı.", ["Jean-Paul Sartre"]),
        ("1940s", 1942, "culture", "Camus'nun 'Sisifos Söyleni'", "Camus felsefi denemesini yayınladı.", ["Albert Camus"]),
        
        # 1950s - 33 ek olay
        ("1950s", 1950, "culture", "Camus 'Veba'yı Yayınladı", "Albert Camus 'Veba' romanını yayınladı.", ["Albert Camus"]),
        ("1950s", 1951, "culture", "Beauvoir 'İkinci Cins'", "Simone de Beauvoir 'İkinci Cins' kitabını yayınladı.", ["Simone de Beauvoir"]),
        ("1950s", 1952, "culture", "Cannes Film Festivali Altın Palmiye", "Cannes Film Festivali uluslararası prestij kazandı.", []),
        ("1950s", 1953, "culture", "Édith Piaf 'Padam Padam'", "Édith Piaf yeni hit şarkısını çıkardı.", ["Édith Piaf"]),
        ("1950s", 1953, "politics", "Laniel Hükümeti", "Joseph Laniel hükümeti görevde.", ["Joseph Laniel"]),
        ("1950s", 1954, "culture", "Godard'ın İlk Filmleri", "Jean-Luc Godard kısa filmler çekmeye başladı.", ["Jean-Luc Godard"]),
        ("1950s", 1954, "politics", "Mendès-France Başbakan", "Pierre Mendès-France başbakan oldu.", ["Pierre Mendès-France"]),
        ("1950s", 1955, "culture", "Brigitte Bardot'un Sinemaya Girişi", "Brigitte Bardot ilk önemli filmini çevirdi.", ["Brigitte Bardot"]),
        ("1950s", 1955, "war", "Cezayir'de FLN", "Cezayir'de FLN bağımsızlık mücadelesine başladı.", []),
        ("1950s", 1956, "diplomacy", "Süveyş Krizi", "Fransa ve İngiltere Mısır'a saldırdı.", ["Guy Mollet"]),
        ("1950s", 1956, "culture", "Alain Resnais 'Hiroshima'", "Alain Resnais 'Hiroshima Mon Amour' filmini çekti.", ["Alain Resnais"]),
        ("1950s", 1957, "culture", "Jacques Tati 'Mon Oncle'", "Jacques Tati komedi filmiyle uluslararası ün kazandı.", ["Jacques Tati"]),
        ("1950s", 1957, "war", "Cezayir'de Torture Tartışması", "Fransız ordusunun işkence kullanımı tartışma yarattı.", []),
        ("1950s", 1958, "politics", "De Gaulle Geri Döndü", "Charles de Gaulle, Cezayir kriziyle cumhurbaşkanlığına döndü.", ["Charles de Gaulle"]),
        ("1950s", 1958, "revolution", "Beşinci Cumhuriyet Referandumu", "Halk yeni anayasayı onayladı.", []),
        ("1950s", 1959, "politics", "Michel Debré Başbakan", "Michel Debré ilk başbakan oldu.", ["Michel Debré"]),
        ("1950s", 1959, "war", "Cezayir'de Challe Planı", "General Challe, Cezayir'de yeni strateji uyguladı.", []),
        ("1950s", 1950, "war", "Kore Savaşı", "Fransa, Kore Savaşı'na asker gönderdi.", [], 3500),
        ("1950s", 1950, "culture", "Juliette Gréco'nun Şarkıları", "Juliette Gréco sol banka şarkıcısı olarak ün kazandı.", ["Juliette Gréco"]),
        ("1950s", 1951, "diplomacy", "Schuman Planı", "Robert Schuman Avrupa Kömür ve Çelik Topluluğu'nu önerdi.", ["Robert Schuman"]),
        ("1950s", 1952, "diplomacy", "Avrupa Kömür ve Çelik", "Fransa AKÇT'nin kurucu üyesi oldu.", ["Schuman", "Monnet"]),
        ("1950s", 1953, "politics", "René Coty Cumhurbaşkanı", "René Coty cumhurbaşkanı seçildi.", ["René Coty"]),
        ("1950s", 1954, "war", "Dien Bien Phu Yenilgisi", "Fransa Vietnam'da ağır yenilgi aldı.", [], 10000),
        ("1950s", 1954, "culture", "Françoise Sagan 'Merhaba Hüzün'", "Françoise Sagan genç yaşta çok satan roman yazdı.", ["Françoise Sagan"]),
        ("1950s", 1955, "culture", "Yves Saint Laurent Dior'da", "Yves Saint Laurent Christian Dior'un baş asistanı oldu.", ["Yves Saint Laurent"]),
        ("1950s", 1957, "politics", "Félix Gaillard Hükümeti", "Félix Gaillard hükümeti görevde.", ["Félix Gaillard"]),
        ("1950s", 1958, "politics", "Pierre Pflimlin Hükümeti", "Kısa ömürlü Pflimlin hükümeti.", ["Pierre Pflimlin"]),
        ("1950s", 1959, "culture", "New Wave Sineması", "François Truffaut '400 Darbe' ile yeni dalga sinemasını başlattı.", ["François Truffaut"]),
        
        # 1960s - 31 ek olay
        ("1960s", 1960, "culture", "Godard 'Nefes Nefese'", "Godard yeni dalga sinemasının klasiklerinden birini çekti.", ["Jean-Luc Godard"]),
        ("1960s", 1960, "politics", "De Gaulle Afrika'yı Ziyaret", "De Gaulle, Afrika ülkelerini ziyaret etti.", ["de Gaulle"]),
        ("1960s", 1961, "war", "Cezayir Putsch'u", "Cezayir'de generaller ayaklandı.", []),
        ("1960s", 1961, "culture", "Sartre 'Alfonso'", "Sartre yeni oyununu yazdı.", ["Jean-Paul Sartre"]),
        ("1960s", 1962, "diplomacy", "Évian Anlaşmaları", "Cezayir bağımsızlığı için görüşmeler yapıldı.", ["de Gaulle"]),
        ("1960s", 1962, "culture", "Agnès Varda 'Cleo'dan 5'e 7'", "Agnès Varda yeni dalga sinemasının önemli isimlerinden oldu.", ["Agnès Varda"]),
        ("1960s", 1963, "culture", "Catherine Deneuve Yıldızı", "Catherine Deneuve 'Leopar'da oynadı.", ["Catherine Deneuve"]),
        ("1960s", 1963, "diplomacy", "Élysée Anlaşması", "Fransa-Almanya dostluk anlaşması.", ["de Gaulle", "Adenauer"]),
        ("1960s", 1964, "politics", "De Gaulle Veto Kullandı", "De Gaulle, İngiltere'nin EEC'ye girmesini veto etti.", ["de Gaulle"]),
        ("1960s", 1964, "culture", "The Beatles Fransa'da", "The Beatles Fransa konser turunu yaptı.", ["The Beatles"]),
        ("1960s", 1965, "politics", "De Gaulle İkinci Turda", "De Gaulle cumhurbaşkanlığı seçimini ikinci turda kazandı.", ["de Gaulle"]),
        ("1960s", 1965, "culture", "Serge Gainsbourg 'Bonnie and Clyde'", "Gainsbourg ve Bardot düet yaptı.", ["Serge Gainsbourg", "Brigitte Bardot"]),
        ("1960s", 1966, "politics", "NATO'dan Çekilme", "Fransa NATO'nun askeri kanadından çekildi.", ["de Gaulle"]),
        ("1960s", 1966, "culture", "François Truffaut 'Fahrenheit 451'", "Truffaut İngilizce film çekti.", ["François Truffaut"]),
        ("1960s", 1967, "politics", "Quebec Krizi", "De Gaulle'nin 'Yaşasın Özgür Quebec' sözü kriz yarattı.", ["de Gaulle"]),
        ("1960s", 1967, "war", "Altı Gün Savaşı", "Fransa, Ortadoğu politikasını değiştirdi.", []),
        ("1960s", 1968, "revolution", "Mayıs 68", "Öğrenci ve işçi ayaklanmaları Fransa'yı sarstı.", [], 5),
        ("1960s", 1968, "culture", "Öğrenci Hareketi", "Sorbonne üniversitesi işgal edildi.", []),
        ("1960s", 1969, "politics", "Pompidou Cumhurbaşkanı", "Georges Pompidou seçildi.", ["Georges Pompidou"]),
        ("1960s", 1969, "culture", "Rolling Stones Fransa'da", "Rolling Stones Fransa konseri verdi.", ["Rolling Stones"]),
        ("1960s", 1960, "culture", "Brigitte Bardot Zirvesi", "Brigitte Bardot sinema kariyerinin zirvesinde.", ["Brigitte Bardot"]),
        ("1960s", 1961, "politics", "Michel Debré Hükümeti", "Michel Debré başbakanlığı sürdü.", ["Michel Debré"]),
        ("1960s", 1962, "culture", "Yves Saint Laurent Markası", "Yves Saint Laurent kendi moda evini kurdu.", ["Yves Saint Laurent"]),
        ("1960s", 1963, "culture", "Alain Delon Yıldızı", "Alain Delon, 'Leopar' filmiyle uluslararası yıldız oldu.", ["Alain Delon"]),
        ("1960s", 1965, "culture", "Jeanne Moreau", "Jeanne Moreau, 'Jules et Jim' ile yıldızı parladı.", ["Jeanne Moreau"]),
        ("1960s", 1966, "culture", "Claude Lelouch 'Bir Erkek Bir Kadın'", "Lelouch filmi Oscar kazandı.", ["Claude Lelouch"]),
        ("1960s", 1967, "culture", "Serge Gainsbourg 'Jane Birkin'", "Gainsbourg ve Birkin çifti oldu.", ["Serge Gainsbourg", "Jane Birkin"]),
        ("1960s", 1968, "culture", "The Who Fransa'da", "The Who Paris konseri verdi.", ["The Who"]),
        ("1960s", 1969, "politics", "Couve de Murville Hükümeti", "Maurice Couve de Murville başbakan oldu.", ["Maurice Couve de Murville"]),
        
        # 1970s - 31 ek olay
        ("1970s", 1970, "culture", "De Gaulle'ün Ölümü", "Charles de Gaulle hayatını kaybetti.", ["de Gaulle"]),
        ("1970s", 1970, "culture", "Sartre 'Aile Ağzı'", "Sartre yeni oyununu yazdı.", ["Jean-Paul Sartre"]),
        ("1970s", 1971, "politics", "Chaban-Delmas Hükümeti", "Jacques Chaban-Delmas başbakan oldu.", ["Jacques Chaban-Delmas"]),
        ("1970s", 1971, "culture", "Françoise Hardy'ın Müziği", "Françoise Hardy yeni albüm yayınladı.", ["Françoise Hardy"]),
        ("1970s", 1972, "politics", "Mesmer Olayı", "Robert Boulin skandalı patlak verdi.", []),
        ("1970s", 1972, "culture", "Claude François'ın Şarkıları", "Claude François popüler şarkılar çıkardı.", ["Claude François"]),
        ("1970s", 1973, "politics", "Messmer Hükümeti", "Pierre Messmer hükümeti.", ["Pierre Messmer"]),
        ("1970s", 1973, "war", "Yom Kippur Savaşı", "Fransa, Ortadoğu savaşında tarafsız kaldı.", []),
        ("1970s", 1974, "politics", "Pompidou'ün Ölümü", "Georges Pompidou hayatını kaybetti.", ["Georges Pompidou"]),
        ("1970s", 1974, "politics", "Giscard d'Estaing Seçildi", "Valéry Giscard d'Estaing cumhurbaşkanı oldu.", ["Giscard d'Estaing"]),
        ("1970s", 1974, "culture", "Giscard'ın Piyanosu", "Giscard televizyonda piyano çaldı.", []),
        ("1970s", 1975, "culture", "Mesrine Suçlusu", "Jacques Mesrine hapisten kaçtı.", ["Jacques Mesrine"]),
        ("1970s", 1976, "politics", "Chirac İlk Başbakan", "Jacques Chirac ilk kez başbakan oldu.", ["Jacques Chirac"]),
        ("1970s", 1976, "culture", "Barre Hükümeti", "Raymond Barre ekonomist başbakan olarak atandı.", ["Raymond Barre"]),
        ("1970s", 1977, "politics", "Paris Belediye Seçimi", "Jacques Chirac Paris belediye başkanı seçildi.", ["Jacques Chirac"]),
        ("1970s", 1978, "politics", "Avrupa Seçimleri", "İlk kez doğrudan Avrupa Parlamentosu seçimleri yapıldı.", []),
        ("1970s", 1978, "culture", "Johnny Hallyday Konserleri", "Johnny Hallyday stadyum konserleri verdi.", ["Johnny Hallyday"]),
        ("1970s", 1979, "diplomacy", "Avrupa Para Sistemi", "Fransa, Avrupa Para Sistemi'ne katıldı.", []),
        ("1970s", 1979, "culture", "Jacques Brel'in Veda Konseri", "Jacques Brel son konserini verdi.", ["Jacques Brel"]),
        ("1970s", 1970, "culture", "Alain Delon ve Romy Schneider", "Ünlü çift filmlerde birlikte oynadı.", ["Alain Delon", "Romy Schneider"]),
        ("1970s", 1971, "culture", "Louis de Funès Komedi", "Louis de Funès komedi filmlerinde zirve yaptı.", ["Louis de Funès"]),
        ("1970s", 1972, "culture", "Jean-Paul Belmondo Aksiyon", "Belmondo aksiyon filmlerinde yıldız oldu.", ["Jean-Paul Belmondo"]),
        ("1970s", 1973, "culture", "Punk Akımı Paris", "Punk müzik Paris'e ulaştı.", []),
        ("1970s", 1974, "culture", "Gérard Depardieu Yükselişte", "Depardieu başrol filmlerinde oynamaya başladı.", ["Gérard Depardieu"]),
        ("1970s", 1975, "culture", "Isabelle Adjani Keşfedildi", "Genç Isabelle Adjani sinemaya girdi.", ["Isabelle Adjani"]),
        ("1970s", 1976, "culture", "Éric Rohmer Filmleri", "Éric Rohmer 'Moral Öyküler' serisini çekti.", ["Éric Rohmer"]),
        ("1970s", 1977, "culture", "Mireille Mathieu Şarkıcı", "Mireille Mathieu popüler şarkıcı oldu.", ["Mireille Mathieu"]),
        ("1970s", 1978, "culture", "Michel Sardou'nun Şarkıları", "Michel Sardou hit şarkılar çıkardı.", ["Michel Sardou"]),
        ("1970s", 1979, "culture", "Julio Iglesias Fransa'da", "Julio Iglesias Fransa'da popüler oldu.", ["Julio Iglesias"]),
        
        # 1980s - 31 ek olay
        ("1980s", 1980, "politics", "Barre Hükümeti", "Raymond Barre hükümeti görevde.", ["Raymond Barre"]),
        ("1980s", 1981, "politics", "Mitterrand Cumhurbaşkanı", "François Mitterrand seçildi.", ["François Mitterrand"]),
        ("1980s", 1981, "culture", "İdam Kaldırıldı", "Fransa'da idam cezası kaldırıldı.", []),
        ("1980s", 1981, "politics", "Komünist Bakanlar", "Komünist Parti hükümete katıldı.", []),
        ("1980s", 1982, "culture", "39 Saat İş Haftası", "Haftalık çalışma süresi 39 saate indirildi.", []),
        ("1980s", 1983, "politics", "Austere Dönüş", "Mitterrand ekonomik politikalardan vazgeçti.", []),
        ("1980s", 1984, "politics", "Avrupa Birliği Anlaşması", "Avrupa Birliği anlaşması imzalandı.", []),
        ("1980s", 1985, "culture", "Rainbow Warrior Baskını", "Greenpeace gemisi Fransız ajanları tarafından battırıldı.", [], 1),
        ("1980s", 1986, "politics", "Kohabitasiyon", "Mitterrand ve Chirac farklı partilerden, kohabitasiyon dönemi.", []),
        ("1980s", 1986, "culture", "Louvre Piramidi", "Louvre önüne cam piramit inşa edildi.", ["I.M. Pei"]),
        ("1980s", 1987, "politics", "Chirac Başbakan", "Chirac, Mitterrand döneminde başbakan.", ["Jacques Chirac"]),
        ("1980s", 1988, "politics", "Mitterrand Yeniden", "Mitterrand ikinci kez cumhurbaşkanı.", ["François Mitterrand"]),
        ("1980s", 1988, "culture", "Cannes Film Festivali", "Cannes 40. yılını kutladı.", []),
        ("1980s", 1989, "culture", "Devrim'in 200. Yılı", "Bastille Günü'nde büyük kutlamalar.", []),
        ("1980s", 1989, "diplomacy", "Berlin Duvarı Yıkıldı", "Fransa, Almanya birliğini destekledi.", []),
        ("1980s", 1980, "culture", "Jean-Jacques Goldman", "Goldman müzik kariyerine başladı.", ["Jean-Jacques Goldman"]),
        ("1980s", 1981, "culture", "Daniel Balavoine", "Balavoine popüler şarkılar çıkardı.", ["Daniel Balavoine"]),
        ("1980s", 1982, "culture", "Florent Pagny", "Florent Pagny müzik dünyasına girdi.", ["Florent Pagny"]),
        ("1980s", 1983, "culture", "Vanessa Paradis", "Genç Vanessa Paradis şarkıcı oldu.", ["Vanessa Paradis"]),
        ("1980s", 1984, "culture", "Patricia Kaas", "Patricia Kaas şarkıcı olarak tanındı.", ["Patricia Kaas"]),
        ("1980s", 1985, "culture", "Étienne Daho", "Étienne Daho yeni dalga müzik yaptı.", ["Étienne Daho"]),
        ("1980s", 1986, "culture", "Jean Reno Sinemada", "Jean Reno film kariyerine başladı.", ["Jean Reno"]),
        ("1980s", 1987, "culture", "Christophe Lambert", "Lambert 'Highlander' ile yıldız oldu.", ["Christophe Lambert"]),
        ("1980s", 1988, "culture", "Sophie Marceau", "Sophie Marceau uluslararası yıldız oldu.", ["Sophie Marceau"]),
        ("1980s", 1989, "culture", "Luc Besson 'Le Grand Bleu'", "Besson su altı filmiyle başarı yakaladı.", ["Luc Besson"]),
        
        # 1990s - 34 ek olay
        ("1990s", 1990, "war", "Körfez Savaşı", "Fransa, Kuveyt'i kurtarma operasyonuna katıldı.", [], 20),
        ("1990s", 1991, "culture", "Mitterrand'ın İkinci Dönemi", "Mitterrand'ın ikinci dönemi sona erdi.", []),
        ("1990s", 1992, "diplomacy", "Maastricht Anlaşması", "Avrupa Birliği kuruldu.", []),
        ("1990s", 1993, "politics", "Kohabitasiyon", "Mitterrand ve Balladur kohabitasiyonu.", []),
        ("1990s", 1994, "culture", "Euro Disney Açıldı", "Disneyland Paris açıldı.", []),
        ("1990s", 1995, "politics", "Chirac Cumhurbaşkanı", "Jacques Chirac seçildi.", ["Jacques Chirac"]),
        ("1990s", 1995, "culture", "Nükleer Testleri", "Fransa Pasifik'te nükleer denemelere başladı.", []),
        ("1990s", 1996, "politics", "Mitterrand'ın Ölümü", "François Mitterrand öldü.", ["François Mitterrand"]),
        ("1990s", 1997, "politics", "Jospin Hükümeti", "Lionel Jospin başbakan oldu.", ["Lionel Jospin"]),
        ("1990s", 1998, "culture", "Dünya Kupası Zaferi", "Fransa Dünya Kupası'nı kazandı.", ["Zinedine Zidane"]),
        ("1990s", 1999, "culture", "Euro'ya Geçiş", "Euro para birimine hazırlık başladı.", []),
        ("1990s", 1999, "war", "Kosova", "Fransa, NATO'nun Kosova operasyonuna katıldı.", []),
        ("1990s", 1990, "culture", "MC Solaar", "MC Solaar Fransız rap müziğinin öncüsü oldu.", ["MC Solaar"]),
        ("1990s", 1991, "culture", "Daft Punk", "Daft Punk kuruldu.", ["Daft Punk"]),
        ("1990s", 1992, "culture", "Céline Dion", "Céline Dion dünya yıldızı oldu.", ["Céline Dion"]),
        ("1990s", 1993, "culture", "Florent Pagny Zirve", "Florent Pagny müzik kariyerinde zirve yaptı.", ["Florent Pagny"]),
        ("1990s", 1994, "culture", "Luc Besson 'Léon'", "Léon filmi başarılı oldu.", ["Luc Besson"]),
        ("1990s", 1995, "culture", "Alain Chabat", "Alain Chabat komedi filmlerinde popüler oldu.", ["Alain Chabat"]),
        ("1990s", 1996, "culture", "Jean Dujardin", "Jean Dujardin televizyonda başladı.", ["Jean Dujardin"]),
        ("1990s", 1997, "culture", "Titanic Gişe Rekoru", "Titanic Fransa'da gişe rekorları kırdı.", []),
        ("1990s", 1998, "culture", "Zidane Dünya Kupası", "Zidane dünya yıldızı oldu.", ["Zinedine Zidane"]),
        ("1990s", 1999, "culture", "Matrix Fransa'da", "Matrix filmi vizyona girdi.", []),
        
        # 2000s - 33 ek olay
        ("2000s", 2000, "culture", "Louvre Piramidi 10. Yıl", "Louvre cam piramidi 10. yılını kutladı.", []),
        ("2000s", 2001, "culture", "Amélie Film", "'Amélie' filmi uluslararası başarı yakaladı.", ["Jean-Pierre Jeunet", "Audrey Tautou"]),
        ("2000s", 2002, "politics", "Chirac Yeniden", "Chirac Le Pen karşısında seçildi.", ["Jacques Chirac"]),
        ("2000s", 2002, "culture", "Euro Kullanıma Girdi", "Fransa Euro'ya geçti.", []),
        ("2000s", 2003, "diplomacy", "Irak'a Karşı", "Fransa, Irak işgaline karşı çıktı.", ["Chirac", "Dominique de Villepin"]),
        ("2000s", 2004, "politics", "AB Anayasası", "Fransa AB Anayasası'nı reddetti.", []),
        ("2000s", 2005, "revolution", "Banliyö Ayaklanmaları", "Paris banliyölerinde gençler ayaklandı.", [], 3),
        ("2000s", 2005, "culture", "Başörtüsü Yasası", "Kamu okullarında dini semboller yasaklandı.", []),
        ("2000s", 2006, "politics", "CPE Protestoları", "Genç istihdam yasası protestoları.", []),
        ("2000s", 2007, "politics", "Sarkozy Cumhurbaşkanı", "Nicolas Sarkozy seçildi.", ["Nicolas Sarkozy"]),
        ("2000s", 2008, "politics", "AB Dönem Başkanlığı", "Fransa, AB dönem başkanlığı yaptı.", []),
        ("2000s", 2009, "diplomacy", "NATO'ya Dönüş", "Fransa NATO'nun askeri komutasına geri döndü.", ["Sarkozy"]),
        ("2000s", 2003, "culture", "Daft Punk 'Human After All'", "Daft Punk yeni albüm yayınladı.", ["Daft Punk"]),
        ("2000s", 2004, "culture", "Paris Olimpiyat Adaylığı", "Paris 2012 için aday oldu (kaybetti).", []),
        ("2000s", 2006, "culture", "Marie Antoinette Filmi", "Sofia Coppola filmi vizyona girdi.", ["Sofia Coppola"]),
        ("2000s", 2008, "culture", "Taken Filmi", "'Taken' filmi büyük başarı yakaladı.", []),
        ("2000s", 2001, "culture", "Omar Sy", "Omar Sy televizyonda başladı.", ["Omar Sy"]),
        ("2000s", 2002, "culture", "Gérard Depardieu Zirvesi", "Depardieu uluslararası yıldız oldu.", ["Gérard Depardieu"]),
        ("2000s", 2004, "culture", "Marion Cotillard", "Marion Cotillard yıldızı parladı.", ["Marion Cotillard"]),
        ("2000s", 2006, "culture", "Soko Müzik", "Soko müzik kariyerine başladı.", ["Soko"]),
        ("2000s", 2007, "culture", "Sébastien Tellier", "Tellier müzik yaptı.", ["Sébastien Tellier"]),
        ("2000s", 2008, "culture", "Yelle", "Yelle popüler şarkıcı oldu.", ["Yelle"]),
        ("2000s", 2009, "culture", "Phoenix", "Phoenix müzik grubu uluslararası başarı yakaladı.", ["Phoenix"]),
        
        # 2010s - 30 ek olay
        ("2010s", 2010, "politics", "G20 Zirvesi", "Fransa G20 zirvesine ev sahipliği yaptı.", []),
        ("2010s", 2011, "politics", "Arap Baharı", "Fransa, Tunus ve Libya'daki devrimleri destekledi.", []),
        ("2010s", 2011, "war", "Libya", "Fransa, Libya'ya hava operasyonları düzenledi.", []),
        ("2010s", 2012, "politics", "Hollande Cumhurbaşkanı", "François Hollande seçildi.", ["François Hollande"]),
        ("2010s", 2013, "politics", "Eşcinsel Evlilik", "Fransa, eşcinsel evliliği yasallaştırdı.", []),
        ("2010s", 2013, "war", "Mali", "Fransa, Mali'de operasyon başlattı.", []),
        ("2010s", 2014, "war", "IŞİD'e Karşı", "Fransa, IŞİD'e karşı hava operasyonlarına başladı.", []),
        ("2010s", 2015, "culture", "Paris İklim Anlaşması", "COP21'de Paris Anlaşması kabul edildi.", []),
        ("2010s", 2015, "terror", "Paris Saldırıları", "IŞİD Paris'te saldırı düzenledi.", [], 130),
        ("2010s", 2016, "culture", "Euro 2016", "Fransa, Euro 2016'ya ev sahipliği yaptı.", []),
        ("2010s", 2016, "terror", "Nice Saldırısı", "Kamyon saldırısı düzenlendi.", [], 86),
        ("2010s", 2017, "politics", "Macron Cumhurbaşkanı", "Emmanuel Macron seçildi.", ["Emmanuel Macron"]),
        ("2010s", 2018, "revolution", "Sarı Yelekliler", "Akaryakıt zammı protestoları.", [], 10),
        ("2010s", 2019, "culture", "Notre-Dame Yangını", "Notre-Dame Katedrali'nde yangın çıktı.", []),
        ("2010s", 2011, "culture", "The Artist", "Sessiz film Oscar kazandı.", ["Michel Hazanavicius"]),
        ("2010s", 2012, "culture", "Paris Moda Haftası", "Moda haftası küresel etkinlik haline geldi.", []),
        ("2010s", 2014, "culture", "Lucy Filmi", "'Lucy' filmi gişe başarısı yakaladı.", ["Luc Besson", "Scarlett Johansson"]),
        ("2010s", 2015, "culture", "Kendji Girac", "Kendji Girac şarkıcı oldu.", ["Kendji Girac"]),
        ("2010s", 2016, "culture", "Lara Fabian", "Lara Fabian konser verdi.", ["Lara Fabian"]),
        ("2010s", 2017, "culture", "Petit Biscuit", "Petit Biscuit elektronik müzik yaptı.", ["Petit Biscuit"]),
        ("2010s", 2018, "culture", "Angèle", "Angèle şarkıcı olarak tanındı.", ["Angèle"]),
        ("2010s", 2019, "culture", "PNL Grubu", "PNL rap grubu popüler oldu.", ["PNL"]),
        
        # 2020s - 37 ek olay
        ("2020s", 2020, "politics", "COVID-19", "Fransa'da ilk kez COVID-19 karantinası.", [], 60000),
        ("2020s", 2020, "culture", "Notre-Dame Restorasyonu", "Restorasyon çalışmaları başladı.", []),
        ("2020s", 2021, "politics", "Aşı Zorunluluğu", "Sağlık çalışanları için aşı zorunluluğu.", []),
        ("2020s", 2022, "politics", "Macron Yeniden", "Emmanuel Macron ikinci kez seçildi.", ["Emmanuel Macron"]),
        ("2020s", 2022, "war", "Ukrayna", "Fransa, Ukrayna'ya yardım sağladı.", []),
        ("2020s", 2023, "revolution", "Emeklilik Protestoları", "Emeklilik reformuna karşı protestolar.", []),
        ("2020s", 2023, "politics", "Pension Reformu", "Macron, emeklilik reformunu geçirdi.", []),
        ("2020s", 2024, "culture", "Paris Olimpiyatları", "Paris üçüncü kez Olimpiyat'a ev sahipliği yapacak.", []),
        ("2020s", 2024, "culture", "Notre-Dame Açılış", "Katedral yeniden açılacak.", []),
        ("2020s", 2020, "culture", "Tenet", "Christopher Nolan filmi vizyona girdi.", ["Christopher Nolan"]),
        ("2020s", 2021, "culture", "Spiral", "Saw serisi filmi gösterime girdi.", []),
        ("2020s", 2022, "culture", "Top Gun: Maverick", "Film Fransa'da gişe başarısı yakaladı.", ["Tom Cruise"]),
        ("2020s", 2023, "culture", "Killers of the Flower Moon", "Scorsese filmi Cannes'de prömiyer yaptı.", ["Martin Scorsese"]),
        ("2020s", 2020, "culture", "Orelsan", "Orelsan rap müzikte zirve yaptı.", ["Orelsan"]),
        ("2020s", 2021, "culture", "Juliette Armanet", "Juliette Armanet şarkıcı oldu.", ["Juliette Armanet"]),
        ("2020s", 2022, "culture", "Vianney", "Vianney müzik yaptı.", ["Vianney"]),
        ("2020s", 2023, "culture", "Zaho de Sagazan", "Zaho de Sagazan sanatçı olarak tanındı.", ["Zaho de Sagazan"]),
        ("2020s", 2024, "culture", "Aya Nakamura", "Aya Nakamura popüler şarkıcı oldu.", ["Aya Nakamura"]),
        ("2020s", 2025, "politics", "Fransa 2025", "Fransa yeni döneme hazırlanıyor.", []),
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
    new_events = generate_more_france_events()
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
