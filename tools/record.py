"""Record timestamped camera frames and raw IMU samples to recordings/<name>/.

Layout: frames/<n>.png, frames.csv (n,t), imu.csv (t,kind,x,y,z,lid_deg), meta.json.
IMU values are raw (accel in g, gyro in deg/s). Needs root for the IMU (see scripts/run.sh).
Usage: sudo .venv/bin/python tools/record.py [--seconds 30] [--name NAME] [--no-camera]
"""
import argparse
import csv
import json
import os
import sys
import time

import cv2

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from camera import Camera  # noqa: E402
from vslam import config  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seconds", type=float, default=30)
    ap.add_argument("--name", default=time.strftime("%Y%m%d-%H%M%S"))
    ap.add_argument("--no-camera", action="store_true")
    ap.add_argument("--no-imu", action="store_true")
    args = ap.parse_args()

    cfg = config.load()
    out = os.path.join(config.ROOT, cfg["recording"]["dir"], args.name)
    os.makedirs(os.path.join(out, "frames"), exist_ok=True)

    imu = None
    if not args.no_imu:
        from macimu import IMU
        imu = IMU()
        imu.start()
    cam = None
    if not args.no_camera:
        c = cfg["camera"]
        cam = Camera(c["index"], c["width"], c["height"], c["fps"])
        cam.start()

    lid = imu.read_lid() if imu else None
    n_frames = n_imu = 0
    t_mono0, t_start = time.monotonic(), None
    with open(os.path.join(out, "frames.csv"), "w", newline="") as ff, \
            open(os.path.join(out, "imu.csv"), "w", newline="") as fi:
        fw, iw = csv.writer(ff), csv.writer(fi)
        fw.writerow(["n", "t"])
        iw.writerow(["t", "kind", "x", "y", "z", "lid_deg"])
        t_start = time.monotonic()
        while time.monotonic() - t_start < args.seconds:
            if cam:
                f = cam.read()
                if f is not None:
                    cv2.imwrite(os.path.join(out, "frames", f"{n_frames:06d}.png"),
                                f.image, [cv2.IMWRITE_PNG_COMPRESSION, 1])
                    fw.writerow([n_frames, f"{f.t:.6f}"])
                    n_frames += 1
            if imu:
                lid_now = imu.read_lid()
                for kind, samples in (("a", imu.read_accel_timed()), ("g", imu.read_gyro_timed())):
                    for s in samples:
                        iw.writerow([f"{s.t:.6f}", kind, s.x, s.y, s.z, lid_now])
                        n_imu += 1
            time.sleep(0.002)

    meta = {"seconds": args.seconds, "frames": n_frames, "imu_samples": n_imu,
            "lid_deg_start": lid, "camera": cfg["camera"], "camera_clock": "time.monotonic",
            "imu_clock": "mach_absolute_time seconds", "monotonic_at_start": t_mono0}
    with open(os.path.join(out, "meta.json"), "w") as f:
        json.dump(meta, f, indent=2)
    if cam:
        cam.stop()
    if imu:
        imu.stop()
    print(f"recorded {n_frames} frames, {n_imu} imu samples -> {out}")


if __name__ == "__main__":
    main()
