from smbus2 import SMBus, i2c_msg
import time
import math


# I2C address
MPU_ADDR = 0x68

# Addresses
PWR_MGMT_1   = 0x6B
ACCEL_XOUT_H = 0x3B
GYRO_XOUT_H  = 0x43

i2c = SMBus(1) 

# Wake up MPU-9250
write = i2c_msg.write(MPU_ADDR, [PWR_MGMT_1, 0x00])
i2c.i2c_rdwr(write)

# Setup values for calibration
accel_offset = [0.0, 0.0, 0.0]
gyro_offset = [0.0, 0.0, 0.0]

# deg prior to alert
TILT_ANGLE_THRESHOLD = 30   


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

    # Convert +2g scale used for pi zero 
    ax_g = ax / 16384.0
    ay_g = ay / 16384.0
    az_g = az / 16384.0

    # Convert to m/s^2 
    ax_ms2 = ax_g * 9.81
    ay_ms2 = ay_g * 9.81
    az_ms2 = az_g * 9.81

    return [ax_ms2, ay_ms2, az_ms2]

def read_gyro():
    # conevert to degress scale from the scale used by mpu 9250
    gx = read_word_2c(GYRO_XOUT_H)
    gy = read_word_2c(GYRO_XOUT_H + 2)
    gz = read_word_2c(GYRO_XOUT_H + 4)
    return [gx / 131.0, gy / 131.0, gz / 131.0]  

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
    accel_offset[2] -= 9.81  # Remove gravity from z direction (downwards)
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
        raise RuntimeError("Calibration failed.")

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

def get_pitch_angles():
    ax, ay, az = read_calibrated_accel()
    pitch = math.degrees(math.atan2(-ax, math.sqrt(ay * ay + az * az)))
    return pitch




# Main function to be called by main.py

def collect_gyro_data(queue=None, verbose=False):
    calibrate_accelerometer()
    gyro_calibration()
    initial_y_tilt = get_y_tilt_angle()

    if verbose:
        print("\nMonitoring tilt...\n")

    while True:
        accel = read_calibrated_accel()
        gyro = read_calibrated_gyro()
        _, ay, az = accel
        gx, _, _ = gyro

        current_y_tilt = math.degrees(math.atan2(ay, az))
        tilt_change = abs(current_y_tilt - initial_y_tilt)

        pitch = get_pitch_angles()

        # if verbose:
        #     print(f"Current tilt Y: {current_y_tilt:.2f}°, Initial: {initial_y_tilt:.2f}°, Δ: {tilt_change:.2f}°")

        alert = None
        samples = 100
        for tilt_change in range(samples):
            tilt_sum += tilt_change
        avg_tilt = round(tilt_sum / samples, 2)
        
        if avg_tilt > TILT_ANGLE_THRESHOLD:
            alert = f"Y Tilt Warning: Y tilt = {tilt_change:.2f} deg"
            if verbose:
                print(alert)        


        if alert and queue:
            message = {
                'sensor': 'gyroscope',
                'value': {
                    'tilt_y': round(avg_tilt, 2),
                    'gx': round(gx, 2),
                    'pitch': round(pitch, 2)
                },
                'alert': alert
            }
            queue.put(message)

        time.sleep(0.1)

# Test function for unit testing

if __name__ == "__main__":
    collect_gyro_data(verbose=True)