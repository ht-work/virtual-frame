#!/usr/bin/env python
# encoding: utf-8


class NetCopyException(Exception):
    def __init__(self, err_msg, err_code=-1):
        self.__err_msg = err_msg
        self.__err_code = err_code
        super().__init__(err_msg, err_code)


class NetCopyEOF(NetCopyException):
    pass


class NetCopyError(NetCopyException):
    pass
