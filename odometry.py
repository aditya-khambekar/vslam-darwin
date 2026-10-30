translation3d = [0, 0, 0]
translationalVelocity3d = [0, 0, 0]
rotation3d = [0, 0, 0]  # rad, integrated about x, y, z

lastTimestamp = 0
lastGyroTimestamp = 0

def callback(sample) -> None:
    global lastTimestamp
    if lastTimestamp == 0:
        lastTimestamp = sample[0]
    else:
        dt = sample[0] - lastTimestamp
        translationalVelocity3d[0] += sample[1] * dt
        translationalVelocity3d[1] += sample[2] * dt
        translationalVelocity3d[2] += sample[3] * dt

        translation3d[0] += translationalVelocity3d[0] * dt
        translation3d[1] += translationalVelocity3d[1] * dt
        translation3d[2] += translationalVelocity3d[2] * dt

        lastTimestamp = sample[0]

def gyro_callback(sample) -> None:
    """sample is (t, wx, wy, wz) with angular rates in rad/s."""
    global lastGyroTimestamp
    if lastGyroTimestamp == 0:
        lastGyroTimestamp = sample[0]
    else:
        dt = sample[0] - lastGyroTimestamp
        rotation3d[0] += sample[1] * dt
        rotation3d[1] += sample[2] * dt
        rotation3d[2] += sample[3] * dt

        lastGyroTimestamp = sample[0]

def get_translation_3d() -> tuple:
    return tuple(translation3d)

def get_rotation_3d() -> tuple:
    return tuple(rotation3d)
