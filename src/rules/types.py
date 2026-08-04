"""
Kural veri modelleri — exercises.json'daki şemanın Python karşılığı.
Saf veri tipleri. Motor (engine.py) bunları kullanır, egzersize özel
mantık burada YOK — sadece yapı tanımı.
"""
from dataclasses import dataclass
from enum import Enum


class CheckType(Enum):
    JOINT = "JOINT"        # 3 nokta, joint_angle kullanır
    VERTICAL = "VERTICAL"  # 2 nokta, vertical_angle kullanır


@dataclass
class AngleCheck:
    type: CheckType
    points: list[str]
    min_angle: float
    max_angle: float
    message: str


@dataclass
class Exercise:
    name: str
    checks: list[AngleCheck]