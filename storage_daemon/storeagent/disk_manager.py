#!/usr/bin/env python
# encoding: utf-8

import re
import enum
import pyudev
import logging
import os
import threading
import glob
import retrying
from retrying import retry

from util_base.sys_util import cat

from . import store_exception
from . import store_util
from . import multipath
from . import store_driver as driver


DEFAULT_LOGICAL_BLOCK_SIZE = 512


@enum.unique
class SCSIType(enum.Enum):
    LocalSCSI = 1
    ISCSI = 2
    FCSCSI = 3


@enum.unique
class DiskType(enum.Enum):
    LocalSCSI = 1
    ISCSI = 2
    FCSCSI = 3
    DM = 4


def Cat(file_path):
    try:
        if not os.path.isfile(file_path):
            raise store_exception.StoreDiskManagerSysfsError('file %s missing' % (file_path))
        return cat(file_path).strip()
    except OSError as e:
        logging.error('failed to cat %s' % (file_path))
        raise store_exception.StoreDiskManagerSysfsError('%s' % (e))
    except UnicodeDecodeError:
        logging.error('failed to cat %s' % (file_path))
        return ''


# Adapter Interface
class SCSIAdapter(object):
    '''
    Base class for all scsi device(local scsi, iscsi and fc)
    '''
    def __init__(self, _type):
        self._type = _type

    @property
    def adapter_type(self):
        return self._type

    def ListController(self):
        raise NotImplementedError('Method not implemented!')

    def ListTarget(self):
        raise NotImplementedError('Method not implemented!')

    def ListLun(self, target=None):
        raise NotImplementedError('Method not implemented!')

    def TargetLogin(self, target=None):
        raise NotImplementedError('Method not implemented!')

    def TargetLogout(self, target=None):
        raise NotImplementedError('Method not implemented!')


class LocalSCSIAdapter(SCSIAdapter):
    def __init__(self):
        super().__init__(SCSIType.LocalSCSI)


class ISCSIAdapter(SCSIAdapter):
    def __init__(self):
        super().__init__(SCSIType.ISCSI)


class FCAdapter(SCSIAdapter):
    def __init__(self):
        super().__init__(SCSIType.FCSCSI)


# scsi host interface
class SCSIHost(object):
    def __init__(self, _type, scsi_id):
        self._type = _type
        self._scsi_id = scsi_id
        self._session = {}
        self._luns = {}

    @property
    def Type(self):
        return self._type

    @property
    def ID(self):
        return self._scsi_id

    def AddSession(self, session):
        self._session[session.ID] = session

    @property
    def Session(self):
        return self._session

    def AddLun(self, disk):
        self._luns[disk.HCTL] = disk

    @property
    def Luns(self):
        return self._luns

    def ToString(self):
        ret_str = ''
        index = 0
        ret_str += ('Type: %s, SCSI_ID: %d, ' % (self._type, self._scsi_id))
        for session in self._session.values():
            ret_str += ('Session%d: {%s}, ' % (index, session.ToString()))
            index += 1
        index = 0
        for lun in self._luns.values():
            ret_str += ('Disk%d: {%s} ' % (index, lun.ToString()))
            index += 1

        return ret_str


class LocalSCSIHost(SCSIHost):
    def __init__(self, scsi_id):
        super().__init__(SCSIType.LocalSCSI, scsi_id)


class ISCSIHost(SCSIHost):
    '''
    scsi_id: int
    '''
    def __init__(self, scsi_id):
        super().__init__(SCSIType.ISCSI, scsi_id)


class FCHost(SCSIHost):
    def __init__(self, scsi_id):
        super().__init__(SCSIType.FCSCSI, scsi_id)


# scsi session interface
class SCSISession(object):
    '''
    session_id: int
    '''
    def __init__(self, _type, session_id):
        self._type = _type
        self._session_id = session_id
        self._luns = {}

    @property
    def Type(self):
        return self._type

    @property
    def ID(self):
        return self._session_id

    def AddLun(self, lun):
        self._luns[lun.HCTL] = lun

    @property
    def Luns(self):
        return self._luns

    def ToString(self):
        ret_str = ''
        index = 0
        ret_str += 'Session Type: %s, Session ID: %d, ' % (self._type, self._session_id)
        for lun in self._luns.values():
            ret_str += 'Lun%d: {%s}, ' % (index, lun.ToString())
            index += 1
        return ret_str


class ISCSISession(SCSISession):
    def __init__(self, session_id):
        super().__init__(SCSIType.ISCSI, session_id)
        self._host = {}

    @property
    def TargetName(self):
        try:
            target_name_file = '/sys/class/iscsi_session/session%d/targetname' % (self._session_id)
            return Cat(target_name_file).strip()
        except store_exception.StoreDiskManagerSysfsError as e:
            logging.info(e)
            return None

    @property
    def IPAddress(self):
        ip_addr_list = []
        for conns in glob.iglob('/sys/class/iscsi_session/session%d/device/connection*/iscsi_connection/connection*' %
                                (self._session_id), recursive=True):
            try:
                ip_addr_file = '%s/address' % (conns)
                port_file = '%s/port' % (conns)
                ip_addr = Cat(ip_addr_file).strip()
                port = Cat(port_file).strip()
                ip_addr_list.append('%s:%s' % (ip_addr, port))
            except store_exception.StoreDiskManagerSysfsError as e:
                logging.error(e)

        # there should be at least one connection
        if len(ip_addr_list) == 0:
            raise store_exception.StoreDiskManagerSysfsError('failed to find ip address for session%d' %
                                                             (self._session_id))
        return ip_addr_list

    @property
    def Host(self):
        return self._host

    def AddIScsiHost(self, host):
        self._host[host.ID] = host

    def CheckHCTL(self, hctl):
        for _hctl in glob.iglob('/sys/class/iscsi_session/session%d/device/target*/*' % (self._session_id),
                                recursive=True):
            if os.path.basename(_hctl).strip() == hctl:
                return True

        return False

    @property
    def State(self):
        return Cat('/sys/class/iscsi_session/session%d/state' % (self._session_id))

    def LoggedIn(self):
        return self.State == 'LOGGED_IN'

    def ToString(self):
        ret_str = ''
        if self.LoggedIn():
            ret_str += 'IP: %s, TargetName %s' % (self.IPAddress, self.TargetName)
        return '%s %s' % (super().ToString(), ret_str)


# disk interface
class Disk(object):
    '''
    disk of all types
    '''
    def __init__(self, sys_path,  _type):
        self._name = os.path.basename(sys_path).strip()
        self._sys_path = sys_path
        self._type = _type
        self._dev_path = '/dev/%s' % (self._name)

    @property
    def Name(self):
        return self._name

    @property
    def Type(self):
        return self._type

    @property
    def DevPath(self):
        return self._dev_path

    @property
    def LogicalBlockSize(self):
        size_file = '%s/queue/logical_block_size' % (self._sys_path)
        if os.path.isfile(size_file):
            try:
                return int(Cat(size_file).strip())
            except ValueError:
                logging.error('failed to get logical block size for "%s"' % (self._sys_path))
                return 0
        else:
            return DEFAULT_LOGICAL_BLOCK_SIZE

    @property
    def Size(self):
        try:
            return int(Cat('%s/size' % (self._sys_path)).strip()) * self.LogicalBlockSize
        except ValueError:
            logging.error('failed to get size for "%s"' % (self._sys_path))
            return 0

    @property
    def ReadOnly(self):
        try:
            return bool(int(Cat('%s/ro' % (self._sys_path)).strip()))
        except ValueError:
            # treat as readonly
            logging.error('failed to get ro for "%s"' % (self._sys_path))
            return True

    @property
    def SCSI_ID(self):
        try:
            return store_util.GetSCSIID('/dev/%s' % (self._name))
        except store_exception.StoreEnvoyException:
            logging.error('failed to get scsi_id for %s' % (self._name))
            return None

    def isAvailable(self):
        return self.SCSI_ID is not None

    def ToString(self):
        return 'Type: %s, Name: %s ,Size: %d, SCSI_ID %s, DevPath %s, %s ' % (self._type, self.Name, self.Size,
                                                                              self.SCSI_ID, self.DevPath,
                                                                              'ReadOnly' if self.ReadOnly
                                                                              else 'ReadWrite')


class LocalDisk(Disk):
    '''
    Local disk
    '''
    def __init__(self, sys_path, h, c, t, l, _type=DiskType.LocalSCSI):
        super().__init__(sys_path, _type)
        self._host_id = int(h)
        self._channel_id = int(c)
        self._target_id = int(t)
        self._lun_id = int(l)
        self._scsi_host = None
        # device mapper
        self._holder = None
        for dm in glob.iglob('%s/holders/*' % (sys_path), recursive=True):
            self._holder = os.path.basename(dm)

    @property
    def HCTL(self):
        return '%s:%s:%s:%s' % (self._host_id, self._channel_id, self._target_id, self._lun_id)

    @property
    def ScsiHost(self):
        return self._scsi_host

    @ScsiHost.setter
    def ScsiHost(self, scsi_host):
        self._scsi_host = scsi_host

    @property
    def Holders(self):
        return self._holder

    def ToString(self):
        ret_str = 'HCTL: %s, Holders: %s' % (self.HCTL, self.Holders)
        return '%s %s' % (super().ToString(), ret_str)


class DiskPartition(Disk):
    pass


class ISCSILun(LocalDisk):
    '''
    scsi disk
    '''
    def __init__(self, sys_path, h, c, t, l):
        super().__init__(sys_path, h, c, t, l, _type=DiskType.ISCSI)
        self._session = None

    @property
    def Session(self):
        return self._session

    @Session.setter
    def Session(self, session):
        self._session = session

    def ToString(self):
        ret_str = ''
        return '%s %s' % (super().ToString(), ret_str)


class DM(Disk):
    '''
    device mapper disk
    '''
    def __init__(self, sys_path):
        super().__init__(sys_path, DiskType.DM)

        # device mapper
        self._slaves = []
        for dm in glob.iglob('%s/slaves/*' % (sys_path), recursive=True):
            self._slaves.append(os.path.basename(dm))

        # modify dev_path to /dev/mapper
        for path in glob.iglob('/dev/mapper/*', recursive=True):
            if os.path.realpath(path) == self.DevPath:
                self._dev_path = path
                break

    @property
    def Slaves(self):
        return self._slaves

    def ToString(self):
        ret_str = 'Slaves: %s ' % (self.Slaves)
        return '%s %s' % (super().ToString(), ret_str)


def _UpdateTopology(dump=False):
    _SCSISessionProbe()
    _SCSIHostProbe()
    _DiskProbe()

    if dump:
        _DumpSCSIHost()
        _DumpSCSISession()
        _DumpSCSIDisk()


def _UDevDiskEvent(action, device):
    logging.info("%s %s" % (action, device))
    try:
        _UpdateTopology()
    except store_exception.StoreDiskManagerBase as e:
        logging.error(e)


def _StartUdevMonitor():
    context = pyudev.Context()
    monitor = pyudev.Monitor.from_netlink(context)
    monitor.filter_by(subsystem='block', device_type='disk')
    monitor.set_receive_buffer_size(128 * 1024 * 1024)
    observer = pyudev.MonitorObserver(monitor, _UDevDiskEvent)
    observer.start()


SCSI_SESSION_LIST = {}
SCSI_SESSION_LIST_LOCK = threading.Lock()


def _SCSISessionProbe():
    global SCSI_SESSION_LIST
    global SCSI_SESSION_LIST_LOCK
    scsi_session_list = {}

    for _session in glob.iglob('/sys/class/iscsi_session/*', recursive=True):
        session_name = os.path.basename(_session.strip())
        session_id = int(session_name[len('session'):])
        session = ISCSISession(session_id)
        scsi_session_list[session_name] = session
        logging.debug('%s %s' % (session.Type, session.ID))

    with SCSI_SESSION_LIST_LOCK:
        SCSI_SESSION_LIST = scsi_session_list


SCSI_HOST_LIST = {}
SCSI_HOST_LIST_LOCK = threading.Lock()


def _SCSIHostProbe():
    def _find_scsi_host(scsi_list, _type):
        search_path = {
            'iscsi': '/sys/class/iscsi_host/*',
            'fc': '/sys/class/fc_host/*',
            'scsi': '/sys/class/scsi_host/*',
        }

        scsi_host_type = {
            'iscsi': ISCSIHost,
            'fc': FCHost,
            'scsi': LocalSCSIHost,
        }

        if _type not in search_path.keys():
            return

        for _host in glob.iglob(search_path[_type], recursive=True):
            host_name = os.path.basename(_host.strip())
            if host_name in scsi_list.keys():
                continue
            host_id = int(host_name[len('host'):])
            host = scsi_host_type[_type](host_id)
            # parse iscsi session
            if _type == 'iscsi':
                for _session_name in glob.iglob('%s/device/session*' % (_host), recursive=True):
                    session_name = os.path.basename(_session_name)
                    logging.debug('host %s, session %s' % (_host, session_name))
                    with SCSI_SESSION_LIST_LOCK:
                        if session_name not in SCSI_SESSION_LIST:
                            raise store_exception.StoreDiskManagerBase('failed to find session %s' % (session_name))
                        session = SCSI_SESSION_LIST[session_name]
                        session.AddIScsiHost(host)
                        host.AddSession(session)
                        logging.debug('%s %s %s' % (session.Type, session.ID, session.TargetName))

            scsi_list[host_name] = host
            logging.debug('%s %s' % (host.Type, host.ID))

    global SCSI_HOST_LIST
    global SCSI_HOST_LIST_LOCK
    scsi_host_list = {}

    _find_scsi_host(scsi_host_list, 'iscsi')
    _find_scsi_host(scsi_host_list, 'fc')
    _find_scsi_host(scsi_host_list, 'scsi')

    with SCSI_HOST_LIST_LOCK:
        SCSI_HOST_LIST = scsi_host_list


SCSI_DISK_LIST = {}
SCSI_DISK_LIST_LOCK = threading.Lock()


def _DiskProbe():
    global SCSI_HOST_LIST
    global SCSI_HOST_LIST_LOCK
    global SCSI_SESSION_LIST
    global SCSI_SESSION_LIST_LOCK
    global SCSI_DISK_LIST
    global SCSI_DISK_LIST_LOCK

    disk_list = {}
    context = pyudev.Context()
    for dev in context.list_devices(subsystem='block', DEVTYPE='disk'):
        logging.debug(dev.sys_path)
        device_path = "%s/device" % (dev.sys_path)
        # for raw disk
        if os.path.islink(device_path):
            try:
                hctl = os.path.basename(os.path.realpath(device_path))
                # try to parse here. If invalid, Exception will raise
                host, channel, target, lun = hctl.split(':')
                logging.debug('%s:%s:%s:%s' % (host, channel, target, lun))
                logging.debug('%s %s' % (dev.properties['DEVNAME'], dev.properties['ID_PATH']))
                with SCSI_HOST_LIST_LOCK:
                    host_name = 'host%s' % (host)
                    if host_name not in SCSI_HOST_LIST:
                        raise store_exception.StoreDiskManagerBase('failed to find host for disk %s' %
                                                                   (device_path))
                    scsi_host = SCSI_HOST_LIST[host_name]
                    if scsi_host.Type == SCSIType.ISCSI:
                        # iscsi lun
                        disk = ISCSILun(dev.sys_path, host, channel, target, lun)
                        disk.ScsiHost = scsi_host
                        scsi_host.AddLun(disk)
                        for session in scsi_host.Session.values():
                            if session.LoggedIn():
                                logging.debug('%s %s' % (session.IPAddress, session.TargetName))
                            if session.CheckHCTL(disk.HCTL):
                                disk.Session = session
                                session.AddLun(disk)
                    if scsi_host.Type == SCSIType.LocalSCSI:
                        # local scsi lun
                        disk = LocalDisk(dev.sys_path, host, channel, target, lun)
                        scsi_host.AddLun(disk)

                disk_list[disk.Name] = disk
                continue

            except KeyError:
                logging.error('failed to get properties "%s" for "%s"' % (hctl, device_path))
            except ValueError:
                logging.error('failed to parse hctl "%s" for "%s"' % (hctl, device_path))
            except FileNotFoundError:
                logging.error('failed to find device file %s' % (device_path))

        # for device mapper disk
        dm_path = "%s/dm" % (dev.sys_path)
        if os.path.isdir(dm_path):
            logging.debug('device mapper disk')
            disk = DM(dev.sys_path)
            disk_list[disk.Name] = disk
            continue

    with SCSI_DISK_LIST_LOCK:
        SCSI_DISK_LIST = disk_list


def _DumpSCSISession():
    global SCSI_SESSION_LIST
    global SCSI_SESSION_LIST_LOCK

    with SCSI_SESSION_LIST_LOCK:
        for session in SCSI_SESSION_LIST.values():
            logging.info(session.ToString())


def _DumpSCSIHost():
    global SCSI_HOST_LIST
    global SCSI_HOST_LIST_LOCK

    with SCSI_HOST_LIST_LOCK:
        for scsi_host in SCSI_HOST_LIST.values():
            logging.info(scsi_host.ToString())


def _DumpSCSIDisk():
    global SCSI_DISK_LIST
    global SCSI_DISK_LIST_LOCK

    with SCSI_DISK_LIST_LOCK:
        for lun in SCSI_DISK_LIST.values():
            logging.info(lun.ToString())


def Init():
    _StartUdevMonitor()
    _UpdateTopology(True)


def GetIscsiTargetList(portal_address, portal_port):
    target_list = []
    targets = store_util.IscsiadmDiscovery('%s:%s' % (portal_address, portal_port))
    logging.debug(targets)
    for target in targets:
        target_name = target.strip()
        target_list.append(target_name)
    return target_list


def GetIscsiTargetListByPortalList(portal_list):
    target_list = []
    _portal_list = portal_list.split(',')

    for portal in _portal_list:
        portal_address = portal.split(':')[0]
        portal_port = portal.split(':')[1]
        _list = GetIscsiTargetList(portal_address, portal_port)
        if portal == _portal_list[0]:
            target_list = _list
        else:
            if target_list != _list:
                raise store_exception.StoreInvalidException(portal_list)

    return target_list


def _RetryingCheckFalse(res):
    return not res


# Wait 2^x * 1000 milliseconds between each retry, up to 10 seconds, then 10 seconds afterwards
# waiting time 2+4+8+10*2 = 34s
# return false will cause retry
@retry(stop_max_attempt_number=5, wait_exponential_multiplier=1000, wait_exponential_max=10000,
       retry_on_result=_RetryingCheckFalse)
def _WaitingIscsiSession(portal_address, portal_port, target_name):
    portal = '%s:%s' % (portal_address, portal_port)
    for _session in glob.iglob('/sys/class/iscsi_session/*', recursive=True):
        session_name = os.path.basename(_session.strip())
        session_id = int(session_name[len('session'):])
        session = ISCSISession(session_id)
        logging.debug('session: ip %s target name %s' % (session.IPAddress, session.TargetName))
        logging.debug('%s:%s %s' % (portal_address, portal_port, target_name))
        if (portal in session.IPAddress) and (target_name.strip() == session.TargetName.strip()):
            return session_id

    return False


# Wait 2000 milliseconds between each retry
# waiting time 2*15 = 30s
# return false will cause retry
@retry(stop_max_attempt_number=15, wait_fixed=2000, retry_on_result=_RetryingCheckFalse)
def _WaitingIscsiLunBySession(session_id):
    global SCSI_DISK_LIST
    global SCSI_DISK_LIST_LOCK
    global SCSI_SESSION_LIST
    global SCSI_SESSION_LIST_LOCK

    _UpdateTopology(True)

    disk_list = []
    with SCSI_SESSION_LIST_LOCK:
        for session in SCSI_SESSION_LIST.values():
            logging.info(session.ID)
            if session.ID == session_id:
                with SCSI_DISK_LIST_LOCK:
                    for lun in session.Luns.values():
                        item = {}
                        logging.debug(lun.ToString())
                        logging.debug('%s %s' % (lun.SCSI_ID, lun.Size))
                        item['SCSI_ID'] = lun.SCSI_ID
                        item['Size'] = lun.Size
                        item['loginstatus'] = store_util.LOGOUT
                        item['multipathstatus'] = multipath.GetMultipathStatus(lun.SCSI_ID)
                        item['speedupsupport'] = GetSpeedSuport(lun.Name)
                        disk_list.append(item)

    if disk_list is not []:
        return disk_list
    return False


def GetIscsiLunListByTarget(portal_list, target_name):
    global SCSI_DISK_LIST
    global SCSI_DISK_LIST_LOCK

    _portal_list = portal_list.split(',')
    lun_list = []
    info_list = []

    try:
        for portal in _portal_list:
            _portal_address = portal.split(':')[0]
            _portal_port = portal.split(':')[1]

            store_util.IscsiadmLogin('%s:%s' % (_portal_address, _portal_port), target_name)
            # waiting for session connected
            session_id = _WaitingIscsiSession(_portal_address, _portal_port, target_name)
            logging.info('session ID: %d' % (session_id))
            # get lun info for specified portal & target
            logging.info('begin to get lun info')
            lun_list = _WaitingIscsiLunBySession(session_id)
            logging.info('end to get lun info')

        for lun in lun_list:
            item = {}
            item['lun'] = lun
            _naa = lun['SCSI_ID']

            # default set naa to multipath.conf
            multipath.EnableMultipath(_naa)
            _path_list = multipath.GetPathList(_naa)

            item['mpath_list'] = _path_list

            info_list.append(item)

        logging.info('the lun info is %s' % info_list)

        return info_list
    except retrying.RetryError:
        logging.error('failed to get session info')
        return None
    finally:
        try:
            for portal in _portal_list:
                _portal_address = portal.split(':')[0]
                _portal_port = portal.split(':')[1]
                # check all datastore  xml and cfg , if datastore is active, don't logout
                if not driver.CheckPortalNeedLogout(portal, target_name):
                    store_util.IscsiadmLogout('%s:%s' % (_portal_address, _portal_port), target_name)
        except Exception as e:
            # ignore any exception here
            logging.error(e)


def GetIscsiLunList(portal_list, target_name):
    target_list = []
    lun_list = {}

    # if target name is not specified list all target on the same portal
    if target_name == '':
        logging.info('target is not specified')
        target_list = GetIscsiTargetListByPortalList(portal_list)
    else:
        target_list.append(target_name)

    for target in target_list:
        luns = GetIscsiLunListByTarget(portal_list, target)
        lun_list[target] = luns

    return lun_list


@enum.unique
class DiskUdevAttribute(enum.Enum):
    '''
    search disk all attribute,
    command :'udevadm info --query=all --name=/dev/sdX'
    '''
    ID_PATH = 1
    ID_TYPE = 2
    ID_FS_TYPE = 3
    ID_SERIAL = 4


def GetDeviceAttribute(attribute, device):
    '''
        device format need /dev/xxx
    '''
    ret = ''
    context = pyudev.Context()
    _device = pyudev.Device.from_device_file(context, device)
    if attribute == DiskUdevAttribute.ID_PATH:
        if 'ID_PATH' in _device:
            ret = _device.get('ID_PATH')

    if attribute == DiskUdevAttribute.ID_TYPE:
        if 'ID_TYPE' in _device:
            ret = _device.get('ID_TYPE')

    if attribute == DiskUdevAttribute.ID_FS_TYPE:
        if 'ID_FS_TYPE' in _device:
            ret = _device.get('ID_FS_TYPE')

    if attribute == DiskUdevAttribute.ID_SERIAL:
        if 'ID_SERIAL' in _device:
            ret = _device.get('ID_SERIAL')

    return ret


def GetIpByDevice(device):
    '''
    ISCSI device
    ID_PATH : ip-x.x.x.x:port-iscsi-target-lun-id
    '''
    ip = ''
    id_path = GetDeviceAttribute(DiskUdevAttribute.ID_PATH, device)
    # address is ip + port, e.g
    address = id_path.split('-')[1]
    ip = address.split(':')[0]

    return ip


def GetLunIdByDevice(device):
    '''
    ISCSI device
    '''
    lun_id = ''
    id_path = GetDeviceAttribute(DiskUdevAttribute.ID_PATH, device)
    lun_id = id_path.split('-')[-1]

    return lun_id


def GetInitiator():
    '''
    get /etc/iscsi/initiatorname.iscsi  initatorname
    '''
    initiatorname = ''

    try:
        with open(store_util.INITIATOR_CONF, 'r') as fd:
            lines = fd.readlines()
            for line in lines:
                if line.strip().split('=')[0] == 'InitiatorName':
                    initiatorname = line.strip().split('=')[1]

    except IOError:
        logging.error("failed to get initiatorname.")

    return initiatorname


def SetInitiator(initiatorname):
    '''
    set /etc/iscsi/initiatorname.iscsi initatorname
    '''
    _initiatorname = initiatorname + '\n'

    try:
        with open(store_util.INITIATOR_CONF, 'r') as r_fd:
            lines = r_fd.readlines()
            index = 0
            for line in lines:
                if line.strip().split('=')[0] == 'InitiatorName':
                    fields = lines[index].split('=')
                    fields[-1] = _initiatorname
                    lines[index] = '='.join(fields)
                    break
                index += 1

            with open(store_util.INITIATOR_CONF, 'w') as w_fd:
                w_fd.writelines(lines)
    except IOError:
        logging.error("failed to set initiatorname.")
        raise store_exception.StoreIOError("failed to set initiatorname")


def GetIpList():
    '''
    get ip list by session
    ip list is ip +port
    e.g [['x.x.x.x:port'],['x.x.x.x:port']]
    '''
    global SCSI_SESSION_LIST
    global SCSI_SESSION_LIST_LOCK

    ip_list = []
    _SCSISessionProbe()
    with SCSI_SESSION_LIST_LOCK:
        for session in SCSI_SESSION_LIST.values():
            ip_list.append(session.IPAddress)

        logging.info("GetIpList is %s" % ip_list)

    return ip_list


def GetAdapterList():
    '''
    LocalSCSI, ISCSI, FC

    '''
    global SCSI_HOST_LIST
    global SCSI_HOST_LIST_LOCK
    t_list = []
    _type_list = []
    adapter_list = []

    _UpdateTopology(True)

    with SCSI_HOST_LIST_LOCK:
        for host in SCSI_HOST_LIST.values():
            t_list.append(host.Type)

    _type_list = set(t_list)

    for adapter_type in _type_list:
        adapter = {}
        # LocalSCSI
        if adapter_type == SCSIType.LocalSCSI:
            adapter['name'] = store_util.LOCAL_SCSI
            adapter['model'] = store_util.LOCAL_SCSI_MODEL
            adapter['type'] = store_util.SCSI
            adapter['status'] = store_util.ACTIVE
            adapter['identifier'] = ''

            adapter_list.append(adapter)

        # FC

    # on first start, no session login, we can not get iscsiadapter, so front can not
    # imput ip to get iscsi lun info. change to check INITIATOR_CONF to init iscsiadapter.
    if os.path.exists(store_util.INITIATOR_CONF):
        adapter = {}
        adapter['name'] = store_util.OPEN_ISCSI
        adapter['model'] = store_util.ISCSI_MODEL
        adapter['type'] = store_util.ISCSI
        adapter['status'] = store_util.ACTIVE
        adapter['identifier'] = GetInitiator()

        adapter_list.append(adapter)

    logging.info("adapter_list is %s" % adapter_list)

    return adapter_list


def GetLocalSCSIResources():
    _resources = []
    global SCSI_HOST_LIST
    global SCSI_HOST_LIST_LOCK

    _UpdateTopology(True)

    with SCSI_HOST_LIST_LOCK:
        for host in SCSI_HOST_LIST.values():
            if host.Type == SCSIType.LocalSCSI:
                for luns in host.Luns.values():
                    resource = {}
                    resource['SCSI_ID'] = luns.SCSI_ID
                    resource['device'] = luns.Name
                    resource['Size'] = luns.Size
                    resource['loginstatus'] = store_util.LOGIN
                    resource['multipathstatus'] = store_util.DISABLE
                    resource['speedupsupport'] = ''

                    _resources.append(resource)

    logging.info("_resources is %s" % _resources)
    return _resources


def GetOpenISCSIResources():
    _resources = []
    _list = []
    global SCSI_HOST_LIST
    global SCSI_HOST_LIST_LOCK

    _UpdateTopology(True)

    with SCSI_HOST_LIST_LOCK:
        for host in SCSI_HOST_LIST.values():
            if host.Type == SCSIType.ISCSI:
                for luns in host.Luns.values():
                    resource = {}
                    resource['SCSI_ID'] = luns.SCSI_ID
                    resource['Size'] = luns.Size
                    resource['loginstatus'] = store_util.LOGIN
                    resource['multipathstatus'] = multipath.GetMultipathStatus(luns.SCSI_ID)
                    resource['speedupsupport'] = GetSpeedSuport(luns.Name)

                    _resources.append(resource)

    _list = store_util.DictListDuplicateRemoval(_resources)

    logging.info("_resources is %s " % _list)
    return _list


def GetFCResources():
    pass


def CheckXcopy(device):
    '''
    check device xcopy  by sg_inq
    'sg_inq  /dev/sdX | grep 3PC=1'
    '''
    ret = store_util.UNSUPPORT
    command = '%s %s' % (store_util.SG_INQ, device)

    std_out, std_err = store_util.StoreCmdRun(command)

    _string = std_out.strip()

    ret_3PC = re.search(r'3PC=\d+', _string).group().split('=')[1]

    if ret_3PC == '1':
        ret = store_util.SUPPORT

    return ret


def CheckWriteSame(device):
    '''
    check device Write same
    'sg_vpd -p lbpv /dev/sdX | grep 'Write same' 1 '
    '''
    ret = store_util.UNSUPPORT
    command_ret = '0'
    command = '%s -p lbpv %s' % (store_util.SG_VPD, device)

    std_out, std_err = store_util.StoreCmdRun(command)

    _string = std_out.split('\n')
    for _str in _string:
        if re.search(r'Write same', _str):
            command_ret = _str[-1]
            break

    if command_ret == '1':
        ret = store_util.SUPPORT

    return ret


def CheckUnmap(device):
    '''
    check device Unmap
    'sg_vpd -p lbpv /dev/sdX | grep 'Unmap command supported''
    '''
    ret = store_util.UNSUPPORT
    command_ret = '0'
    command = '%s -p lbpv %s' % (store_util.SG_VPD, device)

    std_out, std_err = store_util.StoreCmdRun(command)

    _string = std_out.split('\n')
    for _str in _string:
        if re.search(r'Unmap command supported', _str):
            command_ret = _str[-1]
            break

    if command_ret == '1':
        ret = store_util.SUPPORT

    return ret


def CheckATS(device):
    '''
    check device ats
    'sg_vpd -p bl /dev/sdX | grep 'compare and write' awk '{print $(NF-1)}''
    '''
    ret = store_util.UNSUPPORT
    command_ret = '0'
    command = '%s -p bl %s' % (store_util.SG_VPD, device)

    std_out, std_err = store_util.StoreCmdRun(command)

    _string = std_out.split('\n')
    for _str in _string:
        if re.search(r'compare and write', _str):
            command_ret = _str.split()[-2]
            break

    if command_ret != '0':
        ret = store_util.SUPPORT

    return ret


def GetSpeedSuport(device):
    '''
    Check device xcopy, write_same, unmap and ATS
    '''
    _speedSupport = {}

    _device = '/dev/' + device

    _speedSupport['xcopy'] = CheckXcopy(_device)
    _speedSupport['write_same'] = CheckWriteSame(_device)
    _speedSupport['unmap'] = CheckUnmap(_device)
    _speedSupport['ATS'] = CheckATS(_device)

    return _speedSupport


def GetAdapterReSourcesByName(adaptername):
    '''
    get adapter ReSources by adaptername
    '''

    resources = []

    # get local scsi resources
    if adaptername == store_util.LOCAL_SCSI:
        resources = GetLocalSCSIResources()

    # get Open_iscsi resources
    if adaptername == store_util.OPEN_ISCSI:
        resources = GetOpenISCSIResources()

    # get FC resources

    logging.info("Get %s resources is %s" % (adaptername, resources))

    return resources


def GetUsefulDeviceByLocalReSource():
    '''
    get useful device to create local datastore.
    '''
    res_list = []
    disk_list = []

    res_list = GetLocalSCSIResources()

    for res in res_list:
        item = {}
        _device = '/dev/' + res['device']
        _id_type = GetDeviceAttribute(DiskUdevAttribute.ID_TYPE, _device)
        # check if cdrom
        if _id_type == 'cd':
            continue
        _fs_type = GetDeviceAttribute(DiskUdevAttribute.ID_FS_TYPE, _device)
        item['naa'] = res['SCSI_ID']
        item['fstype'] = _fs_type

        disk_list.append(item)

    logging.info('Get useful device to local datastore. %s' % disk_list)

    return disk_list
