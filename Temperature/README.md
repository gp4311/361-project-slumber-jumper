# Temperature Sensor Raspberry Pi Integration

## Wiring Instructions
| DS18B20 | Raspberry Pi    |
|---------|-----------------|
| DAT     | GPIO 4, GPIO 17 |
| VCC     | 3.3V            |
| GND     | GND             |

## Software Setup Instructions

### Enable 1-Wire

#### 1. Open Raspberry Pi Software Configuration Tool

```bash
sudo raspi-config
```

#### 2. Make Edits to Raspberry Pi Config

In the menu, select **3 Interface Options**.
Select **I7 1-wire**.
Select **Yes** to enable one-wire interface.
Select **Finish**.

#### 3. Reboot Raspberry Pi

```bash
sudo reboot
```

#### 4. Verify 1-Wire Kernel Modules (Optional)

```bash
lsmod | grep -i w1_
```
You should see some output like: `w1_therm`..., `w1_gpio`..., `wire`...

### Enable Multiple 1-Wire Buses
#### 1. Edit Config File 
```bash
sudo nano /boot/config.txt
```

#### 2. Add Multiple `dtoverlay` Statements & `gpiopin` Parameter to `w1-gpio` Overlay
For example, to enable 1-Wire buses on GPIO 4 and GPIO 17:
```bash
dtoverlay=w1-gpio,gpiopin=4
dtoverlay=w1-gpio,gpiopin=17
```
Press CTRL-X, then press Y and Enter to save the changes.

#### 3. Reboot Raspberry Pi

```bash
sudo reboot
```

### Upload & Run the Code

#### 1. Start an Editor Window

```bash
sudo nano temperature.py
```

#### 2. Upload Code

Paste the code from `temperature.py` located in this folder and save the file.

#### 3. Run Program

```bash
sudo python thermometer.py
```
