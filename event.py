import json

import time


class Event(object):

    def __init__(self, detector_id, sequence_number, sensors):
        self.detector_id = detector_id
        self.sequence = {"number": sequence_number}
        self.date = {"date": time.asctime(time.gmtime(time.time()))}
        self.__dict__.update(sensors.__dict__)

    def __str__(self):
        return """

        Detector......: %s
        Sequence......: %s
        Barometer.....: %s
        Thermometer...: %s
        Location......: %s
        Vibration.....: %s
        Accelerometer.: %s
        Magnetometer..: %s
        Timing........: %s
        Status........: %s
        Event.........: %s
        """ % (self.detector_id, self.sequence, self.barometer, self.temperature, self.location,
               self.vibration, self.accelerometer, self.magnetometer, self.timing, self.status,
               self.event if 'event' in self.__dict__ else None)

    def to_json(self, pretty=False):
        if pretty:
            return json.dumps(self.__dict__, sort_keys=True, indent=4, separators=(',', ': '))
        else:
            return json.dumps(self.__dict__)
