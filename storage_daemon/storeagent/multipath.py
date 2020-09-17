#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import logging
import json
import traceback


from infi.multipathtools import MultipathClient
from infi.multipathtools import config
from infi.multipathtools import errors


from storeagent import store_util as util
from storeagent import adapters_pb2 as adp_pb2
from storeagent import store_exception
from storeagent import disk_manager

# multipath  policy
# default, used default_multipath.conf defaults
DEFAULT_CONFIG = ("%s/%s" % (util.STORE_CONF_PATH, util.DEFAULT_MULTIPATH_CONF))


# input naa has no "",  eg  "1111111111111111" is error , used 1111111111111111
def GetMultipathJson():
    client = MultipathClient()
    json_string = ''
    try:
        json_string = client._send_and_receive("show multipaths json")

    except errors.TimeoutExpired:
        logging.error(traceback.format_exc())
    except errors.ConnectionError:
        logging.error(traceback.format_exc())
    finally:
        return json_string


def GetPathList(naa):
    path_list = []
    multipath = []
    multipaths = {}
    mps_list = []
    path_group_list = []

    # get multipaths json
    json_string = GetMultipathJson()
    if len(json_string):
        multipaths = json.loads(GetMultipathJson())
    else:
        raise store_exception.StoreMultipathdException("Json_string is null ,Multipatd Exception ")

    if len(multipaths):
        mps_list = multipaths['maps']

    # get multipath by naa
    for mp in mps_list:
        if naa == mp['uuid']:
            multipath = mp
            break

    # get paths
    if len(multipath):
        path_group_list = multipath['path_groups']

    for path_goup in path_group_list:
        p_list = path_goup['paths']
        for path in p_list:
            item = {}
            item['device'] = path['dev']
            # need a interface  GetIpByDevice()
            _device = '/dev/' + item['device']
            item['ip'] = disk_manager.GetIpByDevice(_device)
            item['target'] = path['target_wwnn']
            # need a interface GetLunIdByDevice()
            item['lun_id'] = disk_manager.GetLunIdByDevice(_device)
            item['status'] = path['dm_st']
            path_list.append(item)

    return path_list


def _GetConfigByMultipathd():
    '''
    get config by multipathd
    '''
    m_config = config.Configuration()
    client = MultipathClient()
    flag = False

    try:
        m_config = client.get_multipathd_conf()
        return m_config
    except errors.TimeoutExpired:
        flag = True
        logging.error(traceback.format_exc())
    except errors.ConnectionError:
        flag = True
        logging.error(traceback.format_exc())

    finally:
        if flag:
            raise store_exception.StoreMultipathdException("Multipatd Exception.")


def GetMultipathStatus(naa):
    '''
    get device multiapth status by device naa
    '''
    ret = util.DISABLE
    _config = _GetConfigByMultipathd()

    white_list = _config.whitelist.wwid

    if ('"%s"' % naa) in white_list:
        ret = util.ENABLE

    return ret


def GetPolicy(naa):
    # check naa
    _config = _GetConfigByMultipathd()

    white_list = _config.whitelist.wwid
    multipath_list = _config.multipaths

    if ('"%s"' % naa) not in white_list:
        raise store_exception.StoreInvalidException(naa)

    # get multipath section
    section = config.MultipathEntry()
    for multipath in multipath_list:
        if naa == multipath.wwid.strip('"'):
            section = multipath
            break

    if section.path_grouping_policy is None:
        path_grouping_policy = ''
    else:
        path_grouping_policy = section.path_grouping_policy.strip('"')

    if section.failback is None:
        failback = ''
    else:
        failback = section.failback.strip('"')

    policy = adp_pb2.DEFAULT
    if path_grouping_policy == "failover" and failback == "manual":
        policy = adp_pb2.RECENTLY_USED

    if path_grouping_policy == "failover" and failback == "immediate":
        policy = adp_pb2.FIXED

    if path_grouping_policy == "multibus":
        policy = adp_pb2.LOOP

    # if section path_grouping_policy is group_by_prio , the section option 'prio' has value
    # othrewise the section option 'prio' no value , and used 'section.prio' may error.
    if path_grouping_policy == "group_by_prio":
        if section.prio is None:
            prio = ''
        else:
            prio = section.prio.strip('"')

        if prio == "alua":
            policy = adp_pb2.OPTIMAL

    return policy


def EnableMultipath(naa):
    client = MultipathClient()
    with open(util.MULTIPATH_CONF, 'r') as fd:
        multipath_config_string = fd.read()

    _config = config.Configuration.from_multipathd_conf(multipath_config_string)

    # check naa
    if ('"%s"' % naa) in _config.whitelist.wwid:
        logging.info('naa %s is already set multipath.' % naa)
    else:
        _config.whitelist.wwid.append('"%s"' % naa)
        client.write_to_multipathd_conf(_config)

    # reconfigure
    util.StoreCmdRun("%s reconfigure" % util.MULTIPATHD)
    logging.info("Naa %s is enable multipath." % naa)


def DisableMultipath(naa):
    client = MultipathClient()
    with open(util.MULTIPATH_CONF, 'r') as fd:
        multipath_config_string = fd.read()

    _config = config.Configuration.from_multipathd_conf(multipath_config_string)

    # delete whitelist wwid
    white_list = _config.whitelist.wwid
    multipath_list = _config.multipaths

    # check naa
    if ('"%s"' % naa) not in white_list:
        raise store_exception.StoreInvalidException(naa)

    white_list.remove('"%s"' % naa)
    # delete multipath section if have
    for multipath in multipath_list:
        if naa == multipath.wwid.strip('"'):
            multipath_list.remove(multipath)
            break

    # reconfigure
    client.write_to_multipathd_conf(_config)
    util.StoreCmdRun("%s reconfigure" % util.MULTIPATHD)
    logging.info("Naa %s is disable multipath." % naa)


def SetPolicy(naa, policy):
    client = MultipathClient()
    with open(util.MULTIPATH_CONF, 'r') as fd:
        multipath_config_string = fd.read()

    _config = config.Configuration.from_multipathd_conf(multipath_config_string)

    white_list = _config.whitelist.wwid
    multipath_list = _config.multipaths

    # check naa
    if ('"%s"' % naa) not in white_list:
        raise store_exception.StoreInvalidException(naa)

    # delete old multipath section
    for multipath in multipath_list:
        if naa == multipath.wwid.strip('"'):
            multipath_list.remove(multipath)
            break

    # new multipath section
    new_section = config.MultipathEntry()
    if policy == adp_pb2.DEFAULT:
        logging.info("Naa %s policy change to DEFAULT." % naa)

    if policy == adp_pb2.RECENTLY_USED:
        new_section.wwid = '"%s"' % naa
        new_section.path_grouping_policy = '"failover"'
        new_section.failback = '"manual"'
        multipath_list.append(new_section)
        logging.info("Naa %s policy change to RECENTLY_USED." % naa)

    if policy == adp_pb2.FIXED:
        new_section.wwid = '"%s"' % naa
        new_section.path_grouping_policy = '"failover"'
        new_section.failback = '"immediate"'
        multipath_list.append(new_section)
        logging.info("Naa %s policy change to FIXED." % naa)

    if policy == adp_pb2.LOOP:
        new_section.wwid = '"%s"' % naa
        new_section.path_grouping_policy = '"multibus"'
        multipath_list.append(new_section)
        logging.info("Naa %s policy change to LOOP." % naa)

    if policy == adp_pb2.OPTIMAL:
        new_section.wwid = '"%s"' % naa
        new_section.path_grouping_policy = '"group_by_prio"'
        new_section.prio = '"alua"'
        new_section.failback = '"immediate"'
        multipath_list.append(new_section)
        logging.info("Naa %s policy change to OPTIMAL." % naa)

    # reconfigure
    client.write_to_multipathd_conf(_config)
    util.StoreCmdRun("%s reconfigure" % util.MULTIPATHD)


def SetDefaultConfig():
    # get default_multipath.conf
    client = MultipathClient()
    with open(DEFAULT_CONFIG, 'r') as fd:
        default_config_string = fd.read()
    logging.info("default_config_string is %s" % default_config_string)
    default_config = config.Configuration.from_multipathd_conf(default_config_string)

    # write to /etc/multipath.conf
    client.write_to_multipathd_conf(default_config)

    # reconfigure
    util.StoreCmdRun("%s reconfigure " % util.MULTIPATHD)
