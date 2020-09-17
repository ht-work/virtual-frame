#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import grpc
import logging
import traceback

from storeagent import adapters_pb2_grpc
from storeagent import adapters_pb2
from storeagent import pools_pb2_grpc
from storeagent import pools_pb2
from storeagent import vols_pb2_grpc
from storeagent import vols_pb2
from util_base import log
from storeagent.store_util import StoreAgentConfig
from storeagent.storeagentd import CONFIG_FILE

# config
CFG_FILE = CONFIG_FILE
STORE_CONF = None


def LoadCfg():
    global STORE_CONF
    STORE_CONF = StoreAgentConfig(CFG_FILE)


def ClientLogInit():
    global STORE_CONF
    log.Loginit(STORE_CONF.GetClientLogPath(), STORE_CONF.GetClientLogLevel())


def main():
    global STORE_CONF
    logging.info('storeagent client start')

    try:
        LoadCfg()
        ClientLogInit()
        logging.info('storeagent client start')
        logging.info('listening on %d' % STORE_CONF.GetServicePort())
        with grpc.insecure_channel('0.0.0.0:%d' % STORE_CONF.GetServicePort()) as channel:
            stub1 = adapters_pb2_grpc.AdaptersStub(channel)
            response1 = stub1.GetHostStorageAdapterInfo(adapters_pb2.HostStorageAdapterInfoGetRequest())
            stub2 = pools_pb2_grpc.PoolsStub(channel)
            response2 = stub2.CreateLocalPool(pools_pb2.LocalPoolCreateRequest())
            stub3 = vols_pb2_grpc.VolsStub(channel)
            response3 = stub3.CreateRawVol(vols_pb2.RawVolCreateRequest())

        logging.info("GetHostStorageAdapterInfo : %d" % response1.errno)
        logging.info("CreateLocalPool : %d" % response2.errno)
        logging.info("CreateRawVol : %d" % response3.errno)

    except grpc.RpcError as e:
        logging.error(traceback.print_exc())
        logging.error(e)

    logging.info('storeagent client stop')

if __name__ == '__main__':
    main()
