#!/usr/bin/env python
# encoding: utf-8

import enum
import json


class GrpcAbortReason(object):
    '''
    GrpcAbortReason to show Grpc abort reason in this format.
    {"error_code": %d, "error_msg": %s}
    error_code is defined in "class ErrorCode" and "error_msg" is supplied by user.
    '''
    def __init__(self, error_code, error_msg):
        assert isinstance(error_code, enum.Enum)

        self.__exit = {}
        self.__exit['error_code'] = error_code.value
        self.__exit['error_msg'] = error_msg

    def __str__(self):
        return json.dumps(self.__exit)


@enum.unique
class ErrorCode(enum.Enum):
    '''
    define error code for gprc interface
    '''
    LIBVIRT_CONNECTION_ERROR = 1
