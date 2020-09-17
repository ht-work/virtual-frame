#!/usr/bin/env python
# encoding: utf-8

import logging
import configparser
from . import exception
import os
import enum


_GLOBAL_CFG_FILE = '/etc/vap/util_global.cfg'


# const #
class Const(object):
    class ConstError(PermissionError):
        pass

    def __setattr__(self, name, value):
        if name in self.__dict__.keys():
            raise self.ConstError("Can't rebind const(%s)" % name)
        self.__dict__[name] = value

    def __delattr__(self, name):
        if name in self.__dict__:
            raise self.ConstError("Can't unbind const(%s)" % name)
        raise NameError(name)


__LOCAL_CONST = Const()
__LOCAL_CONST.SHADOW_FILE = '/etc/shadow'


# file operation #
def cat(file_path):
    '''
    Description:
        Read file, return in 'str'
        Use with caution when target file is large(>100M)
    '''
    with open(file_path, mode='rt', encoding='utf-8') as f:
        return f.read()


def echo(file_path, context=""):
    '''
    Description:
        write context an the end of file, adding '\\n' automatically
    '''
    with open(file_path, mode='w', encoding='utf-8') as f:
        f.write("%s\n" % (context))


def _genrandstr(size=10):
    import string
    import random

    return ''.join(random.sample(string.ascii_letters + string.digits, size))


def _do_file_test():
    import tempfile
    import os

    (lvl, tmp) = tempfile.mkstemp(prefix=__name__, text=True)

    randstr = _genrandstr(50)
    echo(tmp, randstr)
    c = cat(tmp)
    print(randstr)
    print(c)
    if c.strip() == randstr:
        print("ok")
    else:
        print("not match")

    if os.path.isfile(tmp):
        os.remove(tmp)


# check password #
def _get_passwd_full_str(user):
    '''
    Description:
        return splited password string
    '''
    try:
        with open(__LOCAL_CONST.SHADOW_FILE, mode='r') as f:
            for line in f:
                str_slice = line.split(':')
                user_name = str_slice[0].strip()
                if user == user_name:
                    return str_slice
            return None
    except Exception:
        logging.error("failed to get password from %s" % __LOCAL_CONST.SHADOW_FILE)


def check_passwd(user='root', pwd=''):
    '''
    Description:
        Check password through shadow file.
        the head of salt indicate diffrent algorithm.
        md5: $1
        blowfish: $2, $2a
        sha: $4, $6
    Return:
        True: user and pwd matched
        False: user and pwd not match
    '''
    import crypt
    try:
        logging.debug(pwd)
        if not isinstance(pwd, str):
            return False

        full_str = _get_passwd_full_str(user)
        if full_str is None:
            return False

        assert (full_str[0].strip() == user)
        salt = full_str[1].strip().rpartition('$')[0]
        check_str = crypt.crypt(pwd, salt)
        if check_str.strip() == full_str[1].strip():
            return True
        else:
            return False
    except Exception:
        logging.error("failed to get password from %s" % __LOCAL_CONST.SHADOW_FILE)


def _do_password_test():
    print(check_passwd(user='root', pwd='123456'))
    print(check_passwd(user='root', pwd='1q2w3e'))
    print(check_passwd(user='root', pwd='1q2w3e4r'))
    print(check_passwd(user='root', pwd='qwe@123'))
    print(check_passwd(user='root', pwd=_genrandstr(6)))
    print(check_passwd(user='root', pwd=_genrandstr(7)))
    print(check_passwd(user='root', pwd=_genrandstr(8)))
    print(check_passwd(user='root', pwd=_genrandstr(6)))
    print(check_passwd(user='root', pwd=_genrandstr(7)))
    print(check_passwd(user='root', pwd=_genrandstr(8)))


# configure file operation #
class BaseConfig(object):
    '''
    Description:
        Base configuration class for parse and write configuration file.
        All config file has a basic section 'global', 'log level' is a mandatory option in 'global'
    '''
    __const = Const()
    __const.valid_log_level = ['debug', 'info', 'warning', 'error', 'critical']

    def __init__(self, file_path):
        self.__file_path = file_path

    def GetLogLevel(self):
        '''
        Description:
            load log level, valid value is "debug, info, warning, error, critical"
        '''
        log_level = self.Get('log_level')
        if log_level is None:
            # if not set, set 'info' as default
            default_log_level = 'info'
            self.Set('log_level', default_log_level)
            return default_log_level
        else:
            ret = log_level.strip().lower()
            if ret not in BaseConfig.__const.valid_log_level:
                raise exception.ConfigException("invalid log level %s" % (log_level))
            return ret

    def GetLogPath(self):
        '''
        Description:
            load log path, the directory path must be exist.
        '''
        log_path = self.Get('log_path')
        if log_path is None:
            raise exception.ConfigException('can not find log path definition in %s' % (self.__file_path))
        else:
            if not os.path.exists(os.path.dirname(log_path)):
                raise exception.ConfigException('invalid log path %s' % (log_path))
            return log_path

    def GetServicePort(self):
        '''
        Description:
            load port.
        Return:
            port (int)
        '''
        port = self.Get('port')
        if port is None:
            raise exception.ConfigException('can not find port definition in %s' % (self.__file_path))
        else:
            return int(port)

    def GetGrpcWorkerSize(self):
        '''
        Description:
            load grpc worker size.
        Return:
            size (int)
        '''
        worker = self.Get('grpc_worker')
        if worker is None:
            # if not set, set 100 as default
            default_worker = 100
            self.Set('grpc_worker', str(default_worker))
            return default_worker
        else:
            return int(worker)

    def Get(self, option_name, section='global'):
        '''
        Description:
           get option from sepcified section
        Return:
            value: return value in string format
            None: failed parse configuraion file
        '''
        conf = configparser.ConfigParser()
        try:
            conf.read(self.__file_path)
            return conf.get(section, option_name)
        except configparser.Error:
            return None

    def Set(self, option_name, value, section='global'):
        '''
        Description:
            set configuration file
        '''
        conf = configparser.ConfigParser()
        try:
            conf.read(self.__file_path)
            if not conf.has_section(section):
                conf.add_section(section)
            conf.set(section, option_name, value)
            conf.write(open(self.__file_path, 'w'))
        except configparser.Error as e:
            raise exception.ConfigException("%s" % (e))

    def DeleteOption(self, option_name, section='global'):
        '''
        Description:
            delete configuration file option_name
        '''
        conf = configparser.ConfigParser()
        try:
            conf.read(self.__file_path)
            conf.remove_option(section, option_name)
            conf.write(open(self.__file_path, 'w'))
        except configparser.Error as e:
            raise exception.ConfigException(("%s" % (e)))

    def DeleteSection(self, section='global'):
        '''
        Description:
            delete configuration file section
        '''
        conf = configparser.ConfigParser()
        try:
            conf.read(self.__file_path)
            conf.remove_section(section)
            conf.write(open(self.__file_path, 'w'))
        except configparser.Error as e:
            raise exception.ConfigException("%s" % (e))

    def GetALLSection(self):
        '''
        Description:
            get configuraion file all section
        '''
        sections = []
        conf = configparser.ConfigParser()
        try:
            conf.read(self.__file_path)
            sections = conf.sections()
            return sections
        except configparser.Error as e:
            raise exception.ConfigException('%s' % (e))


@enum.unique
class HostMode(enum.Enum):
    UNKNOWN = 0         # invalid mode
    NORMAL = 1          # normal mode
    MAINTENANCE = 2     # maintenance mode


class GlobalConfig(BaseConfig):
    def __init__(self):
        file_path = _GLOBAL_CFG_FILE
        super().__init__(file_path)

    def GetServicePort(self, agent_name):
        '''
        Description:
            load service port
        Return:
            port (int)
        '''
        agent_list = ['sys_agent', 'virt_agent', 'store_agent', 'net_agent']
        if agent_name not in agent_list:
            raise exception.ConfigException('agent name is wrong. agent name:%s' % (agent_name))

        port = super().Get('service_port', section=agent_name)
        if port is None:
            raise exception.ConfigException('can not find %s service port in %s' % (agent_name, self.__file_path))

        return int(port)

    def GetConfigHostMode(self):
        '''
        Description:
            load host mode
        Return:
            mode (enum)
        '''
        mode = super().Get("host_mode")
        if mode is None:
            raise exception.ConfigException('can not find host mode definition in %s' % (self.__file_path))

        return StringToHostMode(mode)

    def SetConfigHostMode(self, mode):
        '''
        Description:
            set host mode, only called by sys-agent
        '''
        super().Set('host_mode', HostModeToString(mode))


def _do_global_config_test():
    try:
        conf = GlobalConfig()
        print(conf.GetConfigHostMode())
        print(conf.GetServicePort("sys_agent"))
        print(conf.GetServicePort("virt_agent"))
        print(conf.GetServicePort("store_agent"))
        conf.SetConfigHostMode(HostMode.NORMAL)
        print(conf.GetConfigHostMode())
    except exception.ConfigException as e:
        print(e)


def _do_config_test():
    try:
        config_file = 'config_test.cfg'
        conf = BaseConfig(config_file)
        print(conf.GetLogLevel())
        print(conf.GetLogPath())
        print(conf.GetServicePort())
        conf.Set('name', 'vap_utils')
        conf.Set('name', 'test_tools', 'virt-agent')
        print(conf.Get('name'))
        print(conf.Get('name', 'virt-agent'))
    except exception.ConfigException as e:
        print(e)


def _do_test():
    _do_file_test()
    print("_do_password_test")
    _do_password_test()
    print("_do_config_test")
    _do_config_test()
    print("_do_global_config_test")
    _do_global_config_test()


_HOST_STR_DICT = {
        HostMode.UNKNOWN: 'unknown',
        HostMode.NORMAL: 'normal',
        HostMode.MAINTENANCE: 'maintenance',
        }


def HostModeToString(mode):
    return _HOST_STR_DICT.get(mode, 'unknown')


def StringToHostMode(mode):
    reverse = {v: k for k, v in _HOST_STR_DICT.items()}
    return reverse.get(mode, HostMode.UNKNOWN)


# main #
if __name__ == "__main__":
    _do_test()
