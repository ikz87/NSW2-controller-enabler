# NSW2 Controller Enabler
Based on [HHL's enabler](https://handheldlegend.github.io/procon2tool/). Currently only works on linux because I don't use windows but PR submissions are more than welcome

## Usage
Run `enable_hid.py` when your controller is connected via USB, that's pretty much it. It will enable HID input for Nintendo Switch 2 Gamecube/Pro controllers.

A virtual controller is created. This is for setting up stick calibration and analog triggers.

## Permissions
To run this, your user must be in the `input` group

Then, create a udev rule at `/etc/udev/rules.d/50-nintendo-switch.rules` with the following contents:
```
SUBSYSTEM=="usb", ATTR{idVendor}=="057e", ATTR{idProduct}=="2066", MODE="0666"
SUBSYSTEM=="usb", ATTR{idVendor}=="057e", ATTR{idProduct}=="2067", MODE="0666"
SUBSYSTEM=="usb", ATTR{idVendor}=="057e", ATTR{idProduct}=="2069", MODE="0666"
SUBSYSTEM=="usb", ATTR{idVendor}=="057e", ATTR{idProduct}=="2073", MODE="0666"
SUBSYSTEM=="hidraw", ATTRS{idVendor}=="057e", ATTRS{idProduct}=="2066", MODE="0666"
SUBSYSTEM=="hidraw", ATTRS{idVendor}=="057e", ATTRS{idProduct}=="2067", MODE="0666"
SUBSYSTEM=="hidraw", ATTRS{idVendor}=="057e", ATTRS{idProduct}=="2069", MODE="0666"
SUBSYSTEM=="hidraw", ATTRS{idVendor}=="057e", ATTRS{idProduct}=="2073", MODE="0666"
```

and reload your rules with `sudo udevadm control --reload-rules`


## Automation
Create a udev rule at `/etc/udev/rules.d/99-nsw2-controller.rules` with the following contents:
```
ACTION=="add", SUBSYSTEM=="usb", ATTR{idVendor}=="057e", ATTRS{idProduct}=="2066|2067|2069|2073", RUN+="<repository path>/enable_hid.py"
```
and reload your rules with `sudo udevadm control --reload-rules`

Make the script executable with `chmod +x <repository path>/enable_hid.py`

This will make the script run everytime a NSW2 Pro controller or GC controller are connected via USB, resulting in a seamless experience as shown below

![2025-07-10_00-08-14-ezgif com-optimize](https://github.com/user-attachments/assets/ed17b7df-1399-4a63-a9e5-54037b42834b)
