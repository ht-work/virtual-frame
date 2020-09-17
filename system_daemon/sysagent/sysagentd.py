#!/usr/bin/python3
# -*- coding: utf-8 -*-
import os
import sys
import time
import logging
import daemon
from concurrent import futures

import grpc

from util_base.sys_util import GlobalConfig

from sysagent.util import ExternalSysUtil as ExUtil
from sysagent.util import ExternalConfig as ExCfg

import sysagent.sysapi
import sysagent.worker
import sysagent.driver


_ONE_DAY_IN_SECONDS = 60 * 60 * 24
_CONFIG_FILE = '/etc/vap/sysagentd.cfg'
_WORKDIR = os.getcwd()


def InitFileServerPortDict():
    conf = ExCfg(_CONFIG_FILE)
    port_max = int(conf.ConfigGet('file_server', 'port_max'))
    port_min = int(conf.ConfigGet('file_server', 'port_min'))

    logging.info("file server port range: (%d, %d)" % (port_min, port_max))

    for port in range(port_min, port_max):
        sysagent.driver.ReleaseFileserverPort(port)


def InitGlobalCfg():
    conf = GlobalConfig()
    sysagent.driver.SetSysHostMode(conf.GetConfigHostMode())
    sysagent.driver.SYS_AGENT_PORT = conf.GetServicePort("sys_agent")
    sysagent.driver.VIRT_AGENT_PORT = conf.GetServicePort("virt_agent")
    sysagent.driver.STORE_AGENT_PORT = conf.GetServicePort("store_agent")


def StartServe(port):
    s = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    sysagent.sysapi.add_to_server(s)
    s.add_insecure_port('0.0.0.0:%d' % port)
    s.start()
    logging.debug('sysagend listening on %d' % port)
    try:
        while True:
            time.sleep(_ONE_DAY_IN_SECONDS)
    except KeyboardInterrupt:
        s.stop(0)


def StartDaemonize():
    try:
        conf = ExCfg(_CONFIG_FILE)
        log_path = conf.ConfigGetLogPath()
        log_level = conf.ConfigGetLogLevel()

        log_dir = os.path.dirname(log_path)
        if not os.path.exists(log_dir):
            os.mkdir(log_dir)

        ExUtil.LogInit(log_path, log_level)
        logging.debug('logging init ok.')
        InitFileServerPortDict()
        InitGlobalCfg()
    except Exception as e:
        print(e)
        sys.exit(1)
    sysagent.worker.StartWork()
    StartServe(sysagent.driver.SYS_AGENT_PORT)


def Main():
    with daemon.DaemonContext():
        StartDaemonize()
