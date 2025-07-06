#   Import required libraries
import os
import glob
import time

#   Load kernel modules to interface with sensor
os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')

#   Set up paths and filenames for reading temp data
base_dir = '/sys/bus/w1/devices/'
#   Search for folder that starts with "28"
device_folder = glob.glob(base_dir + '28*')[0]
#   File containing raw temperature data
device_file = device_folder + '/w1_slave'


#   Get temp readings from file and return list
def read_temp_raw():
    f = open(device_file, 'r')
    lines = f.readlines()
    f.close()
    return lines


#   Read temperature data and return Celsius value
def read_temp():
    lines = read_temp_raw()
    #   Check for valid data
    while lines[0].strip()[-3:] != 'YES':
        time.sleep(0.2)
        lines = read_temp_raw()
    equals_pos = lines[1].find('t=')
    if equals_pos != -1:
        temp_string = lines[1][equals_pos + 2:]
        temp_c = float(temp_string) / 1000.0
        return temp_c


#   Call functions and print temperature reading
while True:
    temperature_celsius = read_temp()
    print(f'Temperature: {temperature_celsius:.2f} °C')

    #   Send alert if abnormal temperature reading
    if temperature_celsius <= 36.5:
        print("COLD WARNING: Infant’s temperature is below normal. Current temperature is below 36.5°C. Please ensure the infant is warm and check for any signs of discomfort or illness.")
    elif temperature_celsius >= 38.9:
        print("CRITICAL OVERHEAT ALERT: Current temperature is above 38.9°C. Take immediate action and consult a healthcare professional.")
    elif temperature_celsius >= 37.2:
        print("OVERHEAT ALERT: Infant’s temperature is above normal. Current temperature is above 37.2°C. Monitor infant closely - consider removing extra clothing or blankets.")

    print('')

    #   Delay between each temperature reading
    time.sleep(1)

    #   TO DO:
    #   - determine frequency of messaging (1 minute?),
    #   - take average of 60 temperature readings (frequency: 1 second?),
    #   - save data to file
