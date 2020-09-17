#!/usr/bin/env python
# -*- coding: utf-8 -*-

import envoy
import logging

from net_agent import UpLinkManager_pb2
from net_agent import NicManager
from net_agent import OvsManager

from net_agent import net_agent_util as util
from net_agent import net_agentd_exception


class UpLinkHandle(OvsManager.OvsHandle):
    def __init__(self, vswitch_name=""):
        super(UpLinkHandle, self).__init__(vswitch_name)

    def set_dynamic_bond(self, conf):
        nic_list = ""

        if conf.bond_mode != UpLinkManager_pb2.UpLinkConf.BALANCE_SLB and \
                conf.bond_mode != UpLinkManager_pb2.UpLinkConf.BALANCE_TCP:
            raise net_agentd_exception.NetAgentException('The bond_mode is incorrect')

        if conf.bond_name is None:
            raise net_agentd_exception.NetAgentException('The bond_name is incorrect')

        if conf.bond_mode == UpLinkManager_pb2.UpLinkConf.BALANCE_TCP:
            bond_mode = 'balance-tcp'
        if conf.bond_mode == UpLinkManager_pb2.UpLinkConf.BALANCE_SLB:
            bond_mode = 'balance-slb'

        for nic_name in conf.nic_names:
            nic_list = nic_list + ' ' + nic_name

        cmd_str = '%s add-bond %s %s %s lacp=active bond_mode=%s' % (util.OVS_VSCTL_CMD,
                                                                     self._vswitch_name,
                                                                     conf.bond_name,
                                                                     nic_list,
                                                                     bond_mode)
        cmd = envoy.run(cmd_str)
        if cmd.status_code == 0:
            logging.info('%s success' % cmd_str)
        else:
            raise net_agentd_exception.NetAgentException('%s failed \n%s' % (cmd_str, cmd.std_err))

    def set_static_bond(self, conf):
        nic_list = ""

        if conf.bond_mode != UpLinkManager_pb2.UpLinkConf.BALANCE_SLB and \
                conf.bond_mode != UpLinkManager_pb2.UpLinkConf.BALANCE_TCP and \
                conf.bond_mode != UpLinkManager_pb2.UpLinkConf.ACTIVE_BACKUP:
            raise net_agentd_exception.NetAgentException('The bond_mode range is incorrect')

        if conf.bond_mode == UpLinkManager_pb2.UpLinkConf.BALANCE_TCP:
            bond_mode = 'balance-tcp'
        if conf.bond_mode == UpLinkManager_pb2.UpLinkConf.BALANCE_SLB:
            bond_mode = 'balance-slb'
        if conf.bond_mode == UpLinkManager_pb2.UpLinkConf.ACTIVE_BACKUP:
            bond_mode = 'active-backup'

        for nic_name in conf.nic_names:
            nic_list = nic_list + ' ' + nic_name

        """
        :Because the difference between the active-backup mode and the other two mode is not clear,
        :so use two branches to solve this problem.
        """
        if conf.bond_mode == UpLinkManager_pb2.UpLinkConf.BALANCE_SLB or \
                conf.bond_mode == UpLinkManager_pb2.UpLinkConf.BALANCE_TCP:
            cmd_str = '%s add-bond %s %s %s lacp=off bond_mode=%s' % (util.OVS_VSCTL_CMD,
                                                                      self._vswitch_name,
                                                                      conf.bond_name,
                                                                      nic_list,
                                                                      bond_mode)

            cmd = envoy.run(cmd_str)
            if cmd.status_code == 0:
                logging.info('%s success' % cmd_str)
            else:
                raise net_agentd_exception.NetAgentException('%s failed \n%s' % (cmd_str, cmd.std_err))
        else:
            cmd_str = '%s add-bond %s %s %s lacp=off bond_mode=%s' % (util.OVS_VSCTL_CMD,
                                                                      self._vswitch_name,
                                                                      conf.bond_name,
                                                                      nic_list,
                                                                      bond_mode)

            cmd = envoy.run(cmd_str)
            if cmd.status_code == 0:
                logging.info('%s success' % cmd_str)
            else:
                raise net_agentd_exception.NetAgentException('%s failed \n%s' % (cmd_str, cmd.std_err))

    def set_single_uplink_port(self, nic):
        nic_object = NicManager.NicHandle(nic)
        if nic_object.get_nic_type() != NicManager.NicType.PHYSICAL or nic_object.is_nic_free() is False:
            raise net_agentd_exception.NetAgentException("nic is in use or not physical nic")

        cmd_str = '%s add-port %s %s' % (util.OVS_VSCTL_CMD, self._vswitch_name, nic)
        cmd = envoy.run(cmd_str)
        if cmd.status_code == 0:
            logging.info('%s success' % cmd_str)
        else:
            raise net_agentd_exception.NetAgentException('%s failed \n%s' % (cmd_str, cmd.std_err))

    def set_bond_uplink_port(self, conf):
        for nic in conf.nic_names:
            nic_object = NicManager.NicHandle(nic)
            if nic_object.get_nic_type() != NicManager.NicType.PHYSICAL or nic_object.is_nic_free() is False:
                raise net_agentd_exception.NetAgentException("nic is in use or not physical nic")

        if conf.lacp is True:
            self.set_dynamic_bond(conf)
        else:
            self.set_static_bond(conf)

    def get_uplink_port_name(self):
        uplink_port_name = ""

        try:
            phy_nics_list_uuid = []
            interface_list = self.get_interface_list()
            for interface in interface_list:
                nic_object = NicManager.NicHandle(interface)
                if nic_object.get_nic_type() == NicManager.NicType.PHYSICAL:
                    phy_nics_list_uuid.append(self.get_interface_uuid(interface))

            if len(phy_nics_list_uuid) == 0:
                logging.info("have no uplink port")
            if len(phy_nics_list_uuid) == 1:
                uplink_port_name = self.get_interface_name_by_uuid(phy_nics_list_uuid[0])
            if len(phy_nics_list_uuid) > 1:
                bond_port = []
                port_list = self.get_port_list()
                for port in port_list:
                    interface_uuid_list = self.get_interface_of_port(port)
                    for interface_uuid in interface_uuid_list:
                        if interface_uuid in phy_nics_list_uuid:
                            bond_port.append(port)

                if len(bond_port) != 1:
                    logging.error("too much uplink port")
                else:
                    uplink_port_name = bond_port[0]
        except:
            logging.error("get_uplink_port failed")

        return uplink_port_name
