import math
import threading
import time

import numpy as np
import pyautogui


class MouseController:
    """Palm-normalized gestures and distance-based cursor smoothing.

    The worker targets 180 iterations/s, not a measured camera/input rate.
    An injected backend permits regression tests without desktop input.
    """

    def __init__(self, wCam, hCam, smoothening=4, frameR_x=130, frameR_y=115,
                 click_ratio=0.35, right_click_ratio=0.35, *, backend=None,
                 start_thread=True):
        self.wCam, self.hCam = wCam, hCam
        self.smoothening = smoothening
        self.frameR_x, self.frameR_y = frameR_x, frameR_y
        self.click_ratio, self.right_click_ratio = click_ratio, right_click_ratio
        self._input = backend if backend is not None else pyautogui
        self._input.PAUSE = 0
        self._input.FAILSAFE = True
        self.wScr, self.hScr = self._input.size()
        self._lock = threading.RLock()
        self._stop = threading.Event()
        self.active = True
        self.is_left_clicked = False
        self.is_right_clicked = False
        self.scroll_start_y = None
        self.last_right_click_time = 0
        self.fps_val = 0
        self.hand_type_val = "N/A"
        self.action_val = "Ready"
        self.last_error = ""
        self.prev_x_track = None
        self.prev_y_track = None
        self.clocX, self.clocY = self._input.position()
        self.target_x, self.target_y = self.clocX, self.clocY
        self.has_target = False
        self.mouse_thread = None
        if start_thread:
            self.mouse_thread = threading.Thread(target=self._mouse_interpolation_loop, daemon=True)
            self.mouse_thread.start()

    def _release_left(self):
        if self.is_left_clicked:
            # A held button must be releasable even at a fail-safe corner.
            # Only this release bypasses the corner check, under the same lock.
            old = self._input.FAILSAFE
            try:
                self._input.FAILSAFE = False
                self._input.mouseUp()
            finally:
                self._input.FAILSAFE = old
                self.is_left_clicked = False

    def release_input(self, reason="No Hand"):
        with self._lock:
            try:
                self._release_left()
            finally:
                self.is_right_clicked = False
                self.has_target = False
                self.scroll_start_y = None
                self.prev_x_track = None
                self.prev_y_track = None
                self.action_val = reason

    def set_active(self, active):
        with self._lock:
            self.active = bool(active) and not self._stop.is_set()
            self.release_input("Ready" if self.active else "System Off")

    def close(self):
        self._stop.set()
        self.set_active(False)
        if self.mouse_thread is not None and self.mouse_thread is not threading.current_thread():
            self.mouse_thread.join(timeout=1.0)

    def _mouse_interpolation_loop(self):
        while not self._stop.is_set():
            try:
                with self._lock:
                    if self.active and self.has_target:
                        dx, dy = self.target_x - self.clocX, self.target_y - self.clocY
                        dist = math.hypot(dx, dy)
                        scale = 4.0 / max(1.0, self.smoothening)
                        alpha = scale * (0.008 + (0.25 - 0.008) * min(1.0, (dist / 45.0) ** 2))
                        self.clocX += dx * alpha
                        self.clocY += dy * alpha
                        if abs(dx) > 0.5 or abs(dy) > 0.5:
                            self._input.moveTo(int(self.clocX), int(self.clocY))
            except Exception as exc:
                self.last_error = str(exc)
                try:
                    self.set_active(False)
                except Exception as release_exc:
                    self.last_error += "; release failed: " + str(release_exc)
            self._stop.wait(1.0 / 180.0)

    @staticmethod
    def get_distance(p1_coord, p2_coord):
        return math.hypot(p2_coord[0] - p1_coord[0], p2_coord[1] - p1_coord[1])

    def move_and_action(self, lmList, fingers, palm_scale, img=None):
        with self._lock:
            if not self.active:
                self.release_input("System Off")
                return
            if not lmList:
                self.release_input("No Hand")
                return
            if (len(lmList) != 21 or len(fingers) != 5 or
                    not math.isfinite(palm_scale) or palm_scale <= 1e-6 or
                    any(len(p) != 3 or not all(math.isfinite(v) for v in p[1:]) for p in lmList)):
                self.release_input("Invalid Hand")
                return
            try:
                self._apply_gesture(lmList, fingers, palm_scale)
            except Exception as exc:
                self.last_error = str(exc)
                self.active = False
                self.release_input("Input Error")

    def _apply_gesture(self, lmList, fingers, palm_scale):
        thumb, index, middle = (lmList[n][1:] for n in (4, 8, 12))
        x_track, y_track = lmList[5][1:]
        if self.prev_x_track is None:
            self.prev_x_track, self.prev_y_track = x_track, y_track
        if math.hypot(x_track - self.prev_x_track, y_track - self.prev_y_track) < 0.6:
            x_track, y_track = self.prev_x_track, self.prev_y_track
        else:
            self.prev_x_track, self.prev_y_track = x_track, y_track

        left_ratio = self.get_distance(thumb, index) / palm_scale
        right_ratio = self.get_distance(thumb, middle) / palm_scale
        right_pinched = right_ratio < self.right_click_ratio
        right_edge = right_pinched and not self.is_right_clicked
        # Rearm only on release, including while other gestures have priority.
        self.is_right_clicked = right_pinched
        scroll = fingers[1:5] == [1, 1, 1, 0]

        if not scroll and (fingers[1] == 1 or self.is_left_clicked):
            rx = min(max(0, self.frameR_x), (self.wCam - 1) / 2)
            ry = min(max(0, self.frameR_y), (self.hCam - 1) / 2)
            x = float(np.interp(x_track, (rx, self.wCam - rx), (0, self.wScr - 1)))
            y = float(np.interp(y_track, (ry, self.hCam - ry), (0, self.hScr - 1)))
            if not self.has_target:
                self.clocX, self.clocY = self._input.position()
                self.target_x, self.target_y = x, y
                self.has_target = True
            if math.hypot(x - self.clocX, y - self.clocY) > 1.5:
                self.target_x, self.target_y = x, y
            if left_ratio < self.click_ratio:
                if not self.is_left_clicked:
                    self.is_left_clicked = True
                    self._input.mouseDown()
                self.action_val = "Left Click / Drag"
            else:
                self._release_left()
                self.action_val = "Moving"
            self.scroll_start_y = None
        elif not scroll and right_pinched:
            self.has_target = False
            now = time.monotonic()
            if right_edge and now - self.last_right_click_time > 0.5:
                self._input.rightClick()
                self.last_right_click_time = now
            self.action_val = "Right Click"
            self._release_left()
            self.scroll_start_y = None
        elif scroll:
            self.has_target = False
            self._release_left()
            self.action_val = "Scrolling"
            y = lmList[9][2]
            if self.scroll_start_y is None:
                self.scroll_start_y = y
            else:
                diff = y - self.scroll_start_y
                if abs(diff) > 15:
                    speed = -int((diff - math.copysign(15, diff)) * 0.25)
                    if speed:
                        self._input.scroll(speed)
        else:
            self.has_target = False
            self._release_left()
            self.scroll_start_y = None
            self.action_val = "Ready"
