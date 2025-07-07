from multiprocessing import Process, Queue
from sensors.Temperature.temperature import collect_temperature_data
from sensors.MPU9250.accel_gyro import collect_gyro_data
from ble.ble_sender import main as ble_main

def main():
    # Shared queue for sensor data
    data_queue = Queue()

    # Define processes
    processes = [
        Process(target=collect_temperature_data, args=(data_queue,)),
        Process(target=collect_gyro_data, args=(data_queue,)),
        Process(target=ble_main, args=(data_queue,))
    ]

    # Start processes
    for p in processes:
        p.start()

    # Wait for all processes to complete
    for p in processes:
        p.join()

if __name__ == "__main__":
    main()
