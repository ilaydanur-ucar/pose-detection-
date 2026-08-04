"""
Kural motoru — TEK genel değerlendirme fonksiyonu.
Egzersize özel if/else YOK (CLAUDE.md kural 4). Her egzersiz aynı
evaluate() ile değerlendirilir; fark sadece exercises.json'daki veridir.

Saf katman: MediaPipe/OpenCV import etmez, log yazmaz.
"""
from src.rules.types import Exercise, CheckType
from src.geometry.angles import joint_angle, vertical_angle
from src.geometry.point import Point


def evaluate(points: dict[str, Point], exercise: Exercise) -> list[str]:
    """
    points: {"left_hip": Point(...), "left_knee": Point(...), ...}
    Döner: ihlal edilen kuralların mesaj listesi. Boşsa -> poz doğru.
    """
    violations = []

    for check in exercise.checks:
        if check.type == CheckType.JOINT:
            a, b, c = (points[name] for name in check.points)
            angle = joint_angle(a, b, c)
        else:  # VERTICAL
            a, b = (points[name] for name in check.points)
            angle = vertical_angle(a, b)

        if not (check.min_angle <= angle <= check.max_angle):
            violations.append(check.message)

    return violations