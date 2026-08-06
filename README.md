# FormCheck

Kamera görüntüsünden eklem açısı hesaplayıp egzersiz formunu değerlendiren mobil kişisel antrenör uygulaması.


## Özellikler

- 5 egzersiz: Squat, Chair Pose, Plank, Planör duruşu, Tree Pose
- Gerçek zamanlı tekrar sayma (histerezisli durum makinesi)
- 0–100 arası form skoru (bulanık mantık tabanlı ağırlıklı skorlama)
- Anlık, öncelik sıralı geri bildirim mesajı
- Set sonu özeti: tekrar sayısı, en sık hata, ROM grafiği
- Kamera veya yüklenmiş video ile çalışabilir (test/demo modu)

---

## Teknoloji

| Katman | Teknoloji |
|---|---|
| Prototip dili | Python 3.11 |
| Poz tespiti | `mediapipe` (BlazePose, 33 landmark) |
| Görüntü / kamera | OpenCV (`opencv-python`) |
| Matematik | NumPy |
| Test | pytest |
| Çalışma yeri | Masaüstü prototip → hedef: mobil |

> Karar mantığı (`geometry/` + `rules/`) saf Python fonksiyonlarıdır; MediaPipe/OpenCV/kameradan bağımsızdır. Bu sayede aynı matematik, mobil sürüme taşınırken birebir yeniden yazılabilir — kütüphaneye bağımlı hiçbir karar mantığı yoktur.

---

## Kurulum

```bash
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS / Linux
pip install -r requirements.txt
python main.py
```

`main.py` kamerayı açar, her karede poz tespiti yapıp eklem açılarını hesaplar ve ekranda iskeleti + form geri bildirimini gösterir. Çıkmak için pencere seçiliyken `q`.

```bash
python -m pytest               # geometry/ ve rules/ testleri — kamera gerektirmez
```

> MediaPipe, Python 3.11 ile uyumludur. Python 3.13 ile kurulum başarısız olursa 3.11'lik bir sanal ortam kullanın.

---

## Klasör yapısı

```
src/
  capture/     kamera akışı (OpenCV)
  pose/        MediaPipe kurulumu ve işleme döngüsü (sensör katmanı)
  geometry/    açı formülleri — saf fonksiyon, MediaPipe/OpenCV'ye bağımlı değil
  filter/      zamansal yumuşatma (medyan + EMA)
  rules/       kural motoru + tekrar sayacı (FSM) — saf fonksiyon
  ui/          çizim / ekran katmanı (OpenCV)
exercises.json             5 egzersizin kuralları (koddan okunur)
models/                    MediaPipe model dosyası
docs/
  calibration-poses.json   3 statik kalibrasyon pozu — Gün 1 doğrulama
main.py                    giriş noktası
requirements.txt           bağımlılıklar
```

`geometry/` ve `rules/` neden MediaPipe/OpenCV'den bağımsız tutuluyor: bkz. `ARCHITECTURE.md` §5.

---

## Proje dokümanları

| Dosya | İçerik |
|---|---|
| [`CLAUDE.md`](./CLAUDE.md) | Kodlama ajanları için bağlayıcı kurallar ve yasaklar |
| [`ARCHITECTURE.md`](./ARCHITECTURE.md) | SOLID/DRY uygulanışı, katman diyagramı, taşınabilirlik yol haritası |
| [`personal-trainer-is-analizi.md`](./personal-trainer-is-analizi.md) | Ana spesifikasyon — tüm formüller, kural tabloları, test planı |
| [`gelistirici-devir-teslim.md`](./gelistirici-devir-teslim.md) | Görev sırası, hazır agent prompt'ları, bilinen tuzaklar |
| [`gun-1-plani.md`](./gun-1-plani.md) | Blok blok ilk gün görevleri |
| [`literatur-incelemesi.md`](./literatur-incelemesi.md) | Akademik kaynaklar, eşiklerin gerekçesi |

Yeni katkı yapmadan önce `CLAUDE.md`'yi okuyun — özellikle eşik değerlerinin nereye yazılacağı ve hangi klasörün MediaPipe'tan bağımsız kalması gerektiği konusunda.

---




