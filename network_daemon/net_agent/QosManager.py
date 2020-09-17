#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import envoy
import logging
import json
from lxml import etree

from net_agent import OvsManager
from net_agent import net_agent_util as util
from net_agent import net_agentd_exception


class QosRule():
    def __init__(self):
        self.direction = ""
        self.average = ""
        self.peak = ""
        self.burst = ""


def check_qos_rules(rules):
    """Check the legality of the qos rules
    :param:{"rules": qos rules}
    """

    direction_list = []

    for rule in rules:
        direction = rule["direction"]
        if direction != "in" and direction != "out":
            raise net_agentd_exception.NetAgentException("direction %s error" % direction)
        if not rule["average"]:
            raise net_agentd_exception.NetAgentException("must have average")

        direction_list.append(direction)

    before_length = len(direction_list)
    direction_list = list(set(direction_list))
    after_length = len(direction_list)

    if before_length != after_length:
        raise net_agentd_exception.NetAgentException("rule have same direction")


def generate_qos_rules_file(qos_name, qos_rules):
    """generate qos_name.xml file by rules
    :param:{"qos_name": qos rule filename
            "qos_rules": qos rules}
    :return: rules list
    """

    root_xml = etree.Element("qos")

    etree.SubElement(root_xml, "qos_name").text = qos_name
    qos_rules_xml = etree.SubElement(root_xml, "qos_rules")

    qos_rules_json = json.loads(qos_rules)["rules"]
    check_qos_rules(qos_rules_json)

    for qos_rule_json in qos_rules_json:
        direction = qos_rule_json["direction"]
        average = qos_rule_json["average"]
        peak = qos_rule_json["peak"]
        burst = qos_rule_json["burst"]

        rule_xml = etree.SubElement(qos_rules_xml, "rule")

        etree.SubElement(rule_xml, "direction").text = "%s" % direction
        etree.SubElement(rule_xml, "average").text = average

        if peak:
            etree.SubElement(rule_xml, "peak").text = peak

        if burst:
            etree.SubElement(rule_xml, "burst").text = burst

    tree = etree.ElementTree(root_xml)
    qos_rules_path = os.path.join(util.NET_AGENT_QOS_CONF_DIR, qos_name + '.xml')
    tree.write(qos_rules_path, pretty_print=True,
               xml_declaration=True, encoding='utf-8')


def remove_qos_rules_file(path):
    try:
        os.remove(path)
    except Exception as e:
        logging.error("%s" % e)
        raise net_agentd_exception.NetAgentException("cannot remove %s" % path)


def get_qos_rules(qos_name):
    """parse qos_name.xml file to get qos rules
    :param:{"qos_name": qos rule filename}
    :return: rules list
    """
    rules = []

    path = os.path.join(util.NET_AGENT_QOS_CONF_DIR, qos_name + '.xml')
    xml_tree = util.ReadXml(path)
    qos_rules = util.GetXmlElementByXpath(xml_tree, 'qos_rules')
    for qos_rule in qos_rules:
        rule = QosRule()
        for item in qos_rule:
            if item.tag == "direction":
                rule.direction = item.text
            if item.tag == "average":
                rule.average = item.text
            if item.tag == "peak":
                rule.peak = item.text
            if item.tag == "burst":
                rule.burst = item.text

        rules.append(rule)

    return rules


def get_qos_rules_to_json(qos_name):
    """get qos rules use json format
    :param:{"qos_name": qos rule filename}
    :return: rules list str(json format)
    """

    rules = get_qos_rules(qos_name)
    qos_rules = {}
    qos_rules["rules"] = []

    for rule in rules:
        qos_rule = {}
        qos_rule["direction"] = rule.direction
        qos_rule["average"] = rule.average
        qos_rule["peak"] = rule.peak
        qos_rule["burst"] = rule.burst

        qos_rules["rules"].append(qos_rule)

    qos_json = json.dumps(qos_rules)

    return qos_json


class QosHandle(OvsManager.OvsHandle):
    def __init__(self,
                 vswitch_name="",
                 qos_name="default"):
        super(QosHandle, self).__init__(vswitch_name)
        self._qos_name = qos_name
        self._qos_rules_path = os.path.join(util.NET_AGENT_QOS_CONF_DIR, self._qos_name + '.xml')

    def attach_rules(self, iface):
        """attach rules to iface
        :param:{"iface": which iface will be attach qos rules}
        """

        qos_rules = get_qos_rules(self._qos_name)

        for rule in qos_rules:
            if rule.direction == "in":
                option = ''
                if rule.average:
                    option = "ingress_policing_rate=%s" % rule.average
                if rule.burst:
                    option = option + ' ' + "ingress_policing_burst=%s" % rule.burst

                cmd_str = '%s set Interface %s %s' % (util.OVS_VSCTL_CMD,
                                                      iface,
                                                      option)
                ovs_cmd = envoy.run(cmd_str)
                if ovs_cmd.status_code != 0:
                    raise net_agentd_exception.NetAgentException("%s failed:\n%s" % (cmd_str, ovs_cmd.std_err))
            if rule.direction == "out":
                cmd_str = '%s set port %s qos=@%s -- \
                           --id=@%s create qos type=linux-htb other-config:max-rate=%s other-config:qosname=%s\
                           queues:%s=@%squeue -- \
                           --id=@%squeue create queue other-config:min-rate=%s other-config:qosname=%s' % (
                               util.OVS_VSCTL_CMD,
                               iface,
                               self._qos_name,
                               self._qos_name,
                               rule.average,
                               self._qos_name,
                               self.iface_to_ofport(iface),
                               iface,
                               iface,
                               rule.average,
                               self._qos_name)
                ovs_cmd = envoy.run(cmd_str)
                if ovs_cmd.status_code != 0:
                    raise net_agentd_exception.NetAgentException("%s failed:\n%s" % (cmd_str, ovs_cmd.std_err))

                cmd_str = '%s add-flow %s \"in_port=%s, actions=set_queue:%s, normal\"' % (
                    util.OVS_OFCTL_CMD,
                    self._vswitch_name,
                    self.iface_to_ofport(iface),
                    self.iface_to_ofport(iface))
                ovs_cmd = envoy.run(cmd_str)
                if ovs_cmd.status_code != 0:
                    raise net_agentd_exception.NetAgentException("%s failed:\n%s" % (cmd_str, ovs_cmd.std_err))

    def detach_rules(self, iface):
        """detach rules to iface
        :param:{"iface": which iface will be detach qos rules}
        """

        qos_rules = get_qos_rules(self._qos_name)

        for rule in qos_rules:
            if rule.direction == "in":
                option = ''
                if rule.average:
                    option = "ingress_policing_rate=0"
                if rule.burst:
                    option = option + ' ' + "ingress_policing_burst=0"

                cmd_str = '%s set Interface %s %s' % (util.OVS_VSCTL_CMD,
                                                      iface,
                                                      option)
                ovs_cmd = envoy.run(cmd_str)
                if ovs_cmd.status_code != 0:
                    raise net_agentd_exception.NetAgentException("%s failed:\n%s" % (cmd_str, ovs_cmd.std_err))

            if rule.direction == "out":
                cmd_str = '%s clear port %s qos' % (util.OVS_VSCTL_CMD,
                                                    iface)
                ovs_cmd = envoy.run(cmd_str)
                if ovs_cmd.status_code != 0:
                    raise net_agentd_exception.NetAgentException("%s failed:\n%s" % (cmd_str, ovs_cmd.std_err))
