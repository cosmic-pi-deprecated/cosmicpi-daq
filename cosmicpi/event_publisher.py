import json
import logging

import pika
from pika.exceptions import ConnectionClosed, ProbableAuthenticationError

log = logging.getLogger(__name__)


class EventPublisher(object):
    """Publish events"""

    def __init__(self, options):
        host = options.broker["host"]
        port = options.broker["port"]
        username = options.broker["username"]
        password = options.broker["password"]

        try:
            self.connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=host, port=port, credentials=pika.PlainCredentials(username, password)))
            self.channel = self.connection.channel()
            self.channel.exchange_declare(exchange='events', type='fanout')
        except (ConnectionClosed, ProbableAuthenticationError) as e:
            log.error("Fatal: Couldn't establish a connection to the broker. Please check the connection parameters.")
            log.error("Fatal: Connection parameters were: %s:%s@%s:%s" % (username, password, host, port))
            raise e

    def send_event_pkt(self, pkt):
        properties = pika.BasicProperties(content_type='application/json')
        self.channel.basic_publish(exchange='events', routing_key='', body=json.dumps(pkt), properties=properties)

    def close(self):
        self.connection.close()
