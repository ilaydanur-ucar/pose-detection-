"""
Entry point — generic multi-exercise pipeline (camera -> MediaPipe -> Point ->
geometry -> rules -> screen). No exercise-specific code here (OCP,
ARCHITECTURE.md §3): every exercise is driven entirely by exercises.json.

Run: python main.py | Keys 1-9 switch exercise | 'q' quits
"""
import json
import logging
import cv2

from src.logging_config import setup_logging
from src.pose.processor import (
    PoseProcessor,
    LEFT_SHOULDER, LEFT_ELBOW, LEFT_WRIST, LEFT_HIP, LEFT_KNEE, LEFT_ANKLE,
    RIGHT_SHOULDER, RIGHT_ELBOW, RIGHT_WRIST, RIGHT_HIP, RIGHT_KNEE, RIGHT_ANKLE,
    NOSE,
)
from src.pose.hand_processor import HandProcessor, HAND_CONNECTIONS
from src.geometry.angles import joint_angle
from src.geometry.point import Point
from src.rules.types import Exercise, AngleCheck, CheckType
from src.rules.engine import evaluate

setup_logging(level=logging.DEBUG)  # kept at DEBUG for now (team decision) — revisit later
logger = logging.getLogger(__name__)

EXERCISE_KEYS = [
    "squat", "chair_pose", "plank", "planor", "tree_pose", "bridge",
    "posture_check", "t_pose", "overhead_reach",
]

# Single place mapping exercises.json point names to MediaPipe landmark
# indices (DRY) — reuses the indices already defined in processor.py.
NAME_TO_INDEX = {
    "left_shoulder": LEFT_SHOULDER, "right_shoulder": RIGHT_SHOULDER,
    "left_elbow": LEFT_ELBOW, "right_elbow": RIGHT_ELBOW,
    "left_wrist": LEFT_WRIST, "right_wrist": RIGHT_WRIST,
    "left_hip": LEFT_HIP, "right_hip": RIGHT_HIP,
    "left_knee": LEFT_KNEE, "right_knee": RIGHT_KNEE,
    "left_ankle": LEFT_ANKLE, "right_ankle": RIGHT_ANKLE,
    "nose": NOSE,
}


def load_exercises(json_path: str) -> dict[str, Exercise]:
    """Loads every exercise entry from exercises.json into Exercise objects."""
    with open(json_path, encoding="utf-8") as f:
        raw = json.load(f)
    exercises = {}
    for key, data in raw.items():
        checks = [
            AngleCheck(
                type=CheckType(c["type"]),
                points=c["points"],
                min_angle=c["min_angle"],
                max_angle=c["max_angle"],
                message=c["message"],
                low_message=c.get("low_message"),
                high_message=c.get("high_message"),
            )
            for c in data["checks"]
        ]
        exercises[key] = Exercise(name=data["name"], checks=checks)
    return exercises


# Drawing helpers (DRY — same "black outline + colored fill" trick everywhere
# so text/points/lines stay readable over any background).

def draw_text(frame, text, pos, color=(0, 255, 0)):
    cv2.putText(frame, text, pos, cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 5)
    cv2.putText(frame, text, pos, cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)


def draw_point(frame, p, color=(0, 255, 0)):
    cv2.circle(frame, (int(p.x), int(p.y)), 8, (0, 0, 0), -1)
    cv2.circle(frame, (int(p.x), int(p.y)), 6, color, -1)


def draw_line(frame, p1, p2, color=(0, 255, 0)):
    pt1, pt2 = (int(p1.x), int(p1.y)), (int(p2.x), int(p2.y))
    cv2.line(frame, pt1, pt2, (0, 0, 0), 6)      # black outline (thick)
    cv2.line(frame, pt1, pt2, color, 3)          # colored fill (thin)


def mirror_point(p: Point, frame_width: int) -> Point:
    """
    Mirrors a point horizontally. Used ONLY right before drawing (CLAUDE.md:
    mirroring only happens in the drawing/OpenCV layer, never leaks into
    geometry/). MediaPipe is given the RAW/unmirrored frame, so angle
    calculations must happen before this call, on the original points.
    """
    return Point(x=frame_width - p.x, y=p.y)


def collect_points(processor, landmarks, names, width, height):
    """
    Collects every point an exercise's checks need.
    Returns (points, missing): points is a name->Point dict, or None if any
    requested name wasn't visible enough; missing is the list of point names
    that failed visibility (empty when points is not None).
    """
    points = {}
    missing = []
    for name in names:
        index = NAME_TO_INDEX[name]
        if not processor.is_visible(landmarks, index):
            missing.append(name)
            continue
        points[name] = processor.get_point(landmarks, index, width, height)
    if missing:
        return None, missing
    return points, []


def draw_exercise_checks(frame, exercise: Exercise, points: dict, width: int):
    """
    Generic skeleton drawing: connects each check's own points, mirrored for
    display. DISTANCE checks draw two separate segments (measured pair +
    reference pair) instead of one connected chain — the four points aren't
    meant to form a path.
    """
    for check in exercise.checks:
        pts_d = [mirror_point(points[name], width) for name in check.points]
        if check.type == CheckType.DISTANCE:
            draw_line(frame, pts_d[0], pts_d[1])
            draw_line(frame, pts_d[2], pts_d[3])
        else:
            for a, b in zip(pts_d, pts_d[1:]):
                draw_line(frame, a, b)
        for p in pts_d:
            draw_point(frame, p)


def draw_arm(frame, processor, landmarks, width, height,
             shoulder_i, elbow_i, wrist_i, label, color, fallback_pos):
    """
    Standalone upper-body sanity check, independent of the selected exercise
    (all 6 exercises need leg landmarks, so none of them draw anything while
    only the upper body is in frame — this lets you verify the pipeline from
    a desk/webcam without standing back). DRY: same logic for both arms,
    only the landmark indices differ.
    """
    visible = all(processor.is_visible(landmarks, i) for i in (shoulder_i, elbow_i, wrist_i))
    if not visible:
        draw_text(frame, f"{label} arm not clearly visible", fallback_pos, color=(0, 0, 255))
        return

    shoulder = processor.get_point(landmarks, shoulder_i, width, height)
    elbow = processor.get_point(landmarks, elbow_i, width, height)
    wrist = processor.get_point(landmarks, wrist_i, width, height)
    angle = joint_angle(shoulder, elbow, wrist)

    shoulder_d = mirror_point(shoulder, width)
    elbow_d = mirror_point(elbow, width)
    wrist_d = mirror_point(wrist, width)

    draw_line(frame, shoulder_d, elbow_d, color)
    draw_line(frame, elbow_d, wrist_d, color)
    draw_text(frame, f"{label} {angle:.0f} deg", fallback_pos, color)
    for p in (shoulder_d, elbow_d, wrist_d):
        draw_point(frame, p, color)


def draw_head(frame, processor, landmarks, width, height, color=(255, 0, 255)):
    """
    Standalone head/neck sanity-check display, same spirit as draw_arm/
    draw_hand — purely visual, doesn't feed into any exercise check.
    BlazePose has no dedicated "neck" landmark, so the shoulder midpoint is
    used as a neck stand-in (plain averaging, not an angle formula — stays
    out of geometry/, CLAUDE.md rule 2 only covers arccos/atan2 formulas).
    """
    visible = all(processor.is_visible(landmarks, i) for i in (NOSE, LEFT_SHOULDER, RIGHT_SHOULDER))
    if not visible:
        return

    nose = processor.get_point(landmarks, NOSE, width, height)
    l_shoulder = processor.get_point(landmarks, LEFT_SHOULDER, width, height)
    r_shoulder = processor.get_point(landmarks, RIGHT_SHOULDER, width, height)
    neck = Point(x=(l_shoulder.x + r_shoulder.x) / 2, y=(l_shoulder.y + r_shoulder.y) / 2)

    nose_d = mirror_point(nose, width)
    neck_d = mirror_point(neck, width)

    draw_line(frame, nose_d, neck_d, color)
    draw_point(frame, nose_d, color)
    draw_point(frame, neck_d, color)


def draw_hand(frame, hand_processor: HandProcessor, hand_landmarks, width, height, label, color=(0, 220, 220)):
    """
    Draws a detected hand's full 21-point skeleton (wrist + fingers), mirrored
    for display — same "compute raw, mirror before drawing" rule as the body.
    Purely visual for now (see hand_processor.py docstring).
    """
    pts_d = [
        mirror_point(hand_processor.get_point(hand_landmarks, i, width, height), width)
        for i in range(21)
    ]
    for a, b in HAND_CONNECTIONS:
        draw_line(frame, pts_d[a], pts_d[b], color)
    for p in pts_d:
        draw_point(frame, p, color)
    draw_text(frame, f"{label} hand", (int(pts_d[0].x) - 20, int(pts_d[0].y) + 30), color)


def main():
    processor = PoseProcessor()  # model_complexity=2 in processor.py (more accurate coordinates)
    hand_processor = HandProcessor()
    exercises = load_exercises("exercises.json")
    current_key = EXERCISE_KEYS[0]

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        logger.error("Could not open camera")
        return

    # Request a higher capture resolution (this webcam's max is 1280x720;
    # falls back to its default, e.g. 640x480, if unsupported). More pixels
    # to work with — NOT a wider field of view, that's fixed by the lens.
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    logger.info("Requested 1280x720, camera reports %dx%d",
                int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))

    logger.info("Camera opened. Keys 1-%d switch exercise, 'q' quits", len(EXERCISE_KEYS))

    while True:
        ok, frame = cap.read()
        if not ok:
            logger.warning("Could not read frame")
            break

        # ROOT CAUSE FIXED: flipping BEFORE MediaPipe consistently reversed
        # the model's anatomical left/right labels (a mirrored body reads
        # backwards to the model). Fix: give MediaPipe the RAW frame (correct
        # labeling), flip only for display at the very end, after points are
        # computed (via mirror_point).

        # MediaPipe expects RGB, OpenCV gives BGR -> convert
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        height, width = frame.shape[:2]

        landmarks = processor.process(frame_rgb, width, height)
        hands = hand_processor.process(frame_rgb)  # independent of body detection

        frame = cv2.flip(frame, 1)   # horizontal mirror fix — display only

        exercise = exercises[current_key]
        draw_text(frame, f"[{current_key}] {exercise.name}", (20, 30), (255, 255, 0))

        # Always-on hand skeletons (visual only, doesn't need a body match).
        for label, hand_landmarks in hands:
            draw_hand(frame, hand_processor, hand_landmarks, width, height, label)

        if landmarks is not None:
            # Diagnostic — kept for now per team decision, to check from here
            # if a left/right mixup ever reappears. Remove once confirmed
            # stable across all 6 exercises.
            for name, idx in [
                ("LEFT  shoulder", LEFT_SHOULDER), ("LEFT  elbow", LEFT_ELBOW), ("LEFT  wrist", LEFT_WRIST),
                ("RIGHT shoulder", RIGHT_SHOULDER), ("RIGHT elbow", RIGHT_ELBOW), ("RIGHT wrist", RIGHT_WRIST),
            ]:
                lm = landmarks.landmark[idx]
                px = lm.x * width
                side = "left-half" if px < width / 2 else "right-half"
                logger.debug("%s idx=%2d vis=%.2f x_px=%6.1f (%s)", name, idx, lm.visibility, px, side)

            # Always-on upper-body sanity check (see draw_arm docstring) —
            # draws regardless of which exercise is selected or visible.
            draw_arm(frame, processor, landmarks, width, height,
                     LEFT_SHOULDER, LEFT_ELBOW, LEFT_WRIST,
                     "LEFT", (0, 255, 0), (20, 100))
            draw_arm(frame, processor, landmarks, width, height,
                     RIGHT_SHOULDER, RIGHT_ELBOW, RIGHT_WRIST,
                     "RIGHT", (255, 165, 0), (20, 130))
            draw_head(frame, processor, landmarks, width, height)

            needed_names = {n for c in exercise.checks for n in c.points}
            points, missing = collect_points(processor, landmarks, needed_names, width, height)

            if points is not None:
                try:
                    violations = evaluate(points, exercise)
                except KeyError as e:
                    logger.error(
                        "Evaluation error: exercise=%s missing_key=%s", current_key, e
                    )
                    draw_text(frame, "Calculation error", (20, 70), color=(0, 0, 255))
                else:
                    logger.debug("Exercise=%s violations=%s", current_key, violations)
                    draw_exercise_checks(frame, exercise, points, width)
                    if violations:
                        draw_text(frame, violations[0], (20, 70), color=(0, 0, 255))
                    else:
                        draw_text(frame, "CORRECT", (20, 70), color=(0, 255, 0))
            else:
                logger.debug("Missing landmarks: %s", missing)
                draw_text(frame, f"Not visible: {', '.join(missing)}", (20, 70), color=(0, 0, 255))
        else:
            logger.warning("No pose landmarks detected in this frame")
            draw_text(frame, "Body not detected", (20, 40), color=(0, 0, 255))

        cv2.imshow("FormCheck", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        for i, ex_key in enumerate(EXERCISE_KEYS, start=1):
            if key == ord(str(i)):
                current_key = ex_key
                logger.info("Exercise switched: %s", current_key)
                break

    cap.release()
    cv2.destroyAllWindows()
    logger.info("Closed")


if __name__ == "__main__":
    main()
