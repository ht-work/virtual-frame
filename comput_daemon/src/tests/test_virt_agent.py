#!/usr/bin/env python
# encoding: utf-8

import pytest
import grpc
import random
import logging
import sys
import uuid

import libvirt
from util_base.libvirt_util import ConnectionPool

import base
from virt_agent import virt_agent_pb2_grpc
from virt_agent import virt_agent_pb2


def genrandstr(size=10):
    import string
    import random

    return ''.join(random.choices(string.ascii_letters + string.digits, k=size))


class TestVirtAgent():
    def testEcho(self):
        try:
            with grpc.insecure_channel("127.0.0.1:9100") as channel:
                stub = virt_agent_pb2_grpc.VirtAgentStub(channel)

                send = genrandstr(100)
                res = stub.Echo(virt_agent_pb2.EchoReq(context=send), timeout=10)
                assert send == res.context

        except grpc.RpcError as e:
            assert 0

    def testHeartBeat(self):
        try:
            with grpc.insecure_channel("127.0.0.1:9100") as channel:
                stub = virt_agent_pb2_grpc.VirtAgentStub(channel)

                send = random.randint(1, 100000)
                res = stub.HeartBeat(virt_agent_pb2.HeartBeatReq(hbid=str(send)), timeout=10)
                assert send == int(res.hbid)

        except grpc.RpcError as e:
            assert 0

    def testGetLibvirtVersion(self):
        try:
            import json
            with grpc.insecure_channel("127.0.0.1:9100") as channel:
                stub = virt_agent_pb2_grpc.VirtAgentStub(channel)

                res = stub.GetLibvirtVersion(virt_agent_pb2.GetLibvirtVersionReq(), timeout=10)
                vers = json.loads(res.libvirt_version)
                assert ('libvirt' in vers)
                assert ('qemu' in vers)

                assert 1
        except grpc.RpcError as e:
            assert 0
