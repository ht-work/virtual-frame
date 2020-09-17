#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import textwrap
import threading
import logging
import traceback
import envoy
import pyudev
import psutil
import uuid

from lxml import etree

from storeagent import store_exception
from storeagent import store_util as util
from storeagent import pools_pb2
from storeagent import store_util_pb2 as util_pb2
from storeagent import disk_manager
from storeagent import storeagentd


class DataStore(object):
    xml_template = textwrap.dedent("""
    <datastore type='%(type)s'>
        <name>%(name)s</name>
        <uuid>%(uuid)s</uuid>
        <naa>%(naa)s</naa>
        <portal>%(portal)s</portal>
        <target>%(target)s</target>
        <mountpoint>%(mountpoint)s</mountpoint>
    </datastore>
    """.strip())

    def __init__(self, uuid):
        self.__name = None
        self.__uuid = uuid
        self.__lock = threading.Lock()

    @property
    def lock(self):
        return self.__lock

    @property
    def name(self):
        return self.__name

    @name.setter
    def name(self, name):
        self.__name = name

    @property
    def uuid(self):
        return self.__uuid

    @uuid.setter
    def uuid(self, uuid):
        assert isinstance(uuid, str)
        self.__uuid = uuid


class DataStoreList(object):
    def __init__(self):
        self.__datastore_list = {}
        self.__lock = threading.Lock()

    @property
    def lock(self):
        return self.__lock

    def append(self, datastore):
        assert isinstance(datastore, DataStore)

        if not self.__lock.locked():
            raise store_exception.StoreLockException('the caller must hold DataStoreList lock')

        with datastore.lock:
            if datastore.uuid in self.__datastore_list:
                raise store_exception.StoreInvalidException('datastore(%s) already in datastore list' % datastore.uuid)
            else:
                self.__datastore_list[datastore.uuid] = datastore

    def get(self, uuid_str):
        if not self.__lock.locked():
            raise store_exception.StoreLockException('the caller must hold DataStoreList lock')

        if not (uuid_str in self.__datastore_list):
            raise store_exception.StoreInvalidException('invalid datastore uuid')

        return self.__datastore_list[uuid_str]

    def pop(self, uuid_str):
        if not self.__lock.locked():
            raise store_exception.StoreLockException('the caller must hold DataStoreList lock')

        if not (uuid_str in self.__datastore_list):
            raise store_exception.StoreInvalidException('invalid datastore uuid')

        return self.__datastore_list.pop(uuid_str)

    def exists(self, uuid_str):
        if not self.__lock.locked():
            raise store_exception.StoreLockException('the caller must hold DataStoreList lock')

        if not (uuid_str in self.__datastore_list):
            return False

        return True

    def __iter__(self):
        if not self.__lock.locked():
            raise store_exception.StoreLockException('the caller must hold DataStoreList lock')

        self.it = iter(self.__datastore_list)
        return self

    def __next__(self):
        if not self.__lock.locked():
            raise store_exception.StoreLockException('the caller must hold DataStoreList lock')

        return self.__datastore_list[next(self.it)]


DATASTORE_LIST = DataStoreList()


def CreateStoreCfg(xml_str, name):
    """ create Datastore conf xml
    :param request : xml_str
                     name the Datastore name
    :return : True create success
              False create fail
    """
    try:
        el = etree.fromstring(xml_str)
        tree = etree.ElementTree(el)
        tree.write('%s/%s.xml' % (util.STORE_XML_PATH, name), pretty_print=True,
                   xml_declaration=True, encoding='utf-8')
        return True
    except store_exception.StoreXmlException:
        logging.critical(traceback.format_exc())
        return False


def ReadXml(xml_file):
    """ read xml file
    :param request : xml file path
    :returns : etree._ElementTree
    """
    try:
        return etree.parse(xml_file)
    except OSError:
        logging.error(traceback.format_exc())
        raise store_exception.StoreOsErrorException(xml_file)
    except etree.LxmlError:
        logging.critical(traceback.format_exc())
        raise store_exception.StoreXmlException(xml_file)


def GetXmlElementByXpath(xml_tree, xpath):
    """ get Element from ElementTree by xpath
    :param request : xml tree
    :returns : etree._Element
    """
    try:
        return xml_tree.find(xpath)
    except OSError:
        logging.error(traceback.format_exc())
        raise store_exception.StoreOsErrorException(xml_tree)
    except etree.LxmlError:
        logging.critical(traceback.format_exc())
        raise store_exception.StoreXmlException(xml_tree)


def GetDeviceSizeInfo(device):
    """ get device size info
    :param request :device
    :returns : DataStoreSizeInfo {
                   totalsize
                   allocatedsize
                   availablesize
               }
    """
    SizeInfo = pools_pb2.DataStoreSizeInfo()

    total = envoy.run('%s %s  --output=size' % (util.DF, device))
    if total.status_code == 0:
        SizeInfo.totalsize = total.std_out.strip().split('\n')[1].lstrip()
    else:
        raise store_exception.StoreEnvoyException(total)

    allocation = envoy.run('%s %s --output=used' % (util.DF, device))
    if allocation.status_code == 0:
        SizeInfo.allocatedsize = allocation.std_out.strip().split('\n')[1].lstrip()
    else:
        raise store_exception.StoreEnvoyException(allocation)

    avail = envoy.run('%s %s  --output=avail' % (util.DF, device))
    if avail.status_code == 0:
        SizeInfo.availablesize = avail.std_out.strip().split('\n')[1].lstrip()
    else:
        raise store_exception.StoreEnvoyException(avail)

    return SizeInfo


def GetDeviceSizeInfoByName(store_name):
    """ get device size info by store_name
    :param request : store_name
    :returns : DataStoreSizeInfo {
                   totalsize
                   allocatedsize
                   availablesize
               }
    """
    SizeInfo = pools_pb2.DataStoreSizeInfo()
    s_name = store_name

    xml_file = ('%s/%s.xml' % (util.STORE_XML_PATH, s_name))
    xml_tree = ReadXml(xml_file)
    s_naa = GetXmlElementByXpath(xml_tree, 'naa').text
    s_device = GetDeviceByNaa(s_naa)
    SizeInfo = GetDeviceSizeInfo(s_device)

    return SizeInfo


def GetDataStoreInfoByName(store_name):
    '''
    get DataStore info
    request : store_name
    return:  pools_pb2. DataStoreInfo()
    '''
    _store_info = pools_pb2.DataStoreInfo()
    _store_name = store_name
    _size_info = pools_pb2.DataStoreSizeInfo()

    # check xml conf
    xml_file = ('%s/%s.xml' % (util.STORE_XML_PATH, _store_name))
    if os.path.exists(xml_file):
        logging.info('xml_file is %s.' % xml_file)
    else:
        raise store_exception.StoreInvalidException(_store_name)

    # read xml
    xml_tree = ReadXml(xml_file)
    if isinstance(xml_tree, etree._ElementTree):
        # get info
        _s_type = GetXmlElementByXpath(xml_tree, '[@type]').get('type')
        if not _s_type:
            raise store_exception.StoreXmlException(xml_tree)

        _s_naa = GetXmlElementByXpath(xml_tree, 'naa').text
        # block pool naa is none.
        if int(_s_type) != pools_pb2.ISCSI_BLOCK and int(_s_type) != pools_pb2.FC_BLOCK:
            if not _s_naa:
                raise store_exception.StoreXmlException(xml_tree)

        _s_portal = GetXmlElementByXpath(xml_tree, 'portal').text
        _s_target = GetXmlElementByXpath(xml_tree, 'target').text

        _s_mountpoint = GetXmlElementByXpath(xml_tree, 'mountpoint').text
        if not _s_mountpoint:
            raise store_exception.StoreXmlException(xml_tree)
    else:
        raise store_exception.StoreXmlException('read xml fail')

    #  get size info
    if int(_s_type) != pools_pb2.ISCSI_BLOCK and int(_s_type) != pools_pb2.FC_BLOCK:
        if store_name == util.LOCALPOOL:
            with storeagentd.DATASTORE_CONF.lock:
                _s_device = storeagentd.DATASTORE_CONF.GetValue(util.DEVICE, store_name)
        else:
            _s_device = GetDeviceByNaa(_s_naa)

        _size_info = GetDeviceSizeInfo(_s_device)
    else:
        # get block pool size
        _lun_list = []
        _lun_list = disk_manager.GetIscsiLunListByTarget(_s_portal, _s_target)
        for _lun in _lun_list:
            _size = 0
            _size = _lun['Size']
            _size_info.totalsize += _size
            _size_info.allocatedsize += _size
        _size_info.availablesize = 0

    # get state
    with storeagentd.DATASTORE_CONF.lock:
        _s_state = storeagentd.DATASTORE_CONF.GetValue(util.STATE, store_name)
        _s_title = storeagentd.DATASTORE_CONF.GetValue(util.N_TITLE, store_name)

    _store_info.name = _store_name
    _store_info.p_type = int(_s_type)
    _store_info.naa = _s_naa
    _store_info.portal = _s_portal
    _store_info.target = _s_target
    _store_info.totalsize = _size_info.totalsize
    _store_info.allocatedsize = _size_info.allocatedsize
    _store_info.availablesize = _size_info.availablesize
    _store_info.state = str(_s_state)
    _store_info.n_title = str(_s_title)
    _store_info.mountpoint = _s_mountpoint

    return _store_info


def StringToInt(string):
    """ string   to int
    :param request : string
    :returns : int default (KB)
    """
    ret = ''

    num_re = re.match(r'\d+', string)
    if None is num_re:
        logging.error('invalid string %s' % string)
        raise store_exception.StoreInvalidException(num_re)

    num = int(num_re.group())

    unit_re = re.search(r'[K,M,G,T]', string)
    if None is unit_re:
        unit = ''
    else:
        unit = unit_re.group()

    if unit == '':
        ret = num//1024

    if unit == 'K':
        ret = num

    if unit == 'M':
        ret = num*1024

    if unit == 'G':
        ret = num*1024*1024

    if unit == 'T':
        ret = num*1024*1024*1024

    return ret


def QemuCreateVol(json_data):
    """ create a vol with json_data
    :param request : json_data
    :returns : util_pb2.STORE_OK
    """
    s_sizeinfo = pools_pb2.DataStoreSizeInfo()
    q_img_ret = util_pb2.QemuImgReply()

    # load json_data
    j_data = {}
    j_data = json_data
    logging.info('the json_data is %s' % j_data)

    p_name = j_data['p_name']
    vol_path = j_data['vol_path']
    vol_type = j_data['vol_type']
    vol_size = int(j_data['vol_size'])
    preallocation = j_data['preallocation']

    # check filepath
    filepath = ('%s/%s/%s' % (util.STORE_MOUNT_PATH, p_name, vol_path))
    if os.path.exists(filepath):
        logging.error('the %s is already exists' % filepath)
        raise store_exception.StoreInvalidException(filepath)

    # check size
    s_sizeinfo = GetDeviceSizeInfoByName(p_name)
    avail_size = StringToInt(s_sizeinfo.availablesize)
    if avail_size < vol_size:
        logging.error('the DataStore not enough space. avail_size%(KB) vol_size%s(KB)'
                      % (avail_size, vol_size))
        raise store_exception.StoreInvalidException(vol_size)

    # command
    if vol_type == 'raw':
        command = ('create -q -f raw -o preallocation=%s %s %sK' %
                   (preallocation, filepath, vol_size))

    if vol_type == 'qcow2':
        compat = j_data['compat']
        backing_file = j_data['backing_file']
        backing_fmt = j_data['backing_fmt']
        encryption = j_data['encryption']
        cluster_size = int(j_data['cluster_size'])
        lazy_refcounts = j_data['lazy_refcounts']

        # check cluster_size(512 -- 2M)
        if cluster_size < 0.5 or cluster_size > 4096:
            logging.error('cluster_size is %s.' % cluster_size)
            raise store_exception.StoreInvalidException(cluster_size)

        if backing_file == 'null':
            if not backing_fmt == 'null':
                raise store_exception.StoreInvalidException(backing_fmt)
            command = ('create -q -f qcow2'
                       ' -o compat=%s'
                       ' -o cluster_size=%dK'
                       ' -o encryption=%s'
                       ' -o lazy_refcounts=%s'
                       ' -o preallocation=%s %s %s' % (compat,
                                                       cluster_size,
                                                       encryption,
                                                       lazy_refcounts,
                                                       preallocation,
                                                       filepath,
                                                       vol_size))
        else:
            if not os.path.exists(backing_file):
                raise store_exception.StoreInvalidException(backing_file)

            # check backing_file busy
            if util.CheckBusy(backing_file):
                raise store_exception.StoreFileBusyException(backing_file)

            command = ('create -q -f qcow2'
                       ' -o compat=%s'
                       ' -o backing_file=%s'
                       ' -o backing_fmt=%s'
                       ' -o cluster_size=%dK'
                       ' -o encryption=%s'
                       ' -o lazy_refcounts=%s'
                       ' -o preallocation=%s %s %s' % (compat,
                                                       backing_file,
                                                       backing_fmt,
                                                       cluster_size,
                                                       encryption,
                                                       lazy_refcounts,
                                                       preallocation,
                                                       filepath,
                                                       vol_size))

    # create
    logging.info('command is %s.' % command)
    q_img_ret = util.QemuImg(command)

    return q_img_ret.errno


def QemuCreateFullVol(opaque, job=None):
    """ create full vol
    """
    json_data = opaque['json_data']

    QemuCreateVol(json_data)


def GetLocalStoreSizeInfo():
    '''
    get LocalStore size info.
    return : totalsize  KB
             usedsize   KB
    '''
    _list_device = []
    _s_totalsize = 0
    _s_usedsize = 0

    _list_device = disk_manager.GetLocalSCSIResources()

    for item in _list_device:
        used = 0
        total = 0
        device = item['device']

        # device is cdrom skip
        device_type = disk_manager.GetDeviceAttribute(disk_manager.DiskUdevAttribute.ID_TYPE, ('/dev/' + device))
        if device_type == 'cd':
            continue

        # On virtual machine, _list_device  include system disk, need skip.
        std_out, std_err = util.StoreCmdRun('%s %s -o TYPE' % (util.LSBLK, ('/dev/' + device)))
        if re.search(r'part', std_out.strip()):
            continue

        std_out2, std_err2 = util.StoreCmdRun('%s %s --output=used' % (util.DF, ('/dev/' + device)))
        used = int(std_out2.strip().split('\n')[1].lstrip())
        total = int(item['Size'])

        _s_totalsize += total
        _s_usedsize += used

    _s_totalsize = int(_s_totalsize)/1024
    logging.info("GetLocalStoreSizeInfo  totalsize is %s, usedsize is %s" % (_s_totalsize, _s_usedsize))

    return str(_s_totalsize), str(_s_usedsize)


def GetDataStoreFileList(store_name):
    '''
    get DataStore file list
    '''
    _file_list = []

    xml_file = ('%s/%s.xml' % (util.STORE_XML_PATH, store_name))
    xml_tree = ReadXml(xml_file)
    _s_mountpoint = GetXmlElementByXpath(xml_tree, 'mountpoint').text

    _file_list = os.listdir(_s_mountpoint)

    return _file_list


def GetDataStoreNameList():
    '''
    get all DataStore name
    '''

    _name_list = os.listdir(util.STORE_MOUNT_PATH)

    return _name_list


def CheckPortalNeedLogout(portal, target_name):
    '''
        check one portal(x.x.x.x:port) if need logout. if one pool used the portal target_name, we don't logout.
        return True : logout
               False : not logout
    '''
    ret = False

    _xml_list = os.listdir(util.STORE_XML_PATH)
    for _xml in _xml_list:
        xmlfile = ''
        xmlfile = ('%s/%s' % (util.STORE_XML_PATH, _xml))
        _xml_tree = ReadXml(xmlfile)
        if isinstance(_xml_tree, etree._ElementTree):
            _type = GetXmlElementByXpath(_xml_tree, '[@type]').get('type')
            if int(_type) == pools_pb2.LOCAL:
                continue
            _str_portal = GetXmlElementByXpath(_xml_tree, 'portal').text
            _target = GetXmlElementByXpath(_xml_tree, 'target').text
            _portal_list = _str_portal.split(',')
            for _portal in _portal_list:
                if _portal == portal and _target == target_name:
                    ret = True
                    break
            if ret:
                break

    return ret


def GetMountpoint(device):
    '''
        get the device mountpoint, if not mountpoint, return null
    '''
    mountpoint = ''
    disks = psutil.disk_partitions()

    for disk in disks:
        if disk.device == device:
            mountpoint = disk.mountpoint
            break

    return mountpoint


def GetDeviceByNaa(naa):
    '''
        get device by naa,  localpool used GetDeviceByMountPoint, or datastore.cfg
    '''
    device = ''

    context = pyudev.Context()
    for dev in context.list_devices(subsystem='block', DEVTYPE='disk'):
        _naa = dev.get('ID_SERIAL')
        if _naa == naa:
            device = dev.get('DEVNAME')
            break

    return device


def CreateLocalStore(naa, name, n_title):
    '''
        create local Datastore
    '''
    global DATASTORE_LIST

    store_uuid = str(uuid.uuid3(uuid.NAMESPACE_DNS, '%s' % name))
    with DATASTORE_LIST.lock:
        if DATASTORE_LIST.exists(store_uuid):
            logging.error('the name %s is already uesd.' % name)
            raise store_exception.StoreInvalidException(name)
    _store_node = DataStore(store_uuid)

    # check xml
    xmlfile = ('%s/%s.xml' % (util.STORE_XML_PATH, name))
    if os.path.exists(xmlfile):
        raise store_exception.StoreInvalidException(xmlfile)

    # check device
    if name != util.LOCALPOOL:
        device = GetDeviceByNaa(naa)
    else:
        with storeagentd.DATASTORE_CONF.lock:
            device = storeagentd.DATASTORE_CONF.GetValue(util.DEVICE, util.LOCALPOOL)

    if not os.path.exists(device):
        logging.info('the device %s is not exists.' % device)
        raise store_exception.StoreInvalidException(device)

    _mountpoint = GetMountpoint(device)
    if len(_mountpoint):
        logging.info('the device %s is already mountting.' % device)
        raise store_exception.StoreInvalidException(device)
    _mountpoint = os.path.join(util.STORE_MOUNT_PATH, name)

    # CreateStorecfg
    xmlstr = _store_node.xml_template % {
            'type': pools_pb2.LOCAL,
            'name': name,
            'uuid': store_uuid,
            'naa': naa,
            'portal': None,
            'target': None,
            'mountpoint': _mountpoint
            }

    if CreateStoreCfg(xmlstr, name):
        logging.info('Create %s xml success.' % name)
    else:
        raise store_exception.StoreXmlException('Create %s xml failed.' % name)

    # add datastore to DATASTORE_LIST
    with DATASTORE_LIST.lock:
        DATASTORE_LIST.append(_store_node)

    # add section on  datastore.cfg
    with storeagentd.DATASTORE_CONF.lock:
        try:
            storeagentd.DATASTORE_CONF.SetValue(util.STATE, util.INACTIVE, name)
            storeagentd.DATASTORE_CONF.SetValue(util.N_TITLE, n_title, name)
            storeagentd.DATASTORE_CONF.SetValue(util.AUTO_MOUNT, util.TRUE, name)
        except store_exception.StoreDataConfigException:
            if name != util.LOCALPOOL:
                os.remove(xmlfile)
                with DATASTORE_LIST.lock:
                    DATASTORE_LIST.pop(store_uuid)
            raise store_exception.StoreDataConfigException('%s add status failed.' % name)

    logging.info('create datastore %s success.' % name)


def DeleteLocalStore(name):
    '''
        delete local Datastore
    '''
    # check uuid
    store_uuid = str(uuid.uuid3(uuid.NAMESPACE_DNS, '%s' % name))

    with DATASTORE_LIST.lock:
        if not DATASTORE_LIST.exists(store_uuid):
            logging.info('the %s datastore is not exist.' % name)
            raise store_exception.StoreInvalidException(name)

        DATASTORE_LIST.pop(store_uuid)

    # check xml cfg
    xmlfile = ('%s/%s.xml' % (util.STORE_XML_PATH, name))
    if not os.path.exists(xmlfile):
        logging.error('the %s xml conf is not exist.' % name)
        raise store_exception.StoreInvalidException(name)

    # delete datastore.cfg datastore
    with storeagentd.DATASTORE_CONF.lock:
        if name != util.LOCALPOOL:
            storeagentd.DATASTORE_CONF.DeleteStore(name)

    # delete xml cfg
    os.remove(xmlfile)

    logging.info('Delete %s datastore success.' % name)


def StartLocalStore(name):
    '''
        start local store (include  localpool)
    '''
    # check xml cfg
    xmlfile = ('%s/%s.xml' % (util.STORE_XML_PATH, name))
    if not os.path.exists(xmlfile):
        raise store_exception.StoreInvalidException(xmlfile)

    # check  mountpoint, device
    xml_tree = ReadXml(xmlfile)
    if isinstance(xml_tree, etree._ElementTree):
        mountpoint = GetXmlElementByXpath(xml_tree, 'mountpoint').text
        naa = GetXmlElementByXpath(xml_tree, 'naa').text
        device = GetDeviceByNaa(naa)
        logging.info('mountpoint is %s, device is %s' % (mountpoint, device))
        # check mountpoint /data/localpool.
        if mountpoint == util.LOCALPOOL_MOUNTPOINT:
            # get device by datastore.cfg.
            device = storeagentd.DATASTORE_CONF.GetValue(util.DEVICE, name)
    else:
        raise store_exception.StoreXmlException(xmlfile)

    # check auto_mount
    with storeagentd.DATASTORE_CONF.lock:
        _auto_mount = storeagentd.DATASTORE_CONF.GetValue(util.AUTO_MOUNT, name)
        if _auto_mount != util.TRUE:
            if not os.path.exists(mountpoint):
                os.mkdir(mountpoint)

            if util.CheckBusy(mountpoint):
                raise store_exception.StoreFileBusyException(mountpoint)

            if os.listdir(mountpoint):
                logging.error('mountpoint dir %s is not null.' % mountpoint)
                raise store_exception.StoreInvalidException(mountpoint)

            mount_ret = envoy.run('%s %s %s' % (util.MOUNT, device, mountpoint))
            if mount_ret.status_code == 0:
                logging.info('the datastore %s mountting success.' % name)
            else:
                raise store_exception.StoreEnvoyException('mount  %s %s failed.' % (device, mountpoint))

    # update status cfg
    with storeagentd.DATASTORE_CONF.lock:
        storeagentd.DATASTORE_CONF.SetValue(util.STATE, util.ACTIVE, name)

    logging.info('Start datastore %s success.' % name)


def StopLocalStore(name):
    '''
        stop local store
    '''
    # check xml cfg
    xmlfile = ('%s/%s.xml' % (util.STORE_XML_PATH, name))
    if not os.path.exists(xmlfile):
        raise store_exception.StoreInvalidException(xmlfile)

    # check mountpoint device
    xml_tree = ReadXml(xmlfile)
    if isinstance(xml_tree, etree._ElementTree):
        mountpoint = GetXmlElementByXpath(xml_tree, 'mountpoint').text
        if not mountpoint:
            raise store_exception.StoreInvalidException('mountpoint is null')

        # check mountpoint busy
        if util.CheckBusy(mountpoint):
            raise store_exception.StoreFileBusyException(mountpoint)

        # umount
        with storeagentd.DATASTORE_CONF.lock:
            _auto_mount = storeagentd.DATASTORE_CONF.GetValue(util.AUTO_MOUNT, name)
            if _auto_mount != util.TRUE:
                umount_ret = envoy.run('%s %s' % (util.UMOUNT, mountpoint))
                if umount_ret.status_code == 0:
                    logging.info('datastore %s umount %s success.' % (name, mountpoint))
                else:
                    raise store_exception.StoreEnvoyException('%s umount %s failed' % (name, mountpoint))

        # update datastroe.cfg
        with storeagentd.DATASTORE_CONF.lock:
            storeagentd.DATASTORE_CONF.SetValue(util.STATE, util.INACTIVE, name)
    else:
        raise store_exception.StoreXmlException('%s.xml exception' % name)

    logging.info('datastore %s is stop success.' % name)


def CreateBlockStore(name, portal, target, n_title):
    '''
        create Block DataStore
    '''
    _xml_list = []

    # check uuid
    store_uuid = str(uuid.uuid3(uuid.NAMESPACE_DNS, name))
    with DATASTORE_LIST.lock:
        if DATASTORE_LIST.exists(store_uuid):
            logging.error('the name %s is already used.' % name)
            raise store_exception.StoreInvalidException(name)
    _store_node = DataStore(store_uuid)

    # check xml cfg
    xmlfile = ('%s/%s.xml' % (util.STORE_XML_PATH, name))
    if os.path.exists(xmlfile):
        logging.error('the xml %s is already exists.' % xmlfile)
        raise store_exception.StoreInvalidException(name)

    # check device by portal, target
    # get xmlfile  list
    _xml_list = os.listdir(util.STORE_XML_PATH)
    for xml in _xml_list:
        _file = ''
        _file = ('%s/%s' % (util.STORE_XML_PATH, xml))
        _xml_tree = ReadXml(_file)
        if isinstance(_xml_tree, etree._ElementTree):
            _type = GetXmlElementByXpath(_xml_tree, '[@type]').get('type')
            if int(_type) == pools_pb2.LOCAL:
                continue
            _portal = GetXmlElementByXpath(_xml_tree, 'portal').text
            _target = GetXmlElementByXpath(_xml_tree, 'target').text
            if _portal == portal and _target == target:
                logging.error('the Datastroe %s is confict.' % xml)
                raise store_exception.StoreInvalidException('the portal %s, target %s is invalid.' % (portal, target))
        else:
            raise store_exception.StoreInvalidException(_file)

    # createxmlcfg
    _xmlstr = _store_node.xml_template % {
             'type': pools_pb2.ISCSI_BLOCK,
             'name': name,
             'uuid': store_uuid,
             'naa': None,
             'portal': portal,
             'target': target,
             'mountpoint': util.BLOCK_PATH
            }
    if CreateStoreCfg(_xmlstr, name):
        logging.info('Create %s xml success.' % name)
    else:
        raise store_exception.StoreXmlException('Create %s xml failed.' % name)

    # add to DATASTORE_LIST
    with DATASTORE_LIST.lock:
        DATASTORE_LIST.append(store_uuid)

    # add to DATASTORE_CONF
    with storeagentd.DATASTORE_CONF.lock:
        try:
            storeagentd.DATASTORE_CONF.SetValue(util.STATE, util.INACTIVE, name)
            storeagentd.DATASTORE_CONF.SetValue(util.STATE, util.N_TITLE, n_title)
        except store_exception.StoreDataConfigException:
            os.remove(xmlfile)
            with DATASTORE_LIST.lock:
                DATASTORE_LIST.pop(store_uuid)
            raise store_exception.StoreDataConfigException('%s update datastore.cfg failed.' % name)

    logging.info('create datasotre %s success.' % name)


def DeleteBlockStore(name):
    '''
        delete Block DataStore
    '''
    _state = ''

    xmlfile = ('%s/%s.xml' % (util.STORE_XML_PATH, name))
    if not os.path.exists(xmlfile):
        raise store_exception.StoreInvalidException(xmlfile)

    # get Store state, if inactive delete
    with storeagentd.DATASTORE_CONF.lock:
        _state = storeagentd.DATASTORE_CONF.GetValue(util.STATE, name)

    if _state == util.INACTIVE:
        # delete from DATASTORE_LIST
        store_uuid = uuid.uuid3(uuid.NAMESPACE_DNS, '%s' % name)
        with DATASTORE_LIST.lock:
            if not DATASTORE_LIST.exists(store_uuid):
                logging.error('the %s datastore is not exists.' % name)
                raise store_exception.StoreInvalidException(name)
            DATASTORE_LIST.pop(store_uuid)

        # delete from DATASTORE_CONF
        with storeagentd.DATASTORE_CONF.lock:
            storeagentd.DATASTORE_CONF.DeleteStore(name)

        # delete xml cfg
        os.remove(xmlfile)
    else:
        logging.info('the %s datastore is ACTIVE. please stop datastore.')
        raise store_exception.StoreInvalidException('the datastore is ACTIVE.')

    logging.info('delete datastore %s success.' % name)


def StartBlockStore(name):
    '''
        start block DataStore
    '''
    # check xml
    xmlfile = ('%s/%s.xml' % (util.STORE_XML_PATH, name))
    if not os.path.exists(xmlfile):
        raise store_exception.StoreInvalidException(xmlfile)

    # get portal and target
    _xml_tree = ReadXml(xmlfile)
    if isinstance(_xml_tree, etree._ElementTree):
        _portal = GetXmlElementByXpath(_xml_tree, 'portal').text
        _target = GetXmlElementByXpath(_xml_tree, 'target').text

        # login, if already login we again login has no affect.
        _portal_list = _portal.split(',')
        for item in _portal_list:
            _portal_address = item.split(':')[0]
            _portal_port = item.split(':')[1]
            util.IscsiadmLogin('%s:%s' % ((_portal_address, _portal_port), _target))

    # change DATASTORE_CONF
    with storeagentd.DATASTORE_CONF.lock:
        storeagentd.DATASTORE_CONF.SetValue(util.STATE, util.ACTIVE, name)

    logging.info('start %s datastore success.' % name)


def StopBlockStore(name):
    '''
        stop block DataStore
    '''
    lun_list = []
    _portal_list = []
    # check xml
    xmlfile = ('%s/%s.xml' % (util.STORE_XML_PATH, name))
    if not os.path.exists(xmlfile):
        raise store_exception.StoreInvalidException(name)

    # get portal and target
    _xml_tree = ReadXml(xmlfile)
    if isinstance(_xml_tree, etree._ElementTree):
        _portal = GetXmlElementByXpath(_xml_tree, 'portal').text
        _target = GetXmlElementByXpath(_xml_tree, 'target').text

    # check portal target, get lun by target. check lun if is busy.
    lun_list = disk_manager.GetIscsiLunListByTarget(_portal, _target)
    for lun in lun_list:
        # check busy
        _naa = lun['SCSI_ID']
        _device = GetDeviceByNaa(_naa)
        if util.CheckBusy(_device):
            logging.error('the device %s scsi_id %s is busy.' % (_device, _naa))
            raise store_exception.StoreFileBusyException(_device)

    # logout
    _portal_list = _portal.split(',')
    for item in _portal_list:
        _portal_address = item.split(':')[0]
        _portal_port = item.split(':')[1]
        util.IscsiadmLogout('%s:%s' % (_portal_address, _portal_port), _target)

    # change state to inactive, DATASTORE_CONF.
    with storeagentd.DATASTORE_CONF.lock:
        storeagentd.DATASTORE_CONF.SetValue(util.STAT, util.INACTIVE, name)

    logging.info('stop %s datastore success.' % name)
