#!/usr/bin/env python3
import math
import os
import sys
import time
from typing import List, Optional

import hid
import uinput
import usb.core
import usb.util


class ControllerInitializer:
    """
    Handles the low-level USB communication to initialize the controller,
    switching it into a standard HID-compliant mode.
    """

    # Device constants
    VENDOR_ID = 0x057E
    PRODUCT_ID_GCNSO = 0x2073
    USB_INTERFACE_NUMBER = 1

    # Initialization Commands (abbreviated for clarity)
    INIT_COMMAND_0x03 = bytes(
        [0x03, 0x91, 0x00, 0x0D, 0x00, 0x08, 0x00, 0x00, 0x01, 0x00, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]
    )
    UNKNOWN_COMMAND_0x07 = bytes([0x07, 0x91, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00])
    UNKNOWN_COMMAND_0x16 = bytes([0x16, 0x91, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00])
    REQUEST_CONTROLLER_MAC = bytes(
        [0x15, 0x91, 0x00, 0x01, 0x00, 0x0E, 0x00, 0x00, 0x00, 0x02, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]
    )
    LTK_REQUEST = bytes(
        [0x15, 0x91, 0x00, 0x02, 0x00, 0x11, 0x00, 0x00, 0x00, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]
    )
    UNKNOWN_COMMAND_0x15_ARG_0x03 = bytes([0x15, 0x91, 0x00, 0x03, 0x00, 0x01, 0x00, 0x00, 0x00])
    UNKNOWN_COMMAND_0x09 = bytes(
        [0x09, 0x91, 0x00, 0x07, 0x00, 0x08, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
    )
    IMU_COMMAND_0x02 = bytes([0x0C, 0x91, 0x00, 0x02, 0x00, 0x04, 0x00, 0x00, 0x27, 0x00, 0x00, 0x00])
    OUT_UNKNOWN_COMMAND_0x11 = bytes([0x11, 0x91, 0x00, 0x03, 0x00, 0x00, 0x00, 0x00])
    UNKNOWN_COMMAND_0x0A = bytes(
        [0x0A, 0x91, 0x00, 0x08, 0x00, 0x14, 0x00, 0x00, 0x01, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0x35, 0x00, 0x46, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
    )
    IMU_COMMAND_0x04 = bytes([0x0C, 0x91, 0x00, 0x04, 0x00, 0x04, 0x00, 0x00, 0x27, 0x00, 0x00, 0x00])
    ENABLE_HAPTICS = bytes([0x03, 0x91, 0x00, 0x0A, 0x00, 0x04, 0x00, 0x00, 0x09, 0x00, 0x00, 0x00])
    OUT_UNKNOWN_COMMAND_0x10 = bytes([0x10, 0x91, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00])
    OUT_UNKNOWN_COMMAND_0x01 = bytes([0x01, 0x91, 0x00, 0x0C, 0x00, 0x00, 0x00, 0x00])
    OUT_UNKNOWN_COMMAND_0x03 = bytes([0x03, 0x91, 0x00, 0x01, 0x00, 0x00, 0x00])
    OUT_UNKNOWN_COMMAND_0x0A_ALT = bytes([0x0A, 0x91, 0x00, 0x02, 0x00, 0x04, 0x00, 0x00, 0x03, 0x00, 0x00])
    SET_PLAYER_LED = bytes(
        [0x09, 0x91, 0x00, 0x07, 0x00, 0x08, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
    )

    def __init__(self):
        self.usb_device: Optional[usb.core.Device] = None
        self.usb_endpoint_out: Optional[int] = None
        self.usb_endpoint_in: Optional[int] = None
        self.detached_interfaces: List[int] = []

    def check_permissions(self) -> bool:
        if os.geteuid() != 0:
            print(
                "Warning: Not running as root. If the script fails, you may need to:",
                file=sys.stderr,
            )
            print("1. Run with 'sudo', or", file=sys.stderr)
            print("2. Set up udev rules for device permissions.", file=sys.stderr)
        return True

    def find_usb_device(self) -> Optional[usb.core.Device]:
        return usb.core.find(
            idVendor=self.VENDOR_ID, idProduct=self.PRODUCT_ID_GCNSO
        )

    def detach_kernel_drivers(self, device: usb.core.Device) -> bool:
        try:
            config = device.get_active_configuration()
            for interface in config:
                if device.is_kernel_driver_active(interface.bInterfaceNumber):
                    device.detach_kernel_driver(interface.bInterfaceNumber)
                    self.detached_interfaces.append(interface.bInterfaceNumber)
            return True
        except Exception as e:
            print(f"Error detaching kernel drivers: {e}", file=sys.stderr)
            return False

    def reattach_kernel_drivers(self, device: usb.core.Device):
        for interface_num in self.detached_interfaces:
            try:
                device.attach_kernel_driver(interface_num)
            except usb.core.USBError as e:
                print(
                    f"Warning: Could not reattach kernel driver to interface "
                    f"{interface_num}: {e}",
                    file=sys.stderr,
                )
        self.detached_interfaces.clear()

    def connect_and_initialize(self) -> bool:
        try:
            print("Searching for NSO GameCube controller (USB mode)...")
            device = self.find_usb_device()
            if not device:
                print("USB device not found.", file=sys.stderr)
                return False

            if not self.detach_kernel_drivers(device):
                return False

            device.set_configuration()
            config = device.get_active_configuration()
            interface = config[(self.USB_INTERFACE_NUMBER, 0)]

            for ep in interface:
                if usb.util.endpoint_direction(ep.bEndpointAddress) == usb.util.ENDPOINT_OUT:
                    self.usb_endpoint_out = ep.bEndpointAddress
                elif usb.util.endpoint_direction(ep.bEndpointAddress) == usb.util.ENDPOINT_IN:
                    self.usb_endpoint_in = ep.bEndpointAddress

            if not self.usb_endpoint_out:
                print("Could not find bulk OUT endpoint.", file=sys.stderr)
                return False

            self.usb_device = device
            print("USB device connected. Sending initialization sequence...")
            self._send_initialization_sequence()
            return True

        except Exception as e:
            print(f"USB connection error: {e}", file=sys.stderr)
            return False

    def _send_usb_data(self, data: bytes) -> bool:
        if not self.usb_device or not self.usb_endpoint_out:
            return False
        try:
            self.usb_device.write(self.usb_endpoint_out, data, timeout=1000)
            if self.usb_endpoint_in:
                try:
                    time.sleep(0.01)
                    self.usb_device.read(self.usb_endpoint_in, 64, timeout=100)
                except usb.core.USBTimeoutError:
                    pass
            return True
        except Exception as e:
            print(f"USB send error: {e}", file=sys.stderr)
            return False

    def _send_initialization_sequence(self):
        commands = [
            self.INIT_COMMAND_0x03, self.UNKNOWN_COMMAND_0x07, self.UNKNOWN_COMMAND_0x16,
            self.REQUEST_CONTROLLER_MAC, self.LTK_REQUEST, self.UNKNOWN_COMMAND_0x15_ARG_0x03,
            self.UNKNOWN_COMMAND_0x09, self.IMU_COMMAND_0x02, self.OUT_UNKNOWN_COMMAND_0x11,
            self.UNKNOWN_COMMAND_0x0A, self.IMU_COMMAND_0x04, self.ENABLE_HAPTICS,
            self.OUT_UNKNOWN_COMMAND_0x10, self.OUT_UNKNOWN_COMMAND_0x01,
            self.OUT_UNKNOWN_COMMAND_0x03, self.OUT_UNKNOWN_COMMAND_0x0A_ALT, self.SET_PLAYER_LED,
        ]
        for command in commands:
            if not self._send_usb_data(command):
                print("Failed to send an initialization command.", file=sys.stderr)
            time.sleep(0.05)
        print("Initialization sequence complete!")

    def disconnect(self):
        if self.usb_device:
            try:
                self.reattach_kernel_drivers(self.usb_device)
                usb.util.release_interface(
                    self.usb_device, self.USB_INTERFACE_NUMBER
                )
            except Exception as e:
                print(f"Error during USB disconnect: {e}", file=sys.stderr)
            finally:
                self.usb_device = None
                print("USB device disconnected and kernel drivers reattached.")


class StickCalibrator:
    """Applies Dolphin-style calibration to raw stick values."""

    def __init__(self, calibration_str: str, deadzone: float = 10.0):
        self.radii = [float(r) for r in calibration_str.split()]
        self.deadzone = deadzone
        if len(self.radii) != 32:
            raise ValueError("Calibration string must contain 32 values.")

    def calibrate(self, x: float, y: float) -> tuple[float, float]:
        # Convert to polar coordinates
        magnitude = math.sqrt(x**2 + y**2)/1.3
        if magnitude < self.deadzone:
            return 0.0, 0.0

        angle = math.atan2(y, x)

        # Normalize angle to [0, 2*pi)
        if angle < 0:
            angle += 2 * math.pi

        # Find the two nearest calibration radii
        angle_percent = angle / (2 * math.pi)
        float_index = angle_percent * 32
        index1 = int(float_index) % 32
        index2 = (index1 + 1) % 32
        fraction = float_index - int(float_index)

        # Linearly interpolate between the two radii
        r1 = self.radii[index1]
        r2 = self.radii[index2]
        calibrated_radius_pct = r1 + (r2 - r1) * fraction

        # The calibrated radius is a percentage of the ideal radius (100)
        # We scale our current magnitude by the inverse of this percentage
        scale_factor = 100.0 / calibrated_radius_pct
        corrected_magnitude = magnitude * scale_factor

        # Convert back to cartesian coordinates
        corrected_x = corrected_magnitude * math.cos(angle)
        corrected_y = corrected_magnitude * math.sin(angle)

        return corrected_x, corrected_y


def unpack_12bit_triplet(data):
    """Unpacks three bytes of 12-bit stick data into two 12-bit values."""
    a = data[0] | ((data[1] & 0x0F) << 8)
    b = (data[1] >> 4) | (data[2] << 4)
    return a, b


def main():
    """Main script execution flow."""
    initializer = ControllerInitializer()
    initializer.check_permissions()

    print("--- Step 1: Initializing Controller ---")
    if not initializer.connect_and_initialize():
        sys.exit("Failed to initialize controller. Is it plugged in?")

    vendor_id = initializer.VENDOR_ID
    product_id = initializer.PRODUCT_ID_GCNSO
    initializer.disconnect()

    print("\nController initialized. Waiting for HID device to appear...")
    time.sleep(2)

    hid_device = None
    vdev = None
    try:
        print("\n--- Step 2: Connecting to HID & Creating Virtual Device ---")
        print(f"Searching for HID device (PID: 0x{product_id:04x})...")
        hid_device = hid.device()
        hid_device.open(vendor_id, product_id)
        print("HID device found!")

        # --- Setup Calibration ---
        main_stick_cal_str = "61.28 59.10 59.32 61.42 64.61 60.89 58.93 58.86 57.96 54.91 53.94 55.08 58.76 55.50 52.94 53.47 56.88 54.62 54.06 55.79 59.53 58.33 56.91 58.23 60.40 61.90 61.76 63.32 68.50 63.34 61.14 60.96"
        c_stick_cal_str = "54.74 52.52 52.24 54.58 58.28 55.75 54.01 54.52 55.03 53.14 52.31 53.07 56.86 52.77 51.99 52.16 53.86 52.02 51.43 53.31 56.98 53.29 52.09 52.24 55.01 53.96 53.79 56.05 59.98 56.49 54.20 54.46"
        main_calibrator = StickCalibrator(main_stick_cal_str)
        c_calibrator = StickCalibrator(c_stick_cal_str)
        print("Analog stick calibrators created.")

        events = (
            uinput.BTN_A, uinput.BTN_B, uinput.BTN_X, uinput.BTN_Y,
            uinput.BTN_TL, uinput.BTN_TR, uinput.BTN_TL2, uinput.BTN_TR2,
            uinput.BTN_START, uinput.BTN_SELECT, uinput.BTN_MODE, uinput.BTN_Z,
            uinput.BTN_DPAD_UP, uinput.BTN_DPAD_DOWN, uinput.BTN_DPAD_LEFT, uinput.BTN_DPAD_RIGHT,
            uinput.BTN_THUMBL, uinput.BTN_THUMBR, uinput.BTN_C, uinput.BTN_THUMB, uinput.BTN_THUMB2,
            uinput.ABS_X + (-32768, 32767, 0, 0), uinput.ABS_Y + (-32768, 32767, 0, 0),
            uinput.ABS_RX + (-32768, 32767, 0, 0), uinput.ABS_RY + (-32768, 32767, 0, 0),
            uinput.ABS_Z + (0, 255, 0, 0), uinput.ABS_RZ + (0, 255, 0, 0),
        )

        vdev = uinput.Device(events, name="Virtual Nintendo GameCube Controller (NSO)")
        print("Virtual controller created. Ready for input.")
        print("Press Ctrl+C to exit.")

        while True:
            report = hid_device.read(64)
            if not report:
                print("\nController disconnected.")
                break

            payload = report[1:]
            buttons = payload[0x2:0x5]
            stick1 = payload[0x5:0x8]
            stick2 = payload[0x8:0xB]
            left_trigger = payload[0x0C]
            right_trigger = payload[0x0D]

            # --- Buttons (unchanged) ---
            vdev.emit(uinput.BTN_B, bool(buttons[0] & 0x01))
            vdev.emit(uinput.BTN_A, bool(buttons[0] & 0x02))
            vdev.emit(uinput.BTN_Y, bool(buttons[0] & 0x04))
            vdev.emit(uinput.BTN_X, bool(buttons[0] & 0x08))
            vdev.emit(uinput.BTN_TR, bool(buttons[0] & 0x10))
            vdev.emit(uinput.BTN_TR2, bool(buttons[0] & 0x20))
            vdev.emit(uinput.BTN_START, bool(buttons[0] & 0x40))
            vdev.emit(uinput.BTN_THUMBR, bool(buttons[0] & 0x80))
            vdev.emit(uinput.BTN_DPAD_DOWN, bool(buttons[1] & 0x01))
            vdev.emit(uinput.BTN_DPAD_RIGHT, bool(buttons[1] & 0x02))
            vdev.emit(uinput.BTN_DPAD_LEFT, bool(buttons[1] & 0x04))
            vdev.emit(uinput.BTN_DPAD_UP, bool(buttons[1] & 0x08))
            vdev.emit(uinput.BTN_TL, bool(buttons[1] & 0x10))
            vdev.emit(uinput.BTN_TL2, bool(buttons[1] & 0x20))
            vdev.emit(uinput.BTN_SELECT, bool(buttons[1] & 0x40))
            vdev.emit(uinput.BTN_THUMBL, bool(buttons[1] & 0x80))
            vdev.emit(uinput.BTN_MODE, bool(buttons[2] & 0x01))
            vdev.emit(uinput.BTN_C, bool(buttons[2] & 0x02))
            vdev.emit(uinput.BTN_THUMB2, bool(buttons[2] & 0x04))
            vdev.emit(uinput.BTN_THUMB, bool(buttons[2] & 0x08))
            vdev.emit(uinput.BTN_Z, bool(buttons[2] & 0x10))

            # --- Sticks (with calibration) ---
            x1_raw, y1_raw = unpack_12bit_triplet(stick1)
            x2_raw, y2_raw = unpack_12bit_triplet(stick2)

            # Center the raw values (0-4095 -> -2048 to 2047)
            x1_centered, y1_centered = x1_raw - 2048, y1_raw - 2048
            x2_centered, y2_centered = x2_raw - 2048, y2_raw - 2048

            # Apply calibration
            x1_cal, y1_cal = main_calibrator.calibrate(x1_centered, y1_centered)
            x2_cal, y2_cal = c_calibrator.calibrate(x2_centered, y2_centered)

            # Scale, clamp, and emit to virtual device
            # Note: Y axes are inverted to match standard gamepad behavior
            vdev.emit(uinput.ABS_X, max(-32768, min(32767, int(x1_cal * 16))))
            vdev.emit(uinput.ABS_Y, max(-32768, min(32767, int(-y1_cal * 16))))
            vdev.emit(uinput.ABS_RX, max(-32768, min(32767, int(x2_cal * 16))))
            vdev.emit(uinput.ABS_RY, max(-32768, min(32767, int(-y2_cal * 16))))

            # --- Triggers (unchanged) ---
            vdev.emit(uinput.ABS_Z, left_trigger)
            vdev.emit(uinput.ABS_RZ, right_trigger)

            vdev.syn()

    except IOError:
        print(f"\nCould not open HID device (PID 0x{product_id:04x}).", file=sys.stderr)
    except KeyboardInterrupt:
        print("\nExiting by user request.")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}", file=sys.stderr)
    finally:
        print("\n--- Step 3: Cleaning Up ---")
        if vdev:
            vdev.destroy()
            print("Virtual controller destroyed.")
        if hid_device:
            hid_device.close()
            print("Physical HID device disconnected.")


if __name__ == "__main__":
    main()
