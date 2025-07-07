import sys
import os
sys.path.append(os.path.dirname(__file__))

import max30102
import hrcalc
import time

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from logger import CSVLogger 

import json

# Set abnormal threshold values
hr_high = 160
hr_low = 90
spo2_low = 90

# Set time between alerts to prevent overcommunication
time_between_alerts = 120

sensor = max30102.MAX30102()

def collect_hr_spo2_data(queue=None, verbose=False):
    last_alert_time = 0
    recent_hrs = []
    recent_spo2s = []

    logger = CSVLogger(log_dir='logs', field_name='Value')

    try:

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
                if verbose:
                    print("Poor reading")

            # Average and evaluate every 10 readings
            if len(recent_hrs) == 10:
                avg_hr = sum(recent_hrs) / len(recent_hrs)
                avg_spo2 = sum(recent_spo2s) / len(recent_spo2s)
                recent_hrs = []
                recent_spo2s = []

                if verbose:
                    print(f"HR: {avg_hr:.0f} BPM")
                    print(f"SpO2: {avg_spo2:.0f}%")
                
                if logger:
                    logger.log(json.dumps({'hr': round(avg_hr, 1), 'spo2': round(avg_spo2, 1)}))
                
                alert = None
                if avg_hr > hr_high:
                    alert = f"High heart rate of {avg_hr:.0f} BPM!"
                elif avg_hr < hr_low:
                    alert = f"Low heart rate of {avg_hr:.0f} BPM!"
                elif avg_spo2 < spo2_low:
                    alert = f"Low blood oxygen level of {avg_spo2:.0f}%"

                if alert and current_time - last_alert_time >= time_between_alerts:
                    if queue:
                        message = {
                            'sensor': 'heart',
                            'value': {
                                'hr': round(avg_hr, 1),
                                'spo2': round(avg_spo2, 1)
                            },
                            'alert': alert
                        }
                        queue.put(message)

                    last_alert_time = current_time

            time.sleep(1)
    
    finally:
        logger.close()


# Test function for unit testing

if __name__ == "__main__":
    collect_hr_spo2_data(verbose=True)