# EV3 Bluetooth Motor Control Setup Guide

## Overview
This setup allows your Raspberry Pi to run the garbage classification model and automatically control EV3 motors via Bluetooth. The classification happens on the Raspberry Pi, and motor commands are sent wirelessly to the EV3 brick.

## Architecture
```
Raspberry Pi (main.py) ──Bluetooth──> EV3 Brick (ev3_bluetooth_server.py)
    ↓                                        ↓
Classification Model                    Motor Control
    ↓                                        ↓
motor_control_bluetooth.py ────────> motor_control.py
```

## Setup Instructions

### Step 1: Prepare the EV3 Brick

1. **Install ev3dev on your EV3 brick** (if not already done)
2. **Copy files to EV3:**
   ```bash
   # Copy these files to your EV3 brick
   scp motor_control.py robot@ev3dev.local:~/
   scp ev3_bluetooth_server.py robot@ev3dev.local:~/
   ```

3. **Install Bluetooth dependencies on EV3:**
   ```bash
   # SSH into your EV3
   ssh robot@ev3dev.local
   
   # Install Python Bluetooth
   sudo apt-get update
   sudo apt-get install python3-bluetooth
   ```

4. **Connect your motors to the EV3:**
   - Panel Left Motor → OUTPUT_A
   - Panel Right Motor → OUTPUT_B  
   - Rod Motor → OUTPUT_C
   - Trap Motor → OUTPUT_D

5. **Start the Bluetooth server on EV3:**
   ```bash
   # On the EV3 brick
   python3 ev3_bluetooth_server.py
   ```

### Step 2: Prepare the Raspberry Pi

1. **Install Bluetooth dependencies:**
   ```bash
   # On Raspberry Pi
   sudo apt-get update
   sudo apt-get install bluetooth bluez python3-bluetooth
   pip install pybluez
   ```

2. **Enable Bluetooth and make EV3 discoverable:**
   ```bash
   # Enable Bluetooth
   sudo systemctl enable bluetooth
   sudo systemctl start bluetooth
   
   # Make sure Bluetooth is working
   bluetoothctl
   # In bluetoothctl:
   # power on
   # agent on
   # discoverable on
   # scan on
   # (look for your EV3)
   # pair XX:XX:XX:XX:XX:XX  (EV3 MAC address)
   # trust XX:XX:XX:XX:XX:XX
   # exit
   ```

3. **Test the connection:**
   ```bash
   # Test Bluetooth motor control
   python3 motor_control_bluetooth.py
   ```

### Step 3: Run the Complete System

1. **Start EV3 server (on EV3 brick):**
   ```bash
   python3 ev3_bluetooth_server.py
   ```

2. **Run classification with motor control (on Raspberry Pi):**
   ```bash
   # Basic usage
   python3 main.py
   
   # With quantized model
   python3 main.py --quantized
   
   # With YOLO detection
   python3 main.py --yolo
   
   # Snapshot mode
   python3 main.py --snapshot
   ```

## Usage

### Automatic Operation
- The system will automatically classify garbage when motion is detected
- Motor commands are sent automatically to the EV3 via Bluetooth
- No manual intervention required

### Manual Controls
- **'s'**: Take snapshot (in snapshot mode)
- **'r'**: Release snapshot (in snapshot mode)  
- **'q'**: Quit application

### Classification to Motor Mapping
- **Plastic, Metal, Paper/Cardboard** → Panels shift LEFT
- **Trash** → Panels shift RIGHT
- **Compost/Organic** → Panels stay CENTER
- **Glass, Textiles, Battery** → No movement (rejected items)

## Troubleshooting

### EV3 Connection Issues

1. **"No EV3 devices found"**
   ```bash
   # Make sure EV3 is discoverable
   # Check if EV3 Bluetooth is enabled
   # Try manual pairing first
   ```

2. **"Connection failed"**
   ```bash
   # Restart Bluetooth on both devices
   sudo systemctl restart bluetooth
   
   # Check if server is running on EV3
   ps aux | grep ev3_bluetooth_server
   ```

3. **"Motor init failed"**
   ```bash
   # Check motor connections
   # Verify OUTPUT_A, B, C, D are connected
   # Check EV3 battery level
   ```

### Raspberry Pi Issues

1. **"Import bluetooth could not be resolved"**
   ```bash
   pip install pybluez
   # If that fails:
   sudo apt-get install python3-bluetooth
   ```

2. **"Motor control not available"**
   ```bash
   # Check if motor_control_bluetooth.py is in the same directory
   # Verify Bluetooth is working: bluetoothctl
   ```

### Performance Issues

1. **Slow classification/motor response**
   ```bash
   # Use quantized model for faster inference
   python3 main.py --quantized
   
   # Adjust motor speeds in motor_control.py
   ```

2. **Connection drops**
   ```bash
   # Check Bluetooth range
   # Verify power levels on both devices
   # Restart Bluetooth services
   ```

## Auto-Start Setup (Optional)

### EV3 Auto-Start Server
Create `/etc/systemd/system/ev3-motor-server.service`:
```ini
[Unit]
Description=EV3 Bluetooth Motor Server
After=bluetooth.service

[Service]
Type=simple
User=robot
WorkingDirectory=/home/robot
ExecStart=/usr/bin/python3 /home/robot/ev3_bluetooth_server.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Enable the service:
```bash
sudo systemctl enable ev3-motor-server.service
sudo systemctl start ev3-motor-server.service
```

### Raspberry Pi Auto-Start Classification
Create `/etc/systemd/system/garbage-classifier.service`:
```ini
[Unit]
Description=Garbage Classifier with Motor Control
After=bluetooth.service

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/Garbage-Crew
ExecStart=/usr/bin/python3 /home/pi/Garbage-Crew/main.py --quantized
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable the service:
```bash
sudo systemctl enable garbage-classifier.service
sudo systemctl start garbage-classifier.service
```

## Testing Commands

### Test Individual Motor Functions
```python
# In Python on Raspberry Pi
from motor_control_bluetooth import garbage_sort_controller

# Test individual movements
garbage_sort_controller.shift_panels("left")
garbage_sort_controller.reset_panels()
garbage_sort_controller.extend_rods()
garbage_sort_controller.retract_rods()
garbage_sort_controller.open_trap()
garbage_sort_controller.close_trap()

# Test full classification
garbage_sort_controller.handle_classification("plastic")
```

### Monitor EV3 Server
```bash
# On EV3, check server logs
journalctl -u ev3-motor-server.service -f
```

### Monitor Raspberry Pi Classification
```bash
# On Raspberry Pi, check classification logs  
journalctl -u garbage-classifier.service -f
```
