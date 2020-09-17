#!/usr/bin/env python
# encoding: utf-8

from concurrent import futures
import log
import logging
import time
import grpc
import os
import psutil

import demo_pb2
import demo_pb2_grpc


class DemoServicer(demo_pb2_grpc.DemoServicer):
    def __init__(self):
        pass

    def GetVersion(self, request, context):
        logging.info("%s %s" % (request, context))

        return demo_pb2.Version(id=1, version=str(os.uname()))

    def GetProcesses(self, request, context):
        logging.info("%s %s" % (request, context))

        for p in map(lambda x: psutil.Process(x), psutil.pids()):
            yield demo_pb2.ProcessInfo(pid=p.pid, name=str(p.name))

    def GetCPUPercent(self, request_iterator, context):
        for rq in request_iterator:
            process = psutil.Process(rq.pid)
            yield demo_pb2.ProcessCPUPercent(pinfo=demo_pb2.ProcessInfo(pid=rq.pid,
                                                                        name=str(psutil.Process(rq.pid).name)),
                                             cpu_percent=process.cpu_percent())


def main():
    logging.debug("start")
    server = grpc.server(thread_pool=futures.ThreadPoolExecutor(max_workers=10))
    # server = grpc.server(futures.ThreadPoolExecutor(max_workers = 10))
    demo_pb2_grpc.add_DemoServicer_to_server(DemoServicer(), server)
    server.add_insecure_port("0.0.0.0:6000")
    server.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        server.stop(0)

    logging.debug("stop")

if __name__ == "__main__":
    log.Loginit("demo_server.log", "debug")
    main()
