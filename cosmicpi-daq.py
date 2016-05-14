#!	/usr/bin/python
#	coding: utf8

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
import os
import termios
from optparse import OptionParser

from event import Event
from sock import Socket_io
from keyboard import KeyBoard

class usb_io(object):

    def __init__(self,usbdev,baudrate,timeout):
	self.usbdev   = usbdev
	self.baudrate = baudrate
	self.timeout  = timeout

    def open(self):
        self.usb = serial.Serial(port=self.usbdev, baudrate=self.baudrate, timeout=self.timeout)
        self.attr = termios.tcgetattr(self.usb)
        self.attr[2] = self.attr[2] & ~termios.HUPCL            # Clear HUPCL in control reg (2)
        termios.tcsetattr(self.usb, termios.TCSANOW, self.attr) # and write

    def close(self):
        self.usb.close()

    def readline(self):
        return self.usb.readline()

    def write(self,arg):
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
        print("Fatal: Couln't parse the connection credentials. Format is username:password")
        sys.exit(1)

    try:
        sio = Socket_io(host, port, username, password)
    except ConnectionClosed:
        print ("Fatal: Couln't establish a connection to the broker. Please check the connection parameters.")
        print ("Fatal: Connection parameters were: %s:%s@%s:%s" % (username, password, host, port))
        sys.exit(1)
    except ProbableAuthenticationError:
        print ("Fatal: Couln't establish a connection to the broker. Probably incorrect connection credentials.")
        sys.exit(1)


    pushflg = False

    print ("\n")
    print ("options (Server IP address)     ip   : %s" % host)
    print ("options (Server Port number)    port : %d" % port)
    print ("options (USB device name)       usb  : %s" % usbdev)
    print ("options (Logging directory)     odir : %s" % logdir)
    print ("options (Event logging)         log  : %s" % logflg)
    print ("options (UDP sending)           udp  : %s" % udpflg)
    print ("options (Vibration monitor)     vib  : %s" % vibflg)
    print ("options (Weather Station)       wst  : %s" % wstflg)
    print ("options (Cosmic Ray Station)    cray : %s" % evtflg)
    print ("options (Push notifications)    patk : %s" % patok)
    print ("options (Debug Flag)            debug: %s" % debug)

    print ("\ncosmic_pi monitor running, hit '>' for commands\n")

    ts = time.strftime("%d-%b-%Y-%H-%M-%S", time.gmtime(time.time()))
    lgf = "%s/cosmicpi-logs/%s.log" % (logdir, ts)
    dir = os.path.dirname(lgf)
    if not os.path.exists(dir):
        os.makedirs(dir)
    try:
        log = open(lgf, "w");
    except Exception, e:
        msg = "Exception: Cant open log file: %s" % (e)
        print ("Fatal: %s" % msg)
        sys.exit(1)

    if options.debug:
        print ("\n")
        print ("Log file is: %s" % lgf)

    try:
        usb = usb_io(usbdev,9600,60)
        usb.open()

    except Exception, e:
        msg = "Exception: Cant open USB device: %s" % (e)
        print ("Fatal: %s" % msg)
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
                    print ("LogFile.......: %s\n" % (lgf))

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

            if len(rc) == 0:
                print ("Serial input buffer empty")
                usb.close()
                time.sleep(1)
                usb.open()
                rc = usb.readline()
                if len(rc) == 0:
                    break
                print ("Serial Reopened OK")
                continue
            else:
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
                        print ("")
                        print ("Vibration.....: count:%d direction:%s count:%s " % (vbrts, vib["direction"], vib["count"]))
                        print ("Accelerometer.: x:%s y:%s z:%s" % (acl["x"], acl["y"], acl["z"]))
                        print ("Magnetometer..: x:%s y:%s z:%s" % (mag["x"], mag["y"], mag["z"]))
                        print ("Time..........: uptime:%s time_string:%s sequence_number:%d\n" % (tim["uptime"], tim["time_string"], sqn["number"]))

                        if udpflg:
                            sio.send_event_pkt(vbuf)
                        if logflg:
                            log.write(vbuf + '\n')

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
                        print ("")
                        print ("Barometer.....: temperature:%s pressure:%s altitude:%s" % (bmp["temperature"], bmp["pressure"], bmp["altitude"]))
                        print ("humidity......: temperature:%s humidity:%s altitude:%s" % (htu["temperature"], htu["humidity"], loc["altitude"]))
                        print ("Time..........: uptime:%s time_string:%s sequence_number:%d\n" % (tim["uptime"], tim["time_string"], sqn["number"]))

                        if udpflg:
                            sio.send_event_pkt(wbuf)
                        if logflg:
                            log.write(wbuf + '\n')

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
                        print ("")
                        print ("Cosmic Event..: event_number:%s timer_frequency:%s ticks:%s timestamp:%s" % (
                            evd["event_number"], evd["timer_frequency"], evd["ticks"], evd["timestamp"]))
                        print ("adc[[Ch0][Ch1]: adc:%s" % (str(evd["adc"])))
                        print ("Location......: latitude:%s longitude:%s altitude:%s" % (
                            loc["latitude"], loc["longitude"], loc["altitude"]))
                        print ("Time..........: uptime:%s time_string:%s sequence_number:%d\n" % (tim["uptime"], tim["time_string"], sqn["number"]))

                        if udpflg:
                            sio.send_event_pkt(ebuf)
                        if logflg:
                            log.write(ebuf + '\n')

                        continue
                if debug:
                    sys.stdout.write(rc)
                else:
                    ts = time.strftime("%d/%b/%Y %H:%M:%S", time.gmtime(time.time()))
                    tim = evt.get_tim()
                    sts = evt.get_sts()
                    s = "cosmic_pi:uptime:%s :queue_size:%s time_string:[%s] %s    \r" % (tim["uptime"], sts["queue_size"], ts, tim["time_string"])
                    sys.stdout.write(s)
                    sys.stdout.flush()

    except Exception, e:
        msg = "Exception: main: %s" % (e)
        print ("Fatal: %s" % msg)
        traceback.print_exc()


    finally:
        kbrd.echo_on()
        tim = evt.get_tim()
        print ("\nUp time:%s Quitting ..." % tim["uptime"])
        usb.close()
        log.close()
        sio.close()
        time.sleep(1)
        sys.exit(0)

if __name__ == '__main__':
    main()
