# CNC Foam Cutting Machine Upgrade

The machine was made by the company Step-Four, however documentation is not available since Step-Four went out of business several years ago.

# The machine includes:

1. Four axis stepper motor setup
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

1. DXF -> GCODE : pywing
2. GCODE editing/viewing/sending to Arduino : Candle
3. Arduino GCODE processing firmware : grbl
