#!/usr/bin/python3
# -*- coding: utf-8 -*-

''' pytest for grpc
run as: py.test
'''

import time
import pytest
import logging
import traceback

from storeagent import adapters_pb2 as adp_pb2
from storeagent import adapters_pb2_grpc as adp_grpc
from storeagent import store_util_pb2 as util_pb2
from storeagent import storeapi
from storeagent import store_util
from storeagent import multipath
from storeagent import disk_manager
from storeagent import store_exception


TEST_ENABLE_NAA = '0000000000000000'
TEST_CONFIG_NAA = '9999999999999999'
TEST_INITIATOR_NAME = 'test-initiatorname'
TEST_IP = '172.23.7.144'
TEST_PORT = '3260'
TEST_PORTAL_LIST  = '172.23.7.144:3260,172.23.7.147:3260'

@pytest.fixture(scope='module')
def grpc_add_to_server():
    return adp_grpc.add_AdaptersServicer_to_server

@pytest.fixture(scope='module')
def grpc_server():
    return storeapi.Adapters()

@pytest.fixture(scope='module')
def grpc_adaptersmanager(grpc_channel):
    return storeapi.Adapters


def test_GetStoreAdapterInfo(grpc_adaptersmanager):
    req = adp_pb2.StoreAdapterInfoGetRequest()
    response = grpc_adaptersmanager.GetStoreAdapterInfo(grpc_adaptersmanager, request=req, context=None)
    assert response.errno == util_pb2.STORE_OK


def test_GetAdapterResourcesInfo(grpc_adaptersmanager):
    req = adp_pb2.AdapterResourcesInfoGetRequest()
    req.adaptername = store_util.LOCAL_SCSI
    response = grpc_adaptersmanager.GetAdapterResourcesInfo(grpc_adaptersmanager, request=req, context=None)
    assert response.errno == util_pb2.STORE_OK


def test_EnableDeviceMultipath(grpc_adaptersmanager):
    req = adp_pb2.DeviceMultipathEnableRequest()
    req.naa = TEST_ENABLE_NAA
    response = grpc_adaptersmanager.EnableDeviceMultipath(grpc_adaptersmanager, request=req, context=None)
    assert response.errno == util_pb2.STORE_OK
    assert multipath.GetMultipathStatus(req.naa) == store_util.ENABLE


def test_DisableDeviceMultipath(grpc_adaptersmanager):
    req = adp_pb2.DeviceMultipathDisableRequest()
    req.naa = TEST_ENABLE_NAA
    response = grpc_adaptersmanager.DisableDeviceMultipath(grpc_adaptersmanager, request=req, context=None)
    time.sleep(1)
    assert response.errno == util_pb2.STORE_OK
    assert multipath.GetMultipathStatus(req.naa) == store_util.DISABLE


def test_SetMultipathConfig(grpc_adaptersmanager):
    req = adp_pb2.MultipathConfigSetRequest()
    req.naa = TEST_CONFIG_NAA
    req.policy = adp_pb2.DEFAULT
    multipath.EnableMultipath(req.naa)
    response = grpc_adaptersmanager.SetMultipathConfig(grpc_adaptersmanager, request=req, context=None)
    assert response.errno == util_pb2.STORE_OK

    multipath.DisableMultipath(req.naa)


def test_GetMultipathConfig(grpc_adaptersmanager):
    req = adp_pb2.MultipathConfigGetRequest()
    req.naa = TEST_CONFIG_NAA
    multipath.EnableMultipath(req.naa)

    # Policy DEFAULT
    multipath.SetPolicy(req.naa, adp_pb2.DEFAULT)
    response1 = grpc_adaptersmanager.GetMultipathConfig(grpc_adaptersmanager, request=req, context=None)
    assert response1.errno == util_pb2.STORE_OK
    assert response1.policy == adp_pb2.DEFAULT

    # Policy RECENTLY_USED
    multipath.SetPolicy(req.naa, adp_pb2.RECENTLY_USED)
    response2 = grpc_adaptersmanager.GetMultipathConfig(grpc_adaptersmanager, request=req, context=None)
    assert response2.errno == util_pb2.STORE_OK
    assert response2.policy == adp_pb2.RECENTLY_USED

    # Policy FIXED
    multipath.SetPolicy(req.naa, adp_pb2.FIXED)
    response3 = grpc_adaptersmanager.GetMultipathConfig(grpc_adaptersmanager, request=req, context=None)
    assert response3.errno == util_pb2.STORE_OK
    assert response3.policy == adp_pb2.FIXED

    # Policy LOOP
    multipath.SetPolicy(req.naa, adp_pb2.LOOP)
    response4 = grpc_adaptersmanager.GetMultipathConfig(grpc_adaptersmanager, request=req, context=None)
    assert response4.errno == util_pb2.STORE_OK
    assert response4.policy == adp_pb2.LOOP

    # Policy OPTIMAL
    multipath.SetPolicy(req.naa, adp_pb2.OPTIMAL)
    response5 = grpc_adaptersmanager.GetMultipathConfig(grpc_adaptersmanager, request=req, context=None)
    assert response5.errno == util_pb2.STORE_OK
    assert response5.policy == adp_pb2.OPTIMAL

    multipath.DisableMultipath(req.naa)


def test_SetInitiatorName(grpc_adaptersmanager):
    req = adp_pb2.InitiatorNameSetRequest()
    _initiname = disk_manager.GetInitiator()
    req.initiatorname = TEST_INITIATOR_NAME
    response = grpc_adaptersmanager.SetInitiatorName(grpc_adaptersmanager, request=req, context=None)
    assert response.errno == util_pb2.STORE_OK
    assert disk_manager.GetInitiator() == TEST_INITIATOR_NAME
    disk_manager.SetInitiator(_initiname)


def test_GetInitiatorName(grpc_adaptersmanager):
    _initiname = disk_manager.GetInitiator()
    disk_manager.SetInitiator(TEST_INITIATOR_NAME)
    req = adp_pb2.InitiatorNameGetRequest()
    response = grpc_adaptersmanager.GetInitiatorName(grpc_adaptersmanager, request=req, context=None)
    assert response.errno == util_pb2.STORE_OK
    assert response.initiatorname == TEST_INITIATOR_NAME
    disk_manager.SetInitiator(_initiname)


def test_GetIscsiIpSession(grpc_adaptersmanager):
    req = adp_pb2.IscsiIpSessionGetRequest()
    response = grpc_adaptersmanager.GetIscsiIpSession(grpc_adaptersmanager, request=req, context=None)
    assert response.errno == util_pb2.STORE_OK


def test_GetIscsiTargetsInfo(grpc_adaptersmanager):
    req = adp_pb2.GetIscsiTargetsRequest()
    req.portal_list = TEST_PORTAL_LIST
    response = grpc_adaptersmanager.GetIscsiTargetsInfo(grpc_adaptersmanager, request=req, context=None)
    assert response.errno == util_pb2.STORE_OK


def test_GetIscsiLunInfo(grpc_adaptersmanager):
    req = adp_pb2.GetIscsiLunInfoRequest()
    req.portal_list = TEST_PORTAL_LIST
    req.target_name = ''
    response = grpc_adaptersmanager.GetIscsiLunInfo(grpc_adaptersmanager, request=req, context=None)
    # clean session need time, otherwise test_pool GetUsefullocalDevice may fail.
    time.sleep(60)
    assert response.errno == util_pb2.STORE_OK
