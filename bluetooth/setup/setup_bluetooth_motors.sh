#!/bin/bash
# setup_bluetooth_motors.sh - Setup script for Bluetooth motor control

echo "=== EV3 Bluetooth Motor Control Setup ==="
echo

# Check if running on Raspberry Pi or EV3
if [ -f /etc/rpi-issue ]; then
    DEVICE="raspberry_pi"
    echo "Detected: Raspberry Pi"
elif [ -f /etc/ev3dev-release ]; then
    DEVICE="ev3"
    echo "Detected: EV3 Brick"
else
    echo "Unknown device. Please run on Raspberry Pi or EV3."
    exit 1
fi

echo

if [ "$DEVICE" = "raspberry_pi" ]; then
    echo "Setting up Raspberry Pi for Bluetooth motor control..."
    
    # Update system
    echo "Updating system packages..."
    sudo apt-get update
    
    # Install Bluetooth dependencies
    echo "Installing Bluetooth dependencies..."
    sudo apt-get install -y bluetooth bluez python3-bluetooth libbluetooth-dev
    
    # Install Python Bluetooth library
    echo "Installing PyBluez..."
    pip3 install pybluez || pip install pybluez
    
    # Enable Bluetooth service
    echo "Enabling Bluetooth service..."
    sudo systemctl enable bluetooth
    sudo systemctl start bluetooth
    
    echo
    echo "✓ Raspberry Pi setup complete!"
    echo
    echo "Next steps:"
    echo "1. Make sure your EV3 is running ev3_bluetooth_server.py"
    echo "2. Pair your devices using: bluetoothctl"
    echo "3. Run: python3 main.py"
    
elif [ "$DEVICE" = "ev3" ]; then
    echo "Setting up EV3 for Bluetooth motor control..."
    
    # Update system
    echo "Updating system packages..."
    sudo apt-get update
    
    # Install Bluetooth dependencies
    echo "Installing Bluetooth dependencies..."
    sudo apt-get install -y python3-bluetooth
    
    # Make sure ev3dev libraries are available
    pip3 install ev3dev2 || echo "ev3dev2 should be pre-installed"
    
    echo
    echo "✓ EV3 setup complete!"
    echo
    echo "Next steps:"
    echo "1. Connect motors to OUTPUT_A, B, C, D"
    echo "2. Run: python3 ev3_bluetooth_server.py"
    echo "3. Make sure EV3 is discoverable"
fi

echo
echo "=== Setup Complete ==="
