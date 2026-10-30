import json
import time

from imu import get, CALIBRATION_FILE

DURATION = 3.0


def calibrate(duration: float = DURATION) -> tuple:
    """Average raw accel (g) and gyro (deg/s) readings while the device is still and flat."""
    accel_sums = [0.0, 0.0, 0.0]
    gyro_sums = [0.0, 0.0, 0.0]
    accel_count = 0
    gyro_count = 0
    with get() as _imu:
        end = time.monotonic() + duration
        while time.monotonic() < end:
            for sample in _imu.read_accel_timed():
                accel_sums[0] += sample.x
                accel_sums[1] += sample.y
                accel_sums[2] += sample.z
                accel_count += 1
            for sample in _imu.read_gyro_timed():
                gyro_sums[0] += sample.x
                gyro_sums[1] += sample.y
                gyro_sums[2] += sample.z
                gyro_count += 1
    if accel_count == 0 or gyro_count == 0:
        raise RuntimeError("no IMU samples received during calibration")
    return (tuple(s / accel_count for s in accel_sums),
            tuple(s / gyro_count for s in gyro_sums))


if __name__ == "__main__":
    print(f"Keep the device flat and still; sampling for {DURATION:.0f}s...")
    accel, gyro = calibrate()
    with open(CALIBRATION_FILE, "w") as f:
        json.dump({
            "x": accel[0], "y": accel[1], "z": accel[2],
            "gx": gyro[0], "gy": gyro[1], "gz": gyro[2],
        }, f, indent=2)
    print(f"Saved accel mean {accel} and gyro mean {gyro} to {CALIBRATION_FILE}")
