import cv2
import numpy as np
import requests
import base64
import json
import os
import re
from PIL import Image, ImageDraw, ImageFont

# ============================================================
# YAPILANDIRMA (GÜVENLİ)
# ============================================================
# API anahtarını sisteminize 'OPENROUTER_API_KEY' adıyla ekleyin
# Veya manuel olarak test etmek için geçici olarak buraya yazın
API_KEY = os.getenv("OPENROUTER_API_KEY", "BURAYA_API_ANAHTARINIZI_YAZIN")
MODEL = "google/gemini-2.0-flash-001"
URL = "https://openrouter.ai/api/v1/chat/completions"

def get_translation_for_chunk(chunk_img):
    """Görüntü parçasındaki metinleri tespit eder ve çevirir."""
    _, buffer = cv2.imencode(".png", chunk_img)
    img_b64 = base64.b64encode(buffer).decode()

    prompt = (
        "Manga editörü olarak çalış. Metinleri bul, Türkçe'ye çevir. "
        "Metin alanlarını tam kapsayan kutular ver. SADECE JSON döndür: "
        "[{\"tr\": \"Metin\", \"box_2d\": [ymin, xmin, ymax, xmax]}]"
    )

    payload = {
        "model": MODEL,
        "messages": [{
            "role": "user", 
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}}
            ]
        }]
    }

    headers = {
        "Authorization": f"Bearer {API_KEY}", 
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/manga-translator", # GitHub projeniz için opsiyonel
    }
    
    try:
        r = requests.post(URL, headers=headers, json=payload, timeout=60)
        r.raise_for_status()
        content = r.json()["choices"][0]["message"]["content"]
        json_str = re.search(r'\[.*\]', content, re.DOTALL).group()
        return json.loads(json_str)
    except Exception as e:
        print(f"⚠️ Hata oluştu: {e}")
        return []

def get_clean_bg_color(img, l, t, w, h):
    """Kutunun etrafındaki piksellerden arka plan rengini belirler."""
    h_img, w_img = img.shape[:2]
    m = 5 
    y1, y2 = max(0, t-m), min(h_img, t+h+m)
    x1, x2 = max(0, l-m), min(w_img, l+w+m)
    roi = img[y1:y2, x1:x2].copy()
    
    if roi.size == 0: 
        return (255, 255, 255)
    
    roi[m:-m, m:-m] = 0
    pixels = roi.reshape(-1, 3)
    valid_pixels = pixels[np.any(pixels != [0, 0, 0], axis=1)]
    
    if valid_pixels.size == 0: 
        return (255, 255, 255)
    
    bg_bgr = np.median(valid_pixels, axis=0)
    return tuple(map(int, bg_bgr))

def process_manga(image_path):
    """Manga sayfasını işler, çevirir ve temizlenmiş halini kaydeder."""
    image_path = image_path.strip('"').strip("'").strip()
    if not os.path.exists(image_path):
        print("❌ Dosya bulunamadı!")
        return

    img = cv2.imdecode(np.fromfile(image_path, dtype=np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        return

    h_orig, w_orig = img.shape[:2]
    chunk_h, overlap = 1500, 200
    all_data = []

    print(f"📦 İşleniyor: {os.path.basename(image_path)}")

    for y_start in range(0, h_orig, chunk_h - overlap):
        y_end = min(y_start + chunk_h, h_orig)
        chunk = img[y_start:y_end, 0:w_orig]
        data = get_translation_for_chunk(chunk)
        
        chunk_actual_h = y_end - y_start
        for item in data:
            ymin, xmin, ymax, xmax = item['box_2d']
            item['real_box'] = [
                int((ymin/1000)*chunk_actual_h)+y_start, int((xmin/1000)*w_orig),
                int((ymax/1000)*chunk_actual_h)+y_start, int((xmax/1000)*w_orig)
            ]
            all_data.append(item)

    pil_img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(pil_img)
    
    # Font Ayarı: Arial yoksa varsayılan fonta geçer
    try:
        font_path = "arial.ttf"
    except:
        font_path = None

    for item in all_data:
        try:
            t, l, b, r = item['real_box']
            pad_w = max(4, int((r-l)*0.12))
            pad_h = max(4, int((b-t)*0.12))
            l, t, r, b = max(0, l-pad_w), max(0, t-pad_h), min(w_orig, r+pad_w), min(h_orig, b+pad_h)
            w, h = r - l, b - t

            if w <= 0 or h <= 0 or w > w_orig * 0.9: 
                continue

            # 1. Arka Planı Kapat
            bg_bgr = get_clean_bg_color(img, l, t, w, h)
            bg_rgb = (bg_bgr[2], bg_bgr[1], bg_bgr[0])
            draw.rectangle([l, t, r, b], fill=bg_rgb)

            # 2. Metin Yerleştirme
            text = item['tr'].upper()
            f_size = 50
            
            # Dinamik Boyutlandırma
            while f_size > 8:
                try:
                    font = ImageFont.truetype(font_path, f_size) if font_path else ImageFont.load_default()
                except:
                    font = ImageFont.load_default()
                
                lines, cur_l = [], ""
                for word in text.split():
                    if draw.textlength(cur_l + word + " ", font=font) < (w * 0.92):
                        cur_l += word + " "
                    else:
                        lines.append(cur_l.strip())
                        cur_l = word + " "
                lines.append(cur_l.strip())
                
                if (len(lines) * f_size * 1.2) < (h * 0.96): 
                    break
                f_size -= 2

            # Renk Kontrastı
            bright = (bg_rgb[0]*0.299 + bg_rgb[1]*0.587 + bg_rgb[2]*0.114)
            t_color = (255, 255, 255) if bright < 128 else (0, 0, 0)
            
            cy = t + (h - (len(lines) * f_size * 1.2)) // 2
            for line in lines:
                lw = draw.textlength(line, font=font)
                draw.text((l + (w - lw) // 2, cy), line, fill=t_color, font=font)
                cy += f_size * 1.2
        except Exception:
            continue

    # 3. Kaydetme
    out_path = os.path.splitext(image_path)[0] + "_translated.webp"
    pil_img.save(out_path, "WEBP", lossless=True, quality=100, method=6)
    print(f"✅ Başarıyla kaydedildi: {out_path}")

if __name__ == "__main__":
    print("--- Manga Çevirici (GitHub Sürümü) ---")
    print("Çıkış yapmak için 'q' yazın.")
    
    if API_KEY == "BURAYA_API_ANAHTARINIZI_YAZIN":
        print("⚠️ Uyarı: API anahtarı ayarlanmamış!")

    while True:
        path = input("\nDosya yolunu sürükleyin veya yazın: ").strip()
        if path.lower() == 'q': 
            break
        process_manga(path)