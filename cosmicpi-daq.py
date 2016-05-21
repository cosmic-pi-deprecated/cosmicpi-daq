#! /usr/bin/python
#  coding: utf8

from __future__ import print_function

from pika.exceptions import ConnectionClosed, ProbableAuthenticationError

"""
Talk to the CosmicPi Arduino DUE accross the serial USB link
This program has the following functions ...

1) Build event messages and send them to a server or local port

  Events are any combination of Vibration, Weather and CosmicRays
  Hence the Arduino can behave as a weather station, as a vibration/Siesmic monitor
  and as a cosmic ray detector.
  There is a gyroscope available but I don't use it

2) Perform diagnostics and monitoring of the Arduino via commands

3) Log events to the log file

It is important to keep the Python dictionary objects synchronised with the Arduino firmware
otherwise this monitor will not understand the data being sent to it

julian.lewis lewis.julian@gmail.com 7/Apr/2016

"""

import sys
import serial
import time
import traceback
import termios
import logging.config
from optparse import OptionParser

from sock import Socket_io
from detector import Detector
from command_handler import CommandHandler


logging.config.fileConfig("logging.conf", disable_existing_loggers=False)
logfile = logging.getLogger('file')
console = logging.getLogger(__name__)


class usb_io(object):

    def __init__(self, usbdev, baudrate, timeout):
        self.usbdev   = usbdev
        self.baudrate = baudrate
        self.timeout  = timeout
        self.is_open = False

    def open(self):
        self.usb = serial.Serial(port=self.usbdev, baudrate=self.baudrate, timeout=self.timeout)
        self.attr = termios.tcgetattr(self.usb)
        self.attr[2] = self.attr[2] & ~termios.HUPCL            # Clear HUPCL in control reg (2)
        termios.tcsetattr(self.usb, termios.TCSANOW, self.attr) # and write
        console.info("Serial port %s opened" % self.usbdev)
        self.is_open = True

    def close(self):
        self.usb.close()
        self.is_open = False

    def readline(self):
        if not self.is_open:
            try:
                self.open()
            except Exception as e:
                console.warn("Couldn't open serial port: %s" % e)
                time.sleep(1)

        try:
            line = self.usb.readline()
            if len(line) == 0:
                console.warn("Serial input buffer empty")
                self.close()

        except Exception as e:
            console.warn("Error reading from serial port: %s" % e)
            self.close()
            line = ''

        return line

    def write(self, arg):
        self.usb.write(arg)


def main():
    use = "Usage: %prog [--ip=cosmicpi.ddns.net --port=4901 --usb=/dev/ttyACM0 --debug --dirnam=/tmp]"
    parser = OptionParser(usage=use, version="cosmic_pi version 1.0")

    parser.add_option("-i", "--host", help="Message broker host", dest="host", default="localhost")
    parser.add_option("-p", "--port", help="Message broker port", dest="port", type="int", default="5672")
    parser.add_option("-x", "--credentials", help="Message broker credentials", dest="credentials", default="test:test")
    parser.add_option("-u", "--usb", help="USB device name", dest="usbdev", default="/dev/ttyACM0")
    parser.add_option("-d", "--debug", help="Debug Option", dest="debug", default=False, action="store_true")
    parser.add_option("-o", "--odir", help="Path to log directory", dest="logdir", default="/tmp")
    parser.add_option("-n", "--noip", help="IP Sending", dest="udpflg", default=True, action="store_false")
    parser.add_option("-l", "--log", help="Event Logging", dest="logflg", default=False, action="store_true")
    parser.add_option("-v", "--vib", help="Vibration monitor", dest="vibflg", default=False, action="store_true")
    parser.add_option("-w", "--ws", help="Weather station", dest="wstflg", default=False, action="store_true")
    parser.add_option("-c", "--cray", help="Cosmic ray sending", dest="evtflg", default=True, action="store_false")
    parser.add_option("-k", "--patk", help="Server push notification token", dest="patok", default="")

    options, args = parser.parse_args()

    host = options.host
    port = options.port
    usbdev = options.usbdev
    logdir = options.logdir
    debug = options.debug
    udpflg = options.udpflg
    logflg = options.logflg
    vibflg = options.vibflg
    wstflg = options.wstflg
    evtflg = options.evtflg
    patok = options.patok

    try:
        credentials = options.credentials.split(':')
        username = credentials[0]
        password = credentials[1]
    except Exception:
        console.error("Fatal: Couldn't parse the connection credentials. Format is username:password")
        sys.exit(1)

    try:
        sio = Socket_io(host, port, username, password)
    except ConnectionClosed:
        console.error("Fatal: Couldn't establish a connection to the broker. Please check the connection parameters.")
        console.error("Fatal: Connection parameters were: %s:%s@%s:%s" % (username, password, host, port))
        sys.exit(1)
    except ProbableAuthenticationError:
        console.info("Fatal: Couldn't establish a connection to the broker. Probably incorrect connection credentials.")
        sys.exit(1)


    pushflg = False

    console.debug("options (Server IP address)     ip   : %s" % host)
    console.debug("options (Server Port number)    port : %d" % port)
    console.debug("options (USB device name)       usb  : %s" % usbdev)
    console.debug("options (Logging directory)     odir : %s" % logdir)
    console.debug("options (Event logging)         log  : %s" % logflg)
    console.debug("options (UDP sending)           udp  : %s" % udpflg)
    console.debug("options (Vibration monitor)     vib  : %s" % vibflg)
    console.debug("options (Weather Station)       wst  : %s" % wstflg)
    console.debug("options (Cosmic Ray Station)    cray : %s" % evtflg)
    console.debug("options (Push notifications)    patk : %s" % patok)
    console.debug("options (Debug Flag)            debug: %s" % debug)

    try:
        usb = usb_io(usbdev, 9600, 60)
        usb.open()
    except Exception as e:
        console.error("Exception: Cant open USB device: %s" % (e))
        sys.exit(1)

    detector = Detector(usb, sio, options)

    try:
        detector.start()

        command_handler = CommandHandler(detector, usb, options)
        command_handler.start()

        while True:
            time.sleep(1)

    except Exception, e:
        console.info("Exception: main: %s" % (e))
        traceback.print_exc()

    finally:
        detector.stop()
        console.info("Quitting ...")
        time.sleep(1)
        usb.close()
        sio.close()
        sys.exit(0)

if __name__ == '__main__':
    main()
