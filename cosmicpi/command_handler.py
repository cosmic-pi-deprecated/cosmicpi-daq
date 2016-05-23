import logging
import os
import socket
import threading

log = logging.getLogger(__name__)


class CommandHandler(object):

    def __init__(self, detector, usb, options):
        self.detector = detector
        self.usb = usb
        self.options = options
        self.thread = threading.Thread(target=self.run, args=(), kwargs={})
        self.thread.daemon = True

    def start(self):
        self.thread.start()

    def run(self):
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

        try:
            os.remove("/tmp/cosmicpi.sock")
        except OSError:
            pass

        sock.bind("/tmp/cosmicpi.sock")
        sock.listen(1)
        log.info("Listening for commands on local socket")

        while True:
            conn, addr = sock.accept()

            cmd = conn.recv(1024)
            if not cmd:
                break

            log.info("Received command: %s" % cmd)

            try:
                if cmd == 'd':
                    if self.options.debug:
                        self.options.debug = False
                    else:
                        self.options.debug = True
                    response = "Debug:%s\n" % self.options.debug

                elif cmd == 'v':
                    if self.options.monitoring['vibration']:
                        self.options.monitoring['vibration'] = False
                    else:
                        self.options.monitoring['vibration'] = True
                    response = "Vibration:%s\n" % self.options.monitoring['vibration']

                elif cmd == 'w':
                    if self.options.monitoring['weather']:
                        self.options.monitoring['weather'] = False
                    else:
                        self.options.monitoring['weather'] = True
                    response = "WeatherStation:%s\n" % self.options.monitoring['weather']

                # elif cmd.find("r") != -1:
                #     if len(patok) > 0:
                #         if pushflg:
                #             pushflg = False
                #             print ("Unregister server notifications")
                #         else:
                #             pushflg = True
                #             print ("Register for server notifications")
                #
                #         if udpflg:
                #             evt.set_pat(patok, pushflg)
                #             pbuf = evt.get_notification()
                #             sio.send_event_pkt(pbuf)
                #             sbuf = evt.get_status()
                #             sio.send_event_pkt(sbuf)
                #             print ("Sent notification request:%s" % pbuf)
                #         else:
                #             print ("UDP sending is OFF, can not register with server")
                #             pbuf = ""
                #     else:
                #         print ("Token option is not set")

                elif cmd == 's':
                    tim = self.detector.sensors.timing
                    sts = self.detector.sensors.status
                    loc = self.detector.sensors.location
                    acl = self.detector.sensors.accelerometer
                    mag = self.detector.sensors.magnetometer
                    bmp = self.detector.sensors.barometer
                    htu = self.detector.sensors.temperature
                    vib = self.detector.sensors.vibration

                    response = "ARDUINO STATUS\n"
                    response += "Status........: uptime:%s counter_frequency:%s queue_size:%s missed_events:%s\n" % (
                        tim["uptime"], tim["counter_frequency"], sts["queue_size"], sts["missed_events"])
                    response += ("HardwareStatus: temp_status:%s baro_status:%s accel_status:%s mag_status:%s gps_status:%s\n" % (
                        sts["temp_status"], sts["baro_status"], sts["accel_status"], sts["mag_status"], sts["gps_status"]))
                    response += ("Location......: latitude:%s longitude:%s altitude:%s\n" % (loc["latitude"], loc["longitude"], loc["altitude"]))
                    response += ("Accelerometer.: x:%s y:%s z:%s\n" % (acl["x"], acl["y"], acl["z"]))
                    response += ("Magnetometer..: x:%s y:%s z:%s\n" % (mag["x"], mag["y"], mag["z"]))
                    response += ("Barometer.....: temperature:%s pressure:%s altitude:%s\n" % (bmp["temperature"], bmp["pressure"], bmp["altitude"]))
                    response += ("Humidity......: temperature:%s humidity:%s\n" % (htu["temperature"], htu["humidity"]))
                    response += ("Vibration.....: direction:%s count:%s\n" % (vib["direction"], vib["count"]))

                    response += ("MONITOR STATUS\n")
                    response += ("USB device....: %s\n" % (self.options.usb['device']))
                    response += ("Remote........: Ip:%s Port:%s UdpFlag:%s\n" % (self.options.broker['host'], self.options.broker['port'], self.options.broker['enabled']))
                    # print ("Notifications.: Flag:%s Token:%s" % (pushflg, patok))
                    response += ("Vibration.....: Sent:%d Flag:%s\n" % (self.detector.vbrts, self.options.monitoring['vibration']))
                    response += ("WeatherStation: Flag:%s\n" % (self.options.monitoring['weather']))
                    response += ("Events........: Sent:%d LogFlag:%s\n" % (self.detector.events, self.options.logging['enabled']))

                elif cmd == 'u':
                    if self.usb.enabled:
                        self.usb.disable()
                    else:
                        self.usb.enable()
                    response = ("USB: %s" % ('enabled' if self.usb.enabled else 'disabled'))

                elif cmd == 'n':
                    if self.options.broker['enabled']:
                        self.options.broker['enabled'] = False
                    else:
                        self.options.broker['enabled'] = True
                    response = ("Send:%s\n" % self.options.broker['enabled'])

                elif cmd == 'l':
                    if self.options.logging['enabled']:
                        self.options.logging['enabled'] = False
                    else:
                        self.options.logging['enabled'] = True
                    response = ("Log:%s\n" % self.options.logging['enabled'])

                elif cmd.startswith('arduino'):
                    response = ("%s" % cmd)
                    self.usb.write(cmd.upper())

                else:
                    response = ''

                conn.send(response)

            except Exception as e:
                msg = "Error processing client command: %s" % e
                log.warn(msg)
                conn.send(msg)

