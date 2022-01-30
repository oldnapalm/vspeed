#!/usr/bin/env python
import sys
import time
import platform
import tkinter as tk

from ant.core import driver
from ant.core import node

from usb.core import find

from SDMTx import SDMTx
from config import DEBUG, LOG, NETKEY, SDM_ID

antnode = None
sdm = None

def stop_ant():
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

def disable_event():
    pass

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
    key = node.Network(NETKEY, 'N:ANT+')
    antnode.setNetworkKey(0, key)

    print("Starting SDM with ANT+ ID " + repr(SDM_ID))
    try:
        # Create the SDM object and open it
        sdm = SDMTx(antnode, SDM_ID)
        sdm.open()
    except Exception as e:
        print("sdm error: " + repr(e))
        sdm = None

    master = tk.Tk()
    master.title("Bot")
    master.geometry("200x50")
    master.resizable(False, False)
    master.call('wm', 'attributes', '.', '-topmost', '1')
    master.protocol("WM_DELETE_WINDOW", disable_event)
    w = tk.Scale(master, from_=0.0, to=20.0, digits=3, resolution=0.1, length=200, orient=tk.HORIZONTAL)
    w.pack()

    last = 0
    stopped = True

    print("Main wait loop")
    while True:
        try:
            t = int(time.time())
            if t >= last + 1:
                speed = w.get()
                if speed:
                    sdm.update(speed)
                    stopped = False
                elif not stopped:
                    sdm.update(speed)
                    stopped = True
                last = t
            master.update_idletasks()
            master.update()
        except (KeyboardInterrupt, SystemExit):
            break

except Exception as e:
    print("Exception: " + repr(e))
    if getattr(sys, 'frozen', False):
        input()
finally:
    if not pywin32:
        stop_ant()
