#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import envoy
import logging

from net_agent import OvsManager_pb2
from net_agent import NicManager

from net_agent import net_agent_util as util
from net_agent import net_agentd_exception


def get_vswitch_list():
    vswitch_list = []

    cmd_str = '%s list-br' % util.OVS_VSCTL_CMD
    ovs_cmd = envoy.run(cmd_str)
    if ovs_cmd.status_code == 0:
        all_vswitchs = ovs_cmd.std_out.split("\n")
        vswitch_iter = iter(all_vswitchs)
        for vswitch in vswitch_iter:
            if vswitch != "":
                vswitch_list.append(vswitch)
    else:
        raise net_agentd_exception.NetAgentException("%s failed to run:\n%s" % (cmd_str, ovs_cmd.std_err))

    return vswitch_list


class OvsHandle(NicManager.NicHandle):
    def __init__(self, vswitch_name, internal_nic=""):
        if vswitch_name is None:
            raise net_agentd_exception.NetAgentException("must have vswitch_name")
        self._vswitch_name = vswitch_name
        if internal_nic == "":
            self._internal_nic = self._vswitch_name
        else:
            self._internal_nic = internal_nic
        self._conf_file_path = None

        if os.path.exists(os.path.join(util.SYS_CLASS_NET, self._internal_nic)):
            self._conf_file_path = os.path.join("/etc/sysconfig/network-scripts", "ifcfg-" + self._internal_nic)

        super(OvsHandle, self).__init__(self._internal_nic)

    def get_mode(self):
        mode = OvsManager_pb2.vSwitchConf.VEB

        return mode

    def get_vlan(self):
        vlan = ""

        cmd_str = '%s get Port %s tag' % (util.OVS_VSCTL_CMD, self._internal_nic)
        ovs_cmd = envoy.run(cmd_str)
        if ovs_cmd.status_code == 0:
            vlan = ovs_cmd.std_out.strip()
        else:
            raise net_agentd_exception.NetAgentException("%s failed to run:\n%s" % (ovs_cmd, ovs_cmd.std_err))

        return vlan

    def set_vlan(self, vlan_id):
        min_vlan = 1
        max_vlan = 4094

        if vlan_id == "":
            ovs_cmd = envoy.run('%s clear Port %s tag' % (util.OVS_VSCTL_CMD, self._internal_nic))
            return

        if int(vlan_id) < min_vlan or int(vlan_id) > max_vlan:
            raise net_agentd_exception.NetAgentException('The vlan id range is incorrect')

        cmd_str = '%s set Port %s tag=%s' % (util.OVS_VSCTL_CMD, self._internal_nic, vlan_id)
        ovs_cmd = envoy.run(cmd_str)
        if ovs_cmd.status_code == 0:
            logging.info("%s run success" % cmd_str)
        else:
            raise net_agentd_exception.NetAgentException("%s failed to run:\n%s" % (cmd_str, ovs_cmd.std_err))

    def set_vswitch_multicast(self, is_multicast):
        multicast = "false"
        if is_multicast is True:
            multicast = "true"
        else:
            multicast = "false"

        cmd_str = '%s set Bridge %s mcast_snooping_enable=%s' % (util.OVS_VSCTL_CMD,
                                                                 self._vswitch_name,
                                                                 multicast)
        ovs_cmd = envoy.run(cmd_str)
        if ovs_cmd.status_code != 0:
            raise net_agentd_exception.NetAgentException("%s failed to run:\n%s" % (cmd_str, ovs_cmd.std_err))

    def get_vswitch_multicast(self):
        is_multicast = False

        cmd_str = '%s get Bridge %s mcast_snooping_enable' % (util.OVS_VSCTL_CMD, self._vswitch_name)
        ovs_cmd = envoy.run(cmd_str)
        if ovs_cmd.status_code == 0:
            if ovs_cmd.std_out == "true":
                is_multicast = True
        else:
            raise net_agentd_exception.NetAgentException("%s failed to run:\n%s" % (cmd_str, ovs_cmd.std_err))

        return is_multicast

    def is_vswitch_link(self):
        is_free = False

        operstate = self.get_operstate()
        if operstate in ["up", "unknown"]:
            is_free = True

        return is_free

    def is_vswitch_exist(self):
        is_exist = False

        cmd_str = '%s br-exists %s' % (util.OVS_VSCTL_CMD, self._vswitch_name)
        ovs_cmd = envoy.run(cmd_str)
        if ovs_cmd.status_code == 0:
            is_exist = True
        else:
            logging.error("%s failed to run:\n%s" % (cmd_str, ovs_cmd.std_err))

        return is_exist

    def is_port_exist(self, port):
        is_exist = False

        ovs_cmd = envoy.run('%s port-to-br %s' % (util.OVS_VSCTL_CMD, port))
        if ovs_cmd.status_code == 0:
            if ovs_cmd.std_out.strip() == self._vswitch_name:
                is_exist = True
            else:
                logging.error("vswitch %s doesnt have port %s" % (self._vswitch_name, port))
        else:
            logging.error("port %s doesnt exist" % port)

        return is_exist

    def is_iface_exist(self, iface):
        is_exist = False

        ovs_cmd = envoy.run('%s iface-to-br %s' % (util.OVS_VSCTL_CMD, iface))
        if ovs_cmd.status_code == 0:
            if ovs_cmd.std_out.strip() == self._vswitch_name:
                is_exist = True
            else:
                logging.error("vswitch %s doesnt have iface %s" % (self._vswitch_name, iface))
        else:
            logging.error("iface %s doesnt exist" % iface)

        return is_exist

    def iface_to_ofport(self, iface):
        ofport = ""

        if self.is_iface_exist(iface):
            cmd_str = '%s get interface %s ofport' % (util.OVS_VSCTL_CMD, iface)
            ovs_cmd = envoy.run(cmd_str)
            if ovs_cmd.status_code == 0:
                ofport = ovs_cmd.std_out.strip()
            else:
                logging.error("%s failed to run:\n%s" % (cmd_str, ovs_cmd.std_err))
        else:
            raise net_agentd_exception.NetAgentException("iface %s doesnt exist,cannot get ofport" % iface)

        return ofport

    def remove_port(self, port):
        if self.is_port_exist(port) is True:
            ovs_cmd = envoy.run('%s del-port %s' % (util.OVS_VSCTL_CMD, port))
            if ovs_cmd.status_code != 0:
                raise net_agentd_exception.NetAgentException("remove port failed:\n%s" % ovs_cmd.std_err)

    def create_vswitch(self):
        retval = False

        cmd_str = '%s add-br %s' % (util.OVS_VSCTL_CMD, self._vswitch_name)
        ovs_cmd = envoy.run(cmd_str)
        if ovs_cmd.status_code == 0:
            self._conf_file_path = os.path.join("/etc/sysconfig/network-scripts", "ifcfg-" + self._vswitch_name)

            retval = True
        else:
            raise net_agentd_exception.NetAgentException("%s failed to run:\n%s" % (cmd_str, ovs_cmd.std_err))

        return retval

    def destroy_vswitch(self):
        retval = False

        cmd_str = '%s del-br %s' % (util.OVS_VSCTL_CMD, self._vswitch_name)
        ovs_cmd = envoy.run(cmd_str)
        if ovs_cmd.status_code == 0:
            retval = True
        else:
            raise net_agentd_exception.NetAgentException("%s failed to run:\n%s" % (cmd_str, ovs_cmd.std_err))

        return retval

    def generate_conf_file(self):
        try:
            with open(self._conf_file_path, mode='w', encoding='utf-8') as conf_file:
                conf_file.write("DEVICE=%s\n" % self._internal_nic)
                conf_file.write("NAME=%s\n" % self._internal_nic)
                conf_file.write("ONBOOT=yes\n")
                conf_file.write("DEVICETYPE=ovs\n")
                conf_file.write("TYPE=OVSBridge\n")
                conf_file.write("BOOTPROTO=static\n")

                conf_file.close()
        except Exception:
            raise net_agentd_exception.NetAgentException("failed to generate_conf_file %s" % self._conf_file_path)

    def get_port_list(self):
        port_list = []

        cmd_str = '%s list-ports %s' % (util.OVS_VSCTL_CMD, self._vswitch_name)
        cmd = envoy.run(cmd_str)
        if cmd.status_code == 0:
            port_list = cmd.std_out.strip('\n').rstrip(']').lstrip('[').split(',')
        else:
            raise net_agentd_exception.NetAgentException('%s failed \n%s' % (cmd_str, cmd.std_err))

        return port_list

    def get_interface_list(self):
        interface_list = []

        cmd_str = '%s list-ifaces %s' % (util.OVS_VSCTL_CMD, self._vswitch_name)
        cmd = envoy.run(cmd_str)
        if cmd.status_code == 0:
            interface_list = cmd.std_out.strip('\n').split('\n')
        else:
            raise net_agentd_exception.NetAgentException('%s failed \n%s' % (cmd_str, cmd.std_err))

        return interface_list

    def get_interface_uuid(self, interface):
        uuid = ""

        cmd_str = '%s get interface %s _uuid' % (util.OVS_VSCTL_CMD, interface)
        cmd = envoy.run(cmd_str)
        if cmd.status_code == 0:
            uuid = cmd.std_out.strip('\n')
        else:
            raise net_agentd_exception.NetAgentException('%s failed \n%s' % (cmd_str, cmd.std_err))

        return uuid

    def get_interface_name_by_uuid(self, uuid):
        name = ""

        cmd_str = '%s get interface %s name' % (util.OVS_VSCTL_CMD, uuid)
        cmd = envoy.run(cmd_str)
        if cmd.status_code == 0:
            name = cmd.std_out.strip('\n').strip("\"")
        else:
            raise net_agentd_exception.NetAgentException('%s failed \n%s' % (cmd_str, cmd.std_err))

        return name

    def get_interface_of_port(self, port):
        interface_list = []

        cmd_str = '%s get port %s interface' % (util.OVS_VSCTL_CMD, port)
        cmd = envoy.run(cmd_str)
        if cmd.status_code == 0:
            interface_list = cmd.std_out.strip('\n').strip(']').strip('[').split(',')
        else:
            raise net_agentd_exception.NetAgentException('%s failed \n%s' % (cmd_str, cmd.std_err))

        return interface_list
