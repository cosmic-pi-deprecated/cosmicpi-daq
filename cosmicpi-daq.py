from __future__ import print_function
from optparse import OptionParser

import sys
import time
import serial
import struct


def main():
    parser = OptionParser()
    parser.add_option("-i", "--host", help="Server hostname or IP address", dest="host", default="localhost")
    parser.add_option("-p", "--port", help="Server port", dest="port", type="int", default="4901")
    parser.add_option("-u", "--usb", help="USB device name", dest="usbdev", default="/dev/ttyACM0")
    parser.add_option("-d", "--debug", help="Debug mode", dest="debug", default=False, action="store_true")
    parser.add_option("-o", "--odir", help="Path to log directory", dest="logdir", default="/tmp")
    options, args = parser.parse_args()

    host = options.host
    port = options.port
    usbdev = options.usbdev
    logdir = options.logdir
    debug = options.debug

    try:
        serial_port = serial.Serial(port=usbdev, baudrate=9600, timeout=60)
        serial_port.flush()
    except Exception as e:
        print("Exception: Cant open USB device: %s" % e)
        sys.exit(1)

    while True:
        line = serial_port.readline()
        id = ord(struct.unpack('=c', line[0])[0])

        if id == 1:  # temperature/pressure
            data = struct.unpack("=cffc", line)
            print('1: temperature=%f humidity=%f' % (data[1], data[2]))

        elif id == 2:  # barometer
            if len(line) < 14:
                line += serial_port.readline()
            data = struct.unpack("=cfffc", line)
            print('2: temperature=%f pressure=%f altitude=%f' % (data[1], data[2], data[3]))

        elif id == 3:  # vibration
            data = struct.unpack("=ciic", line)
            print('9: direction=%i count=%i' % (data[1], data[2]))

        elif id == 4:  # magnetic field strength
            data = struct.unpack("=cfffc", line)
            print('4: x=%f y=%f x=%f' % (data[1], data[2], data[3]))

        elif id == 5:  # magnetic orientation
            data = struct.unpack("=cfffc", line)
            print('5: x=%f y=%f x=%f' % (data[1], data[2], data[3]))

        elif id == 6:  # accelerometer
            data = struct.unpack("=cfffc", line)
            print('6: x=%f y=%f x=%f' % (data[1], data[2], data[3]))

        elif id == 7:  # accelerometer orientation
            data = struct.unpack("=cfffc", line)
            print('7: x=%f y=%f x=%f' % (data[1], data[2], data[3]))

        elif id == 8:  # GPS
            data = struct.unpack("=cfffc", line)
            print('8: latitude=%f longitude=%f altitude=%f' % (data[1], data[2], data[3]))

        elif id == 9:  # timing
            data = struct.unpack("=ciiic", line)
            print('9: uptime=%i counter frequency=%i time string=%i' % (data[1], data[2], data[3]))

        elif id == 10:  # statuses
            if len(line) < 30:
                line += serial_port.readline()
            data = struct.unpack("=ciii4?c", line)
            print('10: events on queue=%i missed events=%i buffer error=%i' % (data[1], data[2], data[3]))
            print('10: humidity=%i baro=%i accel=%i mag=%i' % (data[4], data[5], data[6], data[7]))

        elif id == 11:  # ADC readout
            data = struct.unpack("=ciiif600ic", line)
            print('9: event number=%i countnumber=%i ticks=%i timestamp=%f' % (data[1], data[2], data[3], data[4]))

        elif id == 12:  # power
            data = struct.unpack("=ciiic", line)
            print('9: voltage=%i psu overflow=%i adc temperature=%i' % (data[1], data[2], data[3]))

        time.sleep(1)


if __name__ == '__main__':
    main()
