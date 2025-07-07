# sensors/Temperature/temperature.py

import os
import glob
import time

# Load kernel modules to interface with sensor
os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')

# Set up paths and filenames for reading temp data
base_dir = '/sys/bus/w1/devices/'
# Search for folder that starts with "28"
device_folder = glob.glob(base_dir + '28*')[0]
# File containing raw temperature data
device_file = device_folder + '/w1_slave'


# Get temp readings from file and return list
def read_temp_raw():
    f = open(device_file, 'r')
    lines = f.readlines()
    f.close()
    return lines


# Read temperature data and return Celsius value
def read_temp():
    lines = read_temp_raw()
    # Check for valid data
    while lines[0].strip()[-3:] != 'YES':
        time.sleep(0.2)
        lines = read_temp_raw()
    equals_pos = lines[1].find('t=')
    if equals_pos != -1:
        temp_string = lines[1][equals_pos + 2:]
        temp_c = float(temp_string) / 1000.0
        return temp_c


# Main function to be called by main.py

def collect_temperature_data(queue):
    interval_len = 60

    # Set temperature thresholds
    cold_bound = 36.5
    hot_bound = 37.2
    very_hot_bound = 38.9

    while True:
        temp_sum = 0

        # Frequency of readings: 1 second
        # Frequency of messaging: 1 minute (average of 60 temp readings)
        for i in range(interval_len):
            temperature_celsius = read_temp()
            temp_sum += temperature_celsius

            # Delay between each temperature reading
            time.sleep(1)
        
        avg_temp = temp_sum / interval_len
        
        alert = None

        # Send alert if abnormal temperature reading
        if avg_temp <= cold_bound:
            alert = f'COLD WARNING: Temp {avg_temp:.2f}°C < {cold_bound}°C'
        elif avg_temp >= very_hot_bound:
            alert = f'CRITICAL OVERHEAT ALERT: Temp {avg_temp:.2f}°C > {very_hot_bound}°C'
        elif avg_temp >= hot_bound:
            alert = f'OVERHEAT ALERT: Temp {avg_temp:.2f}°C > {hot_bound}°C'
        
        # Send to BLE queue
        message = {
            'sensor': 'temperature',
            'value': avg_temp,
            'alert': alert
        }
        queue.put(message)
    
# TO DO: Log all outputs to a .txt file 