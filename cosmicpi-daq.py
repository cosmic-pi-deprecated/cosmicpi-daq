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
import socket
import select
import serial
import time
import traceback
import os
import termios
import fcntl
import re
import ast
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

        self.HTU = {"Tmh": "0.0", "Hum": "0.0"}
        self.BMP = {"Tmb": "0.0", "Prs": "0.0", "Alb": "0.0"}
        self.VIB = {"Vax": "0", "Vcn": "0"}
        self.MAG = {"Mgx": "0.0", "Mgy": "0.0", "Mgz": "0.0"}
        self.MOG = {"Mox": "0.0", "Moy": "0.0", "Moz": "0.0"}
        self.ACL = {"Acx": "0.0", "Acy": "0.0", "Acz": "0.0"}
        self.AOL = {"Aox": "0.0", "Aoy": "0.0", "Aoz": "0.0"}
        self.LOC = {"Lat": "0.0", "Lon": "0.0", "Alt": "0.0"}
        self.TIM = {"Upt": "0", "Frq": "0", "Sec": "0"}
        self.STS = {"Qsz": "0", "Mis": "0", "Ter": "0", "Htu": "0", "Bmp": "0", "Acl": "0", "Mag": "0", "Gps": "0"}
        self.EVT = {"Evt": "0", "Frq": "0", "Tks": "0", "Etm": "0.0", "Adc": "[[0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0]]"}

        # Add ons

        self.DAT = {"Dat": "s"}  # Date
        self.SQN = {"Sqn": "0"}  # Sequence number
        self.PAT = {"Pat": "s", "Ntf": "0"}  # Pushover application token

        # Now build the main dictionary with one entry for each json string we will process

        self.recd = {"HTU": self.HTU, "BMP": self.BMP, "VIB": self.VIB, "MAG": self.MAG, "MOG": self.MOG,
                     "ACL": self.ACL, "AOL": self.AOL, "LOC": self.LOC, "TIM": self.TIM, "STS": self.STS,
                     "EVT": self.EVT, "DAT": self.DAT, "SQN": self.SQN, "PAT": self.PAT}

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
        try:
            dic = ast.literal_eval(nstr)  # Build a dictionary entry
            kys = dic.keys()  # Get key names, the first is the address
            if self.recd.has_key(kys[0]):  # Check we know about records with this key
                self.recd[kys[0]] = dic[kys[0]]  # and put it in the dictionary at that address

            if kys[0] == "VIB":
                self.newvib = 1

            if kys[0] == "EVT":
                self.newevt = 1

            if kys[0] == "HTU":
                self.newhtu = 1

        except Exception, e:
            # print e
            # print "BAD:%s" % line
            pass  # Didnt understand, throw it away

    def extract(self, entry):
        if self.recd.has_key(entry):
            nstr = "{\'%s\':%s}" % (entry, str(self.recd[entry]))
            return nstr
        else:
            return ""

    # build weather, cosmic ray and vibration event strings suitable to be sent over the network to server
    # these strings are self describing json format for easy decoding at the server end

    def get_weather(self):
        if self.newhtu:
            self.newhtu = 0
            try:
                hum = float(self.recd["HTU"]["Hum"])
                tmb = float(self.recd["BMP"]["Tmb"])
                prs = float(self.recd["BMP"]["Prs"])

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

                self.weather = self.extract("HTU") + \
                               "*" + self.extract("BMP") + \
                               "*" + self.extract("LOC") + \
                               "*" + self.extract("TIM") + \
                               "*" + self.extract("DAT") + \
                               "*" + self.extract("SQN")

                return self.weather

        return ""

    def get_event(self):
        if self.newevt:
            self.newevt = 0
            self.evt = self.extract("EVT") + \
                       "*" + self.extract("BMP") + \
                       "*" + self.extract("ACL") + \
                       "*" + self.extract("MAG") + \
                       "*" + self.extract("HTU") + \
                       "*" + self.extract("STS") + \
                       "*" + self.extract("LOC") + \
                       "*" + self.extract("TIM") + \
                       "*" + self.extract("DAT") + \
                       "*" + self.extract("SQN")
            return self.evt

        return ""

    def get_vibration(self):
        if self.newvib:
            self.newvib = 0
            self.vib = self.extract("VIB") + \
                       "*" + self.extract("ACL") + \
                       "*" + self.extract("MAG") + \
                       "*" + self.extract("LOC") + \
                       "*" + self.extract("TIM") + \
                       "*" + self.extract("DAT") + \
                       "*" + self.extract("SQN")
            return self.vib

        return ""

    def get_notification(self):
        if len(self.recd["PAT"]["Pat"]) > 1:
            return self.extract("PAT")
        return ""

    def get_status(self):
        return self.extract("STS")

    # Here we just return dictionaries

    def get_vib(self):
        return self.recd["VIB"]

    def get_tim(self):
        return self.recd["TIM"]

    def get_loc(self):
        return self.recd["LOC"]

    def get_sts(self):
        return self.recd["STS"]

    def get_bmp(self):
        return self.recd["BMP"]

    def get_acl(self):
        return self.recd["ACL"]

    def get_mag(self):
        return self.recd["MAG"]

    def get_htu(self):
        return self.recd["HTU"]

    def get_evt(self):
        return self.recd["EVT"]

    def get_dat(self):
        self.recd["DAT"]["Dat"] = time.asctime(time.gmtime(time.time()))
        return self.recd["DAT"]

    def get_sqn(self):
        return self.recd["SQN"]

    def nxt_sqn(self):
        self.recd["SQN"]["Sqn"] = self.sqn
        self.sqn = self.sqn + 1

    def get_pat(self):
        return self.recd["PAT"]

    def set_pat(self, token, flag):
        self.recd["PAT"]["Pat"] = token
        self.recd["PAT"]["Ntf"] = flag


# Send UDP packets to the remote server

class Socket_io(object):
    def __init__(self, ipaddr, ipport):
        try:
            self.sok = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        except Exception, e:
            msg = "Exception: Can't open Socket: %s" % (e)
            print ("Sending OFF:%s" % msg)
            udpflg = False

    def send_event_pkt(self, pkt, ipaddr, ipport):
        try:
            sent = 0
            while sent < len(pkt):
                sent = sent + self.sok.sendto(pkt[sent:], (ipaddr, ipport))

        except Exception, e:
            msg = "Exception: Can't sendto: %s" % (e)
            print ("Sending OFF:%s" % msg)
            udpflg = False

    def close(self):
        self.sok.close()


def main():
    use = "Usage: %prog [--ip=cosmicpi.ddns.net --port=4901 --usb=/dev/ttyACM0 --debug --dirnam=/tmp]"
    parser = OptionParser(usage=use, version="cosmic_pi version 1.0")

    parser.add_option("-i", "--ip", help="Server IP address or name", dest="ipaddr", default="localhost")
    parser.add_option("-p", "--port", help="Server portnumber", dest="ipport", type="int", default="4901")
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

    ipaddr = options.ipaddr
    ipport = options.ipport
    usbdev = options.usbdev
    logdir = options.logdir
    debug = options.debug
    udpflg = options.udpflg
    logflg = options.logflg
    vibflg = options.vibflg
    wstflg = options.wstflg
    evtflg = options.evtflg
    patok = options.patok

    pushflg = False

    print ("\n")
    print ("options (Server IP address)     ip   : %s" % ipaddr)
    print ("options (Server Port number)    port : %d" % ipport)
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

    kbrd = KeyBoard()
    kbrd.echo_off()

    evt = Event()
    events = 0
    vbrts = 0
    weathers = 0

    sio = Socket_io(ipaddr, ipport)

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
                            sio.send_event_pkt(pbuf, ipaddr, ipport)
                            sbuf = evt.get_status()
                            sio.send_event_pkt(sbuf, ipaddr, ipport)
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
                    print ("Status........: Upt:%s Frq:%s Qsz:%s Mis:%s" % (
                        tim["Upt"], tim["Frq"], sts["Qsz"], sts["Mis"]))
                    print ("HardwareStatus: Htu:%s Bmp:%s Acl:%s Mag:%s Gps:%s" % (
                        sts["Htu"], sts["Bmp"], sts["Acl"], sts["Mag"], sts["Gps"]))
                    print ("Location......: Lat:%s Lon:%s Alt:%s" % (loc["Lat"], loc["Lon"], loc["Alt"]))
                    print ("Accelarometer.: Acx:%s Acy:%s Acz:%s" % (acl["Acx"], acl["Acy"], acl["Acz"]))
                    print ("Magnatometer..: Mgx:%s Mgy:%s Mgz:%s" % (mag["Mgx"], mag["Mgy"], mag["Mgz"]))
                    print ("Barometer.....: Tmb:%s Prs:%s Alb:%s" % (bmp["Tmb"], bmp["Prs"], bmp["Alb"]))
                    print ("Humidity......: Tmh:%s Hum:%s" % (htu["Tmh"], htu["Hum"]))
                    print ("Vibration.....: Vax:%s Vcn:%s\n" % (vib["Vax"], vib["Vcn"]))

                    print ("MONITOR STATUS")
                    print ("USB device....: %s" % (usbdev))
                    print ("Remote........: Ip:%s Port:%s UdpFlag:%s" % (ipaddr, ipport, udpflg))
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
                    print ("   MAGD, Magomagnatometer display rate, <rate>")
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
                        print ("Vibration.....: Cnt:%d Vax:%s Vcn:%s " % (vbrts, vib["Vax"], vib["Vcn"]))
                        print ("Accelarometer.: Acx:%s Acy:%s Acz:%s" % (acl["Acx"], acl["Acy"], acl["Acz"]))
                        print ("Magnatometer..: Mgx:%s Mgy:%s Mgz:%s" % (mag["Mgx"], mag["Mgy"], mag["Mgz"]))
                        print ("Time..........: Upt:%s Sec:%s Sqn:%d\n" % (tim["Upt"], tim["Sec"], sqn["Sqn"]))

                        if udpflg:
                            sio.send_event_pkt(vbuf, ipaddr, ipport)
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
                        print ("Barometer.....: Tmb:%s Prs:%s Alb:%s" % (bmp["Tmb"], bmp["Prs"], bmp["Alb"]))
                        print ("Humidity......: Tmh:%s Hum:%s Alt:%s" % (htu["Tmh"], htu["Hum"], loc["Alt"]))
                        print ("Time..........: Upt:%s Sec:%s Sqn:%d\n" % (tim["Upt"], tim["Sec"], sqn["Sqn"]))

                        if udpflg:
                            sio.send_event_pkt(wbuf, ipaddr, ipport)
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
                        print ("Cosmic Event..: Evt:%s Frq:%s Tks:%s Etm:%s" % (
                            evd["Evt"], evd["Frq"], evd["Tks"], evd["Etm"]))
                        print ("Adc[[Ch0][Ch1]: Adc:%s" % (str(evd["Adc"])))
                        print ("Time..........: Upt:%s Sec:%s Sqn:%d\n" % (tim["Upt"], tim["Sec"], sqn["Sqn"]))

                        if udpflg:
                            sio.send_event_pkt(ebuf, ipaddr, ipport)
                        if logflg:
                            log.write(ebuf)

                        continue
                if debug:
                    sys.stdout.write(rc)
                else:
                    ts = time.strftime("%d/%b/%Y %H:%M:%S", time.gmtime(time.time()))
                    tim = evt.get_tim();
                    sts = evt.get_sts();
                    s = "cosmic_pi:Upt:%s :Qsz:%s Tim:[%s] %s    \r" % (tim["Upt"], sts["Qsz"], ts, tim["Sec"])
                    sys.stdout.write(s)
                    sys.stdout.flush()

    except Exception, e:
        msg = "Exception: main: %s" % (e)
        print ("Fatal: %s" % msg)
        traceback.print_exc()


    finally:
        kbrd.echo_on()
        tim = evt.get_tim()
        print ("\nUp time:%s Quitting ..." % tim["Upt"])
        ser.close()
        log.close()
        sio.close()
        time.sleep(1)
        sys.exit(0)

if __name__ == '__main__':
    main()
