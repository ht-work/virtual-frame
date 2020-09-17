"""exception handing.
"""
from util_base.exception import UtilBaseException
from sysagent import util_pb2 as u_pb2


class SysagentException(UtilBaseException):
    def __init__(self, err_msg=None, err_code=u_pb2.SYS_FAIL):
        super().__init__(err_msg, err_code)


class SysagentJobException(SysagentException):
    pass


class InvalidValueException(SysagentException):
    pass


class InvalidRequestException(SysagentException):
    pass


class FileNotFoundException(SysagentException):
    pass


class NoAvailablePortException(SysagentException):
    pass


class RemoteRequestFailException(SysagentException):
    pass


class FileTransFailException(SysagentException):
    pass


class HostModeException(SysagentException):
    pass


class SystemOperationException(SysagentException):
    pass


if __name__ == '__main__':
    try:
        raise SysagentException()
    except SysagentException as e:
        print('SysagentException: %s' % e)
        print('SysagentException msg : %s' % e.err_msg)
        print('SysagentException code: %d' % e.err_code)
