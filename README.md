# ANT+ Virtual Stride Based Speed and Distance Monitor

## Overview

This project implements "virtual speed" from heart rate monitor. The calculated speed is broadcasted as such on ANT+ (using [python-ant](https://github.com/mvillalba/python-ant)). Based on [vpower](https://github.com/dhague/vpower) by Darren Hague.

Even if the receiver app runs on the same computer, you will need two ANT+ sticks, because one device can't be used by two apps simultaneously.

Supported devices:
* [ANTUSB2 Stick](http://www.thisisant.com/developer/components/antusb2/) (0fcf:1008: Dynastream Innovations, Inc.)
* [ANTUSB-m Stick](http://www.thisisant.com/developer/components/antusb-m/) (0fcf:1009: Dynastream Innovations, Inc.)

Warning: the [Cycplus ANT Stick](https://tacxfaqx.com/knowledge-base/cycplus-ant-stick/) is not compatible, even though it uses the same Vendor ID and Product ID (0fcf:1008) as the ANTUSB2 Stick.

## Running on Windows

* Download the [standalone executable](https://github.com/oldnapalm/vspeed/releases/latest)
* Install the libusb-win32 driver for the ANT+ device (if not already installed), it can be easily done using [Zadig](https://zadig.akeo.ie/)
  * Options - List All Devices
  * Select ANT+ stick
  * Select libusb-win32 driver and click Replace Driver
* Run the downloaded executable

## Running from source code (Windows, Linux, macOS)

* Install [Python 3](https://www.python.org/downloads/) if not already installed
  * Check "Add Python to PATH" or use the full path in the commands below
* Clone or download this repo
* CD to the repo directory and run `pip install -r requirements.txt`
  * On Linux and macOS use `pip3` instead of `pip`
* [Optional] Run `pip install pywin32` (Windows only, to stop the ANT node on terminal window close)
* Run `python vspeed.py` (or double click **vspeed.py** if you installed the Python Launcher)
  * On Linux and macOS use `python3` instead of `python`
