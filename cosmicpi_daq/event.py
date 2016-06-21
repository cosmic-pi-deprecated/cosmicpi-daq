# -*- coding: utf-8 -*-
#
# This file is part of CosmicPi-DAQ.
# Copyright (C) 2016 Justin Lewis Salmon.
#
# CosmicPi-DAQ is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# CosmicPi-DAQ is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with CosmicPi-DAQ; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.

"""Data acquisition package for reading data from CosmicPi."""

import json
import time


class Event(object):
    """Wrapper around a cosmic event."""

    def __init__(self, detector_id, sequence_number, sensors):
        """Combine sensor data with information about a detector."""
        self.detector_id = detector_id
        self.sequence = {"number": sequence_number}
        self.date = {"date": time.asctime(time.gmtime(time.time()))}
        self.event = None
        self.__dict__.update(sensors.__dict__)

    def __str__(self):
        """Return a string representation."""
        return """

        Detector......: {0.detector_id}
        Sequence......: {0.sequence}
        Barometer.....: {0.barometer}
        Thermometer...: {0.temperature}
        Location......: {0.location}
        Vibration.....: {0.vibration}
        Accelerometer.: {0.accelerometer}
        Magnetometer..: {0.megnetometer}
        Timing........: {0.timing}
        Status........: {0.status}
        Event.........: {0.event}
        """.format(self)

    def to_json(self, pretty=False):
        """Convert event to a JSON representation."""
        if pretty:
            return json.dumps(self.__dict__, sort_keys=True,
                              indent=4, separators=(',', ': '))
        else:
            return json.dumps(self.__dict__)
