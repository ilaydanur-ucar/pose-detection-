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

# MediaPipe Hands' handedness classifier assumes the input image is MIRRORED
# (selfie-style) — this is the opposite assumption from PoseProcessor, which
# is deliberately fed the RAW/unmirrored frame (see main.py's "ROOT CAUSE
# FIXED" comment) so its own left/right labels come out correct. Since we
# feed Hands that same raw frame, its handedness output comes out reversed
# relative to reality — so we swap it back here, once, in the sensor layer,
# instead of leaving every caller to remember this MediaPipe-specific quirk.
_SWAP_HANDEDNESS = {"Left": "Right", "Right": "Left"}


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
            raw_label = handedness.classification[0].label
            label = _SWAP_HANDEDNESS[raw_label]
            hands.append((label, landmarks))
        return hands

    def get_point(self, hand_landmarks, index: int, frame_width: int, frame_height: int) -> Point:
        lm = hand_landmarks.landmark[index]
        return Point(x=lm.x * frame_width, y=lm.y * frame_height)
