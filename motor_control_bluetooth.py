# motor_control_bluetooth.py - Bluetooth client version for Raspberry Pi
import json
import time
try:
    import bluetooth
    BLUETOOTH_AVAILABLE = True
except ImportError:
    print("Warning: PyBluez not available. Install with: pip install pybluez")
    BLUETOOTH_AVAILABLE = False

class BluetoothGarbageSortController:
    """Bluetooth client that controls EV3 motors remotely using the same interface as GarbageSortController"""
    
    def __init__(self, ev3_address=None, port=1):
        self.ev3_address = ev3_address or self.load_saved_address()
        self.port = port
        self.socket = None
        self.connected = False
        
        # Same settings as original controller
        self.speed = 50
        self.panel_deg = 45
        self.rod_deg = 40
        self.trap_deg = 95
        
        if BLUETOOTH_AVAILABLE:
            self.connect()
    
    def load_saved_address(self):
        """Load saved EV3 address from config file"""
        try:
            with open("ev3_config.txt", "r") as f:
                for line in f:
                    if line.startswith("EV3_ADDRESS="):
                        return line.split("=")[1].strip()
        except FileNotFoundError:
            pass
        return None
    
    def discover_ev3(self):
        """Discover EV3 devices via Bluetooth"""
        if not BLUETOOTH_AVAILABLE:
            return None
            
        print("Scanning for EV3 devices...")
        try:
            nearby_devices = bluetooth.discover_devices(lookup_names=True, duration=10)
            
            ev3_devices = []
            for addr, name in nearby_devices:
                if "ev3" in name.lower() or "lego" in name.lower():
                    ev3_devices.append((addr, name))
                    print(f"Found EV3: {name} - {addr}")
            
            if not ev3_devices:
                print("No EV3 devices found")
                return None
            
            if len(ev3_devices) == 1:
                return ev3_devices[0][0]
            else:
                print("Multiple EV3 devices found:")
                for i, (addr, name) in enumerate(ev3_devices):
                    print(f"{i}: {name} - {addr}")
                try:
                    choice = int(input("Select device (number): "))
                    return ev3_devices[choice][0]
                except (ValueError, IndexError):
                    return ev3_devices[0][0]
        except Exception as e:
            print(f"Discovery failed: {e}")
            return None
    
    def connect(self):
        """Connect to EV3 via Bluetooth"""
        if not BLUETOOTH_AVAILABLE:
            print("Bluetooth not available - motor control will be simulated")
            return False
            
        if not self.ev3_address:
            self.ev3_address = self.discover_ev3()
            if not self.ev3_address:
                print("No EV3 address available")
                return False
        
        try:
            self.socket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
            print(f"Connecting to EV3 at {self.ev3_address}...")
            self.socket.connect((self.ev3_address, self.port))
            self.connected = True
            print("✓ Connected to EV3 successfully!")
            
            # Test connection
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
    
    # Same interface as original GarbageSortController
    def shift_panels(self, direction):
        """45° shift: 'left', 'right', or None."""
        response = self._send_command("shift_panels", direction=direction)
        if response.get("status") == "success":
            print(f"Panels moved {direction or 'center'}")
        time.sleep(0.2)
    
    def reset_panels(self):
        """Return panels to center."""
        response = self._send_command("reset_panels")
        if response.get("status") == "success":
            print("Panels reset to center")
        time.sleep(0.2)
    
    def extend_rods(self):
        """Raise support rods."""
        response = self._send_command("extend_rods")
        if response.get("status") == "success":
            print("Rods extended")
        time.sleep(0.2)
    
    def retract_rods(self):
        """Lower support rods."""
        response = self._send_command("retract_rods")
        if response.get("status") == "success":
            print("Rods retracted")
        time.sleep(0.2)
    
    def open_trap(self):
        """Open trap doors."""
        response = self._send_command("open_trap")
        if response.get("status") == "success":
            print("Trap opened")
        time.sleep(0.2)
    
    def close_trap(self):
        """Close trap doors."""
        response = self._send_command("close_trap")
        if response.get("status") == "success":
            print("Trap closed")
        time.sleep(0.2)
    
    def handle_classification(self, label):
        """Main method that handles the full sorting sequence - same as original"""
        print(f"→ Classified: {label}")
        
        # Send the classification command to EV3
        response = self._send_command("classify", label=label)
        
        if response.get("status") == "success":
            print(f"✓ EV3 executed sorting sequence for: {label}")
        elif response.get("status") == "simulated":
            print(f"✓ Simulated sorting sequence for: {label}")
        else:
            print(f"✗ Failed to execute sorting for {label}: {response.get('message', 'Unknown error')}")
    
    def set_motor_settings(self, speed=50, panel_deg=45, rod_deg=90, trap_deg=80):
        """Configure motor settings"""
        self.speed = speed
        self.panel_deg = panel_deg
        self.rod_deg = rod_deg
        self.trap_deg = trap_deg
        
        settings = {
            "speed": speed,
            "panel_deg": panel_deg,
            "rod_deg": rod_deg,
            "trap_deg": trap_deg
        }
        
        response = self._send_command("configure", settings=settings)
        if response.get("status") == "success":
            print(f"✓ Motor settings updated: speed={speed}%, panel={panel_deg}°, rod={rod_deg}°, trap={trap_deg}°")
    
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

# Global instance - will auto-connect when imported
garbage_sort_controller = BluetoothGarbageSortController()
