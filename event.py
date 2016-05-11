# This is the event object, it builds a dictionary from incomming jsom strings
# and provides access to the dictionary entries containing the data for each field.
import json

import time


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