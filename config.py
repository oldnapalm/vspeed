from ant.core import log
from functions import getserial
import hashlib

DEBUG = False

# ANT+ ID of the virtual SDM
# The expression below will choose a fixed ID based on the CPU's serial number
SDM_ID = int(int(hashlib.md5(getserial().encode()).hexdigest(), 16) & 0xfffe) + 1

# Set to None to disable ANT+ message logging
LOG = None
# LOG = log.LogWriter(filename="vspeed.log")

# ANT+ network key
NETKEY = b'\xB9\xA5\x21\xFB\xBD\x72\xC3\x45'
