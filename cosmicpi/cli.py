#!/usr/bin/env python

import argparse
import socket
import sys


def main():
    parser = argparse.ArgumentParser(description='Interact with a running CosmicPi detector.')
    subparsers = parser.add_subparsers(dest='command', help='available commands')

    subparsers.add_parser('s', help='show the status of the detector')
    subparsers.add_parser('d', help='toggle debug output')
    subparsers.add_parser('l', help='toggle event logging')
    subparsers.add_parser('n', help='toggle cosmic event sending')
    subparsers.add_parser('w', help='toggle weather event sending')
    subparsers.add_parser('v', help='toggle vibration event sending')

    arduino_parser = subparsers.add_parser('arduino', help='send commands to the arduino board')
    arduino_subparsers = arduino_parser.add_subparsers(dest='arduino_command', help='available arduino commands')

    arduino_subparsers.add_parser('HTUX', help='reset the HTH chip')
    arduino_subparsers.add_parser('HTUD', help='HTU Temperature-Humidity display rate') \
        .add_argument('value', type=int, help='display rate value to set')
    arduino_subparsers.add_parser('BMPD', help='BMP Temperature-Altitude display rate') \
        .add_argument('value', type=int, help='display rate value to set')
    arduino_subparsers.add_parser('LOCD', help='Location latitude-longitude display rate') \
        .add_argument('value', type=int, help='display rate value to set')
    arduino_subparsers.add_parser('TIMD', help='Timing uptime-frequency-etm display rate') \
        .add_argument('value', type=int, help='display rate value to set')
    arduino_subparsers.add_parser('STSD', help='Status info display rate') \
        .add_argument('value', type=int, help='display rate value to set')
    arduino_subparsers.add_parser('EVQT', help='Event queue dump threshold') \
        .add_argument('value', type=int, help='threshold value to set (1..32)')
    arduino_subparsers.add_parser('ACLD', help='Accelerometer display rate') \
        .add_argument('value', type=int, help='display rate value to set')
    arduino_subparsers.add_parser('MAGD', help='Magnetometer display rate') \
        .add_argument('value', type=int, help='display rate value to set')
    arduino_subparsers.add_parser('ACLT', help='Accelerometer event trigger threshold') \
        .add_argument('value', type=int, help='threshold value to set (0..127')

    args = parser.parse_args()

    command = args.command

    if 'arduino_command' in args:
        command += ' ' + args.arduino_command
        command += ' ' + str(args.value) if hasattr(args, 'value') else ''

    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

    try:
        s.connect("/tmp/cosmicpi.sock")
    except:
        print ("Fatal: Couldn't connect, is the process running?")
        sys.exit(1)

    s.send(command)
    response = s.recv(1024)

    s.close()
    print(str(response))

if __name__ == '__main__':
    main()
