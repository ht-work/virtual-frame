#!/usr/bin/env python
# encoding: utf-8

from lxml import etree
import logging
import traceback
import platform

from . import virt_agent_exception as ve

LINUX_TEMPLATE = '/etc/vap/template.xml'
WINDOWS_TEMPLATE = '/etc/vap/template.xml'


def GetDomainXMLElemByXpath(dom_xml, xpath):
    '''
        input:
            dom_xml: lxml.etree._Element
            xpath: xpath string
        return lxml.etree._Element, from specified xpath
    '''
    try:
        return dom_xml.find(xpath)
    except etree.LxmlError:
        logging.error(traceback.format_exc())
        raise ve.VirtAgentDomainXMLException(xpath)


def GetDomainXMLElemArrayByXpath(dom_xml, xpath):
    '''
        input:
            dom_xml: lxml.etree._Element
            xpath: xpath string
        return lxml.etree._Element array, from specified xpath
    '''
    try:
        return dom_xml.findall(xpath)
    except etree.LxmlError:
        logging.error(traceback.format_exc())
        raise ve.VirtAgentDomainXMLException(xpath)


def GetDomainXMLElemDiskAll(dom_xml):
    '''
        return lxml.etree._Element array, from xpath 'devices[1]/disk'
    '''
    return GetDomainXMLElemArrayByXpath(dom_xml, 'devices[1]/disk')


class XmlManagerObject(object):
    def __init__(self, root_name=None):
        self.root_name = root_name

    def _get_uniq_child(self, root, node_name):
        node = root.xpath('./%s' % node_name)
        if len(node) == 0:
            return None
        if len(node) > 1:
            logging.error(traceback.format_exc())
            raise ve.VirtAgentDomainXMLException('more than one "%s" found in xml' % node_name)
        return node[0]

    def _get_child_array(self, root, node_name):
        return root.xpath('./%s' % node_name)

    def _list_children(self, root):
        return root.xpath('./*')

    def _get_uniq_child_text(self, root, node_name):
        text = root.xpath('./%s/text()' % node_name)
        if len(text) == 0:
            return None
        if len(text) > 1:
            logging.error(traceback.format_exc())
            raise ve.VirtAgentDomainXMLException('more than one "%s" found in xml' % node_name)
        return text[0]

    def _get_child_text_array(self, root, node_name):
        return root.xpath('./%s/text()' % node_name)

    def _get_child_property(self, root, node_name, prop_name, default=None):
        props = root.xpath('./%s/@%s' % (node_name, prop_name))
        if len(props) == 0:
            return default
        return props[0]

    def _get_child_property_array(self, root, node_name, prop_name):
        return root.xpath('./%s/@%s' % (node_name, prop_name))

    def _create_node(self, node_name, **kwargs):
        return etree.Element(node_name, **kwargs)

    def _create_text_node(self, node_name, value, **kwargs):
        node = self._create_node(node_name, **kwargs)
        node.text = value
        return node

    def _get_root_text(self, root):
        return root.text

    def _get_root_property(self, root, prop_name, default=None):
        if prop_name in root.attrib.keys():
            return root.attrib[prop_name]
        return default

    def _set_root_text(self, root, value):
        root.text = value

    def _set_root_property(self, root, prop_name, prop_value):
        if (prop_name is not None and prop_value is not None):
            root.attrib[prop_name] = prop_value

    def _del_node_property(self, root, prop_name):
        del(root.attrib[prop_name])

    def _add_child(self, root, child):
        root.append(child)

    def _del_child(self, root, child):
        root.remove(child)

    def parse_str(self, xmlstr):
        return self.parse(etree.fromstring(xmlstr))

    def parse(self, root):
        if root is None:
            raise ve.VirtAgentDomainXmlInvalidInputException('root is None')
        if root.tag != self.root_name:
            raise ve.VirtAgentDomainXmlInvalidInputException('root name must be %(root_name)s but not %(tag)s' % {
                                                             'root_name': self.root_name, 'tag': root.tag})

    def to_xml_tree(self, xml_str):
        return etree.XML(xml_str)

    def format(self):
        return self._create_node(self.root_name)

    def to_xml_str(self, pretty_print=True):
        return etree.tostring(self.format(), encoding='unicode',
                              pretty_print=pretty_print)

    def _to_dict(self):
        doc = {}
        for prop_name, prop_value in self.__dict__.items():
            if prop_name == 'root_name':
                continue
            doc[prop_name] = prop_value
        return doc

    def _get_property(self, prop_name):
        _prop = None
        if prop_name in self.__dict__.keys():
            _prop = self.__dict__.fromkeys(prop_name)
        return _prop

    def _update_property(self, prop_name, prop_value):
        if prop_name in self.__dict__.keys():
            self.__dict__.update({prop_name: prop_value})
        else:
            logging.warning('update %s: property %s is not supported' % (self.root_name, prop_name))

    def _update_properties(self, properties):
        for prop_name, prop_value in properties.items():
            if isinstance(prop_value, str):
                self._update_property(prop_name, prop_value)


class XmlManagerDomainSnapshot(XmlManagerObject):
    '''
    <domainsnapshot>
        <name>1566963079</name>
        <state>running</state>
          <creationTime>1566963079</creationTime>
        <memory snapshot='internal'/>
        <disks>
            <disk name='vda' snapshot='internal'/>
        </disks>
        <domain>
            ...
        </domain>
    </domainsnapshot>
    '''

    def __init__(self, root_name="domainsnapshot",
                 name=None,
                 state=None,
                 creationTime=None,
                 memory_snapshot=None,
                 memory_file=None,
                 parent=None,
                 active='0',
                 disks=[],
                 domain=None):
        self.root_name = root_name
        self.name = name
        self.state = state
        self.active = active
        self.parent = parent
        self.creationTime = creationTime
        self.memory_snapshot = memory_snapshot
        self.memory_file = memory_file
        self.disks = disks
        self.domain = domain

    def parse(self, root):
        self.disks = []
        self.name = self._get_uniq_child_text(root, 'name')
        self.state = self._get_uniq_child_text(root, 'state')
        self.creationTime = self._get_uniq_child_text(root, 'creationTime')
        self.memory_snapshot = self._get_child_property(root, 'memory', 'snapshot')
        if self.memory_snapshot == 'external':
            self.memory_file = self._get_child_property(root, 'memory', 'file')
        self.active = self._get_uniq_child_text(root, 'active')
        _parent = self._get_uniq_child(root, 'parent')
        if _parent is not None:
            self.parent = self._get_uniq_child_text(_parent, 'name')

        _disks = self._get_uniq_child(root, 'disks')
        for disk in self._get_child_array(_disks, 'disk'):
            _disk_obj = XmlManagerDomainSnapshotDisk()
            _disk_obj.parse(disk)
            self.disks.append(_disk_obj)
        _domain = self._get_uniq_child(root, 'domain')
        if _domain is not None:
            self.domain = XmlManagerDomain()
            self.domain.parse(_domain)

    def format(self):
        root = super(XmlManagerDomainSnapshot, self).format()
        self._add_child(root, self._create_text_node("name", self.name))
        self._add_child(root, self._create_text_node("state", self.state))
        self._add_child(root, self._create_text_node("creationTime", self.creationTime))
        self._add_child(root, self._create_text_node("active", self.active))
        if self.parent is not None:
            _parent = self._create_node("parent")
            self._add_child(_parent, self._create_text_node("name", self.parent))
            self._add_child(root, _parent)
        if self.memory_file is not None:
            self._add_child(root, self._create_node("memory", snapshot=self.memory_snapshot, file=self.memory_file))
        else:
            self._add_child(root, self._create_node("memory", snapshot=self.memory_snapshot))
        disks = self._create_node("disks")
        for disk in self.disks:
            self._add_child(disks, disk.format())
        self._add_child(root, disks)
        if self.domain is not None:
            self._add_child(root, self.domain.format())

        return root


class XmlManagerDomainSnapshotDisk(XmlManagerObject):
    def __init__(self, root_name="disk",
                 name=None,
                 snapshot=None,
                 driver_type=None,
                 source_file=None):
        self.root_name = root_name
        self.name = name
        self.snapshot = snapshot
        self.driver_type = driver_type
        self.source_file = source_file

    def parse(self, root):
        self.name = self._get_root_property(root, 'name')
        self.snapshot = self._get_root_property(root, 'snapshot')
        if self.snapshot == 'external':
            self.type = self._get_root_property(root, 'type')
            self.driver_type = self._get_child_property(root, 'driver', 'type')
            self.source_file = self._get_child_property(root, 'source', 'file')

    def format(self):
        root = super(XmlManagerDomainSnapshotDisk, self).format()
        self._set_root_property(root, 'name', self.name)
        self._set_root_property(root, 'snapshot', self.snapshot)
        if self.snapshot == 'external':
            self._add_child(root, self._create_node('driver', type=self.driver_type))
            self._add_child(root, self._create_node('source', file=self.source_file))

        return root


class XmlManagerDomain(XmlManagerObject):
    '''
        * Json format: read config / schema.json
        * Xml template: read config / template.xml
    '''

    def __init__(self):
        super(XmlManagerDomain, self).__init__(root_name="domain")

        self.type = None
        self.title = None
        self.uuid = None
        self.name = None
        self.memory = None
        self.currentMemory = None
        self.metadata = None
        self.on_poweroff = None
        self.on_reboot = None
        self.on_crash = None
        self.vcpu = None
        self.os = None
        self.clock = None
        self.features = None
        self.cpu = None
#        self.pm = None
        ''' devices is object array '''
        self.devices = []

    def _parse_basic_props(self, root):
        self.title = self._get_uniq_child_text(root, 'title')
        self.type = self._get_root_property(root, 'type')
        self.uuid = self._get_uniq_child_text(root, 'uuid')
        self.name = self._get_uniq_child_text(root, 'name')
        self.memory = self._get_uniq_child_text(root, 'memory')
        self.currentMemory = self._get_uniq_child_text(root, 'currentMemory')
        self.metadata = self._get_uniq_child_text(root, 'metadata')
        self.on_poweroff = self._get_uniq_child_text(root, 'on_poweroff')
        self.on_reboot = self._get_uniq_child_text(root, 'on_reboot')
        self.on_crash = self._get_uniq_child_text(root, 'on_crash')

    def parse(self, root):
        '''
            parse a xml file into XmlManagerDomain object
        '''
        super(XmlManagerDomain, self).parse(root)
        self._parse_basic_props(root)
        self.vcpu = XmlManagerDomainVCPU()
        self.vcpu.parse(self._get_uniq_child(root, 'vcpu'))
        self.clock = XmlManagerDomainClock()
        self.clock.parse(self._get_uniq_child(root, 'clock'))
        self.os = XmlManagerDomainOS()
        self.os.parse(self._get_uniq_child(root, 'os'))
        self.features = XmlManagerDomainFeatures()
        self.features.parse(self._get_uniq_child(root, 'features'))
        _cpu = self._get_uniq_child(root, 'cpu')
        if _cpu is not None:
            self.cpu = XmlManagerDomainCPU()
            self.cpu.parse(self._get_uniq_child(root, 'cpu'))
        if platform.machine() == 'x86_64':
            self.pm = XmlManagerDomainPM()
            self.pm.parse(self._get_uniq_child(root, 'pm'))
        else:
            logging.info('PM not supported on %s platform' % platform.machine())
        _devices = self._get_uniq_child(root, 'devices')
        for disk in self._get_child_array(_devices, 'disk'):
            _disk_obj = XmlManagerDomainDisk()
            _disk_obj.parse(disk)
            self.devices.append(_disk_obj)
        for interface in self._get_child_array(_devices, 'interface'):
            _interface_obj = XmlManagerDomainInterface()
            _interface_obj.parse(interface)
            self.devices.append(_interface_obj)
        for controller in self._get_child_array(_devices, 'controller'):
            _controller_obj = XmlManagerDomainController()
            _controller_obj.parse(controller)
            self.devices.append(_controller_obj)
        for input in self._get_child_array(_devices, 'input'):
            _input_obj = XmlManagerDomainInput()
            _input_obj.parse(input)
            self.devices.append(_input_obj)
        for graphics in self._get_child_array(_devices, 'graphics'):
            _graphics_obj = XmlManagerDomainGraphics()
            _graphics_obj.parse(graphics)
            self.devices.append(_graphics_obj)
        for video in self._get_child_array(_devices, 'video'):
            _video_obj = XmlManagerDomainVideo()
            _video_obj.parse(video)
            self.devices.append(_video_obj)
        for serial in self._get_child_array(_devices, 'serial'):
            _serial_obj = XmlManagerDomainSerial()
            _serial_obj.parse(serial)
            self.devices.append(_serial_obj)
        for console in self._get_child_array(_devices, 'console'):
            _console_obj = XmlManagerDomainConsole()
            _console_obj.parse(console)
            self.devices.append(_console_obj)
        for hub in self._get_child_array(_devices, 'hub'):
            _hub_obj = XmlManagerDomainHub()
            _hub_obj.parse(hub)
            self.devices.append(_hub_obj)
        for sound in self._get_child_array(_devices, 'sound'):
            _sound_obj = XmlManagerDomainSound()
            _sound_obj.parse(sound)
            self.devices.append(_sound_obj)
        for channel in self._get_child_array(_devices, 'channel'):
            _channel_obj = XmlManagerDomainChannel()
            _channel_obj.parse(channel)
            self.devices.append(_channel_obj)
        for memballoon in self._get_child_array(_devices, 'memballoon'):
            _memballoon_obj = XmlManagerDomainMemballoon()
            _memballoon_obj.parse(memballoon)
            self.devices.append(_memballoon_obj)

    def parse_template(self, os_type):
        '''
            parse a template xml file into XmlManagerDomain object
        '''
        root = None
        try:
            if os_type == 'windows':
                tree = etree.parse(WINDOWS_TEMPLATE)
            else:
                tree = etree.parse(LINUX_TEMPLATE)
            root = tree.getroot()
        except etree.LxmlError:
            logging.error(traceback.format_exc())
            raise ve.VirtAgentDomainXMLException('xml template is invalid')
        self.parse(root)

    def create_devices(self, json_data):
        '''
           json eg:
                {
                    'disk':[{'properties': {'driver_type':'raw', ...}],
                    'interface':[{'dev': '88:54:00:c8:ed:00', 'properties': {...}}]
                }
        '''
        for tag, devices in json_data.items():
            for device in devices:
                if tag == 'disk':
                    dev_obj = XmlManagerDomainDisk()
                elif tag == 'interface':
                    dev_obj = XmlManagerDomainInterface()
                    dev_obj.mac = device['dev']
                elif tag == 'controller':
                    dev_obj = XmlManagerDomainController()
                elif tag == 'input':
                    dev_obj = XmlManagerDomainInput()
                elif tag == 'graphics':
                    dev_obj = XmlManagerDomainGraphics()
                elif tag == 'video':
                    dev_obj = XmlManagerDomainVideo()
                elif tag == 'serial':
                    dev_obj = XmlManagerDomainSerial()
                elif tag == 'console':
                    dev_obj = XmlManagerDomainConsole()
                elif tag == 'hub':
                    dev_obj = XmlManagerDomainHub()
                elif tag == 'sound':
                    dev_obj = XmlManagerDomainSound()
                elif tag == 'channel':
                    dev_obj = XmlManagerDomainChannel()
                elif tag == 'memballoon':
                    dev_obj = XmlManagerDomainMemballoon()
                else:
                    logging.warning('device type %s is not supported' % tag)
                    continue

                dev_obj._update_properties(device['properties'])
                self.add_device(dev_obj)

        self._refresh_target_devs()

    def del_devices(self, json_data):
        '''
            eg:
                {
                    'disk':[{'target_dev': 'sda'}],
                    'interface':[{'mac': '88:54:00:c8:ed:00'}]
                }
        '''
        if 'disk' in json_data.keys():
            disks = self.get_devices(devtype='disk')
            for disk in disks:
                for item in json_data['disk']:
                    if disk.target_dev == item['dev']:
                        self.del_device(disk)
            self._refresh_target_devs()
        elif 'interface' in json_data.keys():
            interfaces = self.get_devices(devtype='interface')
            for interface in interfaces:
                for item in json_data['interface']:
                    if interface.mac == item['dev']:
                        self.del_device(interface)
        else:
            logging.warning('device type is not supported')

    def _refresh_target_devs(self):
        num_virtio = 0
        num_scsi = 0
        num_ide = 0
        for device in self.devices:
            if device.root_name == 'disk':
                if device.target_bus == 'virtio':
                    prefix = 'vd'
                    index = chr(ord('a') + num_virtio)
                    num_virtio += 1
                elif device.target_bus == 'scsi':
                    prefix = 'sd'
                    index = chr(ord('a') + num_scsi)
                    num_scsi += 1
                elif device.target_bus == 'ide':
                    prefix = 'hd'
                    index = chr(ord('a') + num_ide)
                    num_ide += 1
                else:
                    logging.warning('target bus type %s not supported.' % device.target_bus)
                device.target_dev = prefix + index

    def insert_cdrom(self, json_data):
        '''
            insert a cdrom
        '''
        if 'disk' in json_data.keys():
            disks = self.get_devices(devtype='disk')
            for disk in disks:
                for item in json_data['disk']:
                    if disk.target_dev == item['dev']:
                        disk.insert(item['properties']['source'])
        else:
            logging.warning('insert failed, no "disk" found in request')

    def eject_cdrom(self, json_data):
        '''
            eject a cdrom
        '''
        if 'disk' in json_data.keys():
            disks = self.get_devices(devtype='disk')
            for disk in disks:
                for item in json_data['disk']:
                    if disk.target_dev == item['dev']:
                        disk.eject()
        else:
            logging.warning('eject failed, no "disk" found in request')

    def update_properties(self, json_data):
        '''
            Use json to update XmlManagerDomain properties(parsed before update)
            json for create e.g:
                {
                    'titile':'',
                    'uuid':'',
                    'clock':'localtime',
                    'vcpu':{},
                    'memory':{},
                    'currentMemory':{},
                    'cpu':{},
                    'devices':[] # devices is never used
                }
            json for modify e.g:
                # only disk  and interface is supported to modify
                {
                    'disk':[{"dev":"", "properties":{...}}],
                    'interface':[{"dev":"", "properties":{...}}]
                }
        '''
        if 'clock' in json_data:
            self.clock._update_properties(json_data['clock'])
        if 'vcpu' in json_data:
            self.vcpu._update_properties(json_data['vcpu'])
        if 'cpu' in json_data:
            self.cpu._update_properties(json_data['cpu'])
        if 'devices' in json_data and 'disk' in json_data['devices'].keys():
            # you can also use {'disk':[{...}]...} to update devices
            for disk in self.get_devices(devtype='disk'):
                for item in json_data['devices']['disk']:
                    if disk.target_dev is None:
                        # add disk
                        disk._update_properties(item['properties'])
                    elif 'dev' in item and item['dev'] == disk.target_dev:
                        # modify disk
                        disk._update_properties(item['properties'])
        if 'devices' in json_data and'interface' in json_data['devices'].keys():
            for interface in self.get_devices(devtype='interface'):
                for item in json_data['devices']['interface']:
                    if interface.mac is None:
                        # add network
                        interface._update_properties(item['properties'])
                    elif item['dev'] == interface.mac:
                        # modify network
                        interface._update_properties(item['properties'])
        self._update_properties(json_data)

    def add_device(self, dev):
        self.devices.append(dev)

    def del_device(self, dev):
        self.devices.remove(dev)

    def get_devices(self, devtype='all'):
        devs = []
        for dev in self.devices:
            if(devtype == 'all' or dev.root_name == devtype):
                devs.append(dev)
        return devs

    def remove_backingStore(self):
        for disk in self.get_devices('disk'):
            disk.backingStore = None

    def _format_basic_props(self, root):
        self._set_root_property(root, 'type', self.type)
        self._add_child(root, self._create_text_node("title", self.title))
        self._add_child(root, self._create_text_node("uuid", self.uuid))
        self._add_child(root, self._create_text_node("name", self.name))
        self._add_child(root, self._create_text_node("memory", self.memory))
        self._add_child(root, self._create_text_node("currentMemory", self.currentMemory))
        self._add_child(root, self._create_text_node("metadata", self.metadata))
        self._add_child(root, self._create_text_node("on_poweroff", self.on_poweroff))
        self._add_child(root, self._create_text_node("on_reboot", self.on_reboot))
        self._add_child(root, self._create_text_node("on_crash", self.on_crash))

    def format(self):
        '''
            format XmlManagerDomain object properties and devices properties into XML
        '''
        root = super(XmlManagerDomain, self).format()
        self._format_basic_props(root)
        self._add_child(root, self.vcpu.format())
        self._add_child(root, self.clock.format())
        self._add_child(root, self.os.format())
        self._add_child(root, self.features.format())
        if self.cpu is not None:
            self._add_child(root, self.cpu.format())
        if platform.machine() == 'x86_64':
            self._add_child(root, self.pm.format())
        devices = self._create_node("devices")
        for device in self.devices:
            self._add_child(devices, device.format())
        self._add_child(root, devices)
        return root

    def to_dict(self):
        '''
            collect all properties of XmlManagerDomain and devices objects into a dictionary
        '''
        _dict = super(XmlManagerDomain, self)._to_dict()
        _dict['vcpu'] = self.vcpu._to_dict()
        _dict['os'] = self.os._to_dict()
        _dict['clock'] = self.clock._to_dict()
        _dict['features'] = self.features._to_dict()
        if self.cpu is not None:
            _dict['cpu'] = self.cpu._to_dict()
        if platform.machine() == 'x86_64':
            _dict['pm'] = self.pm._to_dict()
        _dict['devices'] = {}
        for device in self.devices:
            if device.root_name not in _dict['devices']:
                _dict['devices'][device.root_name] = []
            _dict['devices'][device.root_name].append(device._to_dict())
        return _dict


class XmlManagerDomainClock(XmlManagerObject):
    def __init__(self):
        super(XmlManagerDomainClock, self).__init__(root_name="clock")
        self.offset = None

    def parse(self, root):
        super(XmlManagerDomainClock, self).parse(root)
        self.offset = self._get_root_property(root, 'offset', default='utc')

    def format(self):
        root = super(XmlManagerDomainClock, self).format()
        self._set_root_property(root, 'offset', self.offset)
        return root


class XmlManagerDomainVCPU(XmlManagerObject):
    def __init__(self):
        super(XmlManagerDomainVCPU, self).__init__(root_name="vcpu")
        self.current = None
        self.num = None

    def parse(self, root):
        super(XmlManagerDomainVCPU, self).parse(root)
        self.num = self._get_root_text(root)
        self.current = self._get_root_property(root, 'current')
        if self.current is None:
            self.current = self.num

    def format(self):
        root = super(XmlManagerDomainVCPU, self).format()
        self._set_root_text(root, self.num)
        self._set_root_property(root, 'current', self.current)
        return root


class XmlManagerDomainOS(XmlManagerObject):
    def __init__(self):
        super(XmlManagerDomainOS, self).__init__(root_name="os")
        self.type = None
        self.arch = None
        self.machine = None
        ''' string array '''
        self.boots = []
        '''
            Needed by aarch64
        '''
        self.loader = None
        self.loader_type = None
        self.nvram = None

    def parse(self, root):
        super(XmlManagerDomainOS, self).parse(root)
        self.type = self._get_uniq_child_text(root, 'type')
        self.arch = self._get_child_property(root, 'type', 'arch')
        self.machine = self._get_child_property(root, 'type', 'machine')
        self.boots = self._get_child_property_array(root, 'boot', 'dev')
        self.loader_type = self._get_child_property(root, 'loader', 'type')
        self.loader = self._get_uniq_child_text(root, 'loader')
        self.nvram = self._get_uniq_child_text(root, 'nvram')

    def format(self):
        root = super(XmlManagerDomainOS, self).format()
        self._add_child(root, self._create_text_node("type", self.type, arch=self.arch, machine=self.machine))
        for boot in self.boots:
            self._add_child(root, self._create_node("boot", dev=boot))
        if self.loader is not None and self.loader_type is not None:
            self._add_child(root, self._create_text_node("loader", self.loader, type=self.loader_type))
        if self.nvram is not None:
            self._add_child(root, self._create_node("nvram"))
        return root


class XmlManagerDomainFeatures(XmlManagerObject):
    def __init__(self):
        super(XmlManagerDomainFeatures, self).__init__(root_name="features")
        ''' string array '''
        self.features = []

    def parse(self, root):
        super(XmlManagerDomainFeatures, self).parse(root)
        for feature in self._list_children(root):
            self.features.append(feature.tag)

    def format(self):
        root = super(XmlManagerDomainFeatures, self).format()
        for name in self.features:
            self._add_child(root, self._create_node(name))
        return root


class XmlManagerDomainCPU(XmlManagerObject):
    def __init__(self):
        super(XmlManagerDomainCPU, self).__init__(root_name="cpu")
        self.sockets = None
        self.cores = None
        self.threads = None
        '''
            Needed by qemu machine
        '''
        self.mode = None
        self.model = None

    def _parse_topology(self, root):
        self.sockets = self._get_child_property(root, 'topology', 'sockets', default='1')
        self.cores = self._get_child_property(root, 'topology', 'cores', default='1')
        self.threads = self._get_child_property(root, 'topology', 'threads', default='1')
        self.mode = self._get_root_property(root, 'mode')
        self.model = self._get_root_property(root, 'model')

    def _format_topology(self):
        return self._create_node('topology', sockets=self.sockets, cores=self.cores, threads=self.threads)

    def parse(self, root):
        super(XmlManagerDomainCPU, self).parse(root)
        self._parse_topology(root)

    def format(self):
        root = super(XmlManagerDomainCPU, self).format()
        self._add_child(root, self._format_topology())
        if self.mode is not None:
            self._set_root_property(root, 'mode', self.mode)
        if self.model is not None:
            self._set_root_property(root, 'model', self.model)

        return root


class XmlManagerDomainCPUNUMA(XmlManagerObject):
    def __init__(self):
        super(XmlManagerDomainCPUNUMA, self).__init__(root_name="numa")
        self.cells = []

    def parse(self, root):
        super(XmlManagerDomainCPUNUMA, self).parse(root)
        for cell in self._get_child_array(root, 'cell'):
            _cell_obj = XmlManagerDomainCPUNUMACell()
            _cell_obj.parse(cell)
            self.cells.append(_cell_obj)

    def format(self):
        root = super(XmlManagerDomainCPUNUMA, self).format()
        for cell in self.cells:
            self._add_child(root, cell.format())
        return root


class XmlManagerDomainCPUNUMACell(XmlManagerObject):
    def __init__(self):
        super(XmlManagerDomainCPUNUMACell, self).__init__(root_name="cell")
        self.id = None
        self.cpus = None
        self.memory = None
        self.unit = None
        self.discard = None

    def parse(self, root):
        super(XmlManagerDomainCPUNUMACell, self).parse(root)
        self.id = self._get_child_property(root, 'cell', 'id')
        self.cpus = self._get_child_property(root, 'cell', 'cpus')
        self.memory = self._get_child_property(root, 'cell', 'memory')
        self.unit = self._get_child_property(root, 'cell', 'unit')
        self.discard = self._get_child_property(root, 'cell', 'discard')
        logging.error('PPPid: %s, cpus: %s, memory:%s, unit:%s, discard:%s' %
                      (self.id, self.cpus, self.memory, self.unit, self.discard))

    def format(self):
        root = super(XmlManagerDomainCPUNUMACell, self).format()
        logging.error('FFFFid: %s, cpus: %s, memory:%s, unit:%s, discard:%s' %
                      (self.id, self.cpus, self.memory, self.unit, self.discard))
        self._create_node('cell', id=self.id, cpus=self.cpus, memory=self.memory, unit=self.unit, discard=self.discard)
        return root


class XmlManagerDomainPM(XmlManagerObject):
    def __init__(self):
        super(XmlManagerDomainPM, self).__init__(root_name="pm")
        ''' string array '''
        self.disabled = []

    def parse(self, root):
        super(XmlManagerDomainPM, self).parse(root)
        for strategy in self._list_children(root):
            self.disabled.append(strategy.tag)

    def format(self):
        root = super(XmlManagerDomainPM, self).format()
        for name in self.disabled:
            self._add_child(root, self._create_node(name, enabled='no'))
        return root


class XmlManagerDomainEmulator(XmlManagerObject):
    def __init__(self):
        super(XmlManagerDomainEmulator, self).__init__(root_name="emulator")
        self.emulator = None

    def parse(self, root):
        super(XmlManagerDomainEmulator, self).parse(root)
        self.emulator = self._get_uniq_child_text(root, 'emulator')

    def format(self):
        root = super(XmlManagerDomainEmulator, self).format()
        self._set_root_text('emulator', self.emulator)
        return root


class XmlManagerDomainBackingStore(XmlManagerObject):
    def __init__(self):
        super(XmlManagerDomainBackingStore, self).__init__(root_name="backingStore")
        self.type = None
        self.index = None
        self.format_type = None
        self.source_file = None
        self.backingStore = None

    def _to_dict(self):
        doc = {}
        doc = super(XmlManagerDomainBackingStore, self)._to_dict()
        if self.backingStore is not None:
            doc['backingStore'] = self.backingStore._to_dict()
        return doc

    def parse(self, root):
        super(XmlManagerDomainBackingStore, self).parse(root)
        self.type = self._get_root_property(root, 'type')
        self.index = self._get_root_property(root, 'index')
        self.format_type = self._get_child_property(root, 'format', 'type')
        self.source_file = self._get_child_property(root, 'source', 'file')
        _backingStore = self._get_uniq_child(root, 'backingStore')
        if _backingStore is not None:
            self.backingStore = XmlManagerDomainBackingStore()
            self.backingStore.parse(_backingStore)

    def format(self):
        root = super(XmlManagerDomainBackingStore, self).format()
        if self.type is not None:
            self._set_root_property(root, 'type', self.type)
        if self.index is not None:
            self._set_root_property(root, 'index', self.index)
        if self.format_type is not None:
            self._add_child(root, self._create_node('format', type=self.format_type))
        if self.source_file is not None:
            self._add_child(root, self._create_node('source', file=self.source_file))
        if self.backingStore is not None:
            self._add_child(root, self.backingStore.format())
        return root

    def change_source_file(self, origin, target):
        if self.source_file == origin:
            self.source_file = target
        elif self.backingStore is not None:
            self.backingStore.change_source_file(origin, target)


class XmlManagerDomainDeviceAddress(XmlManagerObject):
    def __init__(self):
        super(XmlManagerDomainDeviceAddress, self).__init__(root_name='address')
        self.type = None
        self.domain = None
        self.bus = None
        self.slot = None
        self.function = None
        self.multifunction = None
        self.controller = None
        self.target = None
        self.unit = None

    def parse(self, root):
        super(XmlManagerDomainDeviceAddress, self).parse(root)
        self.type = self._get_root_property(root, 'type')
        self.domain = self._get_root_property(root, 'domain')
        self.bus = self._get_root_property(root, 'bus')
        self.slot = self._get_root_property(root, 'slot')
        self.function = self._get_root_property(root, 'function')
        self.multifunction = self._get_root_property(root, 'multifunction')
        self.port = self._get_root_property(root, 'port')
        self.controller = self._get_root_property(root, 'controller')
        self.target = self._get_root_property(root, 'target')
        self.unit = self._get_root_property(root, 'unit')

    def format(self):
        root = super(XmlManagerDomainDeviceAddress, self).format()
        self._set_root_property(root, 'type', self.type)
        self._set_root_property(root, 'bus', self.bus)
        if self.domain is not None:
            self._set_root_property(root, 'domain', self.domain)
        if self.slot is not None:
            self._set_root_property(root, 'slot', self.slot)
        if self.function is not None:
            self._set_root_property(root, 'function', self.function)
        if self.multifunction is not None:
            self._set_root_property(root, 'multifunction', self.multifunction)
        if self.port is not None:
            self._set_root_property(root, 'prot', self.port)
        if self.controller is not None:
            self._set_root_property(root, 'controller', self.controller)
        if self.target is not None:
            self._set_root_property(root, 'target', self.target)

        if self.unit is not None:
            self._set_root_property(root, 'unit', self.unit)

        return root


class XmlManagerDomainDevice(XmlManagerObject):
    def __init__(self, root_name):
        super(XmlManagerDomainDevice, self).__init__(root_name=root_name)
        self.address = None

    def parse(self, root):
        super(XmlManagerDomainDevice, self).parse(root)
        _address = self._get_uniq_child(root, 'address')
        if _address is not None:
            self.address = XmlManagerDomainDeviceAddress()
            self.address.parse(_address)

    def format(self):
        root = super(XmlManagerDomainDevice, self).format()
        if self.address is not None:
            self._add_child(root, self.address.format())
        return root

    def _to_dict(self):
        doc = super(XmlManagerDomainDevice, self)._to_dict()
        if self.address is not None:
            doc['address'] = self.address._to_dict()
        return doc


class XmlManagerDomainDisk(XmlManagerDomainDevice):
    def __init__(self):
        super(XmlManagerDomainDisk, self).__init__(root_name="disk")
        ''' string array '''
        self.type = None
        self.device = None
        self.driver_name = None
        self.driver_type = None
        self.source = None
        self.target_dev = None
        self.target_bus = None
        self.backingStore = None

    def _to_dict(self):
        doc = {}
        doc['dev'] = self.target_dev
        doc['properties'] = super(XmlManagerDomainDisk, self)._to_dict()
        if self.backingStore is not None:
            doc['backingStore'] = self.backingStore._to_dict()
        return doc

    def change_backingfile(self, origin, target):
        if self.backingStore is not None:
            self.backingStore.change_source_file(origin, target)

    def parse(self, root):
        super(XmlManagerDomainDisk, self).parse(root)
        self.type = self._get_root_property(root, 'type')
        self.device = self._get_root_property(root, 'device')
        _driver_name = self._get_child_property(root, 'driver', 'name')
        if _driver_name is not None:
            self.driver_name = _driver_name
        _driver_type = self._get_child_property(root, 'driver', 'type')
        if _driver_type is not None:
            self.driver_type = _driver_type
        if self.type == 'file':
            self.source = self._get_child_property(root, 'source', 'file')
        else:
            self.source = self._get_child_property(root, 'source', 'dev')
        self.target_dev = self._get_child_property(root, 'target', 'dev')
        self.target_bus = self._get_child_property(root, 'target', 'bus')
        _backingStore = self._get_uniq_child(root, 'backingStore')
        if _backingStore is not None:
            self.backingStore = XmlManagerDomainBackingStore()
            self.backingStore.parse(_backingStore)

    def format(self):
        root = super(XmlManagerDomainDisk, self).format()
        self._set_root_property(root, 'type', self.type)
        self._set_root_property(root, 'device', self.device)
        if self.driver_name is not None and self.driver_type is not None:
            self._add_child(root, self._create_node('driver', name=self.driver_name, type=self.driver_type))
        if self.driver_name is not None and self.driver_type is None:
            self._add_child(root, self._create_node('driver', name=self.driver_name))
        if self.source is not None:
            if self.type == 'file':
                    self._add_child(root, self._create_node('source', file=self.source))
            else:
                    self._add_child(root, self._create_node('source', dev=self.source))
        self._add_child(root, self._create_node('target', dev=self.target_dev, bus=self.target_bus))
        if self.backingStore is not None:
            self._add_child(root, self.backingStore.format())
        return root

    def insert(self, path):
        self.source = path

    def eject(self):
        self.source = None


class XmlManagerDomainInterface(XmlManagerDomainDevice):
    def __init__(self):
        super(XmlManagerDomainInterface, self).__init__(root_name="interface")
        self.type = None
        self.mac = None
        self.source = None
        self.model_type = None
        self.driver_name = None
        self.hotpluggable_state = None

    def _to_dict(self):
        doc = {}
        doc['dev'] = self.mac
        doc['properties'] = super(XmlManagerDomainInterface, self)._to_dict()
        return doc

    def parse(self, root):
        super(XmlManagerDomainInterface, self).parse(root)
        self.mac = self._get_child_property(root, 'mac', 'address')
        self.type = self._get_root_property(root, 'type')
        if self.type == 'bridge':
            self.source = self._get_child_property(root, 'source', 'bridge')
        elif self.type == 'network':
            self.source = self._get_child_property(root, 'source', 'network')
        else:
            raise ve.VirtAgentNotImplementedException('Network type %s is not supported' % self.type)
        self.model_type = self._get_child_property(root, 'model', 'type')
        self.driver_name = self._get_child_property(root, 'driver', 'name')

    def format(self):
        root = super(XmlManagerDomainInterface, self).format()
        self._set_root_property(root, 'type', self.type)
        self._add_child(root, self._create_node('mac', address=self.mac))
        if self.type == 'bridge':
            self._add_child(root, self._create_node('source', bridge=self.source))
        elif self.type == 'network':
            self._add_child(root, self._create_node('source', network=self.source))
        else:
            err_msg = 'Network type %s is not supported' % self.type
            logging.error(err_msg)
            raise ve.VirtAgentNotImplementedException(err_msg)
        self._add_child(root, self._create_node('model', type=self.model_type))
        if self.driver_name is not None:
            self._add_child(root, self._create_node('driver', name=self.driver_name))
        return root


class XmlManagerDomainController(XmlManagerDomainDevice):
    def __init__(self):
        super(XmlManagerDomainController, self).__init__(root_name="controller")
        self.type = None
        self.index = None

    def parse(self, root):
        super(XmlManagerDomainController, self).parse(root)
        self.type = self._get_root_property(root, 'type')
        self.index = self._get_root_property(root, 'index')
        _model = self._get_root_property(root, 'model')
        if _model is not None:
            self.model = _model

    def format(self):
        root = super(XmlManagerDomainController, self).format()
        self._set_root_property(root, 'type', self.type)
        self._set_root_property(root, 'index', self.index)
        if self._get_property('model') is not None:
            self._set_root_property(root, 'model', self.model)

        return root


class XmlManagerDomainInput(XmlManagerDomainDevice):
    def __init__(self):
        super(XmlManagerDomainInput, self).__init__(root_name="input")
        self.type = None
        self.bus = None

    def parse(self, root):
        super(XmlManagerDomainInput, self).parse(root)
        self.type = self._get_root_property(root, 'type')
        self.bus = self._get_root_property(root, 'bus')

    def format(self):
        root = super(XmlManagerDomainInput, self).format()
        self._set_root_property(root, 'type', self.type)
        self._set_root_property(root, 'bus', self.bus)
        return root


class XmlManagerDomainGraphics(XmlManagerDomainDevice):
    def __init__(self):
        super(XmlManagerDomainGraphics, self).__init__(root_name="graphics")
        self.type = None
        self.port = None
        self.autoport = None
        self.listen = None

    def parse(self, root):
        super(XmlManagerDomainGraphics, self).parse(root)
        self.type = self._get_root_property(root, 'type')
        self.port = self._get_root_property(root, 'port', default='-1')
        self.autoport = self._get_root_property(root, 'autoport', default='yes')
        self.listen = self._get_root_property(root, 'listen', default='0.0.0.0')

    def format(self):
        root = super(XmlManagerDomainGraphics, self).format()
        self._set_root_property(root, 'type', self.type)
        self._set_root_property(root, 'port', self.port)
        self._set_root_property(root, 'autoport', self.autoport)
        self._set_root_property(root, 'listen', self.listen)
        return root


class XmlManagerDomainVideo(XmlManagerDomainDevice):
    def __init__(self):
        super(XmlManagerDomainVideo, self).__init__(root_name="video")
        self.model_type = None
        self.model_vram = None
        self.primary = None

    def parse(self, root):
        super(XmlManagerDomainVideo, self).parse(root)
        self.model_type = self._get_child_property(root, 'model', 'type', default='virtio')
        self.model_vram = self._get_child_property(root, 'model', 'vram', default='65536')
        self.primary = self._get_child_property(root, 'model', 'primary', default='no')

    def format(self):
        root = super(XmlManagerDomainVideo, self).format()
        self._add_child(
            root,
            self._create_node(
                'model',
                type=self.model_type,
                vram=self.model_vram,
                primary=self.primary))
        return root


class XmlManagerDomainSerial(XmlManagerDomainDevice):
    def __init__(self):
        super(XmlManagerDomainSerial, self).__init__(root_name="serial")
        self.type = None
        self.source_path = None
        self.target_type = None
        self.target_port = None
        self.model_name = None

    def parse(self, root):
        super(XmlManagerDomainSerial, self).parse(root)
        self.type = self._get_root_property(root, 'type')
        self.source_path = self._get_child_property(root, 'source', 'path')
        self.target_type = self._get_child_property(root, 'target', 'type')
        self.target_port = self._get_child_property(root, 'target', 'port')
        _target = self._get_uniq_child(root, 'target')
        self.model_name = self._get_child_property(_target, 'model', 'name')

    def format(self):
        root = super(XmlManagerDomainSerial, self).format()
        self._set_root_property(root, 'type', self.type)
        if self.source_path is not None:
            self._add_child(root, self._create_node('source', path=self.source_path))
        self._add_child(root, self._create_node('target', type=self.target_type, port=self.target_port))
        self._add_child(self._get_uniq_child(root, 'target'), self._create_node('model', name=self.model_name))
        return root


class XmlManagerDomainConsole(XmlManagerDomainDevice):
    def __init__(self):
        super(XmlManagerDomainConsole, self).__init__(root_name="console")
        self.type = None
        self.target_type = None
        self.target_port = None

    def parse(self, root):
        super(XmlManagerDomainConsole, self).parse(root)
        self.type = self._get_root_property(root, 'type')
        self.target_type = self._get_child_property(root, 'target', 'type')
        self.target_port = self._get_child_property(root, 'target', 'port')

    def format(self):
        root = super(XmlManagerDomainConsole, self).format()
        self._set_root_property(root, 'type', self.type)
        self._add_child(root, self._create_node('target', type=self.target_type, port=self.target_port))
        return root


class XmlManagerDomainHub(XmlManagerDomainDevice):
    def __init__(self):
        super(XmlManagerDomainHub, self).__init__(root_name="hub")
        self.type = None

    def parse(self, root):
        super(XmlManagerDomainHub, self).parse(root)
        self.type = self._get_root_property(root, 'type')

    def format(self):
        root = super(XmlManagerDomainHub, self).format()
        self._set_root_property(root, 'type', self.type)
        return root


class XmlManagerDomainSound(XmlManagerDomainDevice):
    def __init__(self):
        super(XmlManagerDomainSound, self).__init__(root_name="sound")
        self.model = None

    def parse(self, root):
        super(XmlManagerDomainSound, self).parse(root)
        self.model = self._get_root_property(root, 'model')

    def format(self):
        root = super(XmlManagerDomainSound, self).format()
        self._set_root_property(root, 'model', self.model)
        return root


class XmlManagerDomainChannel(XmlManagerDomainDevice):
    def __init__(self):
        super(XmlManagerDomainChannel, self).__init__(root_name="channel")
        self.type = None
        self.target_type = None
        self.target_name = None

    def parse(self, root):
        super(XmlManagerDomainChannel, self).parse(root)
        self.type = self._get_root_property(root, 'type')
        self.target_type = self._get_child_property(root, 'target', 'type')
        self.target_name = self._get_child_property(root, 'target', 'name')

    def format(self):
        root = super(XmlManagerDomainChannel, self).format()
        self._set_root_property(root, 'type', self.type)
        self._add_child(root, self._create_node('target', type=self.target_type, name=self.target_name))
        return root


class XmlManagerDomainMemballoon(XmlManagerDomainDevice):
    def __init__(self):
        super(XmlManagerDomainMemballoon, self).__init__(root_name="memballoon")
        self.model = None

    def parse(self, root):
        super(XmlManagerDomainMemballoon, self).parse(root)
        self.model = self._get_root_property(root, 'model')

    def format(self):
        root = super(XmlManagerDomainMemballoon, self).format()
        self._set_root_property(root, 'model', self.model)
        return root
