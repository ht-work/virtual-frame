#!/bin/bash

if [ "X$1" == "Xclean" ]; then
    find ./ -name __pycache__ | xargs rm -rf
    find ./ -name "*pb2*.py" | xargs rm -rf
    find ./ -name "*.pyc" | xargs rm -rf
    find ./ -name build | xargs rm -rf
    find ./ -name dist | xargs rm -rf
    find ./ -name storeagent.egg-info | xargs rm -rf
else
    python3 -m grpc_tools.protoc --python_out=. --grpc_python_out=.  -I./proto  storeagent/adapters.proto storeagent/pools.proto storeagent/store_util.proto storeagent/vols.proto
fi

