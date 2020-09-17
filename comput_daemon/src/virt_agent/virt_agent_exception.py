#!/usr/bin/env python
# encoding: utf-8

from util_base.exception import UtilBaseException

from . import virt_agent_pb2 as pb


class VirtAgentException(UtilBaseException):
    def __init__(self, err_msg, err_code=pb.LIBVIRT_ERR_INTERNAL_ERROR):
        super().__init__(err_msg, err_code)


class VirtAgentLockException(VirtAgentException):
    pass


class VirtAgentInvalidException(VirtAgentException):
    pass


class VirtAgentNotImplementedException(VirtAgentException):
    pass


class VirtAgentDomainXmlInvalidInputException(VirtAgentException):
    pass


class VirtAgentLibvirtException(VirtAgentException):
    pass


class VirtAgentDomainXMLException(VirtAgentException):
    pass


class VirtAgentJobException(VirtAgentException):
    def __init__(self, err_msg, err_code=pb.VIRT_AGENT_ERR_INVALID_JOB_ID):
        super().__init__(err_msg, err_code)


class VirtAgentDomainDiskInvalidSourceException(VirtAgentException):
    pass


class VirtAgentDomainDiskInvalidTargetException(VirtAgentException):
    pass


class VirtAgentJsonValidationException(VirtAgentException):
    pass


class VirtAgentRPCApiCallException(VirtAgentException):
    pass


class VirtAgentMigrationException(VirtAgentException):
    def __init__(self, err_msg='', err_code=pb.LIBVIRT_ERR_INTERNAL_ERROR):
        super().__init__(err_msg, err_code)
