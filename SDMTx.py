import sys
from ant.core import message, node
from ant.core.constants import *
from ant.core.exceptions import ChannelError

from config import NETKEY, DEBUG

DEVICE_TYPE = 0x7C
CHANNEL_PERIOD = 8134


# Transmitter for Stride Based Speed and Distance Monitor
class SDMTx(object):
    class SDMData:
        def __init__(self):
            self.instantaneousSpeed = 0
            self.strideCount = 0

    def __init__(self, antnode, sensor_id):
        self.antnode = antnode

        # Get the channel
        self.channel = antnode.getFreeChannel()
        try:
            self.channel.name = 'C:SDM'
            network = node.Network(NETKEY, 'N:ANT+')
            self.channel.assign(network, CHANNEL_TYPE_TWOWAY_TRANSMIT)
            self.channel.setID(DEVICE_TYPE, sensor_id, 0)
            self.channel.period = CHANNEL_PERIOD
            self.channel.frequency = 57
        except ChannelError as e:
            print("Channel config error: " + repr(e))
        self.SDMData = SDMTx.SDMData()

    def open(self):
        self.channel.open()

    def close(self):
        self.channel.close()

    def unassign(self):
        self.channel.unassign()

    def update(self, speed, cadence=0):
        if DEBUG: print('SDMTx: update called with speed ', speed)
        self.SDMData.instantaneousSpeed = speed
        if DEBUG: print('instantaneousSpeed ', self.SDMData.instantaneousSpeed)
        speed_ms = speed / 3.6

        if cadence == 0:
            self.SDMData.strideCount = (self.SDMData.strideCount + 1) & 0xff
            if DEBUG: print('strideCount ', self.SDMData.strideCount)

            payload = bytearray(b'\x01')  # Data Page Number
            payload.append(0x00)
            payload.append(self.SDMData.strideCount)  # Time
            payload.append(0x00)
            payload.append(int(speed_ms) & 0xf)
            payload.append(int((speed_ms % 1) * 256) & 0xff)
            payload.append(self.SDMData.strideCount)
            payload.append(0x00)

        else:
            payload = bytearray(b'\x02')
            payload.append(0xff)
            payload.append(0xff)
            payload.append(int(cadence) & 0xff)
            payload.append(int(speed_ms) & 0xf)
            payload.append(int((speed_ms % 1) * 256) & 0xff)
            payload.append(0xff)
            payload.append(0x01)

        ant_msg = message.ChannelBroadcastDataMessage(self.channel.number, data=payload)
        print(f'Speed: {speed:.1f} km/h \r', end="")
        if DEBUG: print('Write message to ANT stick on channel ' + repr(self.channel.number))
        self.antnode.send(ant_msg)
