#!/usr/bin/env python
import os, sys
import time
import csv
import platform

from ant.core import driver, node, event, message
from ant.core.constants import *

from usb.core import find

from SDMTx import SDMTx
from config import DEBUG, LOG, NETKEY, SDM_ID
from functions import interp

if getattr(sys, 'frozen', False):
    # If we're running as a pyinstaller bundle
    SCRIPT_DIR = os.path.dirname(sys.executable)
else:
    SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))

def convertSB(raw):
    value = int(raw[1]) << 8
    value += int(raw[0])
    return value

class CadenceListener(event.EventCallback):
    lastTime = None
    lastRevolutions = None

    def calcCadence(self, time, revolutions):
        if self.lastTime is None:
            return 0

        if time < self.lastTime:
            time += 65536

        if revolutions < self.lastRevolutions:
            revolutions += 65536

        return (revolutions - self.lastRevolutions) * 1024 * 60 / (time - self.lastTime)

    def process(self, msg):
        if isinstance(msg, message.ChannelBroadcastDataMessage):
            page = msg.payload[1] & 0x7F
            if page != 0:
                return

            eventTime = convertSB(msg.payload[5:7])
            if eventTime == self.lastTime:
                return

            revolutions = convertSB(msg.payload[7:9])

            cadence = self.calcCadence(eventTime, revolutions)
            speed = interp(xp, yp, cadence)
            sdm.update(speed, cadence * 2)

            self.lastTime = eventTime
            self.lastRevolutions = revolutions

antnode = None
cadence_sensor = None
sdm = None

last_event = 0
last_time = 0
stopped = True

xp = [0]
yp = [0]
cadence_file = '%s/cadence.csv' % SCRIPT_DIR
if os.path.isfile(cadence_file):
    with open(cadence_file, 'r') as fd:
        reader = csv.reader(fd)
        next(reader, None)
        for line in reader:
            xp.append(int(line[0]))
            yp.append(int(line[1]))
else:
    xp.extend([60, 70, 80, 90, 100])
    yp.extend([5, 7, 10, 12, 15])

def stop_ant():
    if cadence_sensor:
        print("Closing cadence sensor")
        cadence_sensor.close()
        cadence_sensor.unassign()
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

    print("Starting cadence sensor")
    try:
        cadence_sensor = antnode.getFreeChannel()
        cadence_sensor.assign(network, CHANNEL_TYPE_TWOWAY_RECEIVE)
        cadence_sensor.setID(122, 0, 0)
        cadence_sensor.searchTimeout = TIMEOUT_NEVER
        cadence_sensor.period = 8102
        cadence_sensor.frequency = 57
        cadence_sensor.open()
    except Exception as e:
        print("cadence_sensor error: " + repr(e))
        cadence_sensor = None

    cadence_listener = CadenceListener()
    antnode.registerEventListener(cadence_listener)

    print("Starting SDM with ANT+ ID " + repr(SDM_ID))
    try:
        # Create the SDM object and open it
        sdm = SDMTx(antnode, SDM_ID)
        sdm.open()
    except Exception as e:
        print("sdm error: " + repr(e))
        sdm = None

    print("Main wait loop")
    while True:
        try:
            if not stopped:
                t = int(time.time())
                if t >= last_time + 3:
                    if cadence_listener.lastTime == last_event:
                        # Set speed to zero if cadence sensor doesn't update for 3 seconds
                        sdm.SDMData.instantaneousSpeed = 0
                        stopped = True
                    last_event = cadence_listener.lastTime
                    last_time = t
                sdm.update(sdm.SDMData.instantaneousSpeed)
            elif sdm.SDMData.instantaneousSpeed:
                stopped = False
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
