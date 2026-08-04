"""Point tipi — MediaPipe'ın NormalizedLandmark tipinden bağımsız (x, y) piksel koordinatı ve to_pixel() dönüşümü."""
"""
Koordinat noktası — geometri katmanının temel veri tipi.


Üst katman (pose/) MediaPipe landmark'ını bu sade Point'e çevirip öyle verir.
Böylece poz kütüphanesi değişse bile geometry/ kodu hiç dokunulmadan kalır.

Bu katman SAF ve SESSİZDİR — log yazmaz, kütüphane import etmez, sadece veri tutar.
"""
from dataclasses import dataclass 

@dataclass  #Sadece veri tutan sınıf, __init__'i otomatik yazıyor.
class Point:
    x: float #piksel cinsinden yatay konum
    y: float #piksel cinsinden dikey konum
