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
            # Try different discovery methods
            nearby_devices = []
            
            # Method 1: Try standard bluetooth.discover_devices
            try:
                nearby_devices = bluetooth.discover_devices(lookup_names=True, duration=10)
                print(f"Found {len(nearby_devices)} devices using standard discovery")
            except AttributeError:
                print("Standard discovery not available, trying alternative methods...")
                
            # Method 2: If standard discovery fails, try without lookup_names
            if not nearby_devices:
                try:
                    device_addresses = bluetooth.discover_devices(duration=10)
                    nearby_devices = [(addr, f"Device-{addr[-5:]}") for addr in device_addresses]
                    print(f"Found {len(nearby_devices)} devices using basic discovery")
                except:
                    pass
            
            # Method 3: Try using bluetoothctl command as fallback
            if not nearby_devices:
                try:
                    import subprocess
                    print("Trying bluetoothctl discovery...")
                    
                    # Start scan
                    subprocess.run(['bluetoothctl', 'scan', 'on'], timeout=2)
                    time.sleep(5)  # Wait for devices to be discovered
                    
                    # Get devices
                    result = subprocess.run(['bluetoothctl', 'devices'], 
                                          capture_output=True, text=True, timeout=5)
                    
                    for line in result.stdout.split('\n'):
                        if 'Device' in line:
                            parts = line.split()
                            if len(parts) >= 3:
                                addr = parts[1]
                                name = ' '.join(parts[2:])
                                nearby_devices.append((addr, name))
                    
                    # Stop scan
                    subprocess.run(['bluetoothctl', 'scan', 'off'], timeout=2)
                    print(f"Found {len(nearby_devices)} devices using bluetoothctl")
                    
                except Exception as e:
                    print(f"Bluetoothctl discovery failed: {e}")
            
            # Filter for EV3 devices
            ev3_devices = []
            print("\nFound devices:")
            for addr, name in nearby_devices:
                print(f"  {name} - {addr}")
                if "ev3" in name.lower() or "lego" in name.lower():
                    ev3_devices.append((addr, name))
            
            if not ev3_devices:
                print("\n❌ No EV3 devices found")
                print("Try manually entering the EV3 MAC address...")
                manual_addr = input("Enter EV3 MAC address (or press Enter to skip): ").strip()
                if manual_addr:
                    return manual_addr
                return None
            
            if len(ev3_devices) == 1:
                print(f"✅ Found EV3: {ev3_devices[0][1]} - {ev3_devices[0][0]}")
                return ev3_devices[0][0]
            else:
                print(f"\n✅ Found {len(ev3_devices)} EV3 devices:")
                for i, (addr, name) in enumerate(ev3_devices):
                    print(f"  {i+1}. {name} - {addr}")
                try:
                    choice = int(input("Select device (number): ")) - 1
                    if 0 <= choice < len(ev3_devices):
                        return ev3_devices[choice][0]
                    else:
                        return ev3_devices[0][0]
                except (ValueError, IndexError):
                    return ev3_devices[0][0]
                    
        except Exception as e:
            print(f"Discovery failed: {e}")
            print("Try manually entering the EV3 MAC address...")
            manual_addr = input("Enter EV3 MAC address (or press Enter to skip): ").strip()
            if manual_addr:
                return manual_addr
            return None
    
    def connect(self):
        """Connect to EV3 via Bluetooth"""
        if not BLUETOOTH_AVAILABLE:
            print("Bluetooth not available - motor control will be simulated")
            return False
            
        if not self.ev3_address:
            print("No saved EV3 address found. Trying discovery...")
            self.ev3_address = self.discover_ev3()
            if not self.ev3_address:
                print("❌ No EV3 address available")
                print("💡 You can manually set the address by creating ev3_config.txt with:")
                print("   EV3_ADDRESS=XX:XX:XX:XX:XX:XX")
                return False
        
        try:
            self.socket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
            self.socket.settimeout(15)  # 15 second timeout
            
            print(f"Connecting to EV3 at {self.ev3_address}...")
            self.socket.connect((self.ev3_address, self.port))
            self.connected = True
            print("✓ Connected to EV3 successfully!")
            
            # Test connection
            response = self._send_command("ping")
            if response and response.get("status") == "success":
                print("✓ EV3 motor server is responding")
                
                # Save working address for future use
                self.save_working_address()
                return True
            else:
                print("✗ EV3 motor server not responding properly")
                print("💡 Make sure EV3 is running: python3 ev3_bluetooth_server.py")
                return False
                
        except Exception as e:
            print(f"✗ Connection failed: {e}")
            print("💡 Troubleshooting tips:")
            print("   1. Make sure EV3 Bluetooth is enabled and discoverable")
            print("   2. Make sure EV3 is running ev3_bluetooth_server.py")
            print("   3. Try pairing devices first: bluetoothctl")
            print("   4. Check if MAC address is correct")
            
            if self.socket:
                self.socket.close()
            self.connected = False
            return False
    
    def save_working_address(self):
        """Save working EV3 address for future use"""
        try:
            with open("ev3_config.txt", "w") as f:
                f.write(f"EV3_ADDRESS={self.ev3_address}\n")
                f.write(f"# This file was auto-generated\n")
            print(f"✅ Saved working EV3 address: {self.ev3_address}")
        except Exception as e:
            print(f"⚠️  Could not save address: {e}")
    
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
