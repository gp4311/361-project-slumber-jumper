import os
import csv
from datetime import datetime

class CSVLogger:
    def __init__(self, log_dir: str, field_name="Value"):
        """
        Create a new CSV log file in the given directory.
        The filename includes the current timestamp.
        """
        os.makedirs(log_dir, exist_ok=True)
        timestamp_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.log_path = os.path.join(log_dir, f"log_{timestamp_str}.csv")

        self.file = open(self.log_path, mode='w', newline='')
        self.writer = csv.writer(self.file)
        self.writer.writerow(['Time', field_name])  # Write header

    def log(self, value):
        """
        Log the current time and the provided value to the CSV.
        """
        time_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.writer.writerow([time_now, value])
        self.file.flush()

    def close(self):
        """
        Close the log file.
        """
        self.file.close()
