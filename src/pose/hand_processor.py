"""
MediaPipe hand landmark processor — SENSOR LAYER, separate from
PoseProcessor (SRP: one class per model). Gives up to 2 hands, 21
landmarks each (wrist + 4 points per finger), for hand-posture display.
Not wired into the rule engine yet — visual only, exercises.json has no
hand-based checks so far.
"""
import logging
import mediapipe as mp
from src.geometry.point import Point

logger = logging.getLogger(__name__)

# Standard 21-point hand skeleton connections (wrist=0, then 4 joints per
# finger). Exposed here so callers never need to know MediaPipe internals.
HAND_CONNECTIONS = mp.solutions.hands.HAND_CONNECTIONS


class HandProcessor:
    def __init__(self):
        self._hands = mp.solutions.hands.Hands(
            max_num_hands=2,
            min_detection_confidence=0.6,
            min_tracking_confidence=0.6,
        )
        logger.info("MediaPipe Hands initialized")

    def process(self, frame_rgb):
        """
        Returns a list of (label, hand_landmarks) — label is "Left" or
        "Right" (anatomical, from MediaPipe's handedness classification).
        Empty list if no hand is detected.
        """
        result = self._hands.process(frame_rgb)
        if not result.multi_hand_landmarks:
            return []
        hands = []
        for landmarks, handedness in zip(result.multi_hand_landmarks, result.multi_handedness):
            label = handedness.classification[0].label
            hands.append((label, landmarks))
        return hands

    def get_point(self, hand_landmarks, index: int, frame_width: int, frame_height: int) -> Point:
        lm = hand_landmarks.landmark[index]
        return Point(x=lm.x * frame_width, y=lm.y * frame_height)
