#!/usr/bin/env python

from __future__ import print_function

import sys
import logging
import socket
from argparse import ArgumentParser
from ja2mqtt import Jablotron2mqtt



if __name__ == "__main__":

    parser = ArgumentParser(description=\
        "Runs mqtt bridge for jablotron alarms")
    parser.add_argument('--serial-port', '-p', required=True,
        help="Serial port where the JA-80T is connected.")
    parser.add_argument('--host', '-H', default="localhost",
        help="Mqtt host to connect to (default: localhost)")
    parser.add_argument('--mqtt-port', '-P', default="1883",
        help="Mqtt port to connect to (default: 1883)")
    parser.add_argument('--topic', '-t', default="alarm",
        help="Mqtt topic where to publish messages (default: alarm)")
    parser.add_argument('--username', '-u',
        help="Mqtt username")
    parser.add_argument('--password', '-ps',
        help="Mqtt password")
    parser.add_argument('-v', dest='loglevel', action='store_const',
        const=logging.INFO, help="verbose output.")
    parser.add_argument('-d', dest='loglevel', action='store_const',
        const=logging.DEBUG, help="debug output.")
    parser.add_argument('-q', dest='loglevel', action='store_const',
        const=logging.ERROR, help="quiet mode.")

    args = parser.parse_args()

    logging.basicConfig(level=args.loglevel)

    try:
        with Jablotron2mqtt(jablotron_port=args.serial_port,
                            mqtt_host=args.host,
                            mqtt_port=args.mqtt_port,
                            mqtt_topic=args.topic,
                            mqtt_username=args.username,
                            mqtt_password=args.password) as j2m:
            j2m.loop_forever()
    except socket.error as e:
        print("Failed to connect to mqtt host: " +args.host + " - " + str(e), file=sys.stderr)
