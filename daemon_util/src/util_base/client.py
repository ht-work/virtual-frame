#!/usr/bin/env python
# encoding: utf-8

import log
import logging
import time
import grpc
import socket
import random
import traceback

import demo_pb2
import demo_pb2_grpc


def generate_pid(pidlist):
    for p in pidlist:
        yield demo_pb2.ProcessPid(pid=p)


def main():
    logging.info("begin")
    local_id = 0
    hostname = socket.gethostname()

    try:
        with grpc.insecure_channel("10.10.10.124:6000") as channel:
            while True:
                try:
                    pidlist = []
                    stub = demo_pb2_grpc.DemoStub(channel)
                    # ---- GetVersion ----
                    logging.info("run GetVersion")
                    vinfo = stub.GetVersion(demo_pb2.MsgHead(id=local_id, hostname=hostname))
                    local_id += 1
                    logging.info("id %d, version: %s" % (vinfo.id, vinfo.version))
                    # ---- GetProcessList ----
                    logging.info("run GetProcesses")
                    pinfo = stub.GetProcesses(demo_pb2.MsgHead(id=local_id, hostname=hostname))
                    for process in pinfo:
                        logging.info("pid %d, process name %s" % (process.pid, process.name))
                        pidlist.append(process.pid)

                    # ---- GetCPUPercent ----
                    pinfo = stub.GetCPUPercent(generate_pid(pidlist))
                    for process in pinfo:
                        logging.info("pid %d, process name %s cpu %f" % (process.pinfo.pid, process.pinfo.name,
                                                                         process.cpu_percent))

                    time.sleep(random.randint(60, 120))
                except KeyboardInterrupt:
                    break
    except grpc.RpcError as e:
        logging.error(traceback.print_exc())
        logging.error(e)

    logging.info("end")


if __name__ == "__main__":
    log.Loginit("demo_client.log", "debug")
    main()
