# BLE Messaging System

## Requirements

### Raspberry Pi Zero 2 W

- Raspberry Pi OS
- Bluetooth onboard (Zero 2 W has this)
- Python 3 and BlueZ installed

### Windows 11 Laptop

- Bluetooth 4.0+ with BLE support
- Python 3.8+ installed
- `bleak` Python library

## Setup Instructions

### Raspberry Pi (BLE Server)

#### 1. Install Dependencies

```bash
sudo apt update
sudo apt install -y python3-pip bluetooth bluez libglib2.0-dev python3-dbus
```

#### 2. Save the BLE Server Script

Create a file called `ble_server.py` and past in the full GATT server code.

#### 3. Run the BLE GATT Server

```bash
sudo python3 ble_server.py
```

#### 4. Verify Advertisement (Optional)

In another terminal:

```bash
sudo btmon
```

You should see periodic LE Advertising Reports.

### Windows 11 Laptop (BLE Client)

#### 1. Install Dependencies

Install Python 3.8+ from https://www.python.org/downloads/.
Then install the bleak library:
```bash
pip install bleak
```

#### 2. Run the Listener

```bash 
python ble_central.py
```

#### Expected output:

``` ruby
Scanning for PiBLE...
Connected to XX:XX:XX:XX:XX:XX
Listening for notifications...
Received from ...: Hello at 12:34:56
```

