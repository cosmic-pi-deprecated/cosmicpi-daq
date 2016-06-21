#! /usr/bin/python
#  coding: utf8

from __future__ import print_function

import argparse
import logging.config
import sys
import time
import traceback
from config import arg, load_config, print_config

from command_handler import CommandHandler
from detector import Detector
from event_publisher import EventPublisher
from usb_handler import UsbHandler


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

It is important to keep the Python dictionary objects synchronised with the Arduino firmware
otherwise this monitor will not understand the data being sent to it

julian.lewis lewis.julian@gmail.com 7/Apr/2016

"""


def main():
    main_parser = argparse.ArgumentParser(
        prog="cosmicpi",
        description="CosmicPi acquisition process",
        add_help=False)
    main_parser.add_argument(
        "--config",
        help="Path to configuration file",
        default="/etc/cosmicpi.yaml")
    args, remaining_argv = main_parser.parse_known_args()

    # Merge the default config with the configuration file
    config = load_config(args.config)

    # Parse the command line for overrides
    parser = argparse.ArgumentParser(parents=[main_parser])
    parser.set_defaults(**config)

    parser.add_argument(
        "-i", "--host", **arg("broker.host", "Message broker host"))
    parser.add_argument("-p", "--port", **arg("broker.port",
                                              "Message broker port", type=int))
    parser.add_argument("-a", "--username", **
                        arg("broker.username", "Message broker username"))
    parser.add_argument("-b", "--password", **
                        arg("broker.password", "Message broker password"))
    parser.add_argument("-n", "--no-publish", **
                        arg("broker.enabled", "Disable event publication"))
    parser.add_argument("-u", "--usb", **arg("usb.device", "USB device name"))
    parser.add_argument("-d", "--debug", **arg("debug", "Enable debug mode"))
    parser.add_argument("-o", "--log-config", **
                        arg("logging.config", "Path to logging configuration"))
    parser.add_argument("-l", "--no-log", **
                        arg("logging.enabled", "Disable file logging"))
    parser.add_argument("-v",
                        "--no-vib",
                        **arg("monitoring.vibration",
                              "Disable vibration monitoring"))
    parser.add_argument("-w",
                        "--no-weather",
                        **arg("monitoring.weather",
                              "Disable weather monitoring"))
    parser.add_argument("-c",
                        "--no-cosmics",
                        **arg("monitoring.cosmics",
                              "Disable cosmic ray monitoring"))
    parser.add_argument("-k", "--patk", **arg("patok",
                                              "Server push notification token"))

    options = parser.parse_args()

    log_config = options.logging["config"]
    print ("INFO: using logging configuration from %s" % log_config)
    logging.config.fileConfig(log_config, disable_existing_loggers=False)
    console = logging.getLogger(__name__)

    if options.debug:
        print_config(options)

    try:
        publisher = EventPublisher(options)
    except:
        console.error("Exception: Can't connect to broker")
        sys.exit(1)

    try:
        usb = UsbHandler(options.usb['device'], 9600, 60)
        usb.open()
    except Exception as e:
        console.error("Exception: Can't open USB device: %s" % e)
        sys.exit(1)

    detector = Detector(usb, publisher, options)

    try:
        detector.start()
        command_handler = CommandHandler(detector, usb, options)
        command_handler.start()

        while True:
            time.sleep(1)

    except Exception as e:
        console.info("Exception: main: %s" % e)
        traceback.print_exc()

    finally:
        detector.stop()
        console.info("Quitting ...")
        time.sleep(1)
        usb.close()
        publisher.close()
        sys.exit(0)

if __name__ == '__main__':
    main()
