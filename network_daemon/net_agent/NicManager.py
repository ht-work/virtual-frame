#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import psutil
import socket
import envoy
import logging
import traceback
from enum import Enum

from util_base import sys_util
from net_agent import net_agent_util as util
from net_agent import net_agentd_exception

from net_agent import NicManager_pb2


class NicHwClass(Enum):
    NONE = 1
    PCI = 2
    PLATFORM = 3


class NicType(Enum):
    NONE = 1
    PHYSICAL = 2
    VIRTUAL = 3


def get_nic_list(nic_type):
    nic_list = []

    try:
        for nic_name in os.listdir(util.SYS_CLASS_NET):
            nic_object = NicHandle(nic_name)
            type = nic_object.get_nic_type()

            if nic_type == NicManager_pb2.NicListQueryRequest.ALL_PHY_NIC \
                    or nic_type == NicManager_pb2.NicListQueryRequest.FREE_PHY_NIC:

                is_free = nic_object.is_nic_free()

                if type != NicType.PHYSICAL:
                    continue

                if nic_type == NicManager_pb2.NicListQueryRequest.FREE_PHY_NIC:
                    if is_free is False:
                        continue

                nic_list.append(nic_name)

            if nic_type == NicManager_pb2.NicListQueryRequest.VIRTUAL_NIC:
                if type != NicType.VIRTUAL:
                    continue

                nic_list.append(nic_name)

    except:
        logging.error(traceback.format_exc())
        raise net_agentd_exception.NetAgentException("get_nic_list failed")

    return nic_list


def MacAddr2NicName(mac_addr):
    nic_name = ""

    if re.match("([a-f0-9]{2}[:-]){5}[a-f0-9]{2}", mac_addr) is not None:
        try:
            net_ifs = psutil.net_if_addrs()
            for net_if in net_ifs.keys():
                for item in net_ifs[net_if]:
                    if int(socket.AF_PACKET) == item.family:
                        if item.address == mac_addr:
                            nic_name = net_if
        except:
            raise net_agentd_exception.NetAgentException("MacAddr2NicName failed")

    return nic_name


class NicHandle(object):
    def __init__(self, nic_name=""):
        self._nic_name = nic_name
        self._class_net_path = None
        self._real_net_path = None
        self._nic_class = NicHwClass.NONE
        self._conf_file_path = None

        if os.path.exists(os.path.join(util.SYS_CLASS_NET, nic_name)):
            self._class_net_path = os.path.join(util.SYS_CLASS_NET, nic_name)
            self._real_net_path = os.readlink(self._class_net_path)
            self._conf_file_path = os.path.join("/etc/sysconfig/network-scripts", "ifcfg-" + self._nic_name)
            if self._real_net_path.find("devices/pci") != -1:
                self._nic_class = NicHwClass.PCI
            if self._real_net_path.find("devices/platform") != -1:
                self._nic_class = NicHwClass.PLATFORM

    def get_description(self):
        description = ""

        if self._nic_class == NicHwClass.PCI:
            pci_node_pattern = re.compile(r'[0-9]{4}:[0-9]{2}:[0-9]{2}\.[0-9]')
            pci_nodes = pci_node_pattern.findall(self._real_net_path)
            pci_leaf_node = pci_nodes[-1]

            all_pci_description = envoy.run('%s -D' % util.LSPCI_CMD)
            if all_pci_description.status_code == 0:
                pci_description_raw = re.search(pci_leaf_node + '.*', all_pci_description.std_out).group()
                description = re.sub(pci_leaf_node + ' ', '', pci_description_raw, 1)
            else:
                raise net_agentd_exception.NetAgentException("%s failed to run" % util.LSPCI_CMD)

        if self._nic_class == NicHwClass.PLATFORM:
            description = "hns"

        return description

    def get_mac_address(self):
        mac_address = ""

        if self._class_net_path is not None:
            try:
                path = os.path.join(self._class_net_path, "address")
                mac_address = sys_util.cat(path).strip()
            except:
                logging.error("%s get mac address failed" % self._nic_name)
        else:
            raise net_agentd_exception.NetAgentException("%s doesnt exist" % self._nic_name)

        return mac_address

    def get_speed(self):
        speed = ""

        if self._class_net_path is not None:
            try:
                path = os.path.join(self._class_net_path, "speed")
                speed = sys_util.cat(path).strip()
            except:
                logging.error("%s get speed failed" % self._nic_name)
        else:
            raise net_agentd_exception.NetAgentException("%s doesnt exist" % self._nic_name)

        return speed

    def get_operstate(self):
        operstate = "down"

        if self._class_net_path is not None:
            cmd_str = '%s link show %s' % (util.IP_CMD, self._nic_name)
            ovs_show_cmd = envoy.run(cmd_str)
            if ovs_show_cmd.status_code == 0:
                result = re.search('[^_]UP', ovs_show_cmd.std_out)
                if result:
                    operstate = "up"
            else:
                logging.error("%s failed to run" % cmd_str)
        else:
            raise net_agentd_exception.NetAgentException("%s doesnt exist" % self._nic_name)

        return operstate

    def get_mtu(self):
        mtu = ""

        if self._class_net_path is not None:
            try:
                path = os.path.join(self._class_net_path, "mtu")
                mtu = sys_util.cat(path).strip()
            except:
                raise net_agentd_exception.NetAgentException("%s get mtu failed" % self._nic_name)
        else:
            raise net_agentd_exception.NetAgentException("%s doesnt exist" % self._nic_name)

        return mtu

    def set_mtu(self, mtu):
        min_mtu = 64
        max_mtu = 9216

        if int(mtu) < min_mtu or int(mtu) > max_mtu:
            raise net_agentd_exception.NetAgentException('The MTU range is incorrect')

        if self._class_net_path is not None:
            try:
                path = os.path.join(self._class_net_path, "mtu")
                sys_util.echo(path, mtu)
            except:
                raise net_agentd_exception.NetAgentException("%s set mtu failed" % self._nic_name)
        else:
            raise net_agentd_exception.NetAgentException("%s doesnt exist" % self._nic_name)

    def get_driver_name(self):
        driver_name = ""

        if self._class_net_path is not None:
            ethtool_output = envoy.run('%s -i %s' % (util.ETHTOOL_CMD, self._nic_name))
            if ethtool_output.status_code == 0:
                driver_name_raw = re.search('driver' + '.*', ethtool_output.std_out).group()
                driver_name = re.sub('driver' + ': ', '', driver_name_raw, 1)
            else:
                logging.error("%s failed to run\n%s" % (util.ETHTOOL_CMD, ethtool_output.std_err))
        else:
            raise net_agentd_exception.NetAgentException("%s doesnt exist" % self._nic_name)

        return driver_name

    def get_numa(self):
        numa = ""

        if self._class_net_path is not None:
            try:
                numa_node_path = os.path.join(self._class_net_path, "device/numa_node")
                if os.path.exists(numa_node_path):
                    numa = sys_util.cat(numa_node_path).strip()
            except:
                logging.error("%s get numa failed" % self._nic_name)
        else:
            raise net_agentd_exception.NetAgentException("%s doesnt exist" % self._nic_name)

        return numa

    def get_nic_address(self):
        nic_address = ""

        if self._nic_class == NicHwClass.PCI:
            pci_node_pattern = re.compile(r'[0-9]{4}:[0-9]{2}:[0-9]{2}\.[0-9]')
            pci_nodes = pci_node_pattern.findall(self._real_net_path)
            nic_address = pci_nodes[-1]

        if self._nic_class == NicHwClass.PLATFORM:
            platform_node_pattern = re.compile('HISI[0-9a-zA-Z]{4}:[0-9]{2}')
            platform_nodes = platform_node_pattern.findall(self._real_net_path)
            nic_address = platform_nodes[-1]

        return nic_address

    def get_carrier(self):
        carrier = ""

        if self._class_net_path is not None:
            try:
                path = os.path.join(self._class_net_path, "carrier")
                carrier = sys_util.cat(path).strip()
            except:
                logging.error("%s get carrier failed" % self._nic_name)
        else:
            raise net_agentd_exception.NetAgentException("%s doesnt exist" % self._nic_name)

        return carrier

    def get_duplex(self):
        duplex = ""

        if self._class_net_path is not None:
            try:
                path = os.path.join(self._class_net_path, "duplex")
                duplex = sys_util.cat(path).strip()
            except:
                logging.error("%s get duplex failed" % self._nic_name)
        else:
            raise net_agentd_exception.NetAgentException("%s doesnt exist" % self._nic_name)

        return duplex

    def get_tx_bytes(self):
        tx_bytes = ""

        if self._class_net_path is not None:
            try:
                path = os.path.join(self._class_net_path, "statistics/tx_bytes")
                tx_bytes = sys_util.cat(path).strip()
            except:
                logging.error("%s get tx_bytes failed" % self._nic_name)
        else:
            raise net_agentd_exception.NetAgentException("%s doesnt exist" % self._nic_name)

        return tx_bytes

    def get_tx_packets(self):
        tx_packets = ""

        if self._class_net_path is not None:
            try:
                path = os.path.join(self._class_net_path, "statistics/tx_packets")
                tx_packets = sys_util.cat(path).strip()
            except:
                logging.error("%s get tx_packets failed" % self._nic_name)
        else:
            raise net_agentd_exception.NetAgentException("%s doesnt exist" % self._nic_name)

        return tx_packets

    def get_tx_dropped(self):
        tx_dropped = ""

        if self._class_net_path is not None:
            try:
                path = os.path.join(self._class_net_path, "statistics/tx_dropped")
                tx_dropped = sys_util.cat(path).strip()
            except:
                logging.error("%s get tx_dropped failed" % self._nic_name)
        else:
            raise net_agentd_exception.NetAgentException("%s doesnt exist" % self._nic_name)

        return tx_dropped

    def get_tx_errors(self):
        tx_errors = ""

        if self._class_net_path is not None:
            try:
                path = os.path.join(self._class_net_path, "statistics/tx_errors")
                tx_errors = sys_util.cat(path).strip()
            except:
                logging.error("%s get tx_errors failed" % self._nic_name)
        else:
            raise net_agentd_exception.NetAgentException("%s doesnt exist" % self._nic_name)

        return tx_errors

    def get_rx_bytes(self):
        rx_bytes = ""

        if self._class_net_path is not None:
            try:
                path = os.path.join(self._class_net_path, "statistics/rx_bytes")
                rx_bytes = sys_util.cat(path).strip()
            except:
                logging.error("%s get rx_bytes failed" % self._nic_name)
        else:
            raise net_agentd_exception.NetAgentException("%s doesnt exist" % self._nic_name)

        return rx_bytes

    def get_rx_packets(self):
        rx_packets = ""

        if self._class_net_path is not None:
            try:
                path = os.path.join(self._class_net_path, "statistics/rx_packets")
                rx_packets = sys_util.cat(path).strip()
            except:
                logging.error("%s get rx_packets failed" % self._nic_name)
        else:
            raise net_agentd_exception.NetAgentException("%s doesnt exist" % self._nic_name)

        return rx_packets

    def get_rx_dropped(self):
        rx_dropped = ""

        if self._class_net_path is not None:
            try:
                path = os.path.join(self._class_net_path, "statistics/rx_dropped")
                rx_dropped = sys_util.cat(path).strip()
            except:
                logging.error("%s get rx_dropped failed" % self._nic_name)
        else:
            raise net_agentd_exception.NetAgentException("%s doesnt exist" % self._nic_name)

        return rx_dropped

    def get_rx_errors(self):
        rx_errors = ""

        if self._class_net_path is not None:
            try:
                path = os.path.join(self._class_net_path, "statistics/rx_errors")
                rx_errors = sys_util.cat(path).strip()
            except:
                logging.error("%s get rx_errors failed" % self._nic_name)
        else:
            raise net_agentd_exception.NetAgentException("%s doesnt exist" % self._nic_name)

        return rx_errors

    def get_raw_device(self):
        raw_device = ""

        if self._class_net_path is not None:
            raw_device_path = os.path.join(self._class_net_path, "device")
            real_raw_device_path = os.readlink(raw_device_path)
            raw_device_pattern = re.compile('[0-9a-zA-Z:.]{1,}')
            items = raw_device_pattern.findall(real_raw_device_path)
            raw_device = items[-1]
        else:
            raise net_agentd_exception.NetAgentException("%s doesnt exist" % self._nic_name)

        return raw_device

    def get_nic_type(self):
        virtual_driver = {"tun"}
        nic_type = NicType.NONE

        if self._class_net_path is not None:
            index = self._real_net_path.find("/virtual/")
            if index == -1:
                nic_type = NicType.PHYSICAL
            else:
                driver = self.get_driver_name()
                if driver in virtual_driver:
                    nic_type = NicType.VIRTUAL
        else:
            raise net_agentd_exception.NetAgentException("%s doesnt exist" % self._nic_name)

        return nic_type

    def is_nic_free(self):
        is_free = True

        if self._class_net_path is not None:
            cmd_str = '%s show' % util.OVS_VSCTL_CMD
            ovs_show_cmd = envoy.run(cmd_str)
            if ovs_show_cmd.status_code == 0:
                result = re.search('Interface "%s"' % self._nic_name, ovs_show_cmd.std_out)
                if result:
                    is_free = False
            else:
                logging.error("%s failed to run" % cmd_str)
        else:
            raise net_agentd_exception.NetAgentException("%s doesnt exist" % self._nic_name)

        return is_free

    def start_nic(self):
        if self._class_net_path is not None:
            cmd_str = '%s link set %s up' % (util.IP_CMD, self._nic_name)
            command = envoy.run(cmd_str)
            if command.status_code != 0:
                raise net_agentd_exception.NetAgentException("%s failed to run" % cmd_str)
        else:
            raise net_agentd_exception.NetAgentException("%s doesnt exist" % self._nic_name)

    def stop_nic(self):
        if self._class_net_path is not None:
            cmd_str = '%s link set %s down' % (util.IP_CMD, self._nic_name)
            command = envoy.run(cmd_str)
            if command.status_code != 0:
                raise net_agentd_exception.NetAgentException("%s failed to run" % cmd_str)
        else:
            raise net_agentd_exception.NetAgentException("%s doesnt exist" % self._nic_name)

    def get_driver_path_by_driver_name(self, driver_name):
        '''
        ty2280 nic sys path like /sys/bus/platform/drivers/hns-nic,
        but nic dirver name is "hns", so it cannot find sys path by dirver name.
        '''
        if driver_name == "hns":
            driver_name = "hns-nic"

        real_new_driver_path = ""

        find_cmd = envoy.run('%s /sys/bus -name %s' % (util.FIND_CMD, driver_name))
        if find_cmd.status_code == 0:
            new_driver_path = find_cmd.std_out.strip()
            index = new_driver_path.find("/drivers/%s" % driver_name)
            if index != -1:
                real_new_driver_path = new_driver_path
        else:
            raise net_agentd_exception.NetAgentException("%s failed to run" % util.FIND_CMD)

        if real_new_driver_path == "":
            raise net_agentd_exception.NetAgentException("driver %s doesnt exist" % driver_name)

        return real_new_driver_path

    def attach_driver(self, new_driver_path, raw_device):
        if raw_device == "" or os.path.join(new_driver_path) is False:
            raise net_agentd_exception.NetAgentException("parameter error")

        try:
            new_driver_bind_path = os.path.join(new_driver_path, "bind")
            sys_util.echo(new_driver_bind_path, raw_device)
        except:
            raise net_agentd_exception.NetAgentException('changer driver %s failed' % new_driver_path)

    def detach_driver(self):
        raw_device = self.get_raw_device()
        if raw_device:
            try:
                driver_unbind_path = os.path.join(self._class_net_path, "device/driver/unbind")
                sys_util.echo(driver_unbind_path, raw_device)
            except:
                raise net_agentd_exception.NetAgentException(
                    '%s detach driver %s failed' % (raw_device, driver_unbind_path))
        else:
            raise net_agentd_exception.NetAgentException("%s doesnt exist" % raw_device)

    def get_ip(self):
        ip_addr = ""

        try:
            net_ifs = psutil.net_if_addrs()
            for net_if in net_ifs.keys():
                if net_if == self._nic_name:
                    for item in net_ifs[net_if]:
                        if int(socket.AF_INET) == item.family:
                            ip_addr = item.address
        except:
            logging.error("get nic %s ip failed" % self._nic_name)

        return ip_addr

    def clear_ip(self):
        cmd_str = '%s addr flush dev %s' % (util.IP_CMD, self._nic_name)
        cmd = envoy.run(cmd_str)
        if cmd.status_code == 0:
            logging.info("%s clear ip success" % cmd_str)
        else:
            raise net_agentd_exception.NetAgentException("%s failed to run:\n%s" % (cmd_str, cmd.std_err))

    def set_ip_netmask(self, ip_addr, netmask):
        if re.match(r'((2(5[0-5]|[0-4]\d))|[0-1]?\d{1,2})(\.((2(5[0-5]|[0-4]\d))|[0-1]?\d{1,2})){3}', ip_addr) is None:
            raise net_agentd_exception.NetAgentException("set_ip_netmask: ip error")
        netmask_pattern = r'(((255\.){3}(255|254|252|248|240|224|192|128|0+))|' \
            r'((255\.){2}(255|254|252|248|240|224|192|128|0+)\.0)|' \
            r'((255\.)(255|254|252|248|240|224|192|128|0+)(\.0+){2})|' \
            r'((255|254|252|248|240|224|192|128|0+)(\.0+){3}))'
        if re.match(netmask_pattern, netmask) is None:
            raise net_agentd_exception.NetAgentException("set_ip_netmask: netmask error")

        self.save_conf_file_item("IPADDR", ip_addr)
        self.save_conf_file_item("NETMASK", netmask)

        self.clear_ip()

        cmd_str = '%s addr add %s/%s dev %s' % (util.IP_CMD, ip_addr, netmask, self._nic_name)
        cmd = envoy.run(cmd_str)
        if cmd.status_code == 0:
            logging.info("%s run success" % cmd_str)
        else:
            raise net_agentd_exception.NetAgentException("%s failed to run:\n%s" % (cmd_str, cmd.std_err))

    def get_netmask(self):
        netmask = ""

        try:
            net_ifs = psutil.net_if_addrs()
            for net_if in net_ifs.keys():
                if net_if == self._nic_name:
                    for item in net_ifs[net_if]:
                        if int(socket.AF_INET) == item.family:
                            netmask = item.netmask
        except:
            logging.error("get nic %s netmask failed" % self._nic_name)

        return netmask

    def get_gateway(self):
        gateway = ""

        cmd = envoy.run('%s route show' % util.IP_CMD)
        if cmd.status_code == 0:
            search = re.search('default via' + '.*' + self._nic_name, cmd.std_out)
            if search:
                default_gateway_line = search.group()
                ip_partern = r'(2(5[0-5]{1}|[0-4]\d{1})|[0-1]?\d{1,2})(\.(2(5[0-5]{1}|[0-4]\d{1})|[0-1]?\d{1,2})){3}'
                gateway = re.search(ip_partern, default_gateway_line).group()
        else:
            logging.error("%s route show failed to run:\n%s" % (util.IP_CMD, cmd.std_err))

        return gateway

    def set_gateway(self, gateway):
        if re.match(r'((2(5[0-5]|[0-4]\d))|[0-1]?\d{1,2})(\.((2(5[0-5]|[0-4]\d))|[0-1]?\d{1,2})){3}', gateway) is None:
            raise net_agentd_exception.NetAgentException("set_gateway: gateway error")

        cmd = envoy.run('%s route show' % util.IP_CMD)
        if cmd.status_code == 0:
            default_gateway_line_re = re.search('default via' + '.*', cmd.std_out)
            if default_gateway_line_re is not None:
                default_gateway_line = default_gateway_line_re.group()
                old_dev = re.search('dev .*', default_gateway_line)
                if old_dev != 'dev ' + self._nic_name:
                    logging.error("Disable setting up multiple default gateways")
                    return

        self.save_conf_file_item("GATEWAY", gateway)

        cmd = envoy.run('%s add default gw %s' % (util.ROUTE_CMD, gateway))
        if cmd.status_code == 0:
            logging.info("%s: setting default gateway success" % self._nic_name)
        else:
            raise net_agentd_exception.NetAgentException("%s: setting default gateway failed" % self._nic_name)

    def generate_conf_file(self):
        try:
            with open(self._conf_file_path, mode='w', encoding='utf-8') as conf_file:
                conf_file.write("DEVICE=%s\n" % self._nic_name)
                conf_file.write("NAME=%s\n" % self._nic_name)
                conf_file.write("ONBOOT=yes\n")
                conf_file.write("BOOTPROTO=static\n")

                conf_file.close()
        except Exception:
            raise net_agentd_exception.NetAgentException("failed to generate_conf_file %s" % self._conf_file_path)

    def save_conf_file_item(self, key, value):
        try:
            with open(self._conf_file_path, mode='r', encoding='utf-8') as old_file:
                conf = old_file.readlines()
                old_file.close()
        except Exception:
            logging.error("failed to open file %s" % self._conf_file_path)
            return

        re_condition = r'^(%s).*\d+$' % key
        find = False
        for line in conf:
            if re.match(re_condition, line):
                if value == "":
                    del conf[conf.index(line)]
                else:
                    conf[conf.index(line)] = "%s=%s\n" % (key, value)
                find = True

        if find is False:
            conf.append("%s=%s\n" % (key, value))

        try:
            with open(self._conf_file_path, mode='w', encoding='utf-8') as new_file:
                for line in conf:
                    new_file.write(line)
            new_file.close()
        except Exception:
            raise net_agentd_exception.NetAgentException("failed to open file %s" % self._conf_file_path)

    def clear_conf_file(self):
        try:
            if(os.path.exists(self._conf_file_path)):
                with open(self._conf_file_path, mode='w', encoding='utf-8') as file:
                    file.truncate()
                file.close()
        except:
            raise net_agentd_exception.NetAgentException("cannot clear generate_conf_file %s" % self._conf_file_path)

    def remove_conf_file(self):
        try:
            if(os.path.exists(self._conf_file_path)):
                os.remove(self._conf_file_path)
        except:
            raise net_agentd_exception.NetAgentException("cannot remove generate_conf_file %s" % self._conf_file_path)
