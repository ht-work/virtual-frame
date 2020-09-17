#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from util_base.exception import UtilBaseException
from storeagent import store_util_pb2 as util_pb2


class StoreException(UtilBaseException):
    pass


class StoreLockException(StoreException):
    pass


class StoreInvalidException(StoreException):
    pass


class StoreXmlException(StoreException):
    pass


class StoreOsErrorException(StoreException):
    pass


class StoreEnvoyException(StoreException):
    pass


class StoreJsonValidationException(StoreException):
    pass


class StoreQemuImgCommandException(StoreException):
    pass


class StoreFileBusyException(StoreException):
    pass


class StoreDiskManagerBase(StoreException):
    pass


class StoreDiskManagerSysfsError(StoreException):
    pass


class StoreMultipathdException(StoreException):
    pass


class StoreIOError(StoreException):
    pass


class DatastoreListException(StoreException):
    pass


class StoreDataConfigException(StoreException):
    pass


class StoreJobException(StoreException):
    def __init__(self,  err_msg=None, err_code=util_pb2.STORE_INVALID_ERROR):
        super().__init__(err_msg, err_code)
