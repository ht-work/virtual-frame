#!/usr/bin/env python
# encoding: utf-8

from util_base.exception import UtilBaseException
from net_agent import ErrNo_pb2


class NetAgentException(UtilBaseException):
    def __init__(self, err_msg=None, err_code=ErrNo_pb2.SYS_FAIL):
        super().__init__(err_msg, err_code)


if __name__ == '__main__':
    try:
        raise NetAgentException()
    except NetAgentException as e:
        print('NetAgentException: %s' % e)
        print('NetAgentException msg : %s' % e.err_msg)
        print('NetAgentException code: %d' % e.err_code)
