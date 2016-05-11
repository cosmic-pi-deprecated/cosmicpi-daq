# Handle keyboard input, this tests to see if a '>' was typed
import os
import sys
import termios

import fcntl


class KeyBoard(object):
    def __init__(self):
        self.fd = sys.stdin.fileno()

    def echo_off(self):
        self.oldterm = termios.tcgetattr(self.fd)
        self.newattr = termios.tcgetattr(self.fd)
        self.newattr[3] = self.newattr[3] & ~termios.ICANON & ~termios.ECHO
        termios.tcsetattr(self.fd, termios.TCSANOW, self.newattr)
        self.oldflags = fcntl.fcntl(self.fd, fcntl.F_GETFL)
        fcntl.fcntl(self.fd, fcntl.F_SETFL, self.oldflags | os.O_NONBLOCK)

    def echo_on(self):
        termios.tcsetattr(self.fd, termios.TCSAFLUSH, self.oldterm)
        fcntl.fcntl(self.fd, fcntl.F_SETFL, self.oldflags)

    def test_input(self):
        res = False
        try:
            c = sys.stdin.read(1)
            if c == '>':
                res = True
        except IOError:
            pass
        return res
