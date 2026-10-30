import imu
import odometry

if __name__ == "__main__":
    with imu.get() as _imu:
        try:
            while True:
                for sample in imu.read(_imu):
                    odometry.callback(sample)
                for sample in imu.read_gyro(_imu):
                    odometry.gyro_callback(sample)
                print(str(odometry.get_translation_3d()) + " " +  str(odometry.get_rotation_3d()))
        except KeyboardInterrupt:
            pass