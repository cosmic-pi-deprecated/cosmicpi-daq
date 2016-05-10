#!	/usr/bin/python
#	coding: utf8

from __future__ import print_function

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
import fcntl
import pika
import json
from optparse import OptionParser


# Handle keyboard input, this tests to see if a '>' was typed

class KeyBoard(object):
    def __init__(self):
        self.fd = sys.stdin.fileno()

    def echo_off(self):
        self.oldterm = termios.tcgetattr(self.fd)
        self.newattr = termios.tcgetattr(self.fd)
        self.newattr[3] = self.newattr[3] & ~termios.ICANON & ~termios.ECHO
        termios.tcsetattr(self.fd, termios.TCSANOW, self.newattr)
        self.oldflags = fcntl.fcntl(self.fd, fcntl.F_GETFL)
        fcntl.fcntl(self.fd, fcntl.F_SETFL, self.oldflags | os.O_NONBLOCK)

    def echo_on(self):
        termios.tcsetattr(self.fd, termios.TCSAFLUSH, self.oldterm)
        fcntl.fcntl(self.fd, fcntl.F_SETFL, self.oldflags)

    def test_input(self):
        res = False
        try:
            c = sys.stdin.read(1)
            if c == '>':
                res = True
        except IOError:
            pass
        return res


# This is the event object, it builds a dictionary from incomming jsom strings
# and provides access to the dictionary entries containing the data for each field.

class Event(object):
    def __init__(self):

        # These are the json strings we are expecting from the arduino

        self.temperature = {"temperature": "0.0", "humidity": "0.0"}
        self.barometer = {"temperature": "0.0", "pressure": "0.0", "altitude": "0.0"}
        self.vibration = {"direction": "0", "count": "0"}
        self.magnetometer = {"x": "0.0", "y": "0.0", "z": "0.0"}
        self.MOG = {"Mox": "0.0", "Moy": "0.0", "Moz": "0.0"}
        self.accelerometer = {"x": "0.0", "y": "0.0", "z": "0.0"}
        self.AOL = {"Aox": "0.0", "Aoy": "0.0", "Aoz": "0.0"}
        self.location = {"latitude": "0.0", "longitude": "0.0", "altitude": "0.0"}
        self.timing = {"uptime": "0", "counter_frequency": "0", "time_string": "0"}
        self.status = {"queue_size": "0", "missed_events": "0", "buffer_error": "0", "temp_status": "0",
                       "baro_status": "0", "accel_status": "0", "mag_status": "0", "gps_status": "0"}
        self.event = {"event_number": "0", "counter_frequency": "0", "ticks": "0", "timestamp": "0.0", 
                      "adc": "[[0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0]]"}

        # Add ons

        self.date = {"date": "s"}  # Date
        self.sequence = {"number": "0"}  # Sequence number
        self.PAT = {"Pat": "s", "Ntf": "0"}  # Pushover application token

        # Now build the main dictionary with one entry for each json string we will process

        self.recd = {"temperature": self.temperature, "barometer": self.barometer, "vibration": self.vibration, 
                     "magnetometer": self.magnetometer, "MOG": self.MOG, "accelerometer": self.accelerometer, 
                     "AOL": self.AOL, "location": self.location, "timing": self.timing, "status": self.status,
                     "event": self.event, "date": self.date, "sequence": self.sequence, "PAT": self.PAT}

        self.newvib = 0  # Vibration
        self.newevt = 0  # Cosmic ray
        self.newhtu = 0  # Weather report

        self.sqn = 0  # Packet sequenc number

        self.ohum = 0.0  # Old humidity value
        self.otmb = 0.0  # Old barometric temperature value
        self.oprs = 0.0  # Old barometric presure value

    # Convert the incomming json strings into entries in the dictionary

    def parse(self, line):  # parse the incomming json strings from arduino
        nstr = line.replace('\n', '')  # Throw away <crtn>, we dont want them
        nstr = line.replace('\'', '"')
        try:
            dic = json.loads(nstr)  # Build a dictionary entry
            kys = dic.keys()  # Get key names, the first is the address
            if self.recd.has_key(kys[0]):  # Check we know about records with this key
                self.recd[kys[0]] = dic[kys[0]]  # and put it in the dictionary at that address

            if kys[0] == "vibration":
                self.newvib = 1

            if kys[0] == "event":
                self.newevt = 1

            if kys[0] == "temperature":
                self.newhtu = 1

        except Exception, e:
            # print e
            # print "BAD:%s" % line
            pass  # Didnt understand, throw it away

    # build weather, cosmic ray and vibration event strings suitable to be sent over the network to server
    # these strings are self describing json format for easy decoding at the server end

    def get_weather(self):
        if self.newhtu:
            self.newhtu = 0
            try:
                hum = float(self.recd["temperature"]["humidity"])
                tmb = float(self.recd["barometer"]["temperature"])
                prs = float(self.recd["barometer"]["pressure"])

            except Exception, e:
                hum = 0.0
                tmb = 0.0
                prs = 0.0
                pass

            tol = abs(hum - self.ohum) + abs(tmb - self.otmb) + abs(prs - self.oprs)
            if tol > 1.0:
                self.ohum = hum
                self.otmb = tmb
                self.oprs = prs

                self.weather = json.dumps({
                    'temperature': self.recd['temperature'],
                    'barometer': self.recd['barometer'],
                    'location': self.recd['location'],
                    'timing': self.recd['timing'],
                    'date': self.recd['date'],
                    'sequence': self.recd['sequence'],
                })

                return self.weather

        return ""

    def get_event(self):
        if self.newevt:
            self.newevt = 0
            self.evt = json.dumps(self.recd)
            return self.evt

        return ""

    def get_vibration(self):
        if self.newvib:
            self.newvib = 0
            self.vib = json.dumps({
                'accelerometer': self.recd['accelerometer'],
                'magnetometer': self.recd['magnetometer'],
                'location': self.recd['location'],
                'timing': self.recd['timing'],
                'date': self.recd['date'],
                'sequence': self.recd['sequence'],
            })
            return self.vib

        return ""

    def get_notification(self):
        if len(self.recd["PAT"]["Pat"]) > 1:
            return json.dumps(self.recd["PAT"])
        return ""

    def get_status(self):
        return json.dumps(self.recd["status"])

    # Here we just return dictionaries

    def get_vib(self):
        return self.recd["vibration"]

    def get_tim(self):
        return self.recd["timing"]

    def get_loc(self):
        return self.recd["location"]

    def get_sts(self):
        return self.recd["status"]

    def get_bmp(self):
        return self.recd["barometer"]

    def get_acl(self):
        return self.recd["accelerometer"]

    def get_mag(self):
        return self.recd["magnetometer"]

    def get_htu(self):
        return self.recd["temperature"]

    def get_evt(self):
        return self.recd["event"]

    def get_dat(self):
        self.recd["date"]["date"] = time.asctime(time.gmtime(time.time()))
        return self.recd["date"]

    def get_sqn(self):
        return self.recd["sequence"]

    def nxt_sqn(self):
        self.recd["sequence"]["number"] = self.sqn
        self.sqn = self.sqn + 1

    def get_pat(self):
        return self.recd["PAT"]

    def set_pat(self, token, flag):
        self.recd["PAT"]["Pat"] = token
        self.recd["PAT"]["Ntf"] = flag


class Socket_io(object):
    """Publish events"""
    def __init__(self, host, port, username, password):
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=host, port=port,
                                                  credentials=pika.PlainCredentials(username, password)))
        self.channel = self.connection.channel()
        self.channel.exchange_declare(exchange='events', type='fanout')

    def send_event_pkt(self, pkt):
        self.channel.basic_publish(exchange='events', routing_key='', body=json.dumps(pkt))

    def close(self):
        self.connection.close()


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

    credentials = options.credentials.split(':')
    username = credentials[0]
    password = credentials[1]

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
        ser = serial.Serial(port=usbdev, baudrate=9600, timeout=60)
        ser.flush()
    except Exception, e:
        msg = "Exception: Cant open USB device: %s" % (e)
        print ("Fatal: %s" % msg)
        sys.exit(1)

    evt = Event()
    events = 0
    vbrts = 0
    weathers = 0

    sio = Socket_io(host, port, username, password)

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
                        ser.write("HELP")

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
                    ser.write(cmd.upper())

                kbrd.echo_off()

            # Process Arduino data json strings

            rc = ser.readline()


            if len(rc) == 0:
                print ("Serial input buffer empty")
                ser.close()
                time.sleep(1)
                ser = serial.Serial(port=usbdev, baudrate=9600, timeout=60)
                rc = ser.readline()
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
                            log.write(vbuf)

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
                            log.write(wbuf)

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
                        print ("")
                        print ("Cosmic Event..: event_number:%s counter_frequency:%s ticks:%s timestamp:%s" % (
                            evd["event_number"], evd["counter_frequency"], evd["ticks"], evd["timestamp"]))
                        print ("adc[[Ch0][Ch1]: adc:%s" % (str(evd["adc"])))
                        print ("Time..........: uptime:%s time_string:%s sequence_number:%d\n" % (tim["uptime"], tim["time_string"], sqn["number"]))

                        if udpflg:
                            sio.send_event_pkt(ebuf)
                        if logflg:
                            log.write(ebuf)

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
        ser.close()
        log.close()
        sio.close()
        time.sleep(1)
        sys.exit(0)

if __name__ == '__main__':
    main()
