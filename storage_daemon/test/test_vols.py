#!/usr/bin/python3
# -*- coding: utf-8 -*-

''' pytest for grpc
run as: py.test
'''

import pytest
import json

from storeagent import vols_pb2
from storeagent import vols_pb2_grpc
from storeagent import store_util_pb2
from storeagent import storeapi

@pytest.fixture(scope='module')
def grpc_add_to_server():
    return vols_pb2_grpc.add_VolsServicer_to_server

@pytest.fixture(scope='module')
def grpc_servicer():
    return storeapi.Vols()

@pytest.fixture(scope='module')
def grpc_volmanager(grpc_channel):
    return storeapi.Vols

def test_vol_CreateVol(grpc_volmanager):
    req = vols_pb2.VolCreateRequest()
    req.json_data =json.dumps({"p_name":"test", "vol_path":"test" })
    response = grpc_volmanager.CreateVol(grpc_volmanager, request=req, context=None)
    assert response.errno == store_util_pb2.STORE_INVALID_ERROR

