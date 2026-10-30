import json
import math
import os

from macimu import IMU

CALIBRATION_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "calibration.json")
DEFAULT_OFFSETS = (0, 0, 1)
DEFAULT_GYRO_OFFSETS = (0, 0, 0)
GRAVITY = 9.80665


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

def get() -> IMU:
    return IMU()

def read(_imu: IMU) -> list[tuple]:
    sample_list = _imu.read_accel_timed()
    output = []
    for sample in sample_list:
        # add offsets, convert to m*s^-2
        t = (
            sample.t,
            (sample.x + OFFSETS[0]) * GRAVITY,
            (sample.y + OFFSETS[1]) * GRAVITY,
            (sample.z + OFFSETS[2]) * GRAVITY,
        )
        output.append(t)
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
