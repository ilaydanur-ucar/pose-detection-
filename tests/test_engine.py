"""
rules/engine.py testleri — kamerasız, saf fonksiyon testleri.
MediaPipe/OpenCV gerektirmez (CLAUDE.md: rules/ testleri kamerasız).
"""
from src.geometry.point import Point
from src.rules.types import CheckType, AngleCheck, Exercise
from src.rules.engine import evaluate, compute_value, _CHECK_HANDLERS


def make_exercise(check_type, points, min_angle, max_angle, message="ihlal"):
    return Exercise(
        name="test",
        checks=[AngleCheck(type=check_type, points=points, min_angle=min_angle, max_angle=max_angle, message=message)],
    )


class TestJointCheck:
    def test_within_range_no_violation(self):
        ex = make_exercise(CheckType.JOINT, ["a", "b", "c"], 80, 100)
        pts = {"a": Point(0, 10), "b": Point(0, 0), "c": Point(10, 0)}  # 90 derece
        assert evaluate(pts, ex) == []

    def test_out_of_range_returns_message(self):
        ex = make_exercise(CheckType.JOINT, ["a", "b", "c"], 80, 100, message="dizini buk")
        pts = {"a": Point(0, 0), "b": Point(10, 0), "c": Point(20, 0)}  # 180 derece
        assert evaluate(pts, ex) == ["dizini buk"]


class TestComputeValue:
    """compute_value() evaluate()'in icinde kullandigi ayni hesaplamayi
    disariya (ornegin main.py'nin debug loglamasi icin) acar."""

    def test_returns_same_number_evaluate_uses_internally(self):
        check = AngleCheck(type=CheckType.JOINT, points=["a", "b", "c"], min_angle=80, max_angle=100, message="x")
        pts = {"a": Point(0, 10), "b": Point(0, 0), "c": Point(10, 0)}
        assert compute_value(check, pts) == 90.0

    def test_does_not_judge_pass_fail_just_returns_the_number(self):
        # 180 derece, esikleri (80-100) asiyor ama compute_value bunu
        # yorumlamiyor -- ham degeri donuyor, evaluate() karar veriyor.
        check = AngleCheck(type=CheckType.JOINT, points=["a", "b", "c"], min_angle=80, max_angle=100, message="x")
        pts = {"a": Point(0, 0), "b": Point(10, 0), "c": Point(20, 0)}
        assert compute_value(check, pts) == 180.0


class TestVerticalCheck:
    def test_within_range_no_violation(self):
        ex = make_exercise(CheckType.VERTICAL, ["a", "b"], 0, 10)
        pts = {"a": Point(0, 0), "b": Point(0, 10)}  # 0 derece, dikey
        assert evaluate(pts, ex) == []

    def test_out_of_range_returns_message(self):
        ex = make_exercise(CheckType.VERTICAL, ["a", "b"], 0, 10, message="govdeni dogrult")
        pts = {"a": Point(0, 0), "b": Point(10, 0)}  # 90 derece, yatay
        assert evaluate(pts, ex) == ["govdeni dogrult"]


class TestDistanceCheck:
    def test_within_range_no_violation(self):
        # a-b = 5px, reference c-d = 10px -> ratio 0.5, within [0, 1]
        ex = make_exercise(CheckType.DISTANCE, ["a", "b", "c", "d"], 0, 1)
        pts = {"a": Point(0, 0), "b": Point(0, 5), "c": Point(0, 0), "d": Point(10, 0)}
        assert evaluate(pts, ex) == []

    def test_out_of_range_returns_message(self):
        # a-b = 5px, reference c-d = 10px -> ratio 0.5 > max 0.4
        ex = make_exercise(CheckType.DISTANCE, ["a", "b", "c", "d"], 0, 0.4, message="too close")
        pts = {"a": Point(0, 0), "b": Point(0, 5), "c": Point(0, 0), "d": Point(10, 0)}
        assert evaluate(pts, ex) == ["too close"]


class TestElevationCheck:
    """T-pose gibi 'yataya göre yön belirtmeli' kontroller için (ELEVATION
    CheckType) — vertical_angle'ın çözemediği yön-ayrımı gereken durum."""

    def _tpose_arm_check(self):
        return AngleCheck(
            type=CheckType.ELEVATION, points=["shoulder", "wrist"],
            min_angle=-15, max_angle=15, message="adjust",
            low_message="raise it", high_message="lower it",
        )

    def test_horizontal_within_range_no_violation(self):
        ex = Exercise(name="t", checks=[self._tpose_arm_check()])
        pts = {"shoulder": Point(0, 0), "wrist": Point(50, 0)}  # tam yatay
        assert evaluate(pts, ex) == []

    def test_arm_too_low_triggers_low_message(self):
        ex = Exercise(name="t", checks=[self._tpose_arm_check()])
        pts = {"shoulder": Point(0, 0), "wrist": Point(50, 40)}  # bilek asagida
        assert evaluate(pts, ex) == ["raise it"]

    def test_arm_too_high_triggers_high_message(self):
        # eski VERTICAL tabanli check'te bu durum HICBIR ZAMAN yakalanamiyordu
        # (yon bilgisi abs() ile atiliyordu) -- bu regresyon testi o bug'i kilitliyor.
        ex = Exercise(name="t", checks=[self._tpose_arm_check()])
        pts = {"shoulder": Point(0, 0), "wrist": Point(50, -40)}  # bilek yukarida
        assert evaluate(pts, ex) == ["lower it"]


class TestMultipleChecks:
    def test_collects_all_violations_in_order(self):
        ex = Exercise(
            name="test",
            checks=[
                AngleCheck(type=CheckType.JOINT, points=["a", "b", "c"], min_angle=170, max_angle=180, message="joint fail"),
                AngleCheck(type=CheckType.DISTANCE, points=["a", "c", "d", "e"], min_angle=0, max_angle=1, message="distance fail"),
            ],
        )
        # joint(a,b,c)=90 (fail); distance a-c=~14.1, reference d-e=10 -> ratio~1.41 (fail)
        pts = {"a": Point(0, 10), "b": Point(0, 0), "c": Point(10, 0), "d": Point(0, 0), "e": Point(10, 0)}
        assert evaluate(pts, ex) == ["joint fail", "distance fail"]

    def test_no_violations_when_all_checks_pass(self):
        ex = Exercise(
            name="test",
            checks=[
                AngleCheck(type=CheckType.JOINT, points=["a", "b", "c"], min_angle=170, max_angle=180, message="joint fail"),
                AngleCheck(type=CheckType.DISTANCE, points=["a", "c", "d", "e"], min_angle=0, max_angle=100, message="distance fail"),
            ],
        )
        # joint(a,b,c)=180 (ok); distance a-c=20, reference d-e=10 -> ratio=2 (ok, within 0-100)
        pts = {"a": Point(0, 0), "b": Point(10, 0), "c": Point(20, 0), "d": Point(0, 0), "e": Point(10, 0)}
        assert evaluate(pts, ex) == []


class TestCheckHandlersRegistry:
    def test_every_check_type_has_a_handler(self):
        # Yeni bir CheckType eklenip _CHECK_HANDLERS'a kaydedilmezse burada
        # KeyError yerine anlaşılır bir assertion hatası alınsın diye.
        for check_type in CheckType:
            assert check_type in _CHECK_HANDLERS


class TestDirectionalMessages:
    """low_message/high_message: which side of the range was violated picks
    the message; falls back to `message` when the directional one is unset."""

    def _check(self, min_angle, max_angle, low_message=None, high_message=None):
        return AngleCheck(
            type=CheckType.VERTICAL, points=["a", "b"],
            min_angle=min_angle, max_angle=max_angle, message="generic fallback",
            low_message=low_message, high_message=high_message,
        )

    def test_below_min_uses_low_message(self):
        # vertical_angle(a,b) = 0 (straight up) -> below min=80
        ex = Exercise(name="t", checks=[self._check(80, 100, low_message="too low")])
        pts = {"a": Point(0, 0), "b": Point(0, 10)}
        assert evaluate(pts, ex) == ["too low"]

    def test_above_max_uses_high_message(self):
        # vertical_angle is undirected, range [0,90] -> atan2(10,4) ~= 68.2, above max=50
        ex = Exercise(name="t", checks=[self._check(10, 50, high_message="too high")])
        pts = {"a": Point(0, 0), "b": Point(10, -4)}
        assert evaluate(pts, ex) == ["too high"]

    def test_falls_back_to_message_when_directional_unset(self):
        ex = Exercise(name="t", checks=[self._check(80, 100)])  # no low/high_message
        pts = {"a": Point(0, 0), "b": Point(0, 10)}  # below min
        assert evaluate(pts, ex) == ["generic fallback"]

    def test_within_range_no_violation_regardless_of_directional_messages(self):
        ex = Exercise(name="t", checks=[self._check(80, 100, low_message="x", high_message="y")])
        pts = {"a": Point(0, 0), "b": Point(10, 0)}  # 90 degrees, within range
        assert evaluate(pts, ex) == []
