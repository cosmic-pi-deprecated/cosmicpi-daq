import logging
import serial
import termios
import time

log = logging.getLogger(__name__)


class UsbHandler(object):

    def __init__(self, usbdev, baudrate, timeout):
        self.usbdev   = usbdev
        self.baudrate = baudrate
        self.timeout  = timeout
        self.is_open = False
        self.enabled = True

    def open(self):
        self.usb = serial.Serial(port=self.usbdev, baudrate=self.baudrate, timeout=self.timeout)
        self.attr = termios.tcgetattr(self.usb)
        self.attr[2] = self.attr[2] & ~termios.HUPCL            # Clear HUPCL in control reg (2)
        termios.tcsetattr(self.usb, termios.TCSANOW, self.attr) # and write
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
