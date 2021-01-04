# Candle

1. Cannot open shared library - no such file - libgobject-2.0.so.0

	```
	sudo apt-get -y install libgtk2.0-0:i386 libsm6:i386
	```
2. Error while loading shared libraries: libGL.so.1 - no such file

	```
	sudo apt-get -y install libglu1-mesa:i386
	```
3. Lib issue: canberra-gtk-module not loaded
	
	```
	sudo apt -y install libcanberra-gtk-module:i386
	```
4. Failed to load the library: udev, supported versions 1 and 0.
	
	```
	sudo apt -y install libudev-dev:i386
	```
5. Failed to load module: atk-bridge
	
	```
	sudo apt -y install libatk-adaptor:i386
	```

# Errors connecting to Arduino

Enable USB com port access to the current user:

```
sudo usermod -a -G dialout USER
sudo reboot
```

# Manually Upload .hex file to Arduino
(just change the filepath)

```
/snap/arduino/41/hardware/tools/avr/bin/avrdude -C/snap/arduino/41/hardware/tools/avr/etc/avrdude.conf -v -patmega2560 -cwiring -P/dev/ttyACM0 -b115200 -D -Uflash:w:/tmp/grbl.hex:i
```

# Compile grbl-hotwire .hex manually

Error: avr-gcc not found

```
sudo apt-get -y install avr-libc gcc-avr
```

# Pywing Errors
This is not an error, but just a warning showing that you're logged in as a root user.
This is the way it's supposed to be, so just ignore the warning.


```
QStandardPaths: XDG_RUNTIME_DIR not set, defaulting to '/tmp/runtime-root'
```


