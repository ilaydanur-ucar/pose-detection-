"""
MediaPipe poz işleyici — SENSÖR KATMANI.
...
"""
import logging
import mediapipe as mp
from src.geometry.point import Point

logger = logging.getLogger(__name__)

LEFT_SHOULDER = 11
LEFT_ELBOW = 13
LEFT_WRIST = 15
# EKLENDİ — Squat için gereken eklemler
LEFT_HIP = 23
LEFT_KNEE = 25
LEFT_ANKLE = 27

# GEÇİCİ TEŞHİS — sol/sağ karışması ihtimalini test etmek için
RIGHT_SHOULDER = 12
RIGHT_ELBOW = 14
RIGHT_WRIST = 16

VISIBILITY_THRESHOLD = 0.6   # 0.45 denendi, gerçek sebep değildi — geri alındı


class PoseProcessor:
    def __init__(self):
        self._pose = mp.solutions.pose.Pose(
            model_complexity=2,          # 0=hızlı/kaba, 2=en doğru (biraz yavaş ama gerçek zamanlıda sorun olmaz)
            min_detection_confidence=0.6,
            min_tracking_confidence=0.6,
        )
        logger.info("MediaPipe Pose başlatıldı (model_complexity=2)")

    def process(self, frame_rgb, frame_width: int, frame_height: int):
        result = self._pose.process(frame_rgb)
        if not result.pose_landmarks:
            return None
        return result.pose_landmarks

    def get_point(self, landmarks, index: int, frame_width: int, frame_height: int) -> Point:
        lm = landmarks.landmark[index]
        return Point(x=lm.x * frame_width, y=lm.y * frame_height)

    def is_visible(self, landmarks, index: int) -> bool:
        """Bu noktanın güvenilir olup olmadığını söyler — occlusion/gürültü kontrolü."""
        return landmarks.landmark[index].visibility >= VISIBILITY_THRESHOLD