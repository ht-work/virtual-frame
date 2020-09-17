#!/usr/bin/python3
# -*- coding: utf-8 -*-
import os
import re
import logging
import util_base.log
import util_base.sys_util

# global value
SHUTDOWN = 'shutdown'
REBOOT = 'reboot'

# cmd
CMD_SHUTDOWN = '/usr/sbin/shutdown'
CMD_REBOOT = '/usr/sbin/reboot'


class Verify(object):

    def is_ipv4_valid(ipv4):
        pattern = re.compile(
            r'^(1\d{2}|2[0-4]\d|25[0-5]|[1-9]\d|[1-9])\.'
            r'(1\d{2}|2[0-4]\d|25[0-5]|[1-9]\d|\d)\.'
            r'(1\d{2}|2[0-4]\d|25[0-5]|[1-9]\d|\d)\.'
            r'(1\d{2}|2[0-4]\d|25[0-5]|[1-9]\d|\d)$')
        if pattern.match(ipv4):
            return True
        else:
            return False

    def is_hostname_valid(hostname):
        pattern = re.compile(r'^[a-zA-Z0-9._-]*$')
        if pattern.match(hostname):
            return True
        else:
            return False


class ExternalSysUtil(object):
    def LogInit(logpath, loglevel):
        return util_base.log.Loginit(logpath, loglevel)

    def CheckPasswd(user='root', pwd=None):
        try:
            return util_base.sys_util.check_passwd(user, pwd)
        except Exception as e:
            logging.critical(e)
            return False


class ExternalConfig(util_base.sys_util.BaseConfig):
    def __init__(self, file_path):
        if not os.path.exists(file_path):
            raise Exception('cannot access %s: No such file or directory' %
                            file_path)
        super(ExternalConfig, self).__init__(file_path)

    def ConfigGet(self, section='global', key=None):
        return self.Get(key, section)

    def ConfigSet(self, section='global', key=None, value=None):
        self.Set(key, value, section)

    def ConfigGetLogPath(self):
        return self.GetLogPath()

    def ConfigGetServicePort(self):
        return self.GetServicePort()

    def ConfigGetLogLevel(self):
        return self.GetLogLevel()
