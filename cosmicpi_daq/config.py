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

import argparse
import logging
import os

import yaml

log = logging.getLogger(__name__)


def get_default_config():
    """The default, built-in configuration.

    This can be overridden by using the --config option with a YAML
    configuration file. The config file options can then be further
    overridden using CLI args.
    """
    return dict(
        broker=dict(
            host="localhost",
            port=5162,
            username="guest",
            password="guest",
            enabled=True
        ),
        monitoring=dict(
            cosmics=True,
            weather=True,
            vibration=True
        ),
        logging=dict(
            config=os.path.dirname(
                os.path.realpath(__file__)) + "/logging.conf",
            enabled=True
        ),
        usb=dict(
            device='/dev/ttyACM0'
        ),
        commands=dict(
            socket="/var/run/cosmicpi.sock"
        ),
        debug=False
    )


def load_config(path):
    """Return a configuration dictionary containing the result of the merge of
     the default, built-in configuration and a YAML configuration file.

    If no file exists with the given path or the file is badly formatted, the
    default configuration will be returned.
    """
    config = get_default_config()

    if not os.path.exists(path):
        print ("WARN: no config file could be found at %s" % path)
    else:
        try:
            with open(path, "r") as f:
                config_file = yaml.safe_load(f)
                config = merge_config(
                    config, config_file if config_file else {})
        except Exception as e:
            print ("WARN: invalid configuration file at %s: %s" % (path, e))

    return config


def merge_config(default, override, prefix=None):
    """Return the result of the merge of a default and override dictionary"""
    result = dict()
    for k, v in default.items():
        result[k] = v

        prefixed_key = "%s.%s" % (prefix, k) if prefix else k
        if isinstance(v, dict):
            result[k] = merge_config(
                v, override[k] if k in override else dict(), prefixed_key)
        else:
            if k in override:
                result[k] = override[k]

    return result


def arg(dest, help, type=None):
    """Utility function to shorten the argument definitions and deal with
    nested config destinations.
    """
    action = dict(
        dest=dest,
        help=help,
        action=CustomAction,
        default=argparse.SUPPRESS)
    if 'Disable' in help or 'Enable' in help:
        action.update(const=False if 'Disable' in help else True, nargs=0)
    else:
        action.update(type=type, metavar=dest.split('.')[-1])
    return action


def print_config(config):
    """Pretty print the given configuration"""
    log.debug('options: \n' + yaml.dump(
        config.__dict__, explicit_start=True, explicit_end=True,
        default_flow_style=False
    ))


class CustomAction(argparse.Action):
    """Custom argparse action that allows to specify nested destinations using
    dot notation on the "dest" parameter.

    e.g.: parser.add_argument(..., dest="logging.config", action=GroupedAction)
    """

    def __call__(self, parser, namespace, values, option_string=None):
        if self.const is not None:
            self.set_value(namespace, self.const)
        else:
            self.set_value(namespace, values)

    def set_value(self, namespace, value):
        if '.' in self.dest:
            group, dest = self.dest.split('.', 2)
            groupspace = getattr(namespace, group, argparse.Namespace())
            groupspace[dest] = value
            setattr(namespace, group, groupspace)
        else:
            setattr(namespace, self.dest, value)
