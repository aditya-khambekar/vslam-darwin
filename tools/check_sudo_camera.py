"""Run as root to test whether the camera works under sudo:
sudo .venv/bin/python tools/check_sudo_camera.py"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from camera import Camera  # noqa: E402

print("euid:", os.geteuid())
with Camera() as c:
    import time
    time.sleep(2)
    f = c.read()
    print("OK" if f is not None else "NO FRAME", f.image.shape if f else "", f"{c.measured_fps:.1f} fps")
