# CLAUDE.md

Bu dosya, bu repoda çalışan her AI kodlama ajanı (Claude Code dahil) için bağlayıcıdır. Bir görev bu dosyayla çelişiyorsa, önce bu dosyaya uy, sonra sor.

## Proje

FormCheck — kamera görüntüsünden eklem açısı hesaplayıp egzersiz formunu değerlendiren mobil kişisel antrenör uygulaması. Akademik proje. Bu depo, uygulamanın **Python prototipidir**; nihai hedef mobildir, karar mantığı taşınabilir tutulur.

**Dil ve teknoloji:** Python 3.11. Poz tespiti `mediapipe` (BlazePose, 33 landmark). Kamera/görüntü OpenCV. Matematik NumPy. Test pytest.

**Mutlak kısıt:** Karar katmanında öğrenilen model YOK. Sınıflandırıcı yok, eğitim verisi yok, ağırlık dosyası yok. Tüm doğru/yanlış kararı deterministik geometri (`arccos`, `atan2`) ve JSON'dan okunan eşik değerleriyle verilir. Poz tespiti (MediaPipe) tek istisnadır — o bir sensör katmanıdır, kullanmıyoruz demiyoruz çünkü karar vermiyor, yalnızca koordinat üretiyor. Bu ayrım bulanıklaştırılamaz.

## Komutlar

```bash
python main.py            # kamerayı açar, canlı form değerlendirmesi çalıştırır
python -m pytest          # geometry/ ve rules/ testleri — kamera gerektirmez
pip install -r requirements.txt   # bağımlılıkları kur (venv aktifken)
```

## Mimari — üç cümlede

1. Kamera → MediaPipe (sensör katmanı) → 33 landmark.
2. Landmark → geometri (saf fonksiyon) → açı → filtre → kural motoru (JSON'dan okur) → skor + mesaj.
3. Sunucu yok. Tüm işlem cihazda. Kurallar koda gömülmez, `exercises.json` ve `calibration-poses.json`'dan okunur.

Detay için `ARCHITECTURE.md`. Formüllerin türetilmesi için `personal-trainer-is-analizi.md` §5.

## Kesin kurallar (SOLID/DRY — ihlal etme)

1. **`src/geometry/` ve `src/rules/` hiçbir MediaPipe, OpenCV veya çizim (UI) tipini import etmez.** Girdi al, çıktı ver. Bu ikisi kamera/kütüphane olmadan, sadece NumPy ile test edilebilmeli.
2. **Açı formülü tek yerde yaşar.** `jointAngle` ve `verticalAngle` (dosya: `src/geometry/angles.py`) dışında hiçbir dosyada `np.arccos`, `math.acos` veya `math.atan2` çağrısı olmaz. Bir egzersize özel açı hesabı gerekiyorsa, yeni bir formül değil, mevcut fonksiyona yeni bir çağrı.
3. **Eşik değeri koda gömülmez.** Bir sayı (90, 0.15, 12°...) kodda görüyorsan bu bir hatadır — `exercises.json`'a taşı.
4. **Yeni egzersiz = yeni JSON girdisi, yeni kod değil.** `src/rules/engine.py`'yi değiştirmeden 6. egzersiz eklenebilmeli.
5. **Piksel dönüşümü zorunlu.** Açı fonksiyonlarına asla ham `landmark.x/y` (MediaPipe normalize [0,1]) verilmez — önce `to_pixel()`'den geçirilip piksel koordinatına çevrilir. Sebep: `ARCHITECTURE.md` §5.

## Yasaklar

- ❌ Model dosyası, sınıflandırıcı, eğitim döngüsü — hiçbir biçimde (MediaPipe'ın kendi hazır modeli sensör katmanıdır, istisnadır)
- ❌ Backend, API endpoint, veritabanı sunucusu (gerçek zamanlı akış için — bkz. `ARCHITECTURE.md` §7)
- ❌ `src/geometry/` veya `src/rules/` içinde `import mediapipe`, `import cv2` veya çizim kodu
- ❌ Aynı formülün iki yerde ayrı ayrı yazılması (bkz. DRY, `ARCHITECTURE.md` §4 — referans örnek: PostureGuard projesindeki tekrarlanan `atan2` hatası)
- ❌ Aynalama (mirroring) matematik katmanında — yalnızca çizim (OpenCV) katmanında yapılır
- ❌ Kapsam dışı özellik: kullanıcı hesabı, sosyal özellik, beslenme takibi, video kaydını sunucuya gönderme

## Kod stili

- Saf mantık katmanı (`geometry/`, `rules/`) tip ipuçlu (type hints) saf fonksiyonlar. Sınıf gerekmiyorsa kullanma.
- Fonksiyon imzaları küçük ve odaklı: her fonksiyon yalnızca ihtiyacı olan veriyi alır (bkz. ISP, `ARCHITECTURE.md` §3).
- Nokta/koordinat için kendi tipimiz `Point` kullanılır (MediaPipe'ın `NormalizedLandmark` tipi mantık katmanına sızmaz).

## Loglama kuralları

Amaç: hata çıktığında nerede ve neden olduğunu hızlıca bulmak. Python'ın standart `logging` modülü kullanılır — ekstra kütüphane yok.

1. **Tek yerde yapılandırılır.** Logger kurulumu (seviye, format, çıktı) yalnızca `src/logging_config.py`'de yapılır (DRY). Her modül `logging.getLogger(__name__)` ile kendi logger'ını alır — kurulumu tekrar etmez.
2. **Saf katmanlar (`src/geometry/`, `src/rules/`) LOG YAZMAZ.** Bu katmanlar sessizdir: girdi alır, değer döner. Loglamayı onları çağıran üst katman (`src/pose/`, `src/ui/`, `main.py`) yapar. Sebep: `geometry/` ve `rules/` kamerasız ve yan-etkisiz test edilebilmeli; log bir yan etkidir, saflığı bozar. Bir açının neden hesaplandığını loglamak isteyen taraf, fonksiyonu çağırıp dönen değeri kendi loglar.
3. **`print()` kullanılmaz.** Hata ayıklama dahil her çıktı `logger` üzerinden gider. `print` yalnızca kullanıcıya gösterilen son ekran metni için (OpenCV `putText`) değil — o zaten çizim, log değil.
4. **Seviyeler:**
   - `DEBUG` — açı değerleri, ham landmark güveni (geliştirme sırasında, üst katmanda)
   - `INFO` — anlamlı olaylar: tekrar sayıldı, egzersiz değişti, kalibrasyon tamam
   - `WARNING` — kurtarılabilir sorun: landmark görünmüyor (düşük visibility), kare atlandı
   - `ERROR` — işlemi durduran sorun: kamera açılamadı, model dosyası bulunamadı, JSON okunamadı
5. **Her `except` bloğu loglar.** Hatayı sessizce yutma. En azından `logger.error(...)` ile sebebini yaz.

## Dosya haritası

| Dosya | İçerik |
|---|---|
| `personal-trainer-is-analizi.md` | Ana spesifikasyon — tüm formüller, kural tabloları, veri modeli |
| `exercises.json` | 5 egzersizin kuralları (koddan okunur, düzenlenmez) |
| `calibration-poses.json` | 3 statik kalibrasyon pozu — Gün 1'de koordinat sistemi doğrulaması |
| `gelistirici-devir-teslim.md` | Görev sırası, hazır agent prompt'ları, tuzaklar |
| `gun-1-plani.md` | Blok blok Gün 1 görevleri ve kabul kriterleri |
| `ARCHITECTURE.md` | SOLID/DRY uygulanışı, katman diyagramı, genişletme stratejisi |

## Bir görev alınca

1. Görev `exercises.json`'da bir eşik değiştirmekse → dosyayı düzenle, kod dokunma.
2. Görev yeni bir fonksiyon yazmaksa → önce `personal-trainer-is-analizi.md` §5'te ilgili formül var mı bak, varsa aynen uygula, yoksa sor.
3. Görev bir egzersiz eklemekse → `exercises.json`'a yeni girdi, `src/rules/engine.py`'ye dokunma. Dokunman gerekiyorsa bu bir tasarım ihlalidir, durup bildir.
4. Her yeni fonksiyon için birim test yaz — `geometry/` ve `rules/` için kamerasız, pytest.
5. Belirsizlik varsa varsayım yapıp devam etme; hangi kısımda belirsiz olduğunu tek cümlede yaz ve sor.