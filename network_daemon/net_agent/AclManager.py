#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import envoy
import logging
import traceback
from lxml import etree

from net_agent import AclManager_pb2
from net_agent import OvsManager
from net_agent import net_agent_util as util
from net_agent import net_agentd_exception


def generate_acl_rules_file(filter_type, filter_name, in_default_action, out_default_action, rules):
    if filter_type != AclManager_pb2.FILTER_BY_MAC and \
            filter_type != AclManager_pb2.FILTER_BY_IP:
        raise net_agentd_exception.NetAgentException("filter_type:%s error parameter" % filter_type)

    if in_default_action != "accept" and \
            in_default_action != "drop":
        raise net_agentd_exception.NetAgentException("in_default_action:%s error parameter" % in_default_action)

    if out_default_action != "accept" and \
            out_default_action != "drop":
        raise net_agentd_exception.NetAgentException("out_default_action:%s error parameter" % out_default_action)

    try:
        root = etree.Element("acl")

        etree.SubElement(root, "filter_name").text = filter_name
        etree.SubElement(root, "filter_type").text = "%d" % filter_type
        etree.SubElement(root, "in_default_action").text = "accept"
        etree.SubElement(root, "out_default_action").text = "accept"
        acl_rules = etree.SubElement(root, "acl_rules")

        for rule_item in rules:
            rule = etree.SubElement(acl_rules, "rule")
            if rule_item.priority:
                etree.SubElement(rule, "priority").text = rule_item.priority
            if rule_item.direction != AclManager_pb2.AclRule.IN and \
                    rule_item.direction != AclManager_pb2.AclRule.OUT and\
                    rule_item.direction != AclManager_pb2.AclRule.INOUT:
                raise net_agentd_exception.NetAgentException(
                    "rule_item.direction:%s error parameter" % rule_item.direction)
            else:
                etree.SubElement(rule, "direction").text = "%d" % rule_item.direction

            if filter_type == AclManager_pb2.FILTER_BY_MAC:
                if rule_item.src_mac:
                    if rule_item.src_mac_mask:
                        etree.SubElement(
                            rule, "src_mac_addr").text = "%s/%s" % (rule_item.src_mac, rule_item.src_mac_mask)
                    else:
                        etree.SubElement(rule, "src_mac_addr").text = rule_item.src_mac

                if rule_item.dst_mac:
                    if rule_item.dst_mac_mask:
                        etree.SubElement(
                            rule, "dst_mac_addr").text = "%s/%s" % (rule_item.dst_mac, rule_item.dst_mac_mask)
                    else:
                        etree.SubElement(rule, "dst_mac_addr").text = rule_item.dst_mac

                if rule_item.protocol in ["ALL", "ARP", "RARP", "IPv4", "IPv6"]:
                    etree.SubElement(rule, "protocol").text = rule_item.protocol
                else:
                    raise net_agentd_exception.NetAgentException(
                        "rule.protocol: %s error parameter" % rule_item.protocol)

            if filter_type == AclManager_pb2.FILTER_BY_IP:
                if rule_item.src_ip:
                    if rule_item.src_mask:
                        etree.SubElement(rule, "src_ip_addr").text = "%s/%s" % (rule_item.src_ip, rule_item.src_mask)
                    else:
                        etree.SubElement(rule, "src_ip_addr").text = rule_item.src_ip
                if rule_item.src_port:
                    etree.SubElement(rule, "src_port").text = rule_item.src_port

                if rule_item.dst_ip:
                    if rule_item.dst_mask:
                        etree.SubElement(rule, "dst_ip_addr").text = "%s/%s" % (rule_item.dst_ip, rule_item.dst_mask)
                    else:
                        etree.SubElement(rule, "dst_ip_addr").text = rule_item.dst_ip
                if rule_item.dst_port:
                    etree.SubElement(rule, "dst_port").text = rule_item.dst_port

                if rule_item.protocol in ["ALL", "ICMP", "TCP", "UDP"]:
                    etree.SubElement(rule, "protocol").text = rule_item.protocol
                else:
                    raise net_agentd_exception.NetAgentException("rule.protocol: %s error" % rule_item.protocol)

            if rule_item.action != "accept" and rule_item.action != "drop":
                raise net_agentd_exception.NetAgentException("rule_item.action:%s error parameter" % rule_item.action)
            else:
                etree.SubElement(rule, "actions").text = rule_item.action

        tree = etree.ElementTree(root)
        acl_rules_path = os.path.join(util.NET_AGENT_CONF_DIR, filter_name + '.xml')
        tree.write(acl_rules_path, pretty_print=True,
                   xml_declaration=True, encoding='utf-8')

    except Exception:
        logging.critical(traceback.format_exc())
        logging.error("failed to generate %s" % filter_name)


def remove_acl_rules_file(path):
    status = False

    if os.path.exists(path):
        try:
            os.remove(path)
            status = True
        except:
            logging.error("cannot remove %s" % path)

    return status


def parse_acl_rules_file(filter_name):
    rules = []

    path = os.path.join(util.NET_AGENT_CONF_DIR, filter_name + '.xml')
    xml_tree = util.ReadXml(path)
    acl_rules = util.GetXmlElementByXpath(xml_tree, 'acl_rules')
    in_default_action = util.GetXmlElementByXpath(xml_tree, 'in_default_action').text
    for acl_rule in acl_rules:
        rule = ""
        for item in acl_rule:
            if item.tag == "src_mac_addr":
                rule = rule + ',' + "dl_src=%s" % item.text
            if item.tag == "dst_mac_addr":
                rule = rule + ',' + "dl_src=%s" % item.text
            if item.tag == "src_ip_addr":
                rule = rule + ',' + "nw_src=%s" % item.text
            if item.tag == "src_port":
                rule = rule + ',' + "tp_src=%s" % item.text
            if item.tag == "dst_ip_addr":
                rule = rule + ',' + "nw_dst=%s" % item.text
            if item.tag == "dst_port":
                rule = rule + ',' + "tp_dst=%s" % item.text
            if item.tag == "protocol":
                if item.text == "ARP":
                    rule = rule + ',' + "dl_type=0x0806"
                if item.text == "RARP":
                    rule = rule + ',' + "dl_type=0x8035"
                if item.text == "IPv4":
                    rule = rule + ',' + "dl_type=0x0800"
                if item.text == "IPv6":
                    rule = rule + ',' + "dl_type=0x86dd"
                if item.text == "ICMP":
                    rule = rule + ',' + "dl_type=0x0800,nw_proto=1"
                if item.text == "TCP":
                    rule = rule + ',' + "dl_type=0x0800,nw_proto=6"
                if item.text == "UDP":
                    rule = rule + ',' + "dl_type=0x0800,nw_proto=17"
            if item.tag == "actions":
                if in_default_action == "accept" and item.text == "accept":
                    rule = rule + ' ' + "actions=Normal"
                else:
                    rule = rule + ' ' + "actions=drop"

        rule = rule.strip().lstrip(',')
        rules.append(rule)

    return rules


def get_filter_name(filter_name):
    name = ""

    path = os.path.join(util.NET_AGENT_CONF_DIR, filter_name + '.xml')
    if os.path.exists(path):
        xml_tree = util.ReadXml(path)
        name = util.GetXmlElementByXpath(xml_tree, 'filter_name').text
    else:
        raise net_agentd_exception.NetAgentException("%s doesnt exist" % filter_name + '.xml')

    if name == "":
        raise net_agentd_exception.NetAgentException("%s filter_name is null" % filter_name + '.xml')

    return name


def get_filter_type(filter_name):
    filter_type = ""

    path = os.path.join(util.NET_AGENT_CONF_DIR, filter_name + '.xml')
    if os.path.exists(path):
        xml_tree = util.ReadXml(path)
        filter_type = util.GetXmlElementByXpath(xml_tree, 'filter_type').text
        filter_type = int(filter_type)
    else:
        raise net_agentd_exception.NetAgentException("%s doesnt exist" % filter_name + '.xml')

    if filter_type != AclManager_pb2.FILTER_BY_MAC and filter_type != AclManager_pb2.FILTER_BY_IP:
        raise net_agentd_exception.NetAgentException("%s filter_type is error" % filter_name + '.xml')

    return filter_type


def get_in_default_action(filter_name):
    action = ""

    path = os.path.join(util.NET_AGENT_CONF_DIR, filter_name + '.xml')
    if os.path.exists(path):
        xml_tree = util.ReadXml(path)
        action = util.GetXmlElementByXpath(xml_tree, 'in_default_action').text
    else:
        raise net_agentd_exception.NetAgentException("%s doesnt exist" % filter_name + '.xml')

    if action != "accept" and action != "drop":
        raise net_agentd_exception.NetAgentException("%s in_default_action is err" % filter_name + '.xml')

    return action


def get_out_default_action(filter_name):
    action = ""

    path = os.path.join(util.NET_AGENT_CONF_DIR, filter_name + '.xml')
    if os.path.exists(path):
        xml_tree = util.ReadXml(path)
        action = util.GetXmlElementByXpath(xml_tree, 'in_default_action').text
    else:
        raise net_agentd_exception.NetAgentException("%s doesnt exist" % filter_name + '.xml')

    if action != "accept" and action != "drop":
        raise net_agentd_exception.NetAgentException("%s in_default_action is err" % filter_name + '.xml')

    return action


def get_filter_rules(filter_name):
    rules = []

    path = os.path.join(util.NET_AGENT_CONF_DIR, filter_name + '.xml')
    xml_tree = util.ReadXml(path)
    acl_rules = util.GetXmlElementByXpath(xml_tree, 'acl_rules')
    for acl_rule in acl_rules:
        rule = AclManager_pb2.AclRule()
        for item in acl_rule:
            if item.tag == "priority":
                rule.priority = item.text
            if item.tag == "direction":
                rule.direction = int(item.text)
            if item.tag == "protocol":
                rule.protocol = item.text
            if item.tag == "src_ip_addr":
                split = item.text.split('/', 1)
                rule.src_ip = split[0]
                if len(split) == 2:
                    rule.src_mask = split[1]
            if item.tag == "src_port":
                rule.src_port = item.text
            if item.tag == "src_mac_addr":
                split = item.text.split('/', 1)
                rule.src_mac = split[0]
                if len(split) == 2:
                    rule.src_mac_mask = split[1]
            if item.tag == "dst_ip_addr":
                split = item.text.split('/', 1)
                rule.dst_ip = split[0]
                if len(split) == 2:
                    rule.dst_mask = split[1]
            if item.tag == "dst_port":
                rule.dst_port = item.text
            if item.tag == "dst_mac_addr":
                split = item.text.split('/', 1)
                rule.dst_mac = split[0]
                if len(split) == 2:
                    rule.dst_mac_mask = split[1]

            if item.tag == "actions":
                rule.action = item.text

        rules.append(rule)

    return rules


class AclHandle(OvsManager.OvsHandle):
    def __init__(self,
                 vswitch_name="",
                 filter_name="default"):
        super(AclHandle, self).__init__(vswitch_name)
        self._filter_name = filter_name
        self._acl_rules_path = os.path.join(util.NET_AGENT_CONF_DIR, self._filter_name + '.xml')

    def attach_rules(self, ofport):
        while True:
            acl_rules = parse_acl_rules_file(self._filter_name)

            for rule in acl_rules:
                rule_split = rule.split(' ', 1)
                cmd_str = '%s add-flow %s \"%s\"' % (util.OVS_OFCTL_CMD, self._vswitch_name, rule_split[0].strip(
                ) + ',' + 'in_port=%s' % ofport + ' ' + rule_split[1].strip())
                ovs_cmd = envoy.run(cmd_str)
                if ovs_cmd.status_code != 0:
                    logging.error("%s failed:\n%s" % (cmd_str, ovs_cmd.std_err))
            break

    def detach_rules(self, ofport):
        while True:
            acl_rules = parse_acl_rules_file(self._filter_name)

            for rule in acl_rules:
                rule_split = rule.split(' ', 1)
                cmd_str = '%s del-flows %s \"%s\"' % (
                    util.OVS_OFCTL_CMD, self._vswitch_name, rule_split[0].strip() + ',' + 'in_port=%s' % ofport)
                ovs_cmd = envoy.run(cmd_str)
                if ovs_cmd.status_code != 0:
                    logging.error("%s failed:\n%s" % (cmd_str, ovs_cmd.std_err))
            break
