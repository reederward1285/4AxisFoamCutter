# How to use:

Simply run
```
./Gcode_Generator.sh
```
in a linux terminal window. Then, import the left wing profile and the right wing profile. The file format for wing profiles
is just a *.txt or *.dat file with a list of coordinates. Below
is an example:
```
20-32C AIRFOIL
1.000000 0.001600
0.950000 0.012400
0.900000 0.022900
0.800000 0.042800
0.700000 0.061000
0.600000 0.077100
0.500000 0.090500
0.400000 0.100200
0.300000 0.104800
0.250000 0.104400
0.200000 0.101300
0.150000 0.093400
0.100000 0.078000
0.075000 0.066400
0.050000 0.051300
0.025000 0.031700
0.012500 0.019300
0.000000 0.000000
0.012500 -0.005000
0.025000 -0.004200
0.050000 -0.001000
0.075000 0.002800
0.100000 0.006800
0.150000 0.014500
0.200000 0.021700
0.250000 0.028200
0.300000 0.033300
0.400000 0.038500
0.500000 0.038600
0.600000 0.035000
0.700000 0.028600
0.800000 0.020200
0.900000 0.010000
0.950000 0.004400
1.000000 -0.001600
```

Then, choose the rest of your settings, connect to the arduino using the connect button, and then hit the play button to start the machine.

# Background:

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