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
    from -> to çizgisinin DİKEY eksenden sapma açısını derece olarak döndürür.

    0°   = tam dikey (çizgi yukarı-aşağı, örn. dimdik duran gövde)
    90°  = tam yatay (çizgi sağa-sola, örn. yere paralel kol)

    Örn: omuz->kalça çizgisi ile plank'ta gövde eğimini ölçmek için kullanılır.
    """
    dx = to_point.x - from_point.x
    dy = to_point.y - from_point.y

    # atan2(dx, dy): dy'yi referans (dikey eksen) alarak dx sapmasının açısı
    # dy'yi ilk argüman değil ikinci argüman yapmak, 0°'yi "dikey" tanımlar
    angle_rad = np.arctan2(dx, dy) 	#iki koordinattan, güvenli ve yön-bilgili şekilde açı üretir 

    return float(np.degrees(np.abs(angle_rad)))