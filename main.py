"""
Giriş noktası — kol açısı ısınma testi + Squat kontrolü.

Amaç: boru hattının (kamera -> MediaPipe -> Point -> geometry -> rules -> ekran)
uçtan uca çalıştığını doğrulamak. Kol açısı üstte, Squat kontrolü altta.

Çalıştır: python main.py   |   Çık: pencere seçiliyken 'q'
"""
import json
import logging
import cv2

from src.logging_config import setup_logging
from src.pose.processor import (
    PoseProcessor,
    LEFT_SHOULDER, LEFT_ELBOW, LEFT_WRIST,
    LEFT_HIP, LEFT_KNEE, LEFT_ANKLE,
    RIGHT_SHOULDER, RIGHT_ELBOW, RIGHT_WRIST,
)
from src.geometry.angles import joint_angle
from src.geometry.point import Point
from src.rules.types import Exercise, AngleCheck, CheckType
from src.rules.engine import evaluate

setup_logging(level=logging.DEBUG)  # GEÇİCİ — teşhis bitince INFO'ya geri al
logger = logging.getLogger(__name__)


def load_exercise(json_path: str, key: str) -> Exercise:
    """exercises.json'dan bir egzersizi okuyup Exercise nesnesine çevirir."""
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)[key]
    checks = [
        AngleCheck(
            type=CheckType(c["type"]),
            points=c["points"],
            min_angle=c["min_angle"],
            max_angle=c["max_angle"],
            message=c["message"],
        )
        for c in data["checks"]
    ]
    return Exercise(name=data["name"], checks=checks)


# Yazı, nokta ve çizgi çizimi için yardımcı fonksiyonlar (DRY — aynı
# "siyah kontur + renkli üst katman" tekniği hepsinde tekrar kullanılıyor,
# açık/çizgili zeminde bile okunur olsun diye).

def draw_text(frame, text, pos, color=(0, 255, 0)):
    """Okunaklı yazı: önce kalın siyah kontur, sonra üstüne ince renkli yazı."""
    cv2.putText(frame, text, pos, cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 0), 5)
    cv2.putText(frame, text, pos, cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)


def draw_point(frame, p, color=(0, 255, 0)):
    """Okunaklı nokta: siyah kenarlıklı, üstünde küçük renkli daire."""
    cv2.circle(frame, (int(p.x), int(p.y)), 8, (0, 0, 0), -1)
    cv2.circle(frame, (int(p.x), int(p.y)), 6, color, -1)


def draw_line(frame, p1, p2, color=(0, 255, 0)):
    """İki nokta arasına kalın çizgi çizer — kol/gövde 'iskeleti' için."""
    pt1 = (int(p1.x), int(p1.y))
    pt2 = (int(p2.x), int(p2.y))
    cv2.line(frame, pt1, pt2, (0, 0, 0), 6)      # siyah kontur (kalın)
    cv2.line(frame, pt1, pt2, color, 3)          # renkli üst katman (ince)


def mirror_point(p: Point, frame_width: int) -> Point:
    """
    Bir noktayı yatayda aynalar. SADECE çizimden önce, gösterim amacıyla
    kullanılır (CLAUDE.md: aynalama yalnızca çizim/OpenCV katmanında olur,
    geometry/'ye asla sızmaz). MediaPipe'a HAM/aynalanmamış kare verildiği
    için açı hesapları bu fonksiyondan önce, orijinal noktalarla yapılmalı.
    """
    return Point(x=frame_width - p.x, y=p.y)


def draw_arm(frame, processor, landmarks, width, height,
             shoulder_i, elbow_i, wrist_i, label, color, fallback_pos):
    """
    Bir kolu (SOL ya da SAĞ) bağımsız olarak değerlendirip çizer.
    DRY: iki taraf için de aynı mantık, sadece landmark index'leri farklı.
    """
    visible = all(processor.is_visible(landmarks, i) for i in (shoulder_i, elbow_i, wrist_i))
    if not visible:
        logger.debug("%s KOL CIZILMIYOR: gorunur degil", label)
        draw_text(frame, f"{label} kol net gorunmuyor", fallback_pos, color=(0, 0, 255))
        return

    shoulder = processor.get_point(landmarks, shoulder_i, width, height)
    elbow = processor.get_point(landmarks, elbow_i, width, height)
    wrist = processor.get_point(landmarks, wrist_i, width, height)

    angle = joint_angle(shoulder, elbow, wrist)
    logger.debug(
        "%s KOL CIZILIYOR: shoulder=(%.0f,%.0f) elbow=(%.0f,%.0f) wrist=(%.0f,%.0f) angle=%.0f",
        label, shoulder.x, shoulder.y, elbow.x, elbow.y, wrist.x, wrist.y, angle,
    )

    # Çizimden hemen önce aynala — frame de flip edilmiş durumda
    shoulder_d = mirror_point(shoulder, width)
    elbow_d = mirror_point(elbow, width)
    wrist_d = mirror_point(wrist, width)

    draw_line(frame, shoulder_d, elbow_d, color)
    draw_line(frame, elbow_d, wrist_d, color)
    draw_text(frame, f"{label} {angle:.0f} derece", (int(elbow_d.x), int(elbow_d.y) - 20), color)
    for p in (shoulder_d, elbow_d, wrist_d):
        draw_point(frame, p, color)


def main():
    processor = PoseProcessor()  # processor.py içinde model_complexity=2 var (daha doğru koordinat)
    squat = load_exercise("exercises.json", "squat")

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        logger.error("Kamera açılamadı")
        return

    logger.info("Kamera açıldı, test başlıyor (çıkmak için 'q')")

    while True:
        ok, frame = cap.read()
        if not ok:
            logger.warning("Kare okunamadı")
            break

        # KÖK NEDEN BULUNDU: flip'i MediaPipe'tan ÖNCE yapmak, modelin anatomik
        # sol/sağ etiketlerini tutarlı biçimde ters çeviriyordu (aynalanmış bir
        # bedenin görsel anatomisi model için ters okunuyor). Çözüm: MediaPipe'a
        # HAM kareyi ver (doğru etiketleme), flip'i sadece gösterim için EN SONA,
        # noktalar hesaplandıktan sonra uygula (mirror_point ile).

        # MediaPipe RGB bekler, OpenCV BGR verir -> çevir
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        height, width = frame.shape[:2]

        landmarks = processor.process(frame_rgb, width, height)

        frame = cv2.flip(frame, 1)   # yatay ayna düzeltmesi — SADECE gösterim için

        if landmarks is not None:
            # GEÇİCİ TEŞHİS — sol/sağ karışması + neden hiç çizilmediğini bulmak için.
            # x_px artık HAM (aynalanmamış) kareye göre — SOL landmark'ın x'i küçükse
            # (ekranın sol tarafı, flip'ten önceki ham görüntüde) etiketleme doğrudur.
            for name, idx in [
                ("SOL  omuz ", LEFT_SHOULDER), ("SOL  dirsek", LEFT_ELBOW), ("SOL  bilek ", LEFT_WRIST),
                ("SAG  omuz ", RIGHT_SHOULDER), ("SAG  dirsek", RIGHT_ELBOW), ("SAG  bilek ", RIGHT_WRIST),
            ]:
                lm = landmarks.landmark[idx]
                px = lm.x * width
                taraf = "sol-yarida" if px < width / 2 else "sag-yarida"
                logger.debug("%s idx=%2d  vis=%.2f  x_px=%6.1f (%s)", name, idx, lm.visibility, px, taraf)

            # --- Kol açısı (ısınma testi) — SOL ve SAĞ bağımsız, ikisi de çizilir ---
            draw_arm(frame, processor, landmarks, width, height,
                     LEFT_SHOULDER, LEFT_ELBOW, LEFT_WRIST,
                     "SOL", (0, 255, 0), (20, 70))
            draw_arm(frame, processor, landmarks, width, height,
                     RIGHT_SHOULDER, RIGHT_ELBOW, RIGHT_WRIST,
                     "SAG", (255, 165, 0), (20, 100))

            # --- Squat kontrolü ---
            squat_visible = all(
                processor.is_visible(landmarks, i)
                for i in (LEFT_HIP, LEFT_KNEE, LEFT_ANKLE)
            )
            if squat_visible:
                points = {
                    "left_hip": processor.get_point(landmarks, LEFT_HIP, width, height),
                    "left_knee": processor.get_point(landmarks, LEFT_KNEE, width, height),
                    "left_ankle": processor.get_point(landmarks, LEFT_ANKLE, width, height),
                }
                violations = evaluate(points, squat)

                # Çizimden hemen önce aynala — frame de flip edilmiş durumda
                points_d = {name: mirror_point(p, width) for name, p in points.items()}
                draw_line(frame, points_d["left_hip"], points_d["left_knee"])
                draw_line(frame, points_d["left_knee"], points_d["left_ankle"])
                for p in points_d.values():
                    draw_point(frame, p)

                if violations:
                    logger.debug("Squat ihlalleri: %s", violations)
                    draw_text(frame, violations[0], (20, 140), color=(0, 0, 255))
                else:
                    draw_text(frame, "Squat DOGRU", (20, 140), color=(0, 255, 0))
            else:
                draw_text(frame, "Bacak net gorunmuyor", (20, 170), color=(0, 0, 255))
        else:
            draw_text(frame, "Vucut bulunamadi", (20, 40), color=(0, 0, 255))

        cv2.imshow("FormCheck", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    logger.info("Kapatıldı")


if __name__ == "__main__":
    main()