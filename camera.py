import threading
import time
from typing import NamedTuple, Optional

import cv2
import numpy as np


class Frame(NamedTuple):
    t: float  # time.monotonic() at capture, seconds
    image: np.ndarray  # BGR uint8


class Camera:
    """Background-threaded capture; read() returns the newest frame without blocking."""

    def __init__(self, index: int = 0, width: int = 1280, height: int = 720, fps: int = 30):
        self.index = index
        self._req = (width, height, fps)
        self.width = width
        self.height = height
        self.fps = fps
        self.measured_fps = 0.0

        self._cap: Optional[cv2.VideoCapture] = None
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()
        self._frame: Optional[Frame] = None
        self._last_returned_t = 0.0

    def start(self) -> None:
        if self._thread is not None:
            return
        cap = cv2.VideoCapture(self.index, cv2.CAP_AVFOUNDATION)
        if not cap.isOpened():
            cap.release()
            raise RuntimeError(f"could not open camera {self.index}")
        w, h, fps = self._req
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, w)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, h)
        cap.set(cv2.CAP_PROP_FPS, fps)

        # The first read triggers the macOS permission prompt; an empty frame means denied.
        deadline = time.monotonic() + 10
        ok, image = False, None
        while time.monotonic() < deadline:
            ok, image = cap.read()
            if ok and image is not None:
                break
            time.sleep(0.1)
        if not ok:
            cap.release()
            raise RuntimeError(
                "camera opened but returned no frames; check System Settings > "
                "Privacy & Security > Camera for the app running Python")

        self.height, self.width = image.shape[:2]
        self.fps = cap.get(cv2.CAP_PROP_FPS) or fps
        self._cap = cap
        with self._lock:
            self._frame = Frame(time.monotonic(), image)
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def _loop(self) -> None:
        count, window_start = 0, time.monotonic()
        while not self._stop_event.is_set():
            ok, image = self._cap.read()
            if not ok or image is None:
                time.sleep(0.01)
                continue
            now = time.monotonic()
            with self._lock:
                self._frame = Frame(now, image)
            count += 1
            if now - window_start >= 1.0:
                self.measured_fps = count / (now - window_start)
                count, window_start = 0, now

    def read(self) -> Optional[Frame]:
        """Newest frame, or None if there is no new frame since the last call."""
        with self._lock:
            frame = self._frame
        if frame is None or frame.t == self._last_returned_t:
            return None
        self._last_returned_t = frame.t
        return frame

    def stop(self) -> None:
        if self._thread is None:
            return
        self._stop_event.set()
        self._thread.join(timeout=3)
        self._thread = None
        if self._cap is not None:
            self._cap.release()
            self._cap = None
        with self._lock:
            self._frame = None
        self._last_returned_t = 0.0
        self.measured_fps = 0.0

    def __enter__(self) -> "Camera":
        self.start()
        return self

    def __exit__(self, *exc) -> None:
        self.stop()
