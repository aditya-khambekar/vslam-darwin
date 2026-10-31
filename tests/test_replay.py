import os
import sys
import tempfile

import cv2
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tools"))
import replay  # noqa: E402


def test_replay_merges_by_time():
    with tempfile.TemporaryDirectory() as d:
        os.makedirs(f"{d}/frames")
        cv2.imwrite(f"{d}/frames/000000.png", np.zeros((4, 4, 3), np.uint8))
        open(f"{d}/meta.json", "w").write("{}")
        open(f"{d}/frames.csv", "w").write("n,t\n0,1.5\n")
        open(f"{d}/imu.csv", "w").write("t,kind,x,y,z,lid_deg\n1.0,a,0,0,1,90\n2.0,g,0,0,0,None\n")
        kinds = [e[0] for e in replay.replay(d)]
        assert kinds == ["imu", "frame", "imu"]
