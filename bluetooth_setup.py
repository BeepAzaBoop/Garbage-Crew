#!/usr/bin/env python3
# bluetooth_setup.py - Setup Bluetooth connection with EV3

import bluetooth
import time
import subprocess
import sys

def check_bluetooth_service():
    """Check if Bluetooth service is running"""
    try:
        result = subprocess.run(['systemctl', 'is-active', 'bluetooth'], 
                              capture_output=True, text=True)
        if result.stdout.strip() != 'active':
            print("❌ Bluetooth service not running")
            print("Run: sudo systemctl start bluetooth")
            return False
        print("✅ Bluetooth service is running")
        return True
    except Exception as e:
        print(f"❌ Could not check Bluetooth service: {e}")
        return False

def discover_ev3_devices():
    """Discover EV3 devices"""
    print("🔍 Scanning for EV3 devices...")
    print("Make sure your EV3 is discoverable!")
    
    try:
        # Scan for nearby devices
        nearby_devices = bluetooth.discover_devices(lookup_names=True, duration=15)
        
        ev3_devices = []
        print(f"\nFound {len(nearby_devices)} Bluetooth devices:")
        
        for addr, name in nearby_devices:
            print(f"  {name} - {addr}")
            if "ev3" in name.lower() or "lego" in name.lower():
                ev3_devices.append((addr, name))
        
        if not ev3_devices:
            print("\n❌ No EV3 devices found")
            print("Make sure:")
            print("1. EV3 Bluetooth is enabled")
            print("2. EV3 is set to discoverable")
            print("3. EV3 is running ev3_bluetooth_server.py")
            return None
        
        print(f"\n✅ Found {len(ev3_devices)} EV3 device(s):")
        for i, (addr, name) in enumerate(ev3_devices):
            print(f"  {i+1}. {name} - {addr}")
        
        if len(ev3_devices) == 1:
            return ev3_devices[0]
        else:
            while True:
                try:
                    choice = int(input(f"\nSelect EV3 device (1-{len(ev3_devices)}): ")) - 1
                    if 0 <= choice < len(ev3_devices):
                        return ev3_devices[choice]
                    else:
                        print("Invalid choice")
                except ValueError:
                    print("Please enter a number")
                    
    except Exception as e:
        print(f"❌ Discovery failed: {e}")
        return None

def test_connection(address, name):
    """Test connection to EV3"""
    print(f"\n🔗 Testing connection to {name} ({address})...")
    
    try:
        # Try to connect
        sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        sock.settimeout(10)
        sock.connect((address, 1))  # Port 1
        
        # Send ping command
        import json
        ping_command = json.dumps({"action": "ping"})
        sock.send(ping_command.encode('utf-8'))
        
        # Receive response
        response_data = sock.recv(1024)
        response = json.loads(response_data.decode('utf-8'))
        
        sock.close()
        
        if response.get("status") == "success":
            print("✅ Connection test successful!")
            print(f"✅ EV3 server is responding properly")
            return True
        else:
            print("❌ EV3 server not responding correctly")
            return False
            
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        print("Make sure EV3 is running: python3 ev3_bluetooth_server.py")
        return False

def save_ev3_address(address, name):
    """Save EV3 address for future use"""
    try:
        with open("ev3_config.txt", "w") as f:
            f.write(f"EV3_ADDRESS={address}\n")
            f.write(f"EV3_NAME={name}\n")
        print(f"✅ Saved EV3 config: {name} ({address})")
    except Exception as e:
        print(f"⚠️  Could not save config: {e}")

def main():
    print("🤖 EV3 Bluetooth Setup Tool")
    print("=" * 30)
    
    # Check Bluetooth service
    if not check_bluetooth_service():
        return 1
    
    # Discover EV3 devices
    ev3_device = discover_ev3_devices()
    if not ev3_device:
        return 1
    
    address, name = ev3_device
    print(f"\n📱 Selected: {name} ({address})")
    
    # Test connection
    if test_connection(address, name):
        save_ev3_address(address, name)
        print("\n🎉 Setup complete!")
        print("You can now run: python3 main.py")
        return 0
    else:
        print("\n❌ Setup failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
