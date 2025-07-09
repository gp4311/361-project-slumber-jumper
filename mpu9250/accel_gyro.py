from smbus2 import SMBus, i2c_msg
import time
import math


# MPU-9250 I2C address
MPU_ADDR = 0x68

# MPU-9250 Register addresses
PWR_MGMT_1   = 0x6B
ACCEL_XOUT_H = 0x3B
GYRO_XOUT_H  = 0x43

# I2C setup
i2c = SMBus(1)  # On Raspberry Pi, I2C bus 1 is used

# Wake up MPU-9250
write = i2c_msg.write(MPU_ADDR, [PWR_MGMT_1, 0x00])
i2c.i2c_rdwr(write)

# Global offsets
accel_offset = [0.0, 0.0, 0.0]
gyro_offset = [0.0, 0.0, 0.0]

# Thresholds
GYRO_THRESHOLD = 2          # deg/s
TILT_ANGLE_THRESHOLD = 30   # deg


# Helper to read 16-bit signed value from register
def read_word_2c(reg):
    high = i2c.read_byte_data(MPU_ADDR, reg)
    low = i2c.read_byte_data(MPU_ADDR, reg + 1)
    val = (high << 8) + low
    if val >= 0x8000:
        val -= 0x10000
    return val

def read_accel():
    ax = read_word_2c(ACCEL_XOUT_H)
    ay = read_word_2c(ACCEL_XOUT_H + 2)
    az = read_word_2c(ACCEL_XOUT_H + 4)

    # Convert raw to g (±2g scale)
    ax_g = ax / 16384.0
    ay_g = ay / 16384.0
    az_g = az / 16384.0

    # Convert to m/s²
    ax_ms2 = ax_g * 9.81
    ay_ms2 = ay_g * 9.81
    az_ms2 = az_g * 9.81

    return [ax_ms2, ay_ms2, az_ms2]

def read_gyro():
    gx = read_word_2c(GYRO_XOUT_H)
    gy = read_word_2c(GYRO_XOUT_H + 2)
    gz = read_word_2c(GYRO_XOUT_H + 4)
    return [gx / 131.0, gy / 131.0, gz / 131.0]  # ±250°/s scale

def calibrate_accelerometer(samples=100):
    global accel_offset
    print('Calibrating accelerometer ... keep flat')
    acc_sum = [0.0, 0.0, 0.0]

    for _ in range(samples):
        ax, ay, az = read_accel()
        acc_sum[0] += ax
        acc_sum[1] += ay
        acc_sum[2] += az
        time.sleep(0.01)

    accel_offset = [acc_sum[i] / samples for i in range(3)]
    accel_offset[2] -= 9.81  # Remove gravity once
    print("Accelerometer calibration:", accel_offset)

def gyro_calibration(calibration_time=5):
    global gyro_offset
    print("Beginning Gyro calibration (keep still)...")
    offsets = [0.0, 0.0, 0.0]
    num_samples = 0
    end_time = time.time() + calibration_time

    while time.time() < end_time:
        gx, gy, gz = read_gyro()
        offsets[0] += gx
        offsets[1] += gy
        offsets[2] += gz
        num_samples += 1
        time.sleep(0.01)

        if num_samples % 100 == 0:
            print("Still calibrating Gyro...", num_samples)

    if num_samples == 0:
        raise RuntimeError("Gyro calibration failed: no samples collected.")

    gyro_offset = [x / num_samples for x in offsets]
    print("Gyroscope calibration complete:", gyro_offset)

def read_calibrated_accel():
    ax, ay, az = read_accel()
    return [ax - accel_offset[0], ay - accel_offset[1], az - accel_offset[2]]

def read_calibrated_gyro():
    gx, gy, gz = read_gyro()
    return [gx - gyro_offset[0], gy - gyro_offset[1], gz - gyro_offset[2]]

def get_y_tilt_angle():
    _, ay, az = read_calibrated_accel()
    return math.degrees(math.atan2(ay, az))

def get_pitch_roll_angles():
    ax, ay, az = read_calibrated_accel()
    pitch = math.degrees(math.atan2(-ax, math.sqrt(ay * ay + az * az)))
    return pitch


# Main function to be called by main.py

def collect_gyro_data(queue=None, verbose=False):
    calibrate_accelerometer()
    gyro_calibration()
    initial_y_tilt = get_y_tilt_angle()

    if verbose:
        print("\nMonitoring tilt and roll...\n")

    over_threshold_count = 0
    samples = 30
    tilt_sum = 0

    while True:
        alert = None 

        accel = read_calibrated_accel()
        gyro = read_calibrated_gyro()
        _, ay, az = accel
        gx, _, _ = gyro

        current_y_tilt = math.degrees(math.atan2(ay, az))
        tilt_change = abs(current_y_tilt - initial_y_tilt)
        
        if tilt_change > TILT_ANGLE_THRESHOLD:
            over_threshold_count += 1
            tilt_sum += tilt_change
        else:
            over_threshold_count = 0
            tilt_sum = 0

        if over_threshold_count >= samples:  # 30 consecutive seconds above threshold
            avg_tilt = round(tilt_sum / samples, 2)

            alert = f"Y Tilt Warning: Y tilt = {avg_tilt:.2f} deg"
            if verbose:
                print(alert)
            if queue:
                message = {
                    'sensor': 'gyroscope',
                    'value': avg_tilt,
                    'alert': alert
                }
                queue.put(message)
            over_threshold_count = 0
            tilt_sum = 0

        time.sleep(1.0)


# Test function for unit testing

if __name__ == "__main__":
    collect_gyro_data(verbose=True)


