"""Replay a recording as a time-ordered stream of ("frame", t, image) / ("imu", t, kind, x, y, z, lid).

As a script it prints a summary and optionally shows frames: python tools/replay.py <dir> [--show]
"""
import argparse
import csv
import heapq
import json
import os

import cv2


def load(path: str):
    with open(os.path.join(path, "meta.json")) as f:
        meta = json.load(f)
    frames = []
    fp = os.path.join(path, "frames.csv")
    if os.path.exists(fp):
        with open(fp) as f:
            frames = [(float(r["t"]), int(r["n"])) for r in csv.DictReader(f)]
    imu = []
    ip = os.path.join(path, "imu.csv")
    if os.path.exists(ip):
        with open(ip) as f:
            for r in csv.DictReader(f):
                lid = None if r["lid_deg"] in ("", "None") else float(r["lid_deg"])
                imu.append((float(r["t"]), r["kind"], float(r["x"]), float(r["y"]), float(r["z"]), lid))
    return meta, frames, imu


def replay(path: str):
    """Yield events merged by timestamp. Assumes camera and IMU clocks match (verified in Phase 1)."""
    _, frames, imu = load(path)
    ev = heapq.merge(((t, 0, ("frame", n)) for t, n in frames),
                     ((s[0], 1, ("imu",) + s[1:]) for s in imu))
    for t, _, payload in ev:
        if payload[0] == "frame":
            img = cv2.imread(os.path.join(path, "frames", f"{payload[1]:06d}.png"))
            yield ("frame", t, img)
        else:
            yield ("imu", t) + payload[1:]


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--show", action="store_true")
    a = ap.parse_args()
    meta, frames, imu = load(a.path)
    print(meta)
    if frames:
        print(f"frames: {len(frames)}  span {frames[-1][0]-frames[0][0]:.2f}s")
    if imu:
        print(f"imu: {len(imu)}  span {imu[-1][0]-imu[0][0]:.2f}s")
    if a.show:
        for ev in replay(a.path):
            if ev[0] == "frame":
                cv2.imshow("replay", ev[2])
                if cv2.waitKey(33) == 27:
                    break
