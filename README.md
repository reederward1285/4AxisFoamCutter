# CNC Foam Cutting Machine Upgrade

The machine was made by the company Step-Four, however documentation is not available since Step-Four went out of business several years ago.

# The machine includes:

1. Four axis (independent axes) stepper motor setup
2. Step-Four motor controller communicating with a Win98 computer over the parallel port
3. Step-Four power supply for the hot wire

The motor controller will have to be replaced with an Arduino since the S4CUT software locks down the controller.
This prevents the Step-Four controller from being usable with any other software.

# New machine setup:

1. New computer running Linux
2. Arduino Mega 2560 + RAMPS 1.4
3. Step-Four hot wire power supply
4. Four axis stepper motor setup

# Software:

1. Coordinates of profile #1 and #2 convert to GCODE : pywing
2. GCODE editing/viewing/sending to Arduino : pywing
3. Arduino GCODE processing firmware : grbl

# Firmware:
The firmware is a modified version of rckeith's 4.5-axis CNC foam cutting Arduino firmware. It has been modified to accept an XYUZ-axis system.

To upload the firmware, go to the Arduino software. Open Sketch->Include Library->Add .ZIP Library and then open the grbl folder under grbl_firmware_rckeith.

Then, under File->Examples, open grblUpload under grbl. Upload this firmware, and open the serial monitor and type:
```
$$
```
to view the list of settings in the firmware. To change a setting, type:
```
$1 = 10 (Using this format: $### = ###)
```
and hit the send button. Type "$$" again and see the changes to make sure they took effect.

# Setup
To setup a new computer, install Ubuntu 20 LTS and run:
```
git clone https://github.com/reederward1285/4AxisFoamCutter.git
cd Setup
./install_ubuntu_dependencies
```
from the Setup folder. This will install the necessary packages needed for pywing, such as pyqt5.