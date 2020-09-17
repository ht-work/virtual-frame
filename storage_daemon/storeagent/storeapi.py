#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import logging
import traceback

import envoy
import json

from lxml import etree

from storeagent import adapters_pb2 as adp_pb2
from storeagent import adapters_pb2_grpc as adp_grpc
from storeagent import pools_pb2
from storeagent import pools_pb2_grpc as pools_grpc
from storeagent import vols_pb2
from storeagent import vols_pb2_grpc as vols_grpc
from storeagent import store_util_pb2 as util_pb2
from storeagent import store_util as util
from storeagent import store_driver as driver
from storeagent import store_exception
from storeagent import schema
from storeagent import storeagentd
from storeagent import multipath
from storeagent.worker_job import JobType
from . import disk_manager


class Adapters(adp_grpc.AdaptersServicer):
    def GetStoreAdapterInfo(self, request, context):
        _adapter_list = []
        logging.info('GetStoreAdapterInfo')

        _adapter_list = disk_manager.GetAdapterList()

        return adp_pb2.StoreAdapterInfoGetReply(errno=util_pb2.STORE_OK,
                                                adapter_list=json.dumps(_adapter_list))

    def GetAdapterResourcesInfo(self, request, context):
        _adaptername = request.adaptername
        _resources = []
        ret = util_pb2.STORE_OK
        logging.info('GetAdapterResourcesInfo')

        try:
            _resources = disk_manager.GetAdapterReSourcesByName(_adaptername)

        except store_exception.StoreEnvoyException:
            ret = util_pb2.STORE_ENVOY_FAIL
            logging.error(traceback.format_exc())

        except store_exception.StoreMultipathdException:
            ret = util_pb2.STORE_MULTIPATHD_EXCEPTION
            logging.error(traceback.format_exc())

        return adp_pb2.AdapterResourcesInfoGetReply(errno=ret,
                                                    resource_list=json.dumps(_resources))

    def EnableDeviceMultipath(self, request, context):
        naa = request.naa
        ret = util_pb2.STORE_OK
        logging.info("Enable Naa %s multipath." % naa)

        try:
            multipath.EnableMultipath(naa)
        except store_exception.StoreInvalidException:
            ret = util_pb2.STORE_INVALID_ERROR
            logging.error(traceback.format_exc())

        return adp_pb2.DeviceMultipathEnableReply(errno=ret)

    def DisableDeviceMultipath(self, request, context):
        naa = request.naa
        ret = util_pb2.STORE_OK
        logging.info("Disable Naa %s multipath." % naa)

        try:
            multipath.DisableMultipath(naa)
        except store_exception.StoreInvalidException:
            ret = util_pb2.STORE_INVALID_ERROR
            logging.error(traceback.format_exc())

        return adp_pb2.DeviceMultipathDisableReply(errno=ret)

    def GetMultipathConfig(self, request, context):
        naa = request.naa
        ret = util_pb2.STORE_OK
        _path_list = []
        _policy = ''
        logging.info("GetMultipathConfig naa : %s" % naa)

        try:
            _path_list = multipath.GetPathList(naa)
            _policy = multipath.GetPolicy(naa)
        except store_exception.StoreInvalidException:
            ret = util_pb2.STORE_INVALID_ERROR
            logging.error(traceback.format_exc())
        except store_exception.StoreMultipathdException:
            ret = util_pb2.STORE_MULTIPATHD_EXCEPTION
            logging.error(traceback.format_exc())

        return adp_pb2.MultipathConfigGetReply(errno=ret,
                                               paths_list=json.dumps(_path_list),
                                               policy=_policy)

    def SetMultipathConfig(self, request, context):
        naa = request.naa
        policy = request.policy
        ret = util_pb2.STORE_OK
        logging.info("SetMultipathConfig naa: %s, policy: %s" % (naa, policy))

        try:
            multipath.SetPolicy(naa, policy)
        except store_exception.StoreInvalidException:
            ret = util_pb2.STORE_INVALID_ERROR
            logging.error(traceback.format_exc())
        except store_exception.StoreMultipathdException:
            ret = util_pb2.STORE_MULTIPATHD_EXCEPTION
            logging.error(traceback.format_exc())

        return adp_pb2.MultipathConfigSetReply(errno=ret)

    def GetIscsiTargetsInfo(self, request, context):
        portal_list = request.portal_list
        ret = util_pb2.STORE_OK
        _target_list = []
        logging.info('portal_list : %s' % portal_list)

        try:
            _target_list = disk_manager.GetIscsiTargetListByPortalList(portal_list)
        except store_exception.StoreEnvoyException:
            ret = util_pb2.STORE_ENVOY_FAIL
            logging.error(traceback.format_exc())
        except store_exception.StoreInvalidException:
            ret = util_pb2.STORE_INVALID_ERROR
            logging.error(traceback.format_exc())

        return adp_pb2.GetIscsiTargetsReply(errno=ret, target_list=json.dumps(_target_list))

    def GetIscsiLunInfo(self, request, context):
        _portal_list = request.portal_list
        target_name = request.target_name
        ret = util_pb2.STORE_OK
        _lun_list = []
        logging.info('portal: %s, %s' % (_portal_list, target_name))

        try:
            _lun_list = disk_manager.GetIscsiLunList(_portal_list, target_name)
        except store_exception.StoreEnvoyException:
            ret = util_pb2.STORE_ENVOY_FAIL
            logging.error(traceback.format_exc())
        except store_exception.StoreInvalidException:
            ret = util_pb2.STORE_INVALID_ERROR
            logging.error(traceback.format_exc())

        logging.info(_lun_list)
        return adp_pb2.GetIscsiLunInfoReply(errno=ret, lun_list=json.dumps(_lun_list))

    def GetInitiatorName(self, request, context):
        _initiatorname = ''

        _initiatorname = disk_manager.GetInitiator()

        return adp_pb2.InitiatorNameGetReply(errno=util_pb2.STORE_OK, initiatorname=_initiatorname)

    def SetInitiatorName(self, request, context):
        _initiatorname = request.initiatorname
        ret = util_pb2.STORE_OK

        logging.info("set InitiatorName  %s " % _initiatorname)

        try:
            disk_manager.SetInitiator(_initiatorname)

        except store_exception.StoreIOError:
            logging.critical(traceback.format_exc())
            ret = util_pb2.STORE_IOERROR

        return adp_pb2.InitiatorNameSetReply(errno=ret)

    def GetIscsiIpSession(self, request, context):
        _ip_list = []

        _ip_list = disk_manager.GetIpList()

        return adp_pb2.IscsiIpSessionGetReply(errno=util_pb2.STORE_OK, ip_list=json.dumps(_ip_list))


class Pools(pools_grpc.PoolsServicer):
    def CreateLocalPool(self, request, context):
        """ create local datastore
        :param request : request.name
                         request.n_title
                         request.naa scsi_id
        :returns : util_pb2.STORE_OK
                   util_pb2.STORE_INVALID_ERROR the request is invalid
                   util_pb2.STORE_XML_ERROR xmlfile error
                   util_pb2.STORE_DATASTORE_LIST_ERROR use DATASTORE_LIST error.
                   util_pb2.STORE_DATASTPRE_CFG_ERROR use datastore.cfg error
                   util_pb2.STORE_UNKNOWN_ERROR  unknown error.
        """
        ret = util_pb2.STORE_OK
        _naa = request.naa
        _name = request.name
        _n_title = request.n_title

        try:
            driver.CreateLocalStore(_naa, _name, _n_title)

        except store_exception.StoreInvalidException:
            ret = util_pb2.STORE_INVALID_ERROR
            logging.critical(traceback.format_exc())
        except store_exception.StoreXmlException:
            ret = util_pb2.STORE_XML_ERROR
            logging.critical(traceback.format_exc())
        except store_exception.DatastoreListException:
            ret = util_pb2.STORE_DATASTORE_LIST_ERROR
            logging.critical(traceback.format_exc())
        except store_exception.StoreDataConfigException:
            ret = util_pb2.STORE_DATASTPRE_CFG_ERROR
            logging.critical(traceback.format_exc())
        except Exception:
            ret = util_pb2.STORE_UNKNOWN_ERROR
            logging.critical(traceback.format_exc())

        return pools_pb2.LocalPoolCreateReply(errno=ret)

    def DeleteLocalPool(self, request, context):
        """ delete the local DataStore
        :param request : name
        :returns : errno
                   util_pb2.STORE_OK delete success
                   util_pb2.STORE_INVALID_ERROR name is invalid
                   util_pb2.STORE_DATASTPRE_CFG_ERROR use datastore.cfg error
                   util_pb2.STORE_UNKNOWN_ERROR unknown error.
        """
        ret = util_pb2.STORE_OK
        _name = request.name

        try:
            driver.DeleteLocalStore(_name)
        except store_exception.StoreInvalidException:
            ret = util_pb2.STORE_INVALID_ERROR
            logging.critical(traceback.format_exc())
        except store_exception.StoreDataConfigException:
            ret = util_pb2.STORE_DELETE_FAIL
            logging.critical(traceback.format_exc())
        except Exception:
            ret = util_pb2.STORE_UNKNOWN_ERROR
            logging.critical(traceback.format_exc())

        return pools_pb2.LocalPoolDeleteReply(errno=ret)

    def GetPoolInfo(self, request, context):
        """ get DataStore info
        :param request : name
        :returns :
            DataStoreInfo []
            errno : util_pb2.STORE_OK
                    util_pb2.STORE_INVALID_ERROR
                    util_pb2.STORE_OSERROR the OSError
                    util_pb2.STORE_XML_ERROR
                    util_pb2.STORE_GET_DEVICE_SIZEINFO_FAIL get device size info fail
                    util_pb2.STORE_UNKNOWN_ERROR unknown error
        """
        store_info = pools_pb2.DataStoreInfo()
        s_name = request.name
        ret = util_pb2.STORE_OK

        try:
            store_info = driver.GetDataStoreInfoByName(s_name)

        except OSError:
            ret = util_pb2.STORE_OSERROR
            logging.critical(traceback.format_exc())
        except etree.LxmlError:
            ret = util_pb2.STORE_XML_ERROR
            logging.critical(traceback.format_exc())
        except store_exception.StoreEnvoyException:
            ret = util_pb2.STORE_GET_DEVICE_SIZEINFO_FAIL
            logging.critical(traceback.format_exc())
        except store_exception.StoreXmlException:
            ret = util_pb2.STORE_XML_ERROR
            logging.critical(traceback.format_exc())
        except store_exception.StoreInvalidException:
            ret = util_pb2.STORE_INVALID_ERROR
            logging.critical(traceback.format_exc())
        except Exception:
            logging.critical(traceback.format_exc())
            ret = util_pb2.STORE_UNKNOWN_ERROR

        return pools_pb2.PoolInfoGetReply(info=store_info, errno=ret)

    def StartLocalPool(self, request, context):
        """ start local Datastore
        :param request : name Datastore name
               return : util_pb2.STORE_OK
                        util_pb2.STORE_INVALID_ERROR invalid
                        util_pb2.STORE_ENVOY_FAIL run command failed
                        util_pb2.STORE_XML_ERROR  xml error
                        util_pb2.STORE_DATASTPRE_CFG_ERROR use datastore.cfg error
                        util_pb2.STORE_UNKNOWN_ERROR unknown error.
        """
        ret = util_pb2.STORE_OK
        _name = request.name

        try:
            driver.StartLocalStore(_name)
        except store_exception.StoreInvalidException:
            ret = util_pb2.STORE_INVALID_ERROR
            logging.critical(traceback.format_exc())
        except store_exception.StoreEnvoyException:
            ret = util_pb2.STORE_ENVOY_FAIL
            logging.critical(traceback.format_exc())
        except store_exception.StoreXmlException:
            ret = util_pb2.STORE_XML_ERROR
            logging.critical(traceback.format_exc())
        except store_exception.StoreDataConfigException:
            ret = util_pb2.STORE_DATASTPRE_CFG__ERROR
            logging.critical(traceback.format_exc())
        except store_exception.StoreFileBusyException:
            ret = util_pb2.STORE_IS_BUSY
            logging.critical(traceback.format_exc())
        except Exception:
            ret = util_pb2.STORE_UNKNOWN_ERROR
            logging.critical(traceback.format_exc())

        return pools_pb2.LocalPoolStartReply(errno=ret)

    def StopLocalPool(self, request, context):
        """ stop local DataStore
        :param request: name  DataStore name
        :return : errno util_pb2.STORE_OK
                        util_pb2.STORE_INVALID_ERROR invalid
                        util_pb2.STORE_DATASTPRE_CFG_ERROR use datastore.cfg error.
                        util_pb2.STORE_ENVOY_FAIL run command failed.
                        util_pb2.STORE_XML_ERROR  xml error
                        util_pb2.STORE_UNKNOWN_ERROR
        """
        ret = util_pb2.STORE_OK
        _name = request.name
        try:
            driver.StopLocalStore(_name)
        except store_exception.StoreInvalidException:
            ret = util_pb2.STORE_INVALID_ERROR
            logging.critical(traceback.format_exc())
        except store_exception.StoreEnvoyException:
            ret = util_pb2.STORE_ENVOY_FAIL
            logging.critical(traceback.format_exc())
        except store_exception.StoreXmlException:
            ret = util_pb2.STORE_XML_ERROR
            logging.critical(traceback.format_exc())
        except store_exception.StoreDataConfigException:
            ret = util_pb2.STORE_DATASTPRE_CFG_ERROR
            logging.critical(traceback.format_exc())
        except store_exception.StoreFileBusyException:
            ret = util_pb2.STORE_IS_BUSY
            logging.critical(traceback.format_exc())
        except Exception:
            ret = util_pb2.STORE_UNKNOWN_ERROR
            logging.critical(traceback.format_exc())

        return pools_pb2.LocalPoolStopReply(errno=ret)

    def GetOnlyPoolsSize(self, request, context):
        """ get the DataStore  size info
        :param request : naa
        :returns : DataStoreSizeInfo {
                       totalsize
                       allocatedsize
                       availablesize
                   }
                   errno : util_pb2.STORE_OK
                           util_pb2.STORE_GET_DISKPART_FAIL get device info fail
        """
        device_info = pools_pb2.DataStoreSizeInfo()
        ret = util_pb2.STORE_OK
        try:
            _device = driver.GetDeviceByNaa(request.naa)
            device_info = driver.GetDeviceSizeInfo(_device)
        except store_exception.StoreEnvoyException:
            logging.critical(traceback.format_exc())
            ret = util_pb2.STORE_GET_DISKPART_FAIL

        return pools_pb2.OnlyPoolSizeGetReply(datainfo=device_info, errno=ret)

    def GetUsefulLocalDevice(self, request, context):
        """ get useful device to create local DataStore
        :returns : util_pb2.STORE_OK
        """
        ret = util_pb2.STORE_OK
        _list = []

        _list = disk_manager.GetUsefulDeviceByLocalReSource()

        return pools_pb2.UsefulLocalDeviceGetReply(errno=ret, disk_list=json.dumps(_list))

    def CreateIscsiBlockPool(self, request, context):
        """ create block pool
        :return util_pb2.STORE_OK
                util_pb2.STORE_INVALID_ERROR invalid requet
                util_pb2.STORE_XML_ERROR xml cfg error
                util_pb2.STORE_DATASTPRE_CFG_ERROR datastore.cfg error
        """
        ret = util_pb2.STORE_OK
        _name = request.name
        _portal = request.portal
        _target = request.target
        _n_title = request.n_title

        try:
            driver.CreateBlockStore(_name, _portal, _target, _n_title)
        except store_exception.StoreInvalidException:
            ret = util_pb2.STORE_INVALID_ERROR
            logging.critical(traceback.format_exc())
        except store_exception.StoreXmlException:
            ret = util_pb2.STORE_XML_ERROR
            logging.critical(traceback.format_exc())
        except store_exception.StoreDataConfigException:
            ret = util_pb2.STORE_DATASTPRE_CFG_ERROR
            logging.critical(traceback.format_exc())
        except Exception:
            ret = util_pb2.STORE_UNKNOWN_ERROR
            logging.critical(traceback.format_exc())

        return pools_pb2.IscsiBlockPoolCreateReply(errno=ret)

    def DeleteIscsiBlockPool(self, request, context):
        """  delete iscsi block pool
        :return util_pb2.STORE_OK
                util_pb2.STORE_INVALID_ERROR invalid
        """
        ret = util_pb2.STORE_OK
        _name = request.name

        try:
            driver.DeleteBlockStore(_name)
        except store_exception.StoreInvalidException:
            ret = util_pb2.STORE_INVALID_ERROR
            logging.critical(traceback.format_exc())
        except Exception:
            ret = util_pb2.STORE_UNKNOWN_ERROR
            logging.critical(traceback.format_exc())

        return pools_pb2.IscsiBlockPoolDeleteReply(errno=ret)

    def StartIscsiBlockPool(self, request, context):
        """ start iscsi block pool
        :return util_pb2.STORE_OK
                util_pb2.STORE_INVALID_ERROR invalid request
        """
        ret = util_pb2.STORE_OK
        _name = request.name

        try:
            driver.StartBlockStore(_name)
        except store_exception.StoreInvalidException:
            ret = util_pb2.STORE_INVALID_ERROR
            logging.critical(traceback.format_exc())
        except Exception:
            ret = util_pb2.STORE_UNKNOWN_ERROR
            logging.critical(traceback.format_exc())

        return pools_pb2.IscsiBlockPoolStartReply(errno=ret)

    def StopIscsiBlockPool(self, request, context):
        """ stop iscsi block pool
        :return util_pb2.STORE_OK
                util_pb2.STORE_INVALID_ERROR invalid request
                util_pb2.STORE_IS_BUSY some device is busy
        """
        ret = util_pb2.STORE_OK
        _name = request.name

        try:
            driver.StopBlockStore(_name)
        except store_exception.StoreInvalidException:
            ret = util_pb2.STORE_INVALID_ERROR
            logging.critical(traceback.format_exc())
        except store_exception.StoreFileBusyException:
            ret = util_pb2.STORE_IS_BUSY
            logging.critical(traceback.format_exc())
        except Exception:
            ret = util_pb2.STORE_UNKNOWN_ERROR
            logging.critical(traceback.format_exc())

        return pools_pb2.IscsiBlockPoolStopReply(errno=ret)

    def FormatLocalDisk(self, request, context):
        """format local device , default the fstype is ext4.
        :param request: naa
        :returns : util_pb2.STORE_OK
                   util_pb2.STORE_FORMAT_LOCALDISK_FAIL
        """
        naa = request.naa
        _device = driver.GetDeviceByNaa(naa)
        disk_format = envoy.run('%s -F %s' % (util.MKFS_EXT4, _device))

        if disk_format.status_code == 0:
            ret = util_pb2.STORE_OK
        else:
            ret = util_pb2.STORE_FORMAT_LOCALDISK_FAIL
            logging.error("format local disk %s failed" % _device)

        return pools_pb2.LocalDiskFormatReply(errno=ret)

    def GetLocalStoreSize(self, request, context):
        """
        get LocalStoreSize info , include all device which already used Local DataStore
        or can use to create Local DataStore
        """
        _totalsize = ''
        _usedSize = ''
        ret = util_pb2.STORE_OK

        try:
            _totalsize, _usedSize = driver.GetLocalStoreSizeInfo()

        except store_exception.StoreEnvoyException:
            ret = util_pb2.STORE_ENVOY_FAIL
            logging.error(traceback.format_exc())

        return pools_pb2.LocalStoreSizeGetReply(errno=ret, totalsize=_totalsize, usedsize=_usedSize)

    def GetPoolFileList(self, request, context):
        '''
        get DataStore include file list ,
        request: store_name
        return: file_list
                errno
        '''
        store_name = request.name
        ret = util_pb2.STORE_OK
        _list = []

        try:
            _list = driver.GetDataStoreFileList(store_name)
        except OSError:
            ret = util_pb2.STORE_OSERROR
            logging.critical(traceback.format_exc())
        except etree.LxmlError:
            ret = util_pb2.STORE_XML_ERROR
            logging.critical(traceback.format_exc())

        return pools_pb2.PoolFileListGetReply(errno=ret, file_list=json.dumps(_list))

    def GetPoolNameList(self, request, context):
        '''
        get all DataStore name
        return: name_list
                errno
        '''
        ret = util_pb2.STORE_OK
        _list = []

        _list = driver.GetDataStoreNameList()

        return pools_pb2.PoolNameListGetReply(errno=ret, name_list=json.dumps(_list))


class Vols(vols_grpc.VolsServicer):
    def CreateVol(self, request, context):
        """ create Raw vol , preallocation is off, falloc
        :param request : json_data
        :returns : errno util_pb2.STORE_OK   create success
                         util_pb2.STORE_INVALID_ERROR  invalid error
                         util_pb2.STORE_OSERROR the OSError
                         util_pb2.STORE_XML_ERROR  the xml error
                         util_pb2.STORE_QEMU_COMMAND_FAIL run qemu command fail
        """
        json_data = request.json_data
        ret = util_pb2.STORE_OK
        preallocation = ''

        try:
            # vol_type need off  or falloc
            j_data = json.loads(json_data)
            schema.validate(j_data)
            preallocation = j_data['preallocation']
            if preallocation == "full" or preallocation == "metadata":
                raise store_exception.StoreInvalidException(preallocation)

            ret = driver.QemuCreateVol(j_data)

        except OSError:
            logging.critical(traceback.format_exc())
            ret = util_pb2.STORE_OSERROR
        except etree.LxmlError:
            logging.critical(traceback.format_exc())
            ret = util_pb2.STORE_XML_ERROR
        except store_exception.StoreInvalidException:
            logging.critical(traceback.format_exc())
            ret = util_pb2.STORE_INVALID_ERROR
        except store_exception.StoreJsonValidationException:
            logging.critical(traceback.format_exc())
            ret = util_pb2.STORE_INVALID_ERROR
        except store_exception.StoreQemuImgCommandException:
            logging.critical(traceback.format_exc())
            ret = util_pb2.STORE_QEMU_COMMAND_FAIL
        except store_exception.StoreFileBusyException:
            logging.critical(traceback.format_exc())
            ret = util_pb2.STORE_IS_BUSY

        return vols_pb2.VolCreateReply(errno=ret)

    def CreateFullVol(self, request, context):
        """ create a vol which preallocation is full
        :param request: request.json_data
                        request.no_need_notify
        :returns
        """
        json_data = request.json_data
        need_notify = not request.no_need_notify

        try:
            # check json_data
            j_data = json.loads(json_data)
            schema.validate(j_data)
            preallocation = j_data['preallocation']
            if preallocation != "full":
                raise store_exception.StoreInvalidException(preallocation)

        except store_exception.StoreInvalidException:
            logging.critical(traceback.format_exc())
            errno = util_pb2.STORE_INVALID_ERROR
            job_id = 0
            return vols_pb2.FullVolCreateReply(errno=errno, job_id=job_id)

        opaque = {}
        opaque['json_data'] = json_data
        logging.info('json_data is %s' % json_data)

        job_id = storeagentd.WORKER.add_job(JobType.CREATE_FULL_VOL, opaque, need_notify)

        return vols_pb2.FullVolCreateReply(errno=util_pb2.STORE_OK, job_id=job_id)

    def DeleteVol(self, request, context):
        """ delete vol
        :param request: request.p_name  store name
                        request.v_name  vols name
        :returns : errno util_pb2.STORE_OK
        """
        ret = util_pb2.STORE_OK
        p_name = request.p_name
        v_name = request.v_name

        try:
            # check filename
            filepath = ('%s/%s/%s' % (util.STORE_MOUNT_PATH, p_name, v_name))
            if not os.path.exists(filepath):
                logging.error('the vol %s is not exists' % filepath)
                raise store_exception.StoreInvalidException

            # check busy
            if util.CheckBusy(filepath):
                raise store_exception.StoreFileBusyException(filepath)

            # delete
            os.remove(filepath)
            logging.info('delete %s success.' % filepath)

        except OSError:
            logging.critical(traceback.format_exc())
            ret = util_pb2.STORE_OSERROR
        except store_exception.StoreFileBusyException:
            ret = util_pb2.STORE_IS_BUSY
            logging.critical(traceback.format_exc())
        except store_exception.StoreEnvoyException:
            logging.critical(traceback.format_exc())
            ret = util_pb2.STORE_ENVOY_FAIL
        except store_exception.StoreInvalidException:
            logging.critical(traceback.format_exc())
            ret = util_pb2.STORE_INVALID_ERROR

        return vols_pb2.VolDeleteReply(errno=ret)

    def GetVolInfo(self, request, context):
        """ get vol info
        :param request : request.p_name   store name
                         request.v_name   vol name
        :returns : volInfo {
                       volsize   (KB)
                       vol_usedsize  (KB)
                   }
                   errno util_pb2.STORE_OK
        """
        p_name = request.p_name
        v_name = request.v_name
        ret = util_pb2.STORE_OK
        v_info = vols_pb2.VolInfo()
        command = ''
        q_img_ret = util_pb2.QemuImgReply()

        try:
            # check filename
            filepath = ('%s/%s/%s' % (util.STORE_MOUNT_PATH, p_name, v_name))
            if not os.path.exists(filepath):
                logging.error('the filename %s is not exists' % filepath)
                raise store_exception.StoreInvalidException(filepath)

            # command
            command = ('info %s --output json' % filepath)
            logging.info('command: %s' % command)

            # get info
            q_img_ret = util.QemuImg(command)

            j = json.loads(q_img_ret.std_out)
            s_volsize = str(j["virtual-size"])
            s_volusedsize = str(j["actual-size"])

            v_info.volsize = str(driver.StringToInt(s_volsize))
            v_info.vol_usedsize = str(driver.StringToInt(s_volusedsize))

        except OSError:
            logging.critical(traceback.format_exc())
            ret = util_pb2.STORE_OSERROR
        except store_exception.StoreQemuImgCommandException:
            logging.critical(traceback.format_exc())
            ret = util_pb2.STORE_QEMU_COMMAND_FAIL
        except store_exception.StoreInvalidException:
            logging.critical(traceback.format_exc())
            ret = util_pb2.STORE_INVALID_ERROR

        return vols_pb2.VolInfoGetReply(errno=ret, info=v_info)


def add_to_server(s):
    adp_grpc.add_AdaptersServicer_to_server(Adapters(), s)
    pools_grpc.add_PoolsServicer_to_server(Pools(), s)
    vols_grpc.add_VolsServicer_to_server(Vols(), s)
