# Temperature Sensor Raspberry Pi Integration

## Wiring Instructions
| DS18B20 | Raspberry Pi |
|---------|-----------------|
| DAT     | GPIO 4          |
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

### Upload & Run the Code

#### 1. Start an Editor Window

```bash
nano temperature.py
```

#### 2. Upload Code

Paste the code from `temperature.py` located in this folder and save the file.

#### 3. Run Program

```bash
sudo python thermometer.py
```
