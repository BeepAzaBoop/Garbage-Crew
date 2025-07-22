#!/usr/bin/env python3
# quick_bluetooth_test.py - Quick Bluetooth connection test

def test_bluetooth_simple():
    """Simple test without device discovery"""
    
    print("🤖 Quick Bluetooth Test")
    print("=" * 20)
    
    try:
        import bluetooth
        print("✅ PyBluez imported successfully")
    except ImportError as e:
        print(f"❌ PyBluez import failed: {e}")
        print("Install with: pip install pybluez")
        return False
    
    # Get EV3 address from user
    print("\nTo find your EV3 MAC address:")
    print("1. On EV3: Settings > Connections > Bluetooth")
    print("2. Note the MAC address (XX:XX:XX:XX:XX:XX)")
    print()
    
    ev3_address = input("Enter EV3 MAC address: ").strip()
    if not ev3_address:
        print("No address provided")
        return False
    
    # Test connection
    print(f"\nTesting connection to {ev3_address}...")
    
    try:
        import json
        
        # Create socket
        sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        sock.settimeout(10)
        
        # Connect
        sock.connect((ev3_address, 1))
        print("✅ Connected successfully!")
        
        # Send ping
        ping_cmd = json.dumps({"action": "ping"})
        sock.send(ping_cmd.encode('utf-8'))
        
        # Receive response
        response_data = sock.recv(1024)
        response = json.loads(response_data.decode('utf-8'))
        
        if response.get("status") == "success":
            print("✅ EV3 server is responding!")
            
            # Test motor command
            test_cmd = json.dumps({"action": "classify", "label": "plastic"})
            sock.send(test_cmd.encode('utf-8'))
            response_data = sock.recv(1024)
            response = json.loads(response_data.decode('utf-8'))
            
            if response.get("status") == "success":
                print("✅ Motor control test successful!")
            else:
                print(f"⚠️  Motor test response: {response}")
            
        else:
            print(f"❌ Server response: {response}")
        
        sock.close()
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure EV3 Bluetooth is enabled")
        print("2. Make sure EV3 is running: python3 ev3_bluetooth_server.py")
        print("3. Check the MAC address is correct")
        print("4. Try pairing first: bluetoothctl")
        return False

if __name__ == "__main__":
    test_bluetooth_simple()
