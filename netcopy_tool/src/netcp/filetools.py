#!/usr/bin/python3
# -*- coding: utf-8 -*-
import os
import logging
import logging.handlers
import argparse

from . import client
from . import server


LOG_PATH = "/var/log/vap/netcopy.log"
LOG_LEVEL = "info"


def Loginit(filepath=None, loglevel='debug'):
    levels = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL
    }
    if not isinstance(loglevel, str):
        raise TypeError("loglevel need string")

    llvl = loglevel.upper()
    if llvl not in levels:
        raise Exception("invalid log level: %s" % (loglevel))

    log_handler = logging.handlers.WatchedFileHandler(filename=filepath,
                                                      mode='a',
                                                      encoding='utf-8',
                                                      delay=False)

    fmt = logging.Formatter('%(asctime)s %(filename)s(%(funcName)s)[line:%(lineno)d][pid: %(process)d]'
                            '[tid: %(thread)d] %(levelname)s: %(message)s')
    log_handler.setFormatter(fmt)
    logger = logging.getLogger()
    logger.addHandler(log_handler)
    logger.setLevel(levels[loglevel.upper()])


def Init(is_server=False):
    global LOG_PATH
    global LOG_LEVEL

    if is_server:
        log_path = '%s-server.log' % (LOG_PATH[:-4])
    else:
        log_path = LOG_PATH

    log_dir = os.path.dirname(log_path)
    if not os.path.exists(log_dir):
        os.mkdir(log_dir)

    Loginit(log_path, LOG_LEVEL)
    logging.debug("copy file log init success!")


def ServerMain():
    global LOG_LEVEL

    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--ip', nargs='?', type=str, help="server's ip")
    parser.add_argument('-p', '--port', default=10010, type=int, help="server's port")
    parser.add_argument('-v', '--verbose', action='store_true', help='enable debug message')
    args = parser.parse_args()

    if args.verbose:
        LOG_LEVEL = 'debug'

    if args.ip is None:
        print('invalid input')
        return -1

    Init(True)
    server.Server(args.ip, args.port)


def ClientMain():
    global LOG_LEVEL
    parser = argparse.ArgumentParser()
    parser.add_argument('-o', '--operation', choices=['get', 'put'], type=str, help='run as client')
    parser.add_argument('-i', '--ip', type=str, help='server\'s ip')
    parser.add_argument('-p', '--port', default='10010', type=int, help='server\'s port')
    parser.add_argument('-l', '--localfile', type=str, help='path of local file')
    parser.add_argument('-r', '--remotefile', type=str, help='path of remote file')
    parser.add_argument('-v', '--verbose', action='store_true', help='enable debug message')
    args = parser.parse_args()

    if args.verbose:
        LOG_LEVEL = 'debug'

    if args.ip is None or args.localfile is None or args.remotefile is None or args.operation is None:
        print('invalid input')
        return -1

    Init()
    client.Client(args.ip, args.port, args.operation, args.localfile, args.remotefile)
