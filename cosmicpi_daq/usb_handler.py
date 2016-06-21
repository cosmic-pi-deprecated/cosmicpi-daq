# -*- coding: utf-8 -*-
#
# This file is part of CosmicPi-DAQ.
# Copyright (C) 2016 Justin Lewis Salmon.
#
# CosmicPi-DAQ is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# CosmicPi-DAQ is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with CosmicPi-DAQ; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.

"""USB handler implementation."""

import logging
import termios
import time

import serial

log = logging.getLogger(__name__)


class UsbHandler(object):

    def __init__(self, usbdev, baudrate, timeout):
        self.usbdev = usbdev
        self.baudrate = baudrate
        self.timeout = timeout
        self.is_open = False
        self.enabled = True

    def open(self):
        self.usb = serial.Serial(
            port=self.usbdev,
            baudrate=self.baudrate,
            timeout=self.timeout)
        self.attr = termios.tcgetattr(self.usb)
        # Clear HUPCL in control reg (2)
        self.attr[2] = self.attr[2] & ~termios.HUPCL
        termios.tcsetattr(self.usb, termios.TCSANOW, self.attr)  # and write
        log.info("Serial port %s opened" % self.usbdev)
        self.is_open = True

    def close(self):
        try:
            self.usb.close()
        except:
            pass
        self.is_open = False

    def enable(self):
        self.enabled = True
        log.info("Enabling serial port")

    def disable(self):
        self.enabled = False
        log.info("Disabling serial port")
        self.close()

    def readline(self):
        if not self.enabled:
            time.sleep(1)
            return ''

        if not self.is_open:
            try:
                self.open()
            except Exception as e:
                log.warn("Couldn't open serial port: %s" % e)
                time.sleep(1)

        try:
            line = self.usb.readline()
            if len(line) == 0:
                log.warn("Serial input buffer empty")
                self.close()

        except Exception as e:
            log.warn("Error reading from serial port: %s" % e)
            self.close()
            line = ''

        return line

    def write(self, arg):
        self.usb.write(arg)
