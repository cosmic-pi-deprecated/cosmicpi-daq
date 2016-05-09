from __future__ import print_function

import json
from optparse import OptionParser

import sys
import time

import pika
import serial
import struct

from event import Event

import logging

logging.basicConfig(
    format='%(asctime)s %(filename)-12s %(levelname)-8s %(message)s',
    level=logging.DEBUG)
logger = logging.getLogger(__name__)


class Socket_io(object):
    def __init__(self, ipaddr, ipport):
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=ipaddr, port=8080, credentials=pika.PlainCredentials('test', 'test')))
        self.channel = self.connection.channel()
        self.channel.exchange_declare(exchange='events', type='fanout')

    def send_event_pkt(self, pkt):
        self.channel.basic_publish(exchange='events', routing_key='', body=json.dumps(pkt.event))
        logger.info("sent event %r" % pkt)

    def close(self):
        self.connection.close()


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

    event = Event()
    sio = Socket_io(host, port)

    try:
        serial_port = serial.Serial(port=usbdev, baudrate=9600, timeout=60)
        serial_port.flush()
    except Exception as e:
        logger.info("Exception: Cant open USB device: %s" % e)
        sys.exit(1)

    while True:
        line = serial_port.readline()
        id = ord(struct.unpack('=c', line[0])[0])

        if id == 1:
            event.set_temperature(struct.unpack("=cffc", line))
        elif id == 2:
            if len(line) < 14:
                line += serial_port.readline()
            data = struct.unpack("=cfffc", line)
            event.set_barometer(data)

        elif id == 3:  # vibration
            data = struct.unpack("=ciic", line)
            event.set_vibration(data)

        elif id == 4:  # magnetic field strength
            data = struct.unpack("=cfffc", line)
            event.set_mag_field_strength(data)

        elif id == 5:
            data = struct.unpack("=cfffc", line)
            event.set_mag_orientation(data)

        elif id == 6:  # accelerometer
            data = struct.unpack("=cfffc", line)
            event.set_accel(data)

        elif id == 7:  # accelerometer orientation
            data = struct.unpack("=cfffc", line)
            event.set_accel_orientation(data)

        elif id == 8:  # GPS
            data = struct.unpack("=cfffc", line)
            event.set_gps(data)

        elif id == 9:  # timing
            data = struct.unpack("=ciiic", line)
            event.set_timing(data)

        elif id == 10:  # statuses
            if len(line) < 30:
                line += serial_port.readline()
            data = struct.unpack("=ciii4?c", line)
            event.set_status(data)

        elif id == 11:  # ADC readout
            data = struct.unpack("=ciiif600ic", line)
            event.set_adc(data)

        elif id == 12:  # power
            data = struct.unpack("=ciiic", line)
            event.set_power(data)

        time.sleep(1)

        sio.send_event_pkt(event)


if __name__ == '__main__':
    main()
