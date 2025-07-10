#!/usr/bin/env python3
import usb.core
import usb.util
import hid
import time
import threading
import sys
import os
from typing import Optional, List, Tuple

class Switch2ProControllerEnabler:
    # Device constants
    VENDOR_ID = 0x057E
    PRODUCT_ID_JOYCON2_R = 0x2066
    PRODUCT_ID_JOYCON2_L = 0x2067
    PRODUCT_ID_PROCON2 = 0x2069
    PRODUCT_ID_GCNSO = 0x2073
    USB_INTERFACE_NUMBER = 1
    
    # [Previous command constants remain the same...]
    INIT_COMMAND_0x03 = bytes([
        0x03, 0x91, 0x00, 0x0d, 0x00, 0x08,
        0x00, 0x00, 0x01, 0x00,
        0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF
    ])
    
    UNKNOWN_COMMAND_0x07 = bytes([
        0x07, 0x91, 0x00, 0x01,
        0x00, 0x00, 0x00, 0x00
    ])
    
    UNKNOWN_COMMAND_0x16 = bytes([
        0x16, 0x91, 0x00, 0x01,
        0x00, 0x00, 0x00, 0x00
    ])
    
    REQUEST_CONTROLLER_MAC = bytes([
        0x15, 0x91, 0x00, 0x01, 0x00, 0x0e,
        0x00, 0x00, 0x00, 0x02,
        0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF,
        0xFF,
        0xFF, 0xFF, 0xFF, 0xFF, 0xFF
    ])
    
    LTK_REQUEST = bytes([
        0x15, 0x91, 0x00, 0x02, 0x00, 0x11,
        0x00, 0x00, 0x00,
        0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF,
        0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF
    ])
    
    UNKNOWN_COMMAND_0x15_ARG_0x03 = bytes([
        0x15, 0x91, 0x00, 0x03, 0x00, 0x01,
        0x00, 0x00, 0x00
    ])
    
    UNKNOWN_COMMAND_0x09 = bytes([
        0x09, 0x91, 0x00, 0x07, 0x00, 0x08,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00
    ])
    
    IMU_COMMAND_0x02 = bytes([
        0x0c, 0x91, 0x00, 0x02, 0x00, 0x04,
        0x00, 0x00, 0x27,
        0x00, 0x00, 0x00
    ])
    
    OUT_UNKNOWN_COMMAND_0x11 = bytes([
        0x11, 0x91, 0x00, 0x03,
        0x00, 0x00, 0x00, 0x00
    ])
    
    UNKNOWN_COMMAND_0x0A = bytes([
        0x0a, 0x91, 0x00, 0x08, 0x00, 0x14,
        0x00, 0x00, 0x01,
        0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff,
        0x35, 0x00, 0x46,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00
    ])
    
    IMU_COMMAND_0x04 = bytes([
        0x0c, 0x91, 0x00, 0x04, 0x00, 0x04,
        0x00, 0x00, 0x27,
        0x00, 0x00, 0x00
    ])
    
    ENABLE_HAPTICS = bytes([
        0x03, 0x91, 0x00, 0x0a, 0x00, 0x04,
        0x00, 0x00, 0x09,
        0x00, 0x00, 0x00
    ])
    
    OUT_UNKNOWN_COMMAND_0x10 = bytes([
        0x10, 0x91, 0x00, 0x01,
        0x00, 0x00, 0x00, 0x00
    ])
    
    OUT_UNKNOWN_COMMAND_0x01 = bytes([
        0x01, 0x91, 0x00, 0x0c,
        0x00, 0x00, 0x00, 0x00
    ])
    
    OUT_UNKNOWN_COMMAND_0x03 = bytes([
        0x03, 0x91, 0x00, 0x01,
        0x00, 0x00, 0x00
    ])
    
    OUT_UNKNOWN_COMMAND_0x0A_ALT = bytes([
        0x0a, 0x91, 0x00, 0x02, 0x00, 0x04,
        0x00, 0x00, 0x03,
        0x00, 0x00
    ])
    
    SET_PLAYER_LED = bytes([
        0x09, 0x91, 0x00, 0x07, 0x00, 0x08,
        0x00, 0x00, 
        0x01,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00
    ])
    
    # [Previous haptic pattern remains the same...]
    TEST_HAPTIC_PATTERN = [
        [0x93, 0x35, 0x36, 0x1c, 0x0d],
        [0xa8, 0x29, 0xc5, 0xdc, 0x0c],
        [0x75, 0x21, 0xb5, 0x5d, 0x13],
        [0x75, 0xf5, 0x70, 0x1e, 0x11],
        [0xba, 0x55, 0x40, 0x1e, 0x08],
        [0x90, 0x31, 0x10, 0x9e, 0x00],
        [0x90, 0x15, 0x10, 0x9e, 0x00],
        [0x90, 0x15, 0x10, 0x9e, 0x00],
        [0x90, 0x01, 0x10, 0x1e, 0x00],
        [0x90, 0x15, 0x10, 0x9e, 0x00],
        [0x75, 0x15, 0x73, 0x1e, 0x11],
        [0x7b, 0x95, 0x92, 0x5c, 0x13],
        [0x8d, 0xc5, 0xa1, 0x1b, 0x10],
        [0x7e, 0x31, 0xc1, 0xdc, 0x0b],
        [0x6f, 0x2d, 0x31, 0xdc, 0x03],
        [0x75, 0x19, 0x41, 0x9b, 0x03],
        [0x6f, 0x15, 0xe1, 0xda, 0x02],
        [0x66, 0xf1, 0xe0, 0xda, 0x02],
        [0x63, 0xdd, 0x10, 0x5b, 0x02],
        [0x5a, 0xb9, 0x10, 0x5b, 0x02],
        [0x4e, 0x99, 0x50, 0x5a, 0x02],
        [0x45, 0x81, 0x20, 0x5a, 0x02],
        [0x48, 0x85, 0x50, 0x5a, 0x02],
        [0x4b, 0x85, 0x50, 0x5a, 0x02],
        [0x4b, 0x7d, 0x80, 0x5a, 0x02],
        [0x48, 0x71, 0x20, 0x5a, 0x02],
        [0x48, 0x71, 0xc0, 0x99, 0x02],
        [0x45, 0x65, 0x90, 0x99, 0x02],
        [0x42, 0x61, 0x90, 0x99, 0x02],
        [0x3c, 0x59, 0xd0, 0x98, 0x02],
        [0x36, 0x59, 0xa0, 0x98, 0x02],
        [0x30, 0x55, 0x70, 0x18, 0x02],
        [0x2a, 0x55, 0x70, 0x18, 0x02],
        [0x27, 0x4d, 0x70, 0x18, 0x02],
        [0x21, 0x4d, 0x70, 0x18, 0x02],
        [0x24, 0x45, 0x70, 0x18, 0x02],
        [0x2a, 0x45, 0xa0, 0x18, 0x02],
        [0x2d, 0x41, 0xa0, 0x58, 0x01],
        [0x36, 0x41, 0xf0, 0x59, 0x01],
        [0x39, 0x41, 0xf0, 0x59, 0x01],
        [0x3f, 0x39, 0xf0, 0x99, 0x00],
        [0x3f, 0x39, 0xf0, 0x99, 0x00],
        [0x3f, 0x39, 0xf0, 0x99, 0x00],
        [0x3f, 0x31, 0xf0, 0x99, 0x00],
        [0x3f, 0x31, 0xf0, 0x99, 0x00],
        [0x3f, 0x31, 0xf0, 0x99, 0x00],
        [0x3f, 0x2d, 0xf0, 0x99, 0x00],
        [0x3f, 0x2d, 0xf0, 0x99, 0x00],
        [0x3f, 0x2d, 0xf0, 0x99, 0x00],
        [0x3f, 0x25, 0xf0, 0x99, 0x00],
        [0x3f, 0x25, 0xf0, 0x99, 0x00],
        [0x3f, 0x25, 0xf0, 0x99, 0x00],
        [0x3f, 0x25, 0xf0, 0x99, 0x00],
        [0x3f, 0x25, 0xf0, 0x99, 0x00],
        [0x3f, 0x1d, 0xf0, 0x99, 0x00],
        [0x3f, 0x1d, 0xf0, 0x99, 0x00],
        [0x3f, 0x1d, 0xf0, 0x99, 0x00],
        [0x3f, 0x1d, 0xf0, 0x99, 0x00],
        [0x3f, 0x1d, 0xf0, 0x99, 0x00],
        [0x3f, 0x1d, 0xf0, 0x99, 0x00],
        [0x3f, 0x1d, 0xf0, 0x99, 0x00],
        [0x3f, 0x19, 0xf0, 0x99, 0x00],
        [0x3f, 0x19, 0xf0, 0x99, 0x00],
        [0x3f, 0x19, 0xf0, 0x99, 0x00],
        [0x3f, 0x19, 0xf0, 0x99, 0x00],
        [0x3f, 0x19, 0xf0, 0x99, 0x00],
        [0x3f, 0x19, 0xf0, 0x99, 0x00],
        [0x3f, 0x19, 0xf0, 0x99, 0x00],
        [0x3f, 0x19, 0xf0, 0x99, 0x00],
        [0x3f, 0x19, 0xf0, 0x99, 0x00],
        [0x3f, 0x19, 0xf0, 0x99, 0x00],
        [0x3f, 0x19, 0xf0, 0x99, 0x00],
        [0x3f, 0x19, 0xf0, 0x99, 0x00],
        [0x3f, 0x19, 0xf0, 0x99, 0x00],
        [0x3f, 0x19, 0xf0, 0x99, 0x00],
        [0x3f, 0x19, 0xf0, 0x99, 0x00],
        [0x3f, 0x19, 0xf0, 0x99, 0x00],
        [0x3f, 0x01, 0xf0, 0x19, 0x00],
        [0x3f, 0x01, 0xf0, 0x19, 0x00],
        [0x3f, 0x01, 0xf0, 0x19, 0x00],
        [0x3f, 0x01, 0xf0, 0x19, 0x00],
        [0x3f, 0x01, 0xf0, 0x19, 0x00],
        [0x3f, 0x01, 0xf0, 0x19, 0x00],
        [0x3f, 0x01, 0xf0, 0x19, 0x00],
        [0x3f, 0x01, 0xf0, 0x19, 0x00],
        [0x3f, 0x01, 0xf0, 0x19, 0x00],
        [0x3f, 0x01, 0xf0, 0x19, 0x00],
        [0x3f, 0x01, 0xf0, 0x19, 0x00]
    ]
    
    def __init__(self):
        self.usb_device: Optional[usb.core.Device] = None
        self.usb_endpoint_out: Optional[int] = None
        self.usb_endpoint_in: Optional[int] = None
        self.hid_device: Optional[hid.device] = None
        self.haptic_thread: Optional[threading.Thread] = None
        self.haptic_stop_event = threading.Event()
        self.haptic_counter = 0
        self.detached_interfaces = []
        
    def check_permissions(self):
        """Check if we have the necessary permissions"""
        if os.geteuid() != 0:
            print("Warning: Not running as root. You may need to:")
            print("1. Run with sudo, or")
            print("2. Set up udev rules for device permissions")
            return False
        return True
    
    def find_usb_device(self) -> Optional[usb.core.Device]:
        """Find a compatible USB device"""
        product_ids = [
            self.PRODUCT_ID_JOYCON2_L,
            self.PRODUCT_ID_JOYCON2_R,
            self.PRODUCT_ID_PROCON2,
            self.PRODUCT_ID_GCNSO
        ]
        
        for product_id in product_ids:
            device = usb.core.find(idVendor=self.VENDOR_ID, idProduct=product_id)
            if device:
                return device
        return None
    
    def detach_kernel_drivers(self, device: usb.core.Device) -> bool:
        """Safely detach kernel drivers from all interfaces"""
        try:
            # Get the active configuration
            config = device.get_active_configuration()
            
            # Try to detach kernel drivers from all interfaces
            for interface in config:
                interface_num = interface.bInterfaceNumber
                try:
                    if device.is_kernel_driver_active(interface_num):
                        print(f"Detaching kernel driver from interface {interface_num}")
                        device.detach_kernel_driver(interface_num)
                        self.detached_interfaces.append(interface_num)
                        print(f"Successfully detached kernel driver from interface {interface_num}")
                except usb.core.USBError as e:
                    print(f"Warning: Could not detach kernel driver from interface {interface_num}: {e}")
                    continue
            
            return True
            
        except Exception as e:
            print(f"Error detaching kernel drivers: {e}")
            return False
    
    def reattach_kernel_drivers(self, device: usb.core.Device):
        """Reattach kernel drivers to previously detached interfaces"""
        for interface_num in self.detached_interfaces:
            try:
                print(f"Reattaching kernel driver to interface {interface_num}")
                device.attach_kernel_driver(interface_num)
            except usb.core.USBError as e:
                print(f"Warning: Could not reattach kernel driver to interface {interface_num}: {e}")
        
        self.detached_interfaces.clear()
    
    def connect_usb(self) -> bool:
        """Connect to USB device and initialize"""
        try:
            print("Searching for USB device...")
            device = self.find_usb_device()
            if not device:
                print("No compatible USB device found")
                return False
            
            print(f"Found device: {device.product} (VID: 0x{device.idVendor:04x}, PID: 0x{device.idProduct:04x})")
            
            # Check permissions
            self.check_permissions()
            
            # Try to reset the device first
            try:
                print("Resetting device...")
                device.reset()
                time.sleep(1)
            except usb.core.USBError as e:
                print(f"Warning: Could not reset device: {e}")
            
            # Detach kernel drivers
            if not self.detach_kernel_drivers(device):
                print("Failed to detach kernel drivers")
                return False
            
            # Set configuration
            try:
                print("Setting USB configuration...")
                device.set_configuration()
            except usb.core.USBError as e:
                print(f"Error setting configuration: {e}")
                # Try to continue anyway
            
            # Get configuration and find the right interface
            config = device.get_active_configuration()
            interface_found = False
            
            # Try different interface numbers
            for interface_num in [0, 1, 2]:
                try:
                    print(f"Trying to claim interface {interface_num}...")
                    usb.util.claim_interface(device, interface_num)
                    print(f"Successfully claimed interface {interface_num}")
                    
                    # Find endpoints for this interface
                    interface = config[(interface_num, 0)]
                    self.usb_endpoint_out = None
                    self.usb_endpoint_in = None
                    
                    for endpoint in interface:
                        if usb.util.endpoint_direction(endpoint.bEndpointAddress) == usb.util.ENDPOINT_OUT:
                            if endpoint.bmAttributes & 0x03 == 0x02:  # Bulk endpoint
                                self.usb_endpoint_out = endpoint.bEndpointAddress
                                print(f"Found bulk OUT endpoint: 0x{self.usb_endpoint_out:02x}")
                        elif usb.util.endpoint_direction(endpoint.bEndpointAddress) == usb.util.ENDPOINT_IN:
                            if endpoint.bmAttributes & 0x03 == 0x02:  # Bulk endpoint
                                self.usb_endpoint_in = endpoint.bEndpointAddress
                                print(f"Found bulk IN endpoint: 0x{self.usb_endpoint_in:02x}")
                    
                    if self.usb_endpoint_out:
                        self.USB_INTERFACE_NUMBER = interface_num
                        interface_found = True
                        break
                    else:
                        usb.util.release_interface(device, interface_num)
                        
                except usb.core.USBError as e:
                    print(f"Could not claim interface {interface_num}: {e}")
                    continue
            
            if not interface_found:
                print("Could not find suitable interface with bulk OUT endpoint")
                return False
            
            self.usb_device = device
            print(f"USB device connected successfully!")
            print(f"Using interface: {self.USB_INTERFACE_NUMBER}")
            print(f"OUT endpoint: 0x{self.usb_endpoint_out:02x}")
            if self.usb_endpoint_in:
                print(f"IN endpoint: 0x{self.usb_endpoint_in:02x}")
            
            # Send initialization sequence
            self.send_initialization_sequence()
            
            return True
            
        except Exception as e:
            print(f"USB connection error: {e}")
            print("Troubleshooting tips:")
            print("1. Try running with sudo")
            print("2. Make sure the device is not in use by another process")
            print("3. Check if udev rules are set up correctly")
            print("4. Try unplugging and reconnecting the device")
            return False
    
    def connect_hid(self) -> bool:
        """Connect to HID device"""
        try:
            print("Searching for HID device...")
            
            # Find compatible HID device
            devices = hid.enumerate(self.VENDOR_ID)
            compatible_device = None
            
            print("Available HID devices:")
            for dev_info in devices:
                product_name = dev_info.get('product_string', 'Unknown')
                print(f"  - PID: 0x{dev_info['product_id']:04x}, Product: {product_name}")
                
                if dev_info['product_id'] in [
                    self.PRODUCT_ID_JOYCON2_L,
                    self.PRODUCT_ID_JOYCON2_R,
                    self.PRODUCT_ID_PROCON2,
                    self.PRODUCT_ID_GCNSO
                ]:
                    compatible_device = dev_info
                    break
            
            if not compatible_device:
                print("No compatible HID device found")
                return False
            
            product_name = compatible_device.get('product_string', 'Unknown')
            print(f"Found compatible HID device: {product_name}")
            
            # Connect to HID device
            self.hid_device = hid.device()
            self.hid_device.open(self.VENDOR_ID, compatible_device['product_id'])
            
            # Set non-blocking mode
            self.hid_device.set_nonblocking(True)
            
            print("HID device connected successfully!")
            return True
            
        except Exception as e:
            print(f"HID connection error: {e}")
            print("Troubleshooting tips:")
            print("1. Try running with sudo")
            print("2. Make sure hidapi is installed: pip install hidapi")
            print("3. Check if udev rules are set up correctly")
            return False
    
    def send_usb_data(self, data: bytes) -> bool:
        """Send data via USB bulk endpoint"""
        if not self.usb_device or not self.usb_endpoint_out:
            print("USB device not connected")
            return False
        
        try:
            # Send data
            bytes_written = self.usb_device.write(self.usb_endpoint_out, data, timeout=1000)
            print(f"Sent {bytes_written} bytes: {data.hex()}")
            
            # Try to read response
            if self.usb_endpoint_in:
                try:
                    time.sleep(0.01)  # Small delay
                    response = self.usb_device.read(self.usb_endpoint_in, 64, timeout=100)
                    if response:
                        print(f"Response: {bytes(response).hex()}")
                except usb.core.USBTimeoutError:
                    pass  # No response expected for some commands
                except usb.core.USBError as e:
                    print(f"Warning: Could not read response: {e}")
            
            return True
            
        except Exception as e:
            print(f"USB send error: {e}")
            return False
    
    def send_hid_report(self, report_data: bytes) -> bool:
        """Send HID report"""
        if not self.hid_device:
            print("HID device not connected")
            return False
        
        try:
            # Pad report to 64 bytes if needed
            if len(report_data) < 64:
                report_data = report_data + b'\x00' * (64 - len(report_data))
            
            bytes_written = self.hid_device.write(report_data)
            print(f"Sent HID report: {report_data[:16].hex()}...")
            return True
            
        except Exception as e:
            print(f"HID send error: {e}")
            return False
    
    def send_initialization_sequence(self):
        """Send the full initialization sequence"""
        print("Sending initialization sequence...")
        
        commands = [
            ("INIT_COMMAND_0x03", self.INIT_COMMAND_0x03),
            ("UNKNOWN_COMMAND_0x07", self.UNKNOWN_COMMAND_0x07),
            ("UNKNOWN_COMMAND_0x16", self.UNKNOWN_COMMAND_0x16),
            ("REQUEST_CONTROLLER_MAC", self.REQUEST_CONTROLLER_MAC),
            ("LTK_REQUEST", self.LTK_REQUEST),
            ("UNKNOWN_COMMAND_0x15_ARG_0x03", self.UNKNOWN_COMMAND_0x15_ARG_0x03),
            ("UNKNOWN_COMMAND_0x09", self.UNKNOWN_COMMAND_0x09),
            ("IMU_COMMAND_0x02", self.IMU_COMMAND_0x02),
            ("OUT_UNKNOWN_COMMAND_0x11", self.OUT_UNKNOWN_COMMAND_0x11),
            ("UNKNOWN_COMMAND_0x0A", self.UNKNOWN_COMMAND_0x0A),
            ("IMU_COMMAND_0x04", self.IMU_COMMAND_0x04),
            ("ENABLE_HAPTICS", self.ENABLE_HAPTICS),
            ("OUT_UNKNOWN_COMMAND_0x10", self.OUT_UNKNOWN_COMMAND_0x10),
            ("OUT_UNKNOWN_COMMAND_0x01", self.OUT_UNKNOWN_COMMAND_0x01),
            ("OUT_UNKNOWN_COMMAND_0x03", self.OUT_UNKNOWN_COMMAND_0x03),
            ("OUT_UNKNOWN_COMMAND_0x0A_ALT", self.OUT_UNKNOWN_COMMAND_0x0A_ALT),
            ("SET_PLAYER_LED", self.SET_PLAYER_LED),
        ]
        
        for name, command in commands:
            print(f"Sending {name}...")
            if self.send_usb_data(command):
                print(f"  ✓ {name} sent successfully")
            else:
                print(f"  ✗ {name} failed")
            time.sleep(0.05)  # Slightly longer delay
        
        print("Initialization sequence complete!")
    
    def create_haptic_report(self, haptic_data: List[int]) -> bytes:
        """Create a haptic HID report"""
        report = bytearray(64)
        report[0] = 0x02  # Report ID
        report[1] = 0x50 | (self.haptic_counter & 0x0F)
        report[17] = report[1]
        
        # Insert haptic data
        for i, byte_val in enumerate(haptic_data[:5]):
            report[2 + i] = byte_val
            report[18 + i] = byte_val
        
        return bytes(report)
    
    def play_haptic_pattern(self):
        """Play the test haptic pattern"""
        if not self.hid_device:
            print("HID device not connected")
            return
        
        print("Starting haptic playback...")
        self.haptic_stop_event.clear()
        
        def haptic_worker():
            pattern_index = 0
            while not self.haptic_stop_event.is_set() and pattern_index < len(self.TEST_HAPTIC_PATTERN):
                haptic_data = self.TEST_HAPTIC_PATTERN[pattern_index]
                report = self.create_haptic_report(haptic_data)
                
                if self.send_hid_report(report):
                    print(f"Sent haptic packet {pattern_index + 1}/{len(self.TEST_HAPTIC_PATTERN)} "
                          f"(counter: 0x{self.haptic_counter:x})")
                else:
                    print(f"Failed to send haptic packet {pattern_index + 1}")
                
                self.haptic_counter = (self.haptic_counter + 1) & 0x0F
                pattern_index += 1
                
                time.sleep(0.004)  # 4ms intervals
            
            # Send stop command
            stop_report = self.create_haptic_report([0x00, 0x00, 0x00, 0x00, 0x00])
            self.send_hid_report(stop_report)
            print("Haptic playback stopped")
        
        self.haptic_thread = threading.Thread(target=haptic_worker)
        self.haptic_thread.start()
    
    def stop_haptic_pattern(self):
        """Stop haptic playback"""
        if self.haptic_thread and self.haptic_thread.is_alive():
            self.haptic_stop_event.set()
            self.haptic_thread.join()
            print("Haptic playback stopped")
    
    def parse_hex_string(self, hex_str: str) -> bytes:
        """Parse hex string into bytes"""
        cleaned = hex_str.replace('0x', '').replace(',', ' ').replace('  ', ' ').strip()
        hex_pairs = cleaned.split()
        
        data = []
        for hex_pair in hex_pairs:
            if len(hex_pair) > 2:
                raise ValueError(f"Invalid hex value: {hex_pair}")
            padded = hex_pair.zfill(2)
            data.append(int(padded, 16))
        
        return bytes(data)
    
    def send_custom_usb_data(self, hex_str: str) -> bool:
        """Send custom USB data from hex string"""
        try:
            data = self.parse_hex_string(hex_str)
            return self.send_usb_data(data)
        except Exception as e:
            print(f"Error parsing hex data: {e}")
            return False
    
    def send_custom_hid_report(self, hex_str: str) -> bool:
        """Send custom HID report from hex string"""
        try:
            data = self.parse_hex_string(hex_str)
            return self.send_hid_report(data)
        except Exception as e:
            print(f"Error parsing hex data: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from devices"""
        self.stop_haptic_pattern()
        
        if self.hid_device:
            self.hid_device.close()
            self.hid_device = None
            print("HID device disconnected")
        
        if self.usb_device:
            try:
                usb.util.release_interface(self.usb_device, self.USB_INTERFACE_NUMBER)
                self.reattach_kernel_drivers(self.usb_device)
            except:
                pass
            self.usb_device = None
            print("USB device disconnected")


def main():
    """Main CLI interface"""
    enabler = Switch2ProControllerEnabler()
    
    try:
        while True:
            print("\n=== Switch 2 Pro Controller Enabler ===")
            print("1. Connect USB (Enable HID Output)")
            print("2. Connect HID (Dev Mode)")
            print("3. Play Test Haptic")
            print("4. Stop Haptic")
            print("5. Send Custom USB Data")
            print("6. Send Custom HID Report")
            print("7. Exit")
            
            choice = input("\nEnter choice (1-7): ").strip()
            
            if choice == '1':
                enabler.connect_usb()
            elif choice == '2':
                enabler.connect_hid()
            elif choice == '3':
                enabler.play_haptic_pattern()
            elif choice == '4':
                enabler.stop_haptic_pattern()
            elif choice == '5':
                hex_data = input("Enter USB hex data: ").strip()
                if hex_data:
                    enabler.send_custom_usb_data(hex_data)
            elif choice == '6':
                hex_data = input("Enter HID hex data: ").strip()
                if hex_data:
                    enabler.send_custom_hid_report(hex_data)
            elif choice == '7':
                break
            else:
                print("Invalid choice")
                
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        enabler.disconnect()


if __name__ == "__main__":
    main()
