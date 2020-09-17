#!/usr/bin/python3
# -*- coding: utf-8 -*-
import pytest
import sys

sys.path.append('..')
import sysagent.sysagent_pb2
import sysagent.util_pb2


@pytest.fixture(scope='module')
def grpc_add_to_server():
    from sysagent.sysagent_pb2_grpc import add_SysAgentServicer_to_server
    return add_SysAgentServicer_to_server


@pytest.fixture(scope='module')
def grpc_servicer():
    from sysagent.sysapi import SysAgent
    return SysAgent()


@pytest.fixture(scope='module')
def grpc_sysagent(grpc_channel):
    from sysagent.sysapi import SysAgent
    return SysAgent


def test_ConnectHost(grpc_sysagent):
    req = sysagent.sysagent_pb2.HostConnectRequest(manager_ip='1.2.3.4',
                                                   name='weo32&^$#$sd3',
                                                   passwd='bio83;3l4@#$')
    response = grpc_sysagent.ConnectHost(grpc_sysagent, request=req,
                                         context=None)
    assert response.errno == sysagent.util_pb2.SYS_PERMISSION

    req = sysagent.sysagent_pb2.HostConnectRequest(manager_ip='1.2.3.4',
                                                   name='root',
                                                   passwd=None)
    response = grpc_sysagent.ConnectHost(grpc_sysagent, request=req,
                                         context=None)
    assert response.errno == sysagent.util_pb2.SYS_USER_PASSWD

    req = sysagent.sysagent_pb2.HostConnectRequest(manager_ip='1w$@.2^s&.3!.4',
                                                   name=None,
                                                   passwd=None)
    response = grpc_sysagent.ConnectHost(grpc_sysagent, request=req,
                                         context=None)
    assert response.errno == sysagent.util_pb2.SYS_INVAL

    req = sysagent.sysagent_pb2.HostConnectRequest(manager_ip=None,
                                                   name=None,
                                                   passwd=None)
    response = grpc_sysagent.ConnectHost(grpc_sysagent, request=req,
                                         context=None)
    assert response.errno == sysagent.util_pb2.SYS_INVAL


def test_DisConnectHost(grpc_sysagent):
    req = sysagent.sysagent_pb2.HostDisConnectRequest(manager_ip='f&*^3SF.@3')
    response = grpc_sysagent.DisConnectHost(grpc_sysagent, request=req,
                                            context=None)
    assert response.errno == sysagent.util_pb2.SYS_NOTFOUND

    req = sysagent.sysagent_pb2.HostDisConnectRequest(manager_ip=None)
    response = grpc_sysagent.DisConnectHost(grpc_sysagent, request=req,
                                            context=None)
    assert response.errno == sysagent.util_pb2.SYS_NOTFOUND


def test_ModifyHostPasswd(grpc_sysagent):
    req = sysagent.sysagent_pb2.HostPasswdModifyRequest(name=None,
                                                        passwd=None,
                                                        passwd_new=None)
    response = grpc_sysagent.ModifyHostPasswd(grpc_sysagent, request=req,
                                              context=None)
    assert response.errno == sysagent.util_pb2.SYS_INVAL

    req = sysagent.sysagent_pb2.HostPasswdModifyRequest(name='root',
                                                        passwd='d@!f67%$g.%#W',
                                                        passwd_new=None)
    response = grpc_sysagent.ModifyHostPasswd(grpc_sysagent, request=req,
                                              context=None)
    assert response.errno == sysagent.util_pb2.SYS_USER_PASSWD


def test_GetVersion(grpc_sysagent):
    req = sysagent.sysagent_pb2.VersionGetRequest()
    response = grpc_sysagent.GetVersion(grpc_sysagent, request=req,
                                        context=None)
    assert response.errno == sysagent.util_pb2.OK


def test_GetHostInfo(grpc_sysagent):
    req = sysagent.sysagent_pb2.HostInfoGetRequest()
    response = grpc_sysagent.GetHostInfo(grpc_sysagent, request=req,
                                         context=None)
    assert response.errno == sysagent.util_pb2.OK


def test_BeatHeart(grpc_sysagent):
    req = sysagent.sysagent_pb2.HeartBeatRequest(manager_ip='1.2.3.4')
    response = grpc_sysagent.BeatHeart(grpc_sysagent, request=req,
                                       context=None)
    assert response.errno == sysagent.util_pb2.SYS_NOTFOUND

    req = sysagent.sysagent_pb2.HeartBeatRequest()
    response = grpc_sysagent.BeatHeart(grpc_sysagent, request=req,
                                       context=None)
    assert response.errno == sysagent.util_pb2.SYS_NOTFOUND
