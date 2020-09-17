#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import envoy
import logging
import threading

from functools import reduce

from util_base.sys_util import BaseConfig
from storeagent.store_exception import StoreException
from . import store_exception
from storeagent import store_util_pb2 as util_pb2
from util_base import exception as util_exception

# global value
ACTIVE = 'active'
INACTIVE = 'inactive'
DEFAULT_MULTIPATH_CONF = 'default_multipath.conf'
DEFAULT_AGENT_CONF = 'storeagent.cfg'
DEFAULT_SCHEM_JSON = 'schema.json'
DATASTORE_CONF = 'datastore.cfg'
MULTIPATH_CONF = '/etc/multipath.conf'
INITIATOR_CONF = '/etc/iscsi/initiatorname.iscsi'
BLOCK_PATH = '/dev/disk/by-path'
ISCSI_MODEL = 'ISCSI Software Adapter'
LOCAL_SCSI_MODEL = 'Local SCSI'
LOCAL_SCSI = 'Local-SCSI'
OPEN_ISCSI = 'Open-ISCSI'
SCSI = 'SCSI'
ISCSI = 'ISCSI'
SUPPORT = '1'
UNSUPPORT = '0'
ENABLE = 'enable'
DISABLE = 'disable'
LOGIN = 'login'
LOGOUT = 'logout'
LOCALPOOL = 'localpool'
STATE = 'state'
N_TITLE = 'n_title'
DEVICE = 'device'
AUTO_MOUNT = 'auto_mount'
TRUE = 'True'
FALSE = 'False'

# store path
STORE_BASE_PATH = '/opt/storeagent'
STORE_MOUNT_PATH = '/data'
STORE_XML_PATH = '/opt/storeagent/xml'
STORE_JSON_PATH = '/opt/storeagent/json'
STORE_CONF_PATH = '/opt/storeagent/conf'
CONF_PATH = '/etc/vap'
LOCALPOOL_MOUNTPOINT = '/data/localpool'

# cmd
MKFS_EXT4 = '/usr/sbin/mkfs.ext4'
LSBLK = '/usr/bin/lsblk'
DD = '/usr/bin/dd'
MOUNT = '/usr/bin/mount'
UMOUNT = '/usr/bin/umount'
DF = '/usr/bin/df'
LSOF = '/usr/bin/lsof'
QEMU_IMG = '/usr/bin/qemu-img'
SCSI_ID = '/usr/lib/udev/scsi_id'
ISCSIADM = '/usr/sbin/iscsiadm'
MULTIPATHD = '/usr/sbin/multipathd'
SG_INQ = '/usr/bin/sg_inq'
SG_VPD = '/usr/bin/sg_vpd'


def StoreCmdRun(cmd):
    ret = 0
    try:
        cmd_run = envoy.run(cmd)
        if cmd_run.status_code != 0:
            logging.error('%s [%s]' % (cmd, cmd_run.std_err))
            ret = 1
        return (cmd_run.std_out, cmd_run.std_err)
    except Exception:
        ret = 1
        logging.error('run %s error' % (cmd))
    finally:
        if ret:
            raise store_exception.StoreEnvoyException('run %s error' % (cmd))


def CheckBusy(filepath):
    """ check the filepath is busy
    :param request : filepath
    :returns : Ture : busy
               False : not busy
    """
    c_busy = envoy.run('%s %s' % (LSOF, filepath))
    if c_busy.status_code == 0:
        return True
    elif c_busy.status_code == 1:
        return False
    else:
        raise store_exception.StoreEnvoyException(LSOF)


def QemuImg(comand):
    """ qemu-img command
    :param : request : command  (qemu-img --help , or man qemu-img)
    :returns : QemuImgReply {
                   string std_out = 1;
                   errno : util_pb2.STORE_OK run success
               }

    """
    ret = util_pb2.QemuImgReply()

    qemu_img = envoy.run('%s %s' % (QEMU_IMG, comand))
    ret.std_out = qemu_img.std_out.strip()
    if qemu_img.status_code == 0:
        ret.errno = util_pb2.STORE_OK
    else:
        raise store_exception.StoreQemuImgCommandException(ret)

    return ret


def GetSCSIID(dev):
    global SCSI_ID
    scsi_id = ''

    # if the device is lvm , such as  /dev/mapper/centos-root -> dm-0, has no scsi_id,
    # but envoy return status_code 1,
    run_ret = envoy.run('%s -g -u -d %s' % (SCSI_ID, dev))
    if run_ret.status_code == 0 or run_ret.status_code == 1:
        scsi_id = run_ret.std_out.strip()
    else:
        raise store_exception.StoreEnvoyException('scsi_id failed')

    return scsi_id


def IscsiadmDiscovery(portal):
    global ISCSIADM

    target_list = []
    std_out, std_err = StoreCmdRun('%s --mode discovery -t sendtargets --portal %s' % (ISCSIADM, portal))
    for _target in std_out.strip().split('\n'):
        logging.debug(_target)
        try:
            target_portal = _target.split()[0]
            target_name = _target.split()[1]
            if target_portal.startswith(portal):
                target_list.append(target_name)
            IscsiadmSetAutoLogin(portal, target_name)
        except IndexError:
            logging.error('target info: %s' % (_target))
            return []
    return target_list


def IscsiadmLogin(portal, target):
    global ISCSIADM
    global UDEVADM

    std_out, std_err = StoreCmdRun('%s --mode node --portal %s -T %s --login' % (ISCSIADM, portal, target))

    return std_out.strip()


def IscsiadmLogout(portal, target):
    global ISCSIADM

    std_out, std_err = StoreCmdRun('%s --mode node --portal %s -T %s --logout' % (ISCSIADM, portal, target))

    return std_out.strip()


def IscsiadmSetAutoLogin(portal, target, auto_login=False):
    global ISCSIADM

    std_out, std_err = StoreCmdRun('%s --mode node --portal %s -T %s --op update -n node.startup -v %s' %
                                   (ISCSIADM, portal, target, 'automatic' if auto_login else 'manual'))

    return std_out.strip()


class StoreAgentConfig(BaseConfig):

    def GetMaxWorker(self):
        size = self.Get('max_worker')
        if size is None:
            # set 5 as default
            max_worker = 5
            self.Set('max_worker', str(max_worker))
        else:
            max_worker = int(size)
        return max_worker

    def GetClientLogPath(self):
        client_log_path = self.Get('client_log_path')
        if client_log_path is None:
            raise StoreException('can not find log path definition in %s' % self.__file_path)
        else:
            if not os.path.exists(os.path.dirname(client_log_path)):
                raise StoreException('invalid client log path %s' % client_log_path)
            return client_log_path

    def GetClientLogLevel(self):
        LOG_LEVEL = ['debug', 'info', 'warning', 'error', 'critical']
        client_log_level = self.Get('client_log_level')
        if client_log_level is None:
            # if not set,  set 'info' as default
            default_client_log_level = 'info'
            self.Set('client_log_level', default_client_log_level)
            return default_client_log_level
        else:
            ret = client_log_level.strip().lower()
            if ret not in LOG_LEVEL:
                raise StoreException('invalid log level %s' % client_log_level)
            return ret


def DictListDuplicateRemoval(dictlist):
    '''
    dict list duplicate removal
    '''
    _dictlist = []

    def run_function(x, y):
        if y in x:
            ret = x
        else:
            ret = x + [y]

        return ret

    _dictlist = reduce(run_function, [[], ] + dictlist)

    return _dictlist


class DataStoreConfig(BaseConfig):

    def __init__(self, file_path):
        self.__lock = threading.Lock()
        super(DataStoreConfig, self).__init__(file_path)

    @property
    def lock(self):
        return self.__lock

    def GetValue(self, option_name, datastore):
        '''
            get datastore.cfg datastore option_name value
        '''
        _value = self.Get(option_name, datastore)
        return _value

    def SetValue(self, option_name, value, datastore):
        '''
            set datastore.cfg datastore option_name value
        '''
        try:
            self.Set(option_name, value, datastore)
        except util_exception.ConfigException:
            raise StoreException.StoreDataConfigException('Set %s %s %s failed.' % (datastore, option_name, value))

    def DeleteStoreOption(self, option_name, datastore):
        '''
            delete datastore.cfg datastore option_name value
        '''
        try:
            self.DeleteOption(option_name, datastore)
        except util_exception.ConfigException:
            raise StoreException.StoreDataConfigException('Delete %s %s failed.' % (datastore, option_name))

    def DeleteStore(self, datastore):
        '''
            delete datastore.cfg datastore
        '''
        try:
            self.DeleteSection(datastore)
        except util_exception.ConfigException:
            raise StoreException.StoreDataConfigException('Detete %s cfg failed.' % datastore)

    def GetAllStore(self):
        '''
            get all datastore.cfg datastore name
        '''
        store_list = []
        try:
            store_list = self.GetALLSection()
            return store_list
        except util_exception.ConfigException:
            raise StoreException.StoreDataConfigException('get datastore.cfg failed')
