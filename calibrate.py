import json
import math
import time

from imu import get, CALIBRATION_FILE

DURATION = 10.0


class _Stats:
    """Running mean / sample std (Welford) for one axis."""

    def __init__(self):
        self.n = 0
        self.mean = 0.0
        self.m2 = 0.0

    def add(self, v: float) -> None:
        self.n += 1
        d = v - self.mean
        self.mean += d / self.n
        self.m2 += d * (v - self.mean)

    @property
    def std(self) -> float:
        return math.sqrt(self.m2 / (self.n - 1)) if self.n > 1 else 0.0


def calibrate(duration: float = DURATION) -> tuple:
    """Mean and std of raw accel (g) and gyro (deg/s) while the device is still and flat.

    Returns (accel_stats, gyro_stats), each a list of three _Stats (x, y, z).
    """
    accel = [_Stats() for _ in range(3)]
    gyro = [_Stats() for _ in range(3)]
    with get() as _imu:
        end = time.monotonic() + duration
        while time.monotonic() < end:
            for sample in _imu.read_accel_timed():
                for stats, v in zip(accel, (sample.x, sample.y, sample.z)):
                    stats.add(v)
            for sample in _imu.read_gyro_timed():
                for stats, v in zip(gyro, (sample.x, sample.y, sample.z)):
                    stats.add(v)
    if accel[0].n == 0 or gyro[0].n == 0:
        raise RuntimeError("no IMU samples received during calibration")
    return accel, gyro


if __name__ == "__main__":
    print(f"Keep the device flat and still; sampling for {DURATION:.0f}s...")
    accel, gyro = calibrate()
    data = {}
    for axis, a, g in zip("xyz", accel, gyro):
        data[axis] = a.mean
        data["g" + axis] = g.mean
        data["s" + axis] = a.std      # accel std, g
        data["sg" + axis] = g.std     # gyro std, deg/s
    with open(CALIBRATION_FILE, "w") as f:
        json.dump(data, f, indent=2)
    print(f"Saved to {CALIBRATION_FILE}:")
    print(json.dumps(data, indent=2))
