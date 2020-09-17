import logging
import traceback
import os
from lxml import etree
import util_base.log
import util_base.sys_util
from net_agent import net_agentd_exception

SYS_CLASS_NET = '/sys/class/net/'
NET_AGENT_CONF_DIR = '/opt/vap/net_agent/acl'
NET_AGENT_QOS_CONF_DIR = '/opt/vap/net_agent/qos'

OVS_VSCTL_CMD = '/usr/bin/ovs-vsctl'
OVS_OFCTL_CMD = '/usr/bin/ovs-ofctl'

IP_CMD = '/usr/sbin/ip'
ROUTE_CMD = '/usr/sbin/route'
LSPCI_CMD = '/usr/sbin/lspci'
ETHTOOL_CMD = '/usr/sbin/ethtool'
FIND_CMD = '/usr/bin/find'


def ReadXml(xml_file):
    """ read xml file
    :param request : xml file path
    :returns : etree._ElementTree
    """
    try:
        return etree.parse(xml_file)
    except OSError:
        logging.error(traceback.format_exc())
        raise net_agentd_exception.NetAgentException("OSError")
    except etree.LxmlError:
        logging.critical(traceback.format_exc())
        raise net_agentd_exception.NetAgentException("LxmlError")


def GetXmlElementByXpath(xml_tree, xpath):
    """ get Element from ElementTree by xpath
    :param request : xml tree
    :returns : etree._Element
    """
    try:
        return xml_tree.find(xpath)
    except OSError:
        logging.error(traceback.format_exc())
        raise net_agentd_exception.NetAgentException("OSError")
    except etree.LxmlError:
        logging.critical(traceback.format_exc())
        raise net_agentd_exception.NetAgentException("LxmlError")


class ExternalConfig(util_base.sys_util.BaseConfig):
    def __init__(self, file_path):
        if not os.path.exists(file_path):
            raise Exception('cannot access %s: No such file or directory' %
                            file_path)
        super(ExternalConfig, self).__init__(file_path)

    def ConfigGet(self, section='global', key=None):
        return self.Get(key, section)

    def ConfigSet(self, section='global', key=None, value=None):
        self.Set(key, value, section)

    def ConfigGetLogPath(self):
        return self.GetLogPath()

    def ConfigGetServicePort(self):
        return self.GetServicePort()

    def ConfigGetLogLevel(self):
        return self.GetLogLevel()
