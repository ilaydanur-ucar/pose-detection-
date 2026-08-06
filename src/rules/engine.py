"""
Kural motoru — TEK genel değerlendirme fonksiyonu.
Egzersize özel if/else YOK (CLAUDE.md kural 4). Her egzersiz aynı
evaluate() ile değerlendirilir; fark sadece exercises.json'daki veridir.

Saf katman: MediaPipe/OpenCV import etmez, log yazmaz.
"""
from src.rules.types import Exercise, AngleCheck, CheckType
from src.geometry.angles import joint_angle, vertical_angle, normalized_distance, horizontal_elevation
from src.geometry.point import Point

# Strategy pattern: how each CheckType turns into a number (angle/ratio)
# lives here, in a single dict (OCP — ARCHITECTURE.md §3). Adding a new
# check type never requires changing evaluate(), only a line here.
# Point-count contract per type: JOINT=3, VERTICAL=2, DISTANCE=4, ELEVATION=2
# (DISTANCE: pts[0]-pts[1] measured, pts[2]-pts[3] reference for scaling).
_CHECK_HANDLERS = {
    CheckType.JOINT: lambda pts: joint_angle(pts[0], pts[1], pts[2]),
    CheckType.VERTICAL: lambda pts: vertical_angle(pts[0], pts[1]),
    CheckType.DISTANCE: lambda pts: normalized_distance(pts[0], pts[1], pts[2], pts[3]),
    CheckType.ELEVATION: lambda pts: horizontal_elevation(pts[0], pts[1]),
}


def compute_value(check: AngleCheck, points: dict[str, Point]) -> float:
    """
    Bir check'in ham sayısal değerini (açı/oran) hesaplar, doğru/yanlış
    yorumu yapmaz. evaluate() bunu içeride kullanır; main.py da hesaplanan
    değeri EKRANDA/LOGDA GÖRMEK isterse aynı fonksiyonu çağırıp kendi loglar
    (CLAUDE.md loglama kuralı 2 — bu dosya sessiz kalır, log çağıran tarafta).
    """
    pts = [points[name] for name in check.points]
    return _CHECK_HANDLERS[check.type](pts)


def evaluate(points: dict[str, Point], exercise: Exercise) -> list[str]:
    """
    points: {"left_hip": Point(...), "left_knee": Point(...), ...}
    Döner: ihlal edilen kuralların mesaj listesi. Boşsa -> poz doğru.
    """
    violations = []

    for check in exercise.checks:
        angle = compute_value(check, points)

        if angle < check.min_angle:
            violations.append(check.low_message or check.message)
        elif angle > check.max_angle:
            violations.append(check.high_message or check.message)

    return violations