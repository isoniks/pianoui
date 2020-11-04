# Attention - WIP
Work in progress. Don't use it yet.

# Description
Volumio UI for retrofit attempt of Yamaha PianoCraft DVD-E600 with RPi, Volumio 2, DAC, buttons and PSU.

## Hardware
* Yamaha PianoCraft DVD-E600, stripped of internals
* PSU Meanwell RS-15-5 5V 3A 15W 
* Raspberry Pi 2B/3B with Volumio2 image
* RPi DAC Burr-Brown PCM 5122 with GPIO pins
* 2.8" 256x64 Pixels 4-wire SPI OLED Display with SSD1322 controller IC
* 6 pushbuttons, pull-up resistors, breadboard, wires, pins, glue, dremel, crimping tool, soldering iron

### Critical Success Factors
* coffee
* cat
* use 3.3V power for OLED 
* check TWO TIMES wiring (at least the power line) for OLED screen

### Constraints
* make use of 6 push-buttons on front panel.
* the visible area of OLED screen is wider than window in a front glass. First 30 pixels will remain concealed.
* ttf font must support Cyrillic script

### Approach
* Develop screen UI
* Hook-up functions on push-buttons:
  * Play / Pause
  * Stop
  * Prev
  * Next
  * Clear playlist (Eject button)
  * Power off
* Play Yello

## Dependencies
* [socketIO-client](https://pypi.org/project/socketIO-client/)
* PIL
* [luma.oled](https://luma-oled.readthedocs.io/)

## Install
get [ssh access to Volumio](https://volumio.github.io/docs/User_Manual/SSH.html), login
and
enable SPI bus by adding
```
dtparam=spi=on
```
to /boot/userconfig.txt via
```
sudo nano /boot/userconfig.txt
```
and
reconfigute timezone
```
sudo dpkg-reconfigure tzdata
```

### installation steps
```
sudo apt-get update
sudo apt-get install -y python-dev python-pip libfreetype6-dev libjpeg-dev build-essential python-rpi.gpio
sudo pip install --upgrade pip wheel
sudo pip install --upgrade setuptools
sudo pip install --upgrade socketIO-client luma.core==1.8.3 luma.oled==3.1.0
sudo apt-get install python-pycurl
git clone https://github.com/isoniks/pianoui.git
chmod +x ~/pianoui/piui.py
```
### test run
```
cd pianoui/
python piui.py
```

### run as daemon
```
sudo cp ~/pianoui/piui.service /lib/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable piui.service
reboot
```

### how to check the logs
```
sudo journalctl -fu piui.service
```
## Credits & Kudos
Thanks to following folks for their great projects:
* [diehardsk](https://github.com/diehardsk/Volumio-OledUI)
* [Maschine2501](https://github.com/Maschine2501/NR1-UI)
