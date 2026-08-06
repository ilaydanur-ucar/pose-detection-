"""
Açı geometrisi — projenin karar matematiğinin kalbi.

Tüm açı hesapları YALNIZCA burada yaşar (DRY / CLAUDE.md kuralı 2).
Başka hiçbir dosyada np.arccos / math.atan2 çağrılmaz.

Bu katman SAF ve SESSİZDİR: MediaPipe/OpenCV import etmez, log yazmaz.
Girdi olarak kendi Point tipimizi alır, derece (float) döner.
Kamerasız, sadece NumPy ile test edilebilir.
"""
import numpy as np
from src.geometry.point import Point 


def joint_angle(a: Point, b: Point, c: Point) -> float: #type hint ile yazılmış, IDE'ler için faydalı
    """
    B köşesindeki açıyı derece olarak döndürür (2B).

    Örn: a=omuz, b=dirsek, c=bilek -> dirsekteki açı (kol ne kadar bükük).
    Kol düz ~180°, dik bükülü ~90°.
    """
    # B'den çıkan iki vektör (B köşe olduğu için ikisi de B'den başlar)
   
    ba=np.array([a.x-b.x, a.y-b.y])
    bc=np.array([c.x-b.x, c.y-b.y])

    # nokta çarpımı (dot product) — iki vektör ne kadar aynı yöne bakıyor
    dot = np.dot(ba, bc)   #dot = (ba.x × bc.x) + (ba.y × bc.y) işlemini dot ile np yapıyor.

    # vektör uzunlukları (magnitude)
    norm = np.linalg.norm(ba) * np.linalg.norm(bc) #linear algebra norm fonksiyonu ile vektör uzunluğu hesaplanıyor.

    # sıfıra bölme koruması: iki nokta çakışırsa norm=0 olur
    if norm == 0:
        return 0.0

    # cos(açı) = dot / (|ba| * |bc|)
    cos_angle = dot / norm

    # kayan nokta hatası cos'u [-1, 1] dışına taşırabilir -> arccos NaN verir
    # clip ile güvenli aralığa sıkıştırıyoruz 
    cos_angle = np.clip(cos_angle, -1.0, 1.0)

    # radyan -> derece 
    return float(np.degrees(np.arccos(cos_angle)))


def vertical_angle(from_point: Point, to_point: Point) -> float:
    """
    from -> to çizgisinin DİKEY EKSENDEN sapma açısını derece olarak döndürür.
    Yön (hedef kaynağın altında mı üstünde mi) fark etmez — sadece eksene
    göre sapma ölçülür.

    0°   = tam dikey (çizgi yukarı-aşağı, örn. dimdik duran gövde, ya da
           omzun üstüne kalkmış bir bilek)
    90°  = tam yatay (çizgi sağa-sola, örn. yere paralel kol)

    Örn: omuz->kalça çizgisi ile gövde eğimini, omuz->bilek ile kolun ne
    kadar kalktığını ölçmek için kullanılır.
    """
    dx = to_point.x - from_point.x
    dy = to_point.y - from_point.y

    # abs(dx), abs(dy): EKSENDEN sapmayı ölçüyoruz, YÖNDEN değil — hedef
    # kaynağın altında da üstünde de olsa "dikey" aynı şekilde 0° olmalı.
    # (dy'nin işaretini atmadan atan2(dx, dy) kullanmak, hedef kaynağın
    # ÜSTÜNDEYKEN [dy<0] açıyı ~180°'ye kaydırıyordu — "dikey" neredeyse
    # "ters dikey" gibi ölçülüyordu. Örn: kol düz yukarı kalkmışken bile
    # 170-180° dönüyordu, oysa gerçek sapma ~10°'ydi.)
    angle_rad = np.arctan2(abs(dx), abs(dy))

    return float(np.degrees(angle_rad))


def horizontal_elevation(from_point: Point, to_point: Point) -> float:
    """
    from -> to çizgisinin YATAYA göre YÖNLÜ (signed) yükseklik açısı, [-90, 90].

    +90° = to_point tam yukarıda (örn. bilek omzun üstünde, overhead)
      0° = tam yatay (örn. T-pose'ta kol)
    -90° = to_point tam aşağıda

    vertical_angle'dan farkı: bu fonksiyon YÖNÜ atmıyor (abs almıyor).
    Hedefin yatayın üstünde mi altında mı olduğunu ayırt etmen gerekiyorsa
    (örn. T-pose'ta "kolunu indir" ile "kolunu kaldır" farklı mesajlarsa)
    vertical_angle yetmez, çünkü o [0,90] aralığına sıkıştırıp yön bilgisini
    atıyor — bunun yerine bu fonksiyon kullanılır.
    """
    dx = to_point.x - from_point.x
    dy = to_point.y - from_point.y  # piksel: aşağı +, yukarı -

    # -dy: yukarıyı pozitif yapar (piksel ekseni ters, doğal "yükseklik"
    # hissi için çeviriyoruz). abs(dx): sağ/sol kol farkı sonucu etkilemesin,
    # sadece yükseklik yönü (yukarı/aşağı) korunsun.
    angle_rad = np.arctan2(-dy, abs(dx))

    return float(np.degrees(angle_rad))


def distance(a: Point, b: Point) -> float:
    """Euclidean distance between two points (pixels)."""
    return float(np.linalg.norm([a.x - b.x, a.y - b.y]))


def normalized_distance(a: Point, b: Point, ref_a: Point, ref_b: Point) -> float:
    """Distance A-B scaled by reference distance ref_a-ref_b. Gives a
    consistent value regardless of how close/far the person is from the
    camera (e.g. foot-to-knee distance scaled by shoulder width)."""
    ref = distance(ref_a, ref_b)
    return distance(a, b) / ref if ref else 0.0