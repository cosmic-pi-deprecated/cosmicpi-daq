import json

import pika


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