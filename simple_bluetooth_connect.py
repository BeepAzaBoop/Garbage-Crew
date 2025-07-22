# simple_bluetooth_connect.py - Simple Bluetooth connection without discovery
import json
import time

try:
    import bluetooth
    BLUETOOTH_AVAILABLE = True
except ImportError:
    print("Warning: PyBluez not available. Install with: pip install pybluez")
    BLUETOOTH_AVAILABLE = False

class SimpleBluetoothController:
    """Simple Bluetooth controller that connects directly using MAC address"""
    
    def __init__(self, ev3_address=None, port=1):
        self.ev3_address = ev3_address
        self.port = port
        self.socket = None
        self.connected = False
        
        if ev3_address and BLUETOOTH_AVAILABLE:
            self.connect()
    
    def connect_direct(self, mac_address):
        """Connect directly to EV3 using MAC address"""
        if not BLUETOOTH_AVAILABLE:
            print("Bluetooth not available")
            return False
        
        self.ev3_address = mac_address
        return self.connect()
    
    def connect(self):
        """Connect to EV3 via Bluetooth"""
        if not BLUETOOTH_AVAILABLE:
            print("Bluetooth not available - motor control will be simulated")
            return False
            
        if not self.ev3_address:
            print("No EV3 address provided")
            return False
        
        try:
            self.socket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
            self.socket.settimeout(15)  # 15 second timeout
            
            print(f"Connecting to EV3 at {self.ev3_address}...")
            self.socket.connect((self.ev3_address, self.port))
            self.connected = True
            print("✓ Connected to EV3 successfully!")
            
            # Test connection with ping
            response = self._send_command("ping")
            if response and response.get("status") == "success":
                print("✓ EV3 motor server is responding")
                return True
            else:
                print("✗ EV3 motor server not responding properly")
                return False
                
        except Exception as e:
            print(f"✗ Connection failed: {e}")
            if self.socket:
                self.socket.close()
            self.connected = False
            return False
    
    def _send_command(self, action, **kwargs):
        """Send command to EV3 and get response"""
        if not self.connected:
            print(f"Not connected - simulating: {action}")
            return {"status": "simulated", "message": f"Simulated {action}"}
        
        command = {"action": action, **kwargs}
        
        try:
            # Send command
            command_json = json.dumps(command)
            self.socket.send(command_json.encode('utf-8'))
            
            # Receive response
            response_data = self.socket.recv(1024)
            response = json.loads(response_data.decode('utf-8'))
            
            return response
            
        except Exception as e:
            print(f"Command failed: {e}")
            self.connected = False
            return {"status": "error", "message": str(e)}
    
    def handle_classification(self, label):
        """Handle classification with motor control"""
        print(f"→ Classified: {label}")
        response = self._send_command("classify", label=label)
        
        if response.get("status") == "success":
            print(f"✓ EV3 executed sorting sequence for: {label}")
        elif response.get("status") == "simulated":
            print(f"✓ Simulated sorting sequence for: {label}")
        else:
            print(f"✗ Failed to execute sorting for {label}: {response.get('message', 'Unknown error')}")
    
    def stop_all_motors(self):
        """Stop all motors"""
        response = self._send_command("stop_all")
        if response.get("status") == "success":
            print("✓ All motors stopped")
    
    def disconnect(self):
        """Disconnect from EV3"""
        if self.socket and self.connected:
            self.socket.close()
            self.connected = False
            print("Disconnected from EV3")

def get_ev3_address():
    """Get EV3 MAC address from user"""
    print("EV3 Bluetooth Connection")
    print("=" * 25)
    print()
    print("To find your EV3 MAC address:")
    print("1. On EV3: Settings > Connections > Bluetooth")
    print("2. Look for the MAC address (format: XX:XX:XX:XX:XX:XX)")
    print()
    
    # Common EV3 addresses for testing
    print("Examples:")
    print("  24:71:89:XX:XX:XX  (common EV3 prefix)")
    print("  00:16:53:XX:XX:XX  (another EV3 prefix)")
    print()
    
    while True:
        address = input("Enter EV3 MAC address: ").strip()
        if address:
            # Basic validation
            if len(address) == 17 and address.count(':') == 5:
                return address
            else:
                print("Invalid format. Use XX:XX:XX:XX:XX:XX format")
        else:
            return None

def main():
    """Test the simple connection"""
    if not BLUETOOTH_AVAILABLE:
        print("PyBluez not available. Install with: pip install pybluez")
        return
    
    # Get EV3 address
    address = get_ev3_address()
    if not address:
        print("No address provided")
        return
    
    # Create controller and connect
    controller = SimpleBluetoothController()
    if controller.connect_direct(address):
        print("Connection successful!")
        
        # Test classification
        controller.handle_classification("plastic")
        time.sleep(1)
        controller.stop_all_motors()
        controller.disconnect()
    else:
        print("Connection failed")

if __name__ == "__main__":
    main()
