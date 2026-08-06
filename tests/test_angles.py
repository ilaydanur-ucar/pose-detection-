"""
geometry/angles.py testleri — kamerasız, saf fonksiyon testleri.
MediaPipe/OpenCV gerektirmez (CLAUDE.md: geometry/ testleri kamerasız).
"""
from src.geometry.angles import joint_angle, vertical_angle, distance, normalized_distance
from src.geometry.point import Point


class TestJointAngle:
    def test_right_angle(self):
        # a=(0,10) b=(0,0) c=(10,0) -> B'de dik acı
        a, b, c = Point(0, 10), Point(0, 0), Point(10, 0)
        assert joint_angle(a, b, c) == 90.0

    def test_straight_line(self):
        # a, b, c aynı doğrultuda -> 180 derece (kol tam düz)
        a, b, c = Point(0, 0), Point(10, 0), Point(20, 0)
        assert joint_angle(a, b, c) == 180.0

    def test_folded_back(self):
        # c, a ile aynı noktaya katlanmış -> 0 derece
        a, b, c = Point(10, 0), Point(0, 0), Point(10, 0)
        assert joint_angle(a, b, c) == 0.0

    def test_zero_length_vector_returns_zero(self):
        # b, a ile çakışıyor -> norm=0, sıfıra bölme yerine 0.0 dönmeli
        a, b, c = Point(5, 5), Point(5, 5), Point(10, 0)
        assert joint_angle(a, b, c) == 0.0


class TestVerticalAngle:
    def test_upright_line_is_zero_degrees(self):
        # tam dikey çizgi (x sabit) -> 0 derece
        assert vertical_angle(Point(0, 0), Point(0, 10)) == 0.0

    def test_horizontal_line_is_ninety_degrees(self):
        # tam yatay çizgi (y sabit) -> 90 derece
        assert vertical_angle(Point(0, 0), Point(10, 0)) == 90.0

    def test_direction_independent_uses_absolute_angle(self):
        # sağa ve sola aynı miktarda yatan çizgiler aynı sapma açısını vermeli
        right = vertical_angle(Point(0, 0), Point(10, 10))
        left = vertical_angle(Point(0, 0), Point(-10, 10))
        assert right == left

    def test_target_above_source_is_still_near_zero(self):
        # REGRESYON: hedef kaynağın ÜSTÜNDEYKEN (y küçük, örn. omzun üstüne
        # kalkmış bir bilek) de dikey çizgi 0'a yakın olmalı. Bug: eskiden
        # dy negatifken atan2 işareti dönüp ~180° veriyordu.
        angle = vertical_angle(Point(0, 100), Point(1, 0))  # neredeyse dikey, hedef üstte
        assert angle < 10.0

    def test_above_and_below_give_same_angle_for_same_tilt(self):
        # Aynı miktarda yatay sapma, hedef ister altta ister üstte olsun
        # aynı dikeyden-sapma açısını vermeli (yön farketmemeli).
        below = vertical_angle(Point(0, 0), Point(5, 10))   # hedef altta
        above = vertical_angle(Point(0, 0), Point(5, -10))  # hedef üstte
        assert below == above


class TestDistance:
    def test_three_four_five_triangle(self):
        assert distance(Point(0, 0), Point(3, 4)) == 5.0

    def test_same_point_is_zero(self):
        assert distance(Point(7, 7), Point(7, 7)) == 0.0

    def test_is_symmetric(self):
        a, b = Point(1, 2), Point(9, 20)
        assert distance(a, b) == distance(b, a)


class TestNormalizedDistance:
    def test_ratio_scales_by_reference(self):
        # a-b = 5px, reference ref_a-ref_b = 10px -> ratio 0.5
        a, b = Point(0, 0), Point(0, 5)
        ref_a, ref_b = Point(0, 0), Point(10, 0)
        assert normalized_distance(a, b, ref_a, ref_b) == 0.5

    def test_ratio_one_when_equal_to_reference(self):
        a, b = Point(0, 0), Point(0, 10)
        ref_a, ref_b = Point(0, 0), Point(10, 0)
        assert normalized_distance(a, b, ref_a, ref_b) == 1.0

    def test_zero_reference_distance_returns_zero(self):
        # ref_a == ref_b -> reference distance is 0, would divide by zero
        a, b = Point(0, 0), Point(0, 5)
        ref_a = ref_b = Point(3, 3)
        assert normalized_distance(a, b, ref_a, ref_b) == 0.0
