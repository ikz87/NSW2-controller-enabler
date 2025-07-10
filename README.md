# NSW2 Controller Enabler
Based on [HHL's enabler](https://handheldlegend.github.io/procon2tool/). Currently only works on linux because I don't use windows but PR submissions are more than welcome

## Usage
Run `enable_hid.py` when your controller is connected via USB, that's pretty much it. It will enable HID input for Nintendo Switch 2 Gamecube/Pro controllers, but analog trigger axies are missing for the GCC's

Joystick axies are not well calibrated, you'll have to set calibrations correctly where you're gonna use it (Dolphin provides this if you're curious)

Additional tools are provided in `communication_tool.py` for trying out sending data to the controller

## Automatization
Create a udev rule at /etc/udev/rules.d/99-nsw2-controller.rules with the following contents:
```
ACTION=="add", SUBSYSTEM=="usb", ATTR{idVendor}=="057e", ATTRS{idProduct}=="2066|2067|2069|2073", RUN+="<repository path>/enable_hid.py"
```

Make the script executable with `chmod +x <repository path>/enable_hid.py`

This will make the script run everytime a NSW2 Pro controller or GC controller are connected via USB, resulting in a seamless experience as shown below

![2025-07-10_00-08-14-ezgif com-optimize](https://github.com/user-attachments/assets/ed17b7df-1399-4a63-a9e5-54037b42834b)
