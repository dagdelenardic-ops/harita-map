# Jeopolitik Tarih Haritası - Proje Özeti (Handover)

Bu dosya, projenin mevcut durumunu, mimarisini ve yapılan geliştirmeleri özetlemektedir. Başka bir model veya geliştirici için rehber niteliğindedir.

## 🚀 Proje Hakkında
Bu proje, son 100 yılın önemli jeopolitik olaylarını interaktif bir dünya haritası üzerinde görselleştiren bir web uygulamasıdır.

- **Canlı Web Sitesi:** [https://jeopolitik.com.tr](https://jeopolitik.com.tr)
- **Teknoloji Yığını:** Python (Folium), Docker, Google Cloud Run, GitHub Actions (CD).

## 🏗️ Mimari ve Akış
1.  **Veri Kaynağı:** `data/events.json` dosyasında tüm tarihi olaylar, koordinatlar ve kategoriler tutulur.
2.  **Harita Üretimi:** `scripts/geopolitical_map.py` betiği, JSON verisini okur ve `output/geopolitical_map.html` dosyasını (interaktif harita) oluşturur.
3.  **Yayınlama:** Kod GitHub'a (`main` branch) push edildiğinde, Google Cloud Build otomatik olarak yeni bir Docker image'ı oluşturur ve Cloud Run üzerinde yayına alır.

## 🛠️ Yapılan Önemli Geliştirmeler
Son dönemde projeye eklenen kritik özellikler:

1.  **Custom Domain & SSL:** Site `jeopolitik.com.tr` adresine bağlandı ve SSL (HTTPS) kurulumu tamamlandı.
2.  **SEO Optimizasyonu:**
    *   Meta taglar, Açıklamalar (Description) ve Anahtar Kelimeler (Keywords) eklendi.
    *   `robots.txt` ve `sitemap.xml` dosyaları otomatik oluşturuluyor.
3.  **YouTube Entegrasyonu:** "32. Gün" arşivinden önemli tarihi videolar haritadaki olaylara embed (gömülü) edildi.
4.  **Akıllı Wikipedia Linkleri:**
    *   Markdown formatındaki linkler HTML'e çevrildi.
    *   Eğer Türkçe Wikipedia sayfası yoksa, otomatik olarak **İngilizce Wikipedia + Google Translate** (Türkçe seçili) kombinasyonuna yönlendirme eklendi.
5.  **Görsel Geliştirmeler:** Seçilen ülkenin bayrağının ülke sınırları içine (HOI4 tarzı) maskelenerek gelmesi sağlandı.

## 📂 Önemli Dosyalar
- `scripts/geopolitical_map.py`: Ana motor. Haritayı oluşturan, CSS/JS enjekte eden kod.
- `data/events.json`: Projenin kalbi olan veri dosyası.
- `scripts/fix_wiki.py`: Wikipedia linklerini kontrol eden ve düzelten araç.
- `scripts/add_youtube_videos.py`: Videoları toplu olarak eventlere ekleyen araç.
- `Dockerfile`: Projenin Cloud Run'da nasıl çalışacağını belirleyen yapılandırma.

## 🔄 Güncelleme Prosedürü
Yeni bir olay eklemek veya kodu değiştirmek için:
1.  `data/events.json` dosyasını güncelleyin.
2.  Lokalde `python3 scripts/geopolitical_map.py` komutunu çalıştırarak haritayı yenileyin.
3.  Değişiklikleri push edin:
    ```bash
    git add .
    git commit -m "Güncelleme açıklaması"
    git push origin main
    ```
4.  Cloud Run otomatik olarak güncellenecektir.

## 📎 İletişim & Notlar
Google Search Console üzerinden `sitemap.xml` gönderimi yapılmıştır. Alan adı TurkTicaret.net üzerinden kontrol edilmektedir.
