#!/usr/bin/python3
# -*- coding: utf-8 -*-

from concurrent import futures
import time
import logging
import grpc
import traceback
import argparse
import json
import prettytable
import sys
import os

from util_base import log
from storeagent.store_util import StoreAgentConfig
import storeagent.storeapi
from storeagent import store_util as util
from storeagent.worker import Worker
from storeagent import adapters_pb2 as adp_pb2
from storeagent import adapters_pb2_grpc as adp_grpc
from storeagent import store_util_pb2 as util_pb2
from storeagent import multipath
from . import disk_manager

# one day time
_ONE_DAY_IN_SECONDS = 60 * 60 * 24

# config file
STORE_AGENT_CONF = None
DATASTORE_CONF = None
WORKER = None


def LoadConfig():
    global STORE_AGENT_CONF
    global DATASTORE_CONF

    config = ("%s/%s" % (util.CONF_PATH, util.DEFAULT_AGENT_CONF))
    STORE_AGENT_CONF = StoreAgentConfig(config)

    datastore_cfg = ("%s/%s" % (util.STORE_CONF_PATH, util.DATASTORE_CONF))
    DATASTORE_CONF = util.DataStoreConfig(datastore_cfg)


def LogInit():
    global STORE_AGENT_CONF
    log.Loginit(STORE_AGENT_CONF.GetLogPath(), STORE_AGENT_CONF.GetLogLevel())


def SysInit():
    # check /etc/multipath.conf
    if not os.path.exists(util.MULTIPATH_CONF):
        multipath.SetDefaultConfig()


def DataStoreInit():
    # read datastore.cfg mount, value is True mount.
    # read datastore.cfg state, value is active start Datastore, inactive stop Datastore
    pass


def main():
    global STORE_AGENT_CONF
    global WORKER

    try:
        SysInit()
        LoadConfig()
        LogInit()
        DataStoreInit()
        logging.info('storeagent server start')
        logging.info('listening on %d' % STORE_AGENT_CONF.GetServicePort())

        # worker
        WORKER = Worker(STORE_AGENT_CONF.GetMaxWorker())
        WORKER.init_notifier()
        WORKER.run()

        # disk_manager
        disk_manager.Init()

        # grpc server
        s = grpc.server(futures.ThreadPoolExecutor(max_workers=STORE_AGENT_CONF.GetGrpcWorkerSize()))
        storeagent.storeapi.add_to_server(s)
        s.add_insecure_port('0.0.0.0:%d' % STORE_AGENT_CONF.GetServicePort())
        s.start()
        try:
            while True:
                time.sleep(_ONE_DAY_IN_SECONDS)
        except KeyboardInterrupt:
            s.stop(0)
        logging.debug('stop')
    except Exception:
        logging.critical(traceback.format_exc())


def _RunHandler(func, opaque):
    global STORE_AGENT_CONF

    try:
        LoadConfig()
        with grpc.insecure_channel("127.0.0.1:%d" % (STORE_AGENT_CONF.GetServicePort())) as channel:
            stub = adp_grpc.AdaptersStub(channel)
            func(stub, opaque)
    except grpc.RpcError:
        print('connecting to store_agentd failed')


def _Pool_Handler(args):
    print(args)


def _ISCSI_Handler(args):
    def func_target_info(stub, args):
        portal_address = args.address
        portal_port = args.port if args.port else '3260'

        request = adp_pb2.GetIscsiTargetsRequest(ip=portal_address, port=portal_port)
        res = stub.GetIscsiTargetsInfo(request, timeout=10)
        if res.errno != util_pb2.STORE_OK:
            print('failed to get target info')

        tb = prettytable.PrettyTable()
        tb.field_names = ['portal', 'target name']
        for target in sorted(json.loads(res.target_list)):
            tb.add_row(['%s:%s' % (portal_address, portal_port), target])
        print(tb)

    def func_lun_info(stub, args):
        portal_address = args.address
        portal_port = args.port if args.port else '3260'
        target_name = args.target

        request = adp_pb2.GetIscsiLunInfoRequest(ip=portal_address, port=portal_port, target_name=target_name)
        res = stub.GetIscsiLunInfo(request, timeout=30)
        if res.errno != util_pb2.STORE_OK:
            print('failed to get target info')

        tb = prettytable.PrettyTable()
        tb.field_names = ['portal', 'target name', 'scsi id', 'size(bytes)']
        lun_list = json.loads(res.lun_list)
        for target in sorted(lun_list.keys()):
            for disk_name in sorted(lun_list[target].keys()):
                tb.add_row(['%s:%s' % (portal_address, portal_port), target, disk_name, lun_list[target][disk_name]])
        print(tb)

    OP_LIST = {
            'target-info': func_target_info,
            'lun-info': func_lun_info,
    }

    if args.HELP:
        print('valid operation: %s' % (sorted(OP_LIST.keys())))
        sys.exit(0)

    if args.sub_operation not in OP_LIST.keys():
        print('invalid sub_operation: %s' % (args.sub_operation))
        sys.exit(-1)

    _RunHandler(OP_LIST[args.sub_operation], args)


def main_cli():
    OP_LIST = {
        'pool': _Pool_Handler,
        'iscsi': _ISCSI_Handler,
    }
    try:
        parser = argparse.ArgumentParser(description='store agent command line tool')
        parser.add_argument('-v', '--verbose', action='store_true')
        subparsers = parser.add_subparsers(help='sub-command help', dest='operation')

        iscsi = subparsers.add_parser('pool', aliases=['pool'], description='storage pool')
        iscsi.add_argument('-o', '--sub-operation', type=str, help='operation for pool')

        iscsi = subparsers.add_parser('iscsi', aliases=['iscsi'], description='iscsi')
        iscsi.add_argument('-H', '--HELP', action='store_true', help='help for iscsi')
        iscsi.add_argument('-o', '--sub-operation', type=str, help='operation for iscsi')
        iscsi.add_argument('-a', '--address', type=str, help='iscsi portal ip address')
        iscsi.add_argument('-p', '--port', type=str, help='iscsi portal port')
        iscsi.add_argument('-t', '--target', type=str, help='iscsi target name')

        args = parser.parse_args()

        OP_LIST[args.operation](args)
    except Exception as e:
        print(e)
        print(traceback.format_exc())

if __name__ == '__main__':
    main()
