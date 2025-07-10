#!/usr/bin/env python3
from communication_tool import Switch2ProControllerEnabler

def main():
    """Main CLI interface"""
    enabler = Switch2ProControllerEnabler()

    try:
        print("=== Switch 2 Pro Controller Enabler (HID AUTO-ENABLE) ===")
        enabler.connect_usb()
        print("\nUSB HID output enabled. Exiting now.")

    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        enabler.disconnect()


if __name__ == "__main__":
    main()
