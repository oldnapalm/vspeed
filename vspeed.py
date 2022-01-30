#!/usr/bin/env python
import os, sys
import time
import csv
import platform

from ant.core import driver
from ant.core import node
from ant.plus.heartrate import *

from usb.core import find

from SDMTx import SDMTx
from config import DEBUG, LOG, NETKEY, SDM_ID
from functions import interp

if getattr(sys, 'frozen', False):
    # If we're running as a pyinstaller bundle
    SCRIPT_DIR = os.path.dirname(sys.executable)
else:
    SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))

antnode = None
hr_monitor = None
sdm = None

last = 0
stopped = True

xp = [0]
yp = [0]
zones_file = '%s/zones.csv' % SCRIPT_DIR
if os.path.isfile(zones_file):
    with open(zones_file, 'r') as fd:
        reader = csv.reader(fd)
        next(reader, None)
        for line in reader:
            xp.append(int(line[0]))
            yp.append(int(line[1]))
else:
    xp.extend([80, 100, 120, 140, 160, 180])
    yp.extend([0, 9, 10, 11, 12, 15])

def stop_ant():
    if hr_monitor:
        print("Closing HRM")
        hr_monitor.close()
    if sdm:
        print("Closing SDM")
        sdm.close()
        sdm.unassign()
    if antnode:
        print("Stopping ANT node")
        antnode.stop()

pywin32 = False
if platform.system() == 'Windows':
    def on_exit(sig, func=None):
        stop_ant()
    try:
        import win32api
        win32api.SetConsoleCtrlHandler(on_exit, True)
        pywin32 = True
    except ImportError:
        print("Warning: pywin32 is not installed, use Ctrl+C to stop")

def heart_rate_data(computed_heartrate, event_time_ms, rr_interval_ms):
    global last
    global stopped
    t = int(time.time())
    if t >= last + 1:
        speed = interp(xp, yp, computed_heartrate)
        if speed:
            sdm.update(speed)
            stopped = False
        elif not stopped:
            sdm.update(speed)
            stopped = True
        last = t

try:
    devs = find(find_all=True, idVendor=0x0fcf)
    for dev in devs:
        if dev.idProduct in [0x1008, 0x1009]:
            stick = driver.USB2Driver(log=LOG, debug=DEBUG, idProduct=dev.idProduct, bus=dev.bus, address=dev.address)
            try:
                stick.open()
            except:
                continue
            stick.close()
            break
    else:
        print("No ANT devices available")
        if getattr(sys, 'frozen', False):
            input()
        sys.exit()

    antnode = node.Node(stick)
    print("Starting ANT node")
    antnode.start()
    network = node.Network(NETKEY, 'N:ANT+')
    antnode.setNetworkKey(0, network)

    print("Starting SDM with ANT+ ID " + repr(SDM_ID))
    try:
        # Create the SDM object and open it
        sdm = SDMTx(antnode, SDM_ID)
        sdm.open()
    except Exception as e:
        print("sdm error: " + repr(e))
        sdm = None

    print("Starting HRM")
    try:
        # Create the HRM object and open it
        hr_monitor = HeartRate(antnode, network, {'onHeartRateData': heart_rate_data})
        hr_monitor.open()
    except Exception as e:
        print("hr_monitor error: " + repr(e))
        hr_monitor = None

    print("Main wait loop")
    while True:
        try:
            time.sleep(1)
        except (KeyboardInterrupt, SystemExit):
            break

except Exception as e:
    print("Exception: " + repr(e))
    if getattr(sys, 'frozen', False):
        input()
finally:
    if not pywin32:
        stop_ant()
