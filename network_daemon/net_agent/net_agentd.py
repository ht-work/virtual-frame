#!/usr/bin/env python
# -*- coding: utf-8 -*-

from concurrent import futures
import time
import logging
import grpc
import traceback

from util_base import log
from util_base.sys_util import BaseConfig
from net_agent import net_agent_api

_ONE_DAY_IN_SECONDS = 60 * 60 * 24

# general
CONFIG_FILE = '/etc/vap/net_agent.cfg'
NET_AGENT_CONF = None


class NetAgentConfig(BaseConfig):
    pass


def LoadConfig():
    global NET_AGENT_CONF

    NET_AGENT_CONF = NetAgentConfig(CONFIG_FILE)


def LogInit():
    global NET_AGENT_CONF

    log.Loginit(NET_AGENT_CONF.GetLogPath(), NET_AGENT_CONF.GetLogLevel())


def main():
    global NET_AGENT_CONF

    try:
        LoadConfig()
        LogInit()
        logging.info('start')
        logging.info('listening on %d' % NET_AGENT_CONF.GetServicePort())

        server = grpc.server(futures.ThreadPoolExecutor(max_workers=NET_AGENT_CONF.GetGrpcWorkerSize()))

        net_agent_api.add_to_server(server)

        server.add_insecure_port('0.0.0.0:%d' % (NET_AGENT_CONF.GetServicePort()))
        server.start()

        try:
            while True:
                time.sleep(_ONE_DAY_IN_SECONDS)
        except KeyboardInterrupt:
            server.stop(0)

    except Exception:
        logging.critical(traceback.format_exc())


if __name__ == '__main__':
    main()
