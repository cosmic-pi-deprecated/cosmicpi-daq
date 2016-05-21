import json
import logging
import netifaces
import threading

from event import Event

logfile = logging.getLogger('file')
log = logging.getLogger(__name__)


class Sensors(object):
    def __init__(self):
        self.temperature   = {"temperature": "0.0", "humidity": "0.0"}
        self.barometer     = {"temperature": "0.0", "pressure": "0.0", "altitude": "0.0"}
        self.vibration     = {"direction": "0", "count": "0"}
        self.magnetometer  = {"x": "0.0", "y": "0.0", "z": "0.0"}
        self.accelerometer = {"x": "0.0", "y": "0.0", "z": "0.0"}
        self.location      = {"latitude": "0.0", "longitude": "0.0", "altitude": "0.0"}
        self.timing        = {"uptime": "0", "counter_frequency": "0", "time_string": "0"}
        self.status        = {"queue_size": "0", "missed_events": "0", "buffer_error": "0", "temp_status": "0",
                              "baro_status": "0", "accel_status": "0", "mag_status": "0", "gps_status": "0"}

    def update(self, line):
        line = line.replace('\n', '')
        line = line.replace('\'', '"')

        try:
            sensor = json.loads(line)
        except:
            return  # Didn't understand, throw it away

        self.__dict__.update(sensor)
        return sensor


class Detector(object):

    def __init__(self, usb, sio, options):
        self.usb = usb
        self.sio = sio
        self.options = options

        self.sensors = Sensors()

        self.detector_id = self.get_detector_id()

        self.thread = threading.Thread(target=self.run, args=(), kwargs={})
        self.thread.daemon = True
        self.stopping = False

        self.events = 0
        self.vbrts = 0
        self.weathers = 0

        self.sequence_number = 0

    def get_next_sequence(self):
        self.sequence_number += 1
        return self.sequence_number

    def start(self):
        self.thread.start()

    def run(self):
        while not self.stopping:
            line = self.usb.readline()
            self.sio.connection.process_data_events()

            sensor = self.sensors.update(line)
            if not sensor:
                continue

            if self.options.vibflg and 'vibration' in sensor:
                evt = Event(self.detector_id, self.get_next_sequence(), self.sensors)
                self.vbrts += 1
                log.info("Vibration event: %s" % evt)
                self.handle_event(evt)
                continue

            if self.options.wstflg and 'temperature' in sensor:
                evt = Event(self.detector_id, self.get_next_sequence(), self.sensors)
                self.weathers += 1
                log.info("Weather event: %s" % evt)
                self.handle_event(evt)
                continue

            if self.options.evtflg and 'event' in sensor:
                evt = Event(self.detector_id, self.get_next_sequence(), self.sensors)
                self.events += 1
                log.info("Cosmic event: %s" % evt)
                self.handle_event(evt)
                continue

            if self.options.debug:
                log.debug(sensor)

            # else:
            #     ts = time.strftime("%d/%b/%Y %H:%M:%S", time.gmtime(time.time()))
            #     tim = evt.timing
            #     sts = evt.status
            #     s = "cosmic_pi:uptime:%s :queue_size:%s time_string:[%s] %s    \r" % (
            #     tim["uptime"], sts["queue_size"], ts, tim["time_string"])
            #     sys.stdout.write(s)
            #     sys.stdout.flush()

    def stop(self):
        log.info("Stopping detector thread")
        self.stopping = True
        self.thread.join()

    def handle_event(self, event):
        if self.options.udpflg:
            self.sio.send_event_pkt(event.to_json())
        if self.options.logflg:
            logfile.info(event.to_json())

    def get_detector_id(self):
        """Retrieve the unique identifier of this detector.

        Currently the MAC address of the first known network interface is used.
        """
        known_interfaces = ['eth0', 'wlan0', 'en1']

        for interface in known_interfaces:
            if interface in netifaces.interfaces():
                return netifaces.ifaddresses(interface)[netifaces.AF_LINK][0]['addr']

        raise Exception("No detector ID could be determined")
