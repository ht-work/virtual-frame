#!/usr/bin/python3
# -*- coding: utf-8 -*-

''' pytest for grpc
run as: py.test
'''
import os
import platform
import pytest
import envoy

from storeagent import pools_pb2
from storeagent import pools_pb2_grpc
from storeagent import store_util_pb2
from storeagent import storeapi
from storeagent import store_util as util
from storeagent import disk_manager
from storeagent import storeagentd


@pytest.fixture(scope='module')
def grpc_add_to_server():
    return pools_pb2_grpc.add_PoolsServicer_to_server

@pytest.fixture(scope='module')
def grpc_servicer():
    return storeapi.Pools()

@pytest.fixture(scope='module')
def grpc_poolmanager(grpc_channel):
    return storeapi.Pools

# test device need exist and type is scsi disk.
TEST_DEVICE  = '/dev/sdb'
TEST_NAME = 'testlocal'
TEST_TITLE = 'testlocal_title'


def test_pool_FormatLocalDisk(grpc_poolmanager):
    req = pools_pb2.LocalDiskFormatRequest()
    req.naa = disk_manager.GetDeviceAttribute(disk_manager.DiskUdevAttribute.ID_SERIAL, TEST_DEVICE)
    response = grpc_poolmanager.FormatLocalDisk(grpc_poolmanager, request=req, context=None)
    assert response.errno == store_util_pb2.STORE_OK

def test_pool_CreateLocalPool(grpc_poolmanager):
    req = pools_pb2.LocalPoolCreateRequest()
    req.name = TEST_NAME
    req.naa = disk_manager.GetDeviceAttribute(disk_manager.DiskUdevAttribute.ID_SERIAL, TEST_DEVICE)
    req.n_title = TEST_TITLE
    storeagentd.LoadConfig()
    response = grpc_poolmanager.CreateLocalPool(grpc_poolmanager, request=req, context=None)
    assert response.errno == store_util_pb2.STORE_OK

def test_pool_StartLocalPool(grpc_poolmanager):
    req = pools_pb2.LocalPoolStartRequest()
    req.name = TEST_NAME
    response = grpc_poolmanager.StartLocalPool(grpc_poolmanager, request=req, context=None)
    assert response.errno == store_util_pb2.STORE_OK

def test_pool_StopLocalPool(grpc_poolmanager):
    req = pools_pb2.LocalPoolStopRequest()
    req.name = TEST_NAME
    response = grpc_poolmanager.StopLocalPool(grpc_poolmanager, request=req, context=None)
    assert response.errno == store_util_pb2.STORE_OK

def test_pool_GetPoolInfo(grpc_poolmanager):
    req = pools_pb2.PoolInfoGetRequest()
    req.name = TEST_NAME
    response = grpc_poolmanager.GetPoolInfo(grpc_poolmanager, request=req, context=None)
    assert response.errno == store_util_pb2.STORE_OK

def test_pool_GetOnlyPoolsSize(grpc_poolmanager):
    req = pools_pb2.OnlyPoolSizeGetRequest()
    req.naa = disk_manager.GetDeviceAttribute(disk_manager.DiskUdevAttribute.ID_SERIAL, TEST_DEVICE)
    response = grpc_poolmanager.GetOnlyPoolsSize(grpc_poolmanager, request=req, context=None)
    assert response.errno == store_util_pb2.STORE_OK

def test_pool_DeleteLocalPool(grpc_poolmanager):
    req = pools_pb2.LocalPoolDeleteRequest()
    req.name = TEST_NAME
    response = grpc_poolmanager.DeleteLocalPool(grpc_poolmanager, request=req, context=None)
    assert response.errno == store_util_pb2.STORE_OK

def test_pool_GetUsefulLocalDevice(grpc_poolmanager):
    req = pools_pb2.UsefulLocalDeviceGetRequest()
    response = grpc_poolmanager.GetUsefulLocalDevice(grpc_poolmanager, request=req, context=None)
    assert response.errno == store_util_pb2.STORE_OK

def test_pool_GetLocalStoreSize(grpc_poolmanager):
    req = pools_pb2.LocalStoreSizeGetRequest()
    response = grpc_poolmanager.GetLocalStoreSize(grpc_poolmanager, request=req, context=None)
    assert response.errno == store_util_pb2.STORE_OK
