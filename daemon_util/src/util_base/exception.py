#!/usr/bin/env python
# encoding: utf-8

import traceback


class UtilBaseException(Exception):
    def __init__(self, err_msg, err_code=-1):
        self.__err_msg = err_msg
        self.__err_code = err_code
        super().__init__(err_msg, err_code)

    @property
    def err_code(self):
        return self.__err_code

    @property
    def err_msg(self):
        return self.__err_msg


class ConfigException(UtilBaseException):
    pass


class XMLParseException(UtilBaseException):
    '''
    for lxml util
    '''
    pass


class DirectcopyException(UtilBaseException):
    pass


class Md5Exception(UtilBaseException):
    pass


def _do_test():
    try:
        raise UtilBaseException("hello")
    except Exception as e:
        print("Exception: %s" % (e))
        print(traceback.format_exc())


if __name__ == '__main__':
    _do_test()
