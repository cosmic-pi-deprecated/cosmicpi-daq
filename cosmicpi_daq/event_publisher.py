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

"""Publish event via AMQP."""

import json
import logging

import pika
from pika.exceptions import ConnectionClosed, ProbableAuthenticationError

log = logging.getLogger(__name__)


class EventPublisher(object):
    """Publish events."""

    def __init__(self, options):
        """Create new connection and channel."""
        host = options.broker["host"]
        port = options.broker["port"]
        username = options.broker["username"]
        password = options.broker["password"]

        try:
            self.connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=host,
                    port=port,
                    credentials=pika.PlainCredentials(username, password)
                )
            )
            self.channel = self.connection.channel()
            self.channel.exchange_declare(exchange='events', type='fanout')
        except (ConnectionClosed, ProbableAuthenticationError) as e:
            log.error(
                "Fatal: Couldn't establish a connection to the broker. "
                "Please check the connection parameters."
            )
            log.error(
                "Fatal: Connection parameters were: {0}:{1}@{2}:{3}".format(
                    username, password, host, port
                )
            )
            raise e

    def send_event_pkt(self, pkt):
        """Publish an event."""
        properties = pika.BasicProperties(content_type='application/json')
        self.channel.basic_publish(
            exchange='events',
            routing_key='',
            body=json.dumps(pkt),
            properties=properties,
        )

    def close(self):
        """Close AMQP connection."""
        self.connection.close()
