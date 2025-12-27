# 📚 Manga AI Translator & Editor

Bu araç, yapay zeka (Gemini 2.0 Flash) kullanarak manga sayfalarındaki metinleri otomatik olarak tespit eder, Türkçe'ye çevirir ve orijinal arka planı koruyarak metinleri yeniden yerleştirir.

## ✨ Özellikler

- **Akıllı Tespit:** Metin balonlarını ve konumlarını tespit eder.
- **AI Çeviri:** Metinleri manga bağlamına uygun şekilde Türkçe'ye çevirir.
- **Otomatik Temizleme:** Orijinal metni siler ve arka plan rengine göre alanı temizler.
- **Dinamik Font:** Metin uzunluğuna göre yazı boyutunu otomatik ayarlar.
- **WebP Desteği:** Kayıpsız ve yüksek kaliteli WebP formatında çıktı verir.

## 🚀 Kurulum

1. Bu depoyu klonlayın:
   git clone [https://github.com/artienis/manga-translator.git](https://github.com/artienis/manga-translator.git)
   cd manga-translator
Gerekli kütüphaneleri yükleyin:


pip install -r requirements.txt
OpenRouter üzerinden bir API anahtarı alın ve sisteme tanımlayın:

Windows (PowerShell): $env:OPENROUTER_API_KEY="anahtarınız"

Linux/Mac: export OPENROUTER_API_KEY="anahtarınız"

🛠 Kullanım
Programı çalıştırın ve işlemek istediğiniz manga sayfasının yolunu girin:

Bash

python main.py
⚠️ Dikkat
Program arial.ttf fontunu kullanmaya çalışır. Eğer sisteminizde yoksa varsayılan fonta geçiş yapar.

API kullanımı ücrete veya limitlere tabi olabilir.

📄 Lisans
Bu proje MIT Lisansı altında lisanslanmıştır. Detaylar için `LICENSE` dosyasına bakabilirsiniz.