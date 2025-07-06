import max30102
import hrcalc
import time

# Set abnormal threshold values
hr_high = 160
hr_low = 90
spo2_low = 90

# Set time between alerts to prevent overcommunication
time_between_alerts = 120

sensor = max30102.MAX30102()

def get_max30102_data():
    last_alert_time = 0
    recent_hrs = []
    recent_spo2s = []
    while True:
        # Read data
        red, ir = sensor.read_sequential()
        # Calculate HR and SpO2
        hr, hr_is_valid, spo2, spo2_is_valid = hrcalc.calc_hr_and_spo2(ir, red)

        current_time = time.time()
        if hr_is_valid and spo2_is_valid:
            recent_hrs.append(hr)
            recent_spo2s.append(spo2)
        else:
            print("Poor reading")

        # Average last 10 readings
        if len(recent_hrs) == 10:
            avg_hr = sum(recent_hrs) / len(recent_hrs)
            avg_spo2 = sum(recent_spo2s) / len(recent_spo2s)
            print(f"HR: {avg_hr} BPM")
            print(f"SpO2: {avg_spo2} %")
            # Reset arrays
            recent_hrs = []
            recent_spo2s = []

            # Check if abnormal:
            if avg_hr > hr_high:
                message = f"High heart rate of {hr:.0f} BPM!\n"
                if current_time - last_alert_time >= time_between_alerts:
                    # bt_serial.write(message.encode())
                    last_alert_time = current_time
            elif avg_hr < hr_low:
                message = f"Low heart rate of {hr:.0f} BPM!\n"
                if current_time - last_alert_time >= time_between_alerts:
                    # bt_serial.write(message.encode())
                    last_alert_time = current_time
            elif avg_spo2 < spo2_low:
                message = f"Low blood oxygen levels of {spo2:.0f}%\n"
                if current_time - last_alert_time >= time_between_alerts:
                    # bt_serial.write(message.encode())
                    last_alert_time = current_time
            else:
                pass

        time.sleep(1)

if __name__ == "__main__":
   get_max30102_data()