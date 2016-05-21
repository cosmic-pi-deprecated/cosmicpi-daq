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

Typing the '>' character turns on command input

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

from event import Event
from sock import Socket_io
from keyboard import KeyBoard


logging.config.fileConfig("logging.conf")
logfile = logging.getLogger('file')
console = logging.getLogger(__name__)


class usb_io(object):

    def __init__(self, usbdev, baudrate, timeout):
        self.usbdev   = usbdev
        self.baudrate = baudrate
        self.timeout  = timeout

    def open(self):
        self.usb = serial.Serial(port=self.usbdev, baudrate=self.baudrate, timeout=self.timeout)
        self.attr = termios.tcgetattr(self.usb)
        self.attr[2] = self.attr[2] & ~termios.HUPCL            # Clear HUPCL in control reg (2)
        termios.tcsetattr(self.usb, termios.TCSANOW, self.attr) # and write
        console.info("Serial port %s opened" % self.usbdev)

    def close(self):
        self.usb.close()

    def readline(self):
        if not self.usb.is_open:
            try:
                self.open()
            except Exception as e:
                console.warn("Couldn't open serial port: %s" % e)
                time.sleep(1)

        try:
            line = self.usb.readline()
            if len(line) == 0:
                console.warn("Serial input buffer empty")
                self.usb.close()

        except Exception as e:
            console.warn("Error reading from serial port: %s" % e)
            self.usb.close()
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

    console.debug("cosmic_pi monitor running, hit '>' for commands")

    try:
        usb = usb_io(usbdev, 9600, 60)
        usb.open()
    except Exception as e:
        console.error("Exception: Cant open USB device: %s" % (e))
        sys.exit(1)

    evt = Event()
    events = 0
    vbrts = 0
    weathers = 0

    kbrd = KeyBoard()
    kbrd.echo_off()

    try:
        while (True):
            if kbrd.test_input():
                kbrd.echo_on()
                print ("\n")
                cmd = raw_input(">")

                if cmd.find("q") != -1:
                    break

                elif cmd.find("d") != -1:
                    if debug:
                        debug = False
                    else:
                        debug = True
                    print ("Debug:%s\n" % debug)

                elif cmd.find("v") != -1:
                    if vibflg:
                        vibflg = False
                    else:
                        vibflg = True
                    print ("Vibration:%s\n" % vibflg)

                elif cmd.find("w") != -1:
                    if wstflg:
                        wstflg = False
                    else:
                        wstflg = True
                    print ("WeatherStation:%s\n" % wstflg)

                elif cmd.find("r") != -1:
                    if len(patok) > 0:
                        if pushflg:
                            pushflg = False
                            print ("Unregister server notifications")
                        else:
                            pushflg = True
                            print ("Register for server notifications")

                        if udpflg:
                            evt.set_pat(patok, pushflg)
                            pbuf = evt.get_notification()
                            sio.send_event_pkt(pbuf)
                            sbuf = evt.get_status()
                            sio.send_event_pkt(sbuf)
                            print ("Sent notification request:%s" % pbuf)
                        else:
                            print ("UDP sending is OFF, can not register with server")
                            pbuf = ""
                    else:
                        print ("Token option is not set")

                elif cmd.find("s") != -1:
                    tim = evt.get_tim()
                    sts = evt.get_sts()
                    loc = evt.get_loc()
                    acl = evt.get_acl()
                    mag = evt.get_mag()
                    bmp = evt.get_bmp()
                    htu = evt.get_htu()
                    vib = evt.get_vib()

                    print ("ARDUINO STATUS")
                    print ("Status........: uptime:%s counter_frequency:%s queue_size:%s missed_events:%s" % (
                        tim["uptime"], tim["counter_frequency"], sts["queue_size"], sts["missed_events"]))
                    print ("HardwareStatus: temp_status:%s baro_status:%s accel_status:%s mag_status:%s gps_status:%s" % (
                        sts["temp_status"], sts["baro_status"], sts["accel_status"], sts["mag_status"], sts["gps_status"]))
                    print ("Location......: latitude:%s longitude:%s altitude:%s" % (loc["latitude"], loc["longitude"], loc["altitude"]))
                    print ("Accelerometer.: x:%s y:%s z:%s" % (acl["x"], acl["y"], acl["z"]))
                    print ("Magnetometer..: x:%s y:%s z:%s" % (mag["x"], mag["y"], mag["z"]))
                    print ("Barometer.....: temperature:%s pressure:%s altitude:%s" % (bmp["temperature"], bmp["pressure"], bmp["altitude"]))
                    print ("Humidity......: temperature:%s humidity:%s" % (htu["temperature"], htu["humidity"]))
                    print ("Vibration.....: direction:%s count:%s\n" % (vib["direction"], vib["count"]))

                    print ("MONITOR STATUS")
                    print ("USB device....: %s" % (usbdev))
                    print ("Remote........: Ip:%s Port:%s UdpFlag:%s" % (host, port, udpflg))
                    print ("Notifications.: Flag:%s Token:%s" % (pushflg, patok))
                    print ("Vibration.....: Sent:%d Flag:%s" % (vbrts, vibflg))
                    print ("WeatherStation: Flag:%s" % (wstflg))
                    print ("Events........: Sent:%d LogFlag:%s" % (events, logflg))

                elif cmd.find("h") != -1:
                    print ("MONITOR COMMANDS")
                    print ("   q=quit, s=status, d=toggle_debug, n=toggle_send, l=toggle_log")
                    print ("   v=vibration, w=weather, r=toggle_notifications h=help\n")
                    print ("ARDUINO COMMANDS")
                    print ("   NOOP, Do nothing")
                    print ("   HELP, Display commands")
                    print ("   HTUX, Reset the HTH chip")
                    print ("   HTUD, HTU Temperature-Humidity display rate, <rate>")
                    print ("   BMPD, BMP Temperature-Altitude display rate, <rate>")
                    print ("   LOCD, Location latitude-longitude display rate, <rate>")
                    print ("   TIMD, Timing uptime-frequency-etm display rate, <rate>")
                    print ("   STSD, Status info display rate, <rate>")
                    print ("   EVQT, Event queue dump threshold, <threshold 1..32>")
                    print ("   ACLD, Accelerometer display rate, <rate>")
                    print ("   MAGD, Magnetometer display rate, <rate>")
                    print ("   ACLT, Accelerometer event trigger threshold, <threshold 0..127>")
                    print ("")

                    if debug:
                        usb.write("HELP")

                elif cmd.find("n") != -1:
                    if udpflg:
                        udpflg = False
                    else:
                        udpflg = True
                    print ("Send:%s\n" % udpflg)

                elif cmd.find("l") != -1:
                    if logflg:
                        logflg = False
                    else:
                        logflg = True
                    print ("Log:%s\n" % logflg)

                else:
                    print ("Arduino < %s\n" % cmd)
                    usb.write(cmd.upper())

                kbrd.echo_off()

            # Process Arduino data json strings

            rc = usb.readline()
            sio.connection.process_data_events()

            rc = rc.replace('\n', '')
            evt.parse(rc)

            if vibflg:
                vbuf = evt.get_vibration()
                if len(vbuf) > 0:
                    vbrts = vbrts + 1
                    evt.nxt_sqn()
                    dat = evt.get_dat()
                    vib = evt.get_vib()
                    tim = evt.get_tim()
                    acl = evt.get_acl()
                    mag = evt.get_mag()
                    sqn = evt.get_sqn()
                    console.info("")
                    console.info("Vibration.....: count:%d direction:%s count:%s " % (vbrts, vib["direction"], vib["count"]))
                    console.info("Accelerometer.: x:%s y:%s z:%s" % (acl["x"], acl["y"], acl["z"]))
                    console.info("Magnetometer..: x:%s y:%s z:%s" % (mag["x"], mag["y"], mag["z"]))
                    console.info("Time..........: uptime:%s time_string:%s sequence_number:%d\n" % (tim["uptime"], tim["time_string"], sqn["number"]))

                    if udpflg:
                        sio.send_event_pkt(vbuf)
                    if logflg:
                        logfile.info(vbuf)

                    continue
            if wstflg:
                wbuf = evt.get_weather()
                if len(wbuf) > 0:
                    weathers = weathers + 1
                    evt.nxt_sqn()
                    dat = evt.get_dat()
                    tim = evt.get_tim()
                    bmp = evt.get_bmp()
                    htu = evt.get_htu()
                    loc = evt.get_loc()
                    sqn = evt.get_sqn()
                    console.info("")
                    console.info("Barometer.....: temperature:%s pressure:%s altitude:%s" % (bmp["temperature"], bmp["pressure"], bmp["altitude"]))
                    console.info("humidity......: temperature:%s humidity:%s altitude:%s" % (htu["temperature"], htu["humidity"], loc["altitude"]))
                    console.info("Time..........: uptime:%s time_string:%s sequence_number:%d\n" % (tim["uptime"], tim["time_string"], sqn["number"]))

                    if udpflg:
                        sio.send_event_pkt(wbuf)
                    if logflg:
                        logfile.info(wbuf)

                    continue
            if evtflg:
                ebuf = evt.get_event()
                if len(ebuf) > 1:
                    events = events + 1
                    evt.nxt_sqn()
                    dat = evt.get_dat()
                    evd = evt.get_evt()
                    tim = evt.get_tim()
                    sqn = evt.get_sqn()
                    loc = evt.get_loc()
                    console.info("")
                    console.info("Cosmic Event..: event_number:%s timer_frequency:%s ticks:%s timestamp:%s" % (
                        evd["event_number"], evd["timer_frequency"], evd["ticks"], evd["timestamp"]))
                    console.info("adc[[Ch0][Ch1]: adc:%s" % (str(evd["adc"])))
                    console.info("Location......: latitude:%s longitude:%s altitude:%s" % (
                        loc["latitude"], loc["longitude"], loc["altitude"]))
                    console.info("Time..........: uptime:%s time_string:%s sequence_number:%d\n" % (tim["uptime"], tim["time_string"], sqn["number"]))

                    if udpflg:
                        sio.send_event_pkt(ebuf)
                    if logflg:
                        logfile.info(ebuf)

                    continue
            if debug:
                console.debug(rc)
            else:
                ts = time.strftime("%d/%b/%Y %H:%M:%S", time.gmtime(time.time()))
                tim = evt.get_tim()
                sts = evt.get_sts()
                s = "cosmic_pi:uptime:%s :queue_size:%s time_string:[%s] %s    \r" % (tim["uptime"], sts["queue_size"], ts, tim["time_string"])
                sys.stdout.write(s)
                sys.stdout.flush()

    except Exception, e:
        console.info("Exception: main: %s" % (e))
        traceback.print_exc()

    finally:
        kbrd.echo_on()
        tim = evt.get_tim()
        console.info("\nUp time:%s Quitting ..." % tim["uptime"])
        usb.close()
        sio.close()
        time.sleep(1)
        sys.exit(0)

if __name__ == '__main__':
    main()
