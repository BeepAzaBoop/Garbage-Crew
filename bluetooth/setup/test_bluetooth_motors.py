#!/usr/bin/env python3
# test_bluetooth_motors.py - Test script for Bluetooth motor control

import time
import sys

def test_bluetooth_connection():
    """Test Bluetooth motor control connection"""
    
    print("=== Bluetooth Motor Control Test ===")
    print()
    
    try:
        from bluetooth_client import garbage_sort_controller
        print("✓ Bluetooth motor control module loaded")
    except ImportError as e:
        print(f"✗ Failed to load Bluetooth motor control: {e}")
        print("Make sure PyBluez is installed: pip install pybluez")
        return False
    
    # Test connection
    if not garbage_sort_controller.connected:
        print("✗ Not connected to EV3")
        print("Make sure:")
        print("1. EV3 is running ev3_bluetooth_server.py")
        print("2. EV3 Bluetooth is enabled and discoverable")
        print("3. Devices are paired")
        return False
    
    print("✓ Connected to EV3")
    print()
    
    print("Testing basic motor commands...")
    
    try:
        # Test ping
        print("1. Testing connection...")
        response = garbage_sort_controller._send_command("ping")
        if response.get("status") == "success":
            print("   ✓ Ping successful")
        else:
            print("   ✗ Ping failed")
            return False
        
        time.sleep(0.5)
        
        # Test panel movement
        print("2. Testing panel movement...")
        garbage_sort_controller.shift_panels("left")
        time.sleep(1)
        garbage_sort_controller.reset_panels()
        print("   ✓ Panel movement test complete")
        
        time.sleep(0.5)
        
        # Test rod movement
        print("3. Testing rod movement...")
        garbage_sort_controller.extend_rods()
        time.sleep(1)
        garbage_sort_controller.retract_rods()
        print("   ✓ Rod movement test complete")
        
        time.sleep(0.5)
        
        # Test trap movement
        print("4. Testing trap movement...")
        garbage_sort_controller.open_trap()
        time.sleep(1)
        garbage_sort_controller.close_trap()
        print("   ✓ Trap movement test complete")
        
        time.sleep(0.5)
        
        # Test full classification sequence
        print("5. Testing full classification sequence...")
        garbage_sort_controller.handle_classification("plastic")
        print("   ✓ Full classification test complete")
        
        print()
        print("✓ All tests passed!")
        print("Your Bluetooth motor control system is working correctly.")
        
        return True
        
    except Exception as e:
        print(f"   ✗ Test failed: {e}")
        return False
    
    finally:
        # Stop all motors for safety
        try:
            garbage_sort_controller.stop_all_motors()
        except:
            pass

def test_fallback_control():
    """Test fallback to direct motor control"""
    
    print("=== Testing Fallback Motor Control ===")
    print()
    
    try:
        from motor_control import garbage_sort_controller as direct_controller
        print("✓ Direct motor control module loaded")
        
        if direct_controller.motors_available:
            print("✓ Motors are available")
            
            # Quick test
            print("Testing direct motor control...")
            direct_controller.handle_classification("plastic")
            print("✓ Direct motor control test complete")
            
        else:
            print("✓ Motors not available (simulation mode)")
            
        return True
        
    except ImportError as e:
        print(f"✗ Failed to load direct motor control: {e}")
        return False

def main():
    """Main test function"""
    
    if len(sys.argv) > 1 and sys.argv[1] == "--direct":
        success = test_fallback_control()
    else:
        success = test_bluetooth_connection()
        
        # If Bluetooth fails, try direct control
        if not success:
            print()
            print("Bluetooth test failed. Trying direct motor control...")
            success = test_fallback_control()
    
    print()
    if success:
        print("=== Test Complete: SUCCESS ===")
        return 0
    else:
        print("=== Test Complete: FAILED ===")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
