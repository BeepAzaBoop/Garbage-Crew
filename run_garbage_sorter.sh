#!/bin/bash
# run_garbage_sorter.sh - Simple script to run the garbage sorting system

echo "🗑️ Garbage Sorting System Startup 🗑️"
echo "======================================"
echo

# Check if we're on Raspberry Pi
if [ ! -f /etc/rpi-issue ]; then
    echo "❌ This script should be run on Raspberry Pi"
    exit 1
fi

echo "📋 Checking requirements..."

# Check if Python packages are installed
python3 -c "import cv2, torch, bluetooth" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ Missing Python packages. Please run:"
    echo "   pip install -r requirements.txt"
    echo "   pip install pybluez"
    exit 1
fi

echo "✅ Python packages OK"

# Check if camera is available
if [ ! -e /dev/video0 ]; then
    echo "⚠️  Warning: No camera detected at /dev/video0"
fi

echo "✅ Camera check complete"

echo
echo "📶 Starting Bluetooth discovery..."
echo "Make sure your EV3 is running: python3 ev3_bluetooth_server.py"
echo

# Ask user for run options
echo "Select run mode:"
echo "1) Basic (default)"
echo "2) Quantized (faster)"
echo "3) With YOLO detection"
echo "4) Snapshot mode"
echo "5) Quantized + YOLO"
read -p "Enter choice (1-5): " choice

case $choice in
    1) ARGS="" ;;
    2) ARGS="--quantized" ;;
    3) ARGS="--yolo" ;;
    4) ARGS="--snapshot" ;;
    5) ARGS="--quantized --yolo" ;;
    *) ARGS="" ;;
esac

echo
echo "🚀 Starting Garbage Sorting System..."
echo "Args: $ARGS"
echo
echo "Controls:"
echo "  - 's': Take snapshot (in snapshot mode)"
echo "  - 'r': Release snapshot"
echo "  - 'q': Quit"
echo
echo "Press Ctrl+C to stop"
echo

# Run the main program
python3 main.py $ARGS
