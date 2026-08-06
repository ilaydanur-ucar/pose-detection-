"""
Kural motoru — TEK genel değerlendirme fonksiyonu.
Egzersize özel if/else YOK (CLAUDE.md kural 4). Her egzersiz aynı
evaluate() ile değerlendirilir; fark sadece exercises.json'daki veridir.

Saf katman: MediaPipe/OpenCV import etmez, log yazmaz.
"""
from src.rules.types import Exercise, CheckType
from src.geometry.angles import joint_angle, vertical_angle, normalized_distance
from src.geometry.point import Point

# Strategy pattern: how each CheckType turns into a number (angle/ratio)
# lives here, in a single dict (OCP — ARCHITECTURE.md §3). Adding a new
# check type never requires changing evaluate(), only a line here.
# Point-count contract per type: JOINT=3, VERTICAL=2, DISTANCE=4
# (DISTANCE: pts[0]-pts[1] measured, pts[2]-pts[3] reference for scaling).
_CHECK_HANDLERS = {
    CheckType.JOINT: lambda pts: joint_angle(pts[0], pts[1], pts[2]),
    CheckType.VERTICAL: lambda pts: vertical_angle(pts[0], pts[1]),
    CheckType.DISTANCE: lambda pts: normalized_distance(pts[0], pts[1], pts[2], pts[3]),
}


def evaluate(points: dict[str, Point], exercise: Exercise) -> list[str]:
    """
    points: {"left_hip": Point(...), "left_knee": Point(...), ...}
    Döner: ihlal edilen kuralların mesaj listesi. Boşsa -> poz doğru.
    """
    violations = []

    for check in exercise.checks:
        pts = [points[name] for name in check.points]
        angle = _CHECK_HANDLERS[check.type](pts)

        if not (check.min_angle <= angle <= check.max_angle):
            violations.append(check.message)

    return violations