"""Headless regressions: backend events are recorded, never sent to the OS."""
import ast
import math
from pathlib import Path
import sys
import time
import types
import unittest
from unittest.mock import patch

sys.modules.setdefault("pyautogui", types.ModuleType("pyautogui"))
from src.mouse_controller import MouseController


class Backend:
    FAILSAFE = True
    PAUSE = 0

    def __init__(self):
        self.events = []

    def size(self): return (1920, 1080)
    def position(self): return (500, 500)
    def mouseDown(self): self.events.append("down")
    def mouseUp(self): self.events.append(("up", self.FAILSAFE))
    def rightClick(self): self.events.append("right")
    def scroll(self, value): self.events.append(("scroll", value))
    def moveTo(self, x, y): self.events.append(("move", x, y))


def hand(right=False, left=False):
    points = [[i, 300., 200.] for i in range(21)]
    points[4][1:] = (300., 200.)
    points[8][1:] = (300. if left else 350., 200.)
    points[12][1:] = (300. if right else 350., 200.)
    return points


class LifecycleTests(unittest.TestCase):
    def setUp(self):
        self.backend = Backend()
        self.c = MouseController(640, 480, backend=self.backend, start_thread=False)

    def tearDown(self): self.c.close()

    def drag(self): self.c.move_and_action(hand(left=True), [0, 1, 0, 0, 0], 100.)

    def test_pause_releases_drag_and_target(self):
        self.drag(); self.c.set_active(False)
        self.assertEqual(self.backend.events, ["down", ("up", False)])
        self.assertFalse(self.c.has_target)
        self.assertTrue(self.backend.FAILSAFE)

    def test_camera_failure_and_missing_hand_release(self):
        for failure in (lambda: self.c.release_input("Camera Unavailable"),
                        lambda: self.c.move_and_action([], [], 0)):
            self.drag(); failure()
            self.assertFalse(self.c.is_left_clicked)
            self.assertFalse(self.c.has_target)

    def test_right_click_is_once_per_pinch(self):
        with patch("src.mouse_controller.time.monotonic", side_effect=[1., 1.1, 1.6, 3.]):
            for _ in range(3): self.c.move_and_action(hand(right=True), [0]*5, 100.)
            self.c.move_and_action(hand(), [0]*5, 100.)
            self.c.move_and_action(hand(right=True), [0]*5, 100.)
        self.assertEqual(self.backend.events.count("right"), 2)

    def test_zero_nan_and_incomplete_hand_release(self):
        for points, fingers, scale in [(hand(), [0]*5, 0.), (hand(), [0]*5, math.nan),
                                       (hand()[:10], [0]*5, 100.), (hand(), [], 100.)]:
            self.drag(); self.c.move_and_action(points, fingers, scale)
            self.assertEqual(self.c.action_val, "Invalid Hand")
            self.assertFalse(self.c.is_left_clicked)

    def test_nonfinite_coordinates_release(self):
        self.drag(); points = hand(); points[4][1] = math.inf
        self.c.move_and_action(points, [0]*5, 100.)
        self.assertFalse(self.c.is_left_clicked)

    def test_screen_targets_stay_in_pixel_bounds(self):
        points = hand(); points[5][1:] = (1e5, 1e5)
        self.c.move_and_action(points, [0, 1, 0, 0, 0], 100.)
        self.assertEqual((self.c.target_x, self.c.target_y), (1919., 1079.))

    def test_backend_failure_disables_and_releases(self):
        def fail(): raise RuntimeError("backend unavailable")
        self.backend.mouseDown = fail
        self.drag()
        self.assertFalse(self.c.active)
        self.assertFalse(self.c.is_left_clicked)
        self.assertIn("backend unavailable", self.c.last_error)

    def test_close_is_idempotent_and_cannot_reenable(self):
        self.drag(); self.c.close(); self.c.close(); self.c.set_active(True)
        self.assertFalse(self.c.active)
        self.assertEqual(self.backend.events.count(("up", False)), 1)

    def test_worker_can_be_joined(self):
        c = MouseController(640, 480, backend=self.backend)
        c.close()
        self.assertFalse(c.mouse_thread.is_alive())

    def test_detector_rejects_degenerate_palm(self):
        p = Path(__file__).parents[1] / "src/hand_detector.py"
        tree = ast.parse(p.read_text(encoding="utf-8"))
        cls = next(n for n in tree.body if isinstance(n, ast.ClassDef))
        scope = {"math": math}
        exec(compile(ast.Module(body=[cls], type_ignores=[]), str(p), "exec"), scope)
        detector = scope[cls.name].__new__(scope[cls.name])
        detector.lmList = [[i, 0., 0.] for i in range(21)]
        self.assertEqual(detector.fingersUp(), [])


if __name__ == "__main__": unittest.main()
