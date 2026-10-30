import json
import math
import os

from macimu import IMU

CALIBRATION_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "calibration.json")
DEFAULT_OFFSETS = (0, 0, 1)
DEFAULT_GYRO_OFFSETS = (0, 0, 0)
GRAVITY = 9.80665
DEFAULT_ACCEL_STD = (0.01, 0.01, 0.01)  # g, used until calibrated
ACCEL_PROCESS_VAR = 1e-4  # (m/s^2)^2 per sample; raise to track motion faster, lower to smooth more


def load_offsets() -> tuple:
    """Return (accel_offsets, gyro_offsets): the negated stationary means from calibrate.py,
    so a still, flat device reads zero. Accel is in g, gyro in deg/s."""
    try:
        with open(CALIBRATION_FILE) as f:
            c = json.load(f)
        accel = (-c["x"], -c["y"], -c["z"])
    except (FileNotFoundError, KeyError, ValueError):
        return DEFAULT_OFFSETS, DEFAULT_GYRO_OFFSETS
    try:
        gyro = (-c["gx"], -c["gy"], -c["gz"])
    except KeyError:
        gyro = DEFAULT_GYRO_OFFSETS
    return accel, gyro


OFFSETS, GYRO_OFFSETS = load_offsets()


def load_accel_std() -> tuple:
    """Per-axis accel noise std (g) measured by calibrate.py."""
    try:
        with open(CALIBRATION_FILE) as f:
            c = json.load(f)
        return (c["sx"], c["sy"], c["sz"])
    except (FileNotFoundError, KeyError, ValueError):
        return DEFAULT_ACCEL_STD


ACCEL_STD = load_accel_std()


class Kalman:

    def __init__(self, r: float, q: float):
        self.r = max(r, 1e-12)
        self.q = q
        self.x = None
        self.p = 1.0

    def update(self, z: float) -> float:
        if self.x is None:
            self.x, self.p = z, self.r
            return z
        p_pred = self.p + self.q
        k = p_pred / (p_pred + self.r)
        self.x += k * (z - self.x)
        self.p = (1 - k) * p_pred
        return self.x


_accel_filters = [
    Kalman(r=(s * GRAVITY) ** 2, q=ACCEL_PROCESS_VAR) for s in ACCEL_STD
]

def get() -> IMU:
    return IMU()

def read(_imu: IMU) -> list[tuple]:
    sample_list = _imu.read_accel_timed()
    output = []
    for sample in sample_list:
        # add offsets, convert to m*s^-2, then Kalman filter each axis
        raw = (
            (sample.x + OFFSETS[0]) * GRAVITY,
            (sample.y + OFFSETS[1]) * GRAVITY,
            (sample.z + OFFSETS[2]) * GRAVITY,
        )
        output.append((sample.t, *(f.update(v) for f, v in zip(_accel_filters, raw))))
    return output

def read_gyro(_imu: IMU) -> list[tuple]:
    output = []
    for sample in _imu.read_gyro_timed():
        # subtract bias, convert deg/s to rad/s
        output.append((
            sample.t,
            math.radians(sample.x + GYRO_OFFSETS[0]),
            math.radians(sample.y + GYRO_OFFSETS[1]),
            math.radians(sample.z + GYRO_OFFSETS[2]),
        ))
    return output
