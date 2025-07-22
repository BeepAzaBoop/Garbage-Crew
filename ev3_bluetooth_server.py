# ev3_bluetooth_server.py - Run this on the EV3 brick
import bluetooth
import json
import threading
import time

# Import the original motor control class
from motor_control import GarbageSortController

class EV3BluetoothServer:
    """Bluetooth server that runs on EV3 and accepts remote motor control commands"""
    
    def __init__(self, port=1):
        self.controller = GarbageSortController()
        self.server_socket = None
        self.client_socket = None
        self.port = port
        self.running = False
        
        print("EV3 Bluetooth Motor Server")
        print("=" * 30)
        
    def start_server(self):
        """Start the Bluetooth server"""
        try:
            # Create Bluetooth socket
            self.server_socket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
            self.server_socket.bind(("", self.port))
            self.server_socket.listen(1)
            
            print(f"Bluetooth server listening on port {self.port}")
            print("Make sure EV3 is discoverable!")
            print("Waiting for Raspberry Pi connection...")
            
            self.running = True
            
            while self.running:
                try:
                    self.client_socket, address = self.server_socket.accept()
                    print(f"✓ Connected to Raspberry Pi: {address}")
                    
                    # Handle client commands
                    self.handle_client()
                    
                except bluetooth.BluetoothError as e:
                    print(f"Bluetooth error: {e}")
                    if self.running:
                        time.sleep(1)  # Wait before retrying
                except Exception as e:
                    print(f"Server error: {e}")
                    if self.running:
                        time.sleep(1)
                        
        except Exception as e:
            print(f"Failed to start server: {e}")
        finally:
            self.cleanup()
    
    def handle_client(self):
        """Handle commands from connected Raspberry Pi"""
        try:
            while self.running:
                # Receive command
                data = self.client_socket.recv(1024)
                if not data:
                    print("Client disconnected")
                    break
                
                try:
                    # Parse command
                    command = json.loads(data.decode('utf-8'))
                    print(f"Received command: {command}")
                    
                    # Process command
                    response = self.process_command(command)
                    
                    # Send response
                    response_json = json.dumps(response)
                    self.client_socket.send(response_json.encode('utf-8'))
                    
                except json.JSONDecodeError:
                    error_response = {"status": "error", "message": "Invalid JSON command"}
                    self.client_socket.send(json.dumps(error_response).encode('utf-8'))
                except Exception as e:
                    error_response = {"status": "error", "message": f"Command processing error: {str(e)}"}
                    self.client_socket.send(json.dumps(error_response).encode('utf-8'))
                    
        except Exception as e:
            print(f"Client handling error: {e}")
        finally:
            if self.client_socket:
                self.client_socket.close()
                self.client_socket = None
                print("Client disconnected")
    
    def process_command(self, command):
        """Process motor control commands"""
        try:
            action = command.get('action')
            
            if action == 'ping':
                return {"status": "success", "message": "pong"}
            
            elif action == 'classify':
                label = command.get('label')
                if label:
                    print(f"Executing classification sequence for: {label}")
                    self.controller.handle_classification(label)
                    return {"status": "success", "message": f"Sorted: {label}"}
                else:
                    return {"status": "error", "message": "No label provided"}
            
            elif action == 'shift_panels':
                direction = command.get('direction')
                print(f"Shifting panels: {direction}")
                self.controller.shift_panels(direction)
                return {"status": "success", "message": f"Panels shifted: {direction}"}
            
            elif action == 'reset_panels':
                print("Resetting panels")
                self.controller.reset_panels()
                return {"status": "success", "message": "Panels reset"}
            
            elif action == 'extend_rods':
                print("Extending rods")
                self.controller.extend_rods()
                return {"status": "success", "message": "Rods extended"}
            
            elif action == 'retract_rods':
                print("Retracting rods")
                self.controller.retract_rods()
                return {"status": "success", "message": "Rods retracted"}
            
            elif action == 'open_trap':
                print("Opening trap")
                self.controller.open_trap()
                return {"status": "success", "message": "Trap opened"}
            
            elif action == 'close_trap':
                print("Closing trap")
                self.controller.close_trap()
                return {"status": "success", "message": "Trap closed"}
            
            elif action == 'stop_all':
                print("Stopping all motors")
                self.controller.stop_all_motors()
                return {"status": "success", "message": "All motors stopped"}
            
            elif action == 'configure':
                settings = command.get('settings', {})
                print(f"Configuring motors: {settings}")
                self.controller.set_motor_settings(**settings)
                return {"status": "success", "message": "Settings updated"}
            
            else:
                return {"status": "error", "message": f"Unknown action: {action}"}
                
        except Exception as e:
            print(f"Command execution error: {e}")
            return {"status": "error", "message": str(e)}
    
    def cleanup(self):
        """Clean up server resources"""
        print("Shutting down server...")
        self.running = False
        
        if self.client_socket:
            self.client_socket.close()
        if self.server_socket:
            self.server_socket.close()
        
        # Stop all motors for safety
        self.controller.stop_all_motors()
        print("Server shutdown complete")

def main():
    server = EV3BluetoothServer()
    
    try:
        server.start_server()
    except KeyboardInterrupt:
        print("\nServer interrupted by user")
    except Exception as e:
        print(f"Server crashed: {e}")
    finally:
        server.cleanup()

if __name__ == "__main__":
    main()
