#!/usr/bin/env python
# encoding: utf-8
import grpc
import uuid
import pytest
import socket
import time
import traceback
import json
import envoy
from lxml import etree

import libvirt
from google.protobuf import empty_pb2 as empty_pb
from util_base.libvirt_util import ConnectionPool

import base
from virt_agent import virt_agent_pb2 as pb
from virt_agent import virt_agent_pb2_grpc as pb_grpc
from virt_agent import xml_util
from sysagent import sysagent_pb2, sysagent_pb2_grpc, util_pb2


class TestCaseCreateDomain(base.TestCaseDomainBase):
    def setup(self):
        super(TestCaseCreateDomain, self).setup()

    def test_create_domain(self):
        _uuid = str(uuid.uuid4())
        request = pb.DomainCreateReq(os_type='linux', json_data=self.json_template % (_uuid, _uuid))
        try:
            res = self.stub.CreateDomain(request, timeout=10)
        except Exception:
            assert 0

        assert pb.LIBVIRT_ERR_OK == res.code
        assert '' == res.err_msg

        domain = self.conn.lookupByUUIDString(_uuid)
        dom_xml = etree.XML(domain.XMLDesc())
        node_tags = []
        device_tags = []
        for c in dom_xml.getchildren():
            node_tags.append(c.tag)
            if c.tag == 'devices':
                for t in c:
                    device_tags.append(t.tag)

        assert 'title' in node_tags
        assert 'name' in node_tags
        assert 'uuid' in node_tags
        assert 'memory' in node_tags
        assert 'currentMemory' in node_tags
        assert 'vcpu' in node_tags
        assert 'os' in node_tags
        assert 'metadata' in node_tags
        assert 'features' in node_tags
        assert 'cpu' in node_tags
        assert 'pm' in node_tags
        assert 'devices' in node_tags
        assert 'on_poweroff' in node_tags
        assert 'on_reboot' in node_tags
        assert 'on_crash' in node_tags
        assert 'emulator' in device_tags
        assert 'controller' in device_tags
        assert 'input' in device_tags
        assert 'graphics' in device_tags
        assert 'video' in device_tags
        assert 'serial' in device_tags
        assert 'console' in device_tags
        assert 'hub' in device_tags
        assert pb.LIBVIRT_ERR_OK == res.code
        assert '' == res.err_msg

        request = pb.DomainDeleteReq(uuid=_uuid)
        try:
            res = self.stub.DeleteDomain(request, timeout=10)
        except Exception:
            assert 0

    def test_create_domain_multi_interfaces(self):
        _uuid = str(uuid.uuid4())
        self.json_template = """{
                                "type": "qemu",
                                "name": "test_%s",
                                "uuid": "%s",
                                "memory": "1048576",
                                "currentMemory": "1048576",
                                "vcpu":{
                                    "num":"1",
                                    "current":"1"
                                },
                                "cpu":  {
                                    "sockets":"1",
                                    "cores":"1"
                                },
                                "title": "test_domain_title",
                                "metadata":"",
                                "os": {
                                    "boot": [
                                        {
                                            "dev":"hd"
                                        },
                                        {
                                            "dev":"cdrom"
                                        }
                                    ]
                                },
                                "devices": {
                                    "disk":[{
                                        "dev":"hda",
                                        "properties": {
                                            "type":"file",
                                            "device":"cdrom",
                                            "driver_type":"raw",
                                            "driver_name":"qemu",
                                            "source":"/tmp/test_base.iso",
                                            "target_bus":"ide"
                                        }
                                    }],
                                    "interface": [{
                                            "dev":"88:54:00:c8:ed:00",
                                            "properties": {
                                                "type": "bridge",
                                                "source": "vswitch0",
                                                "model_type":"virtio",
                                                "driver_name":"vhost"
                                            }
                                        },
                                        {
                                            "dev":"52:54:00:c4:d3:b2",
                                            "properties": {
                                                "type": "bridge",
                                                "source": "vswitch0",
                                                "model_type":"virtio",
                                                "driver_name":"vhost"
                                            }
                                    }]
                                }}"""
        request = pb.DomainCreateReq(os_type='linux', json_data=self.json_template % (_uuid, _uuid))
        try:
            res = self.stub.CreateDomain(request, timeout=10)
        except Exception:
            assert 0

        assert pb.LIBVIRT_ERR_OK == res.code
        assert '' == res.err_msg

        domain = self.conn.lookupByUUIDString(_uuid)
        dom_xml = etree.XML(domain.XMLDesc())
        node_tags = []
        device_tags = []
        for c in dom_xml.getchildren():
            node_tags.append(c.tag)
            if c.tag == 'devices':
                for t in c:
                    device_tags.append(t.tag)

        dom = self.conn.lookupByUUIDString(_uuid)
        dom_xml = etree.XML(dom.XMLDesc())
        addresses = []
        macs = dom_xml.xpath('//mac')
        for c in macs:
            addresses.append(c.get('address'))
        assert len(macs) == 2
        assert "88:54:00:c8:ed:00" in addresses
        assert "52:54:00:c4:d3:b2"in addresses
        assert 'title' in node_tags
        assert 'name' in node_tags
        assert 'uuid' in node_tags
        assert 'memory' in node_tags
        assert 'currentMemory' in node_tags
        assert 'vcpu' in node_tags
        assert 'os' in node_tags
        assert 'metadata' in node_tags
        assert 'features' in node_tags
        assert 'cpu' in node_tags
        assert 'pm' in node_tags
        assert 'devices' in node_tags
        assert 'on_poweroff' in node_tags
        assert 'on_reboot' in node_tags
        assert 'on_crash' in node_tags
        assert 'emulator' in device_tags
        assert 'controller' in device_tags
        assert 'input' in device_tags
        assert 'graphics' in device_tags
        assert 'video' in device_tags
        assert 'serial' in device_tags
        assert 'console' in device_tags
        assert 'hub' in device_tags
        assert pb.LIBVIRT_ERR_OK == res.code
        assert '' == res.err_msg

        request = pb.DomainDeleteReq(uuid=_uuid)
        try:
            res = self.stub.DeleteDomain(request, timeout=10)
        except Exception:
            assert 0

    def test_create_domain_with_empty_cdrom(self):
        _uuid = str(uuid.uuid4())
        self.json_template = """{
                                "type": "qemu",
                                "name": "test_%s",
                                "uuid": "%s",
                                "memory": "1048576",
                                "currentMemory": "1048576",
                                "clock": {
                                    "offset": "localtime"
                                },
                                "vcpu":{
                                    "num":"1",
                                    "current":"1"
                                },
                                "cpu":  {
                                    "sockets":"1",
                                    "cores":"1"
                                },
                                "title": "test_domain_title",
                                "metadata":"",
                                "os": {
                                    "boot": [
                                        {
                                            "dev":"hd"
                                        },
                                        {
                                            "dev":"cdrom"
                                        }
                                    ]
                                },
                                "devices": {
                                    "disk":[{
                                        "dev":"hda",
                                        "properties": {
                                            "type":"file",
                                            "device":"cdrom",
                                            "driver_type":"raw",
                                            "driver_name":"qemu",
                                            "target_bus":"ide"
                                        }
                                    }],
                                    "interface": [{
                                        "dev":"52:54:00:c4:d3:b2",
                                        "properties": {
                                            "type": "bridge",
                                            "source": "vswitch0",
                                            "model_type":"virtio",
                                            "driver_name":"vhost"
                                        }
                                    }]
                                }}"""
        request = pb.DomainCreateReq(os_type='linux', json_data=self.json_template % (_uuid, _uuid))
        try:
            res = self.stub.CreateDomain(request, timeout=10)
        except Exception:
            assert 0

        assert pb.LIBVIRT_ERR_OK == res.code
        assert '' == res.err_msg

        domain = self.conn.lookupByUUIDString(_uuid)
        dom_xml = etree.XML(domain.XMLDesc())
        node_tags = []
        device_tags = []
        for c in dom_xml.getchildren():
            node_tags.append(c.tag)
            if c.tag == 'devices':
                for t in c:
                    device_tags.append(t.tag)

        dom = self.conn.lookupByUUIDString(_uuid)
        dom_xml = etree.XML(dom.XMLDesc())
        disks = dom_xml.xpath('//disk')
        assert len(disks) == 1
        assert disks[0].get('source') is None
        assert 'title' in node_tags
        assert 'name' in node_tags
        assert 'uuid' in node_tags
        assert 'clock' in node_tags
        assert 'memory' in node_tags
        assert 'currentMemory' in node_tags
        assert 'vcpu' in node_tags
        assert 'os' in node_tags
        assert 'metadata' in node_tags
        assert 'features' in node_tags
        assert 'cpu' in node_tags
        assert 'pm' in node_tags
        assert 'devices' in node_tags
        assert 'on_poweroff' in node_tags
        assert 'on_reboot' in node_tags
        assert 'on_crash' in node_tags
        assert 'emulator' in device_tags
        assert 'controller' in device_tags
        assert 'disk' in device_tags
        assert 'input' in device_tags
        assert 'graphics' in device_tags
        assert 'video' in device_tags
        assert 'serial' in device_tags
        assert 'console' in device_tags
        assert 'hub' in device_tags
        assert pb.LIBVIRT_ERR_OK == res.code
        assert '' == res.err_msg

        request = pb.DomainDeleteReq(uuid=_uuid)
        try:
            res = self.stub.DeleteDomain(request, timeout=10)
        except Exception:
            assert 0

    def test_create_domain_uuid_exists(self):
        request = pb.DomainCreateReq(os_type='linux', json_data=self.json_template % (self.name, self.uuid))
        try:
            res = self.stub.CreateDomain(request, timeout=10)
        except Exception:
            pass

        assert pb.VIRT_AGENT_ERR_INVALID_UUID == res.code
        assert '' != res.err_msg

    def test_create_domain_name_exists(self):
        request = pb.DomainCreateReq(os_type='linux', json_data=self.json_template %
                                     (self.name, str(uuid.uuid4())))
        try:
            res = self.stub.CreateDomain(request, timeout=10)
        except Exception:
            pass

        assert pb.LIBVIRT_ERR_OPERATION_FAILED == res.code
        assert '' != res.err_msg

    def teardown(self):
        super(TestCaseCreateDomain, self).teardown()


class TestCaseDeleteDomain(base.TestCaseDomainBase):
    def setup(self):
        super(TestCaseDeleteDomain, self).setup()

    def test_delete_domain(self):
        dom_ref = None
        request = pb.DomainDeleteReq(uuid=self.uuid)
        try:
            res = self.stub.DeleteDomain(request, timeout=10)
        except Exception:
            assert 0

        assert self.conn is not None
        try:
            dom_ref = self.conn.lookupByUUIDString(self.uuid)
        except libvirt.libvirtError as e:
            assert libvirt.VIR_ERR_NO_DOMAIN == e.get_error_code()

        assert pb.LIBVIRT_ERR_OK == res.code
        assert '' == res.err_msg
        assert None == dom_ref

    def test_delete_domain_uuid_not_exist(self):
        request = pb.DomainDeleteReq(uuid=str(uuid.uuid4()))
        try:
            res = self.stub.DeleteDomain(request, timeout=10)
        except grpc.RpcError as e:
            assert 0
        assert pb.VIRT_AGENT_ERR_INVALID_UUID == res.code
        assert '' != res.err_msg

    def teardown(self):
        super(TestCaseDeleteDomain, self).teardown()


class TestCaseListDomains(base.TestCaseDomainBase):
    def setup(self):
        super(TestCaseListDomains, self).setup()

    def test_list_domains(self):
        try:
            request = empty_pb.Empty()
            res = self.stub.ListDomains(request, timeout=10)
        except Exception:
            assert 0

        assert self.conn is not None
        try:
            domains = self.conn.listDefinedDomains()
        except libvirt.libvirtError as e:
            assert libvirt.VIR_ERR_NO_DOMAIN == e.get_error_code()

        assert pb.LIBVIRT_ERR_OK == res.code
        assert '' == res.err_msg
        assert self.uuid in res.domains

    def teardown(self):
        super(TestCaseListDomains, self).teardown()


class TestCaseGetDomainsState(base.TestCaseDomainBase):
    def setup(self):
        super(TestCaseGetDomainsState, self).setup()

    def test_get_domains_state(self):
        request = pb.DomainsStateGetReq(uuids=[self.uuid])
        try:
            res = self.stub.GetDomainsState(request, timeout=10)
        except Exception:
            assert 0

        assert pb.LIBVIRT_ERR_OK == res.code
        assert '' == res.err_msg
        assert 1 == len(res.states)
        assert self.uuid == res.states[0].uuid
        assert "shutoff" == res.states[0].state

    def test_get_domains_state(self):
        request = pb.DomainsStateGetReq(uuids=[str(uuid.uuid4())])
        try:
            res = self.stub.GetDomainsState(request, timeout=10)
        except grpc.RpcError as e:
            assert 0
        except Exception:
            pass

        assert pb.VIRT_AGENT_ERR_INVALID_UUID == res.code
        assert '' != res.err_msg
        assert 0 == len(res.states)

    def teardown(self):
        super(TestCaseGetDomainsState, self).teardown()


class TestCaseDumpDomains(base.TestCaseDomainBase):
    def setup(self):
        super(TestCaseDumpDomains, self).setup()

    def test_dump_domains(self):
        request = pb.DomainsDumpReq(uuids=[self.uuid])
        try:
            res = self.stub.DumpDomains(request, timeout=10)
        except Exception:
            assert 0

        assert len(res.domains) == 1
        domain = json.loads(res.domains[0])
        assert 'uuid' in domain
        assert 'title' in domain
        assert 'name' in domain
        assert 'uuid' in domain
        assert 'memory' in domain
        assert 'currentMemory' in domain
        assert 'vcpu' in domain
        assert 'os' in domain
        assert 'metadata' in domain
        assert 'features' in domain
        assert 'cpu' in domain
        assert 'pm' in domain
        assert 'devices' in domain
        assert 'on_poweroff' in domain
        assert 'on_reboot' in domain
        assert 'on_crash' in domain
        assert pb.LIBVIRT_ERR_OK == res.code
        assert 'dev' in domain['devices']['disk'][0]
        assert 'properties' in domain['devices']['disk'][0]
        assert 'dev' in domain['devices']['interface'][0]
        assert 'properties' in domain['devices']['interface'][0]

    def teardown(self):
        super(TestCaseDumpDomains, self).teardown()


class TestCaseModifyDomain(base.TestCaseDomainBase):
    def setup(self):
        super(TestCaseModifyDomain, self).setup()

    def test_modify_memory(self):
        test_size = '111111'
        request = pb.DomainModifyReq(uuid=self.uuid, type=pb.OPERATION_TYPE_UPDATE,
                                     json_data=json.dumps({'memory': test_size}))
        try:
            res = self.stub.ModifyDomain(request, timeout=10)
        except Exception:
            assert 0

        dom = self.conn.lookupByUUIDString(self.uuid)
        dom_xml = etree.XML(dom.XMLDesc())
        memory = dom_xml.xpath('./memory')

        assert len(memory) == 1
        assert test_size == memory[0].text
        assert pb.LIBVIRT_ERR_OK == res.code
        assert '' == res.err_msg

    def test_modify_vcpu(self):
        res = None

        test_size = '8'
        request = pb.DomainModifyReq(
            uuid=self.uuid,
            type=pb.OPERATION_TYPE_UPDATE,
            json_data=json.dumps({'vcpu': {
                'num': test_size,
                'current': 2
            },
                'cpu': {
                    'sockets': '2',
                    'cores': '4'
            }
            }))
        try:
            res = self.stub.ModifyDomain(request, timeout=10)
        except Exception:
            pass

        dom = self.conn.lookupByUUIDString(self.uuid)
        dom_xml = etree.XML(dom.XMLDesc())
        vcpu = dom_xml.xpath('//vcpu')

        assert len(vcpu) == 1
        assert test_size == vcpu[0].text
        assert pb.LIBVIRT_ERR_OK == res.code
        assert '' == res.err_msg

    def test_modify_vcpu_failed(self):
        res = None

        test_size = 'test_err'
        request = pb.DomainModifyReq(
            uuid=self.uuid,
            type=pb.OPERATION_TYPE_UPDATE,
            json_data=json.dumps({'vcpu': {
                'num': test_size,
                'current': 2
            }}))
        try:
            res = self.stub.ModifyDomain(request, timeout=10)
        except Exception:
            pass

        assert pb.LIBVIRT_ERR_XML_ERROR == res.code
        assert res.err_msg != ''

    def test_modify_delete_disk(self):
        dom = self.conn.lookupByUUIDString(self.uuid)
        dom_xml = etree.XML(dom.XMLDesc())
        test_targets = dom_xml.xpath('//devices/disk/target')
        assert len(test_targets) > 0
        test_target = test_targets[0].get('dev')
        assert 'hda' == test_target

        request = pb.DomainModifyReq(
            uuid=self.uuid,
            type=pb.OPERATION_TYPE_DELETE,
            json_data=json.dumps({'devices': {"disk": [{"dev": test_target}]}}))
        try:
            res = self.stub.ModifyDomain(request, timeout=10)
        except Exception:
            pass

        dom = self.conn.lookupByUUIDString(self.uuid)
        dom_xml = etree.XML(dom.XMLDesc())
        target = dom_xml.xpath('//devices/disk/target')
        assert len(test_targets) - 1 == len(target)
        assert pb.LIBVIRT_ERR_OK == res.code
        assert res.err_msg is ''

    def test_modify_add_disk(self):
        dom = self.conn.lookupByUUIDString(self.uuid)
        dom_xml = etree.XML(dom.XMLDesc())
        test_disks = dom_xml.xpath('//devices/disk')
        assert len(test_disks) > 0

        request = pb.DomainModifyReq(
            uuid=self.uuid,
            type=pb.OPERATION_TYPE_ADD,
            json_data=json.dumps({'devices': {"disk": [{
                "properties": {
                    "type": "file",
                    "device": "cdrom",
                    "driver_type": "raw",
                    "driver_name": "qemu",
                    "source": "/vms/isos/CentOS-7-x86_64-DVD-1810.iso",
                    "target_bus": "ide"
                }
            }]}}))
        try:
            res = self.stub.ModifyDomain(request, timeout=10)
        except Exception:
            pass

        dom = self.conn.lookupByUUIDString(self.uuid)
        dom_xml = etree.XML(dom.XMLDesc())
        disks = dom_xml.xpath('//devices/disk')
        assert len(test_disks) + 1 == len(disks)
        assert pb.LIBVIRT_ERR_OK == res.code
        assert res.err_msg is ''

    def test_modify_update_disk_target(self):
        dom = self.conn.lookupByUUIDString(self.uuid)
        dom_xml = etree.XML(dom.XMLDesc())
        test_disks = dom_xml.xpath('//devices/disk')
        assert len(test_disks) > 0

        request = pb.DomainModifyReq(
            uuid=self.uuid,
            type=pb.OPERATION_TYPE_UPDATE,
            json_data=json.dumps({'devices': {"disk": [{
                "dev": "hda",
                "properties": {
                    "target_dev": "hdd"
                }
            }]}}))
        try:
            res = self.stub.ModifyDomain(request, timeout=10)
        except Exception:
            pass

        dom = self.conn.lookupByUUIDString(self.uuid)
        dom_xml = etree.XML(dom.XMLDesc())
        target = dom_xml.xpath('//devices/disk/target[@dev="hdd"]')
        assert len(target) > 0
        assert "hdd" == target[0].attrib['dev']
        assert pb.LIBVIRT_ERR_OK == res.code
        assert res.err_msg is ''

    def test_modify_mount(self):
        envoy.run(">/tmp/test_mount.iso")
        dom = self.conn.lookupByUUIDString(self.uuid)
        dom_xml = etree.XML(dom.XMLDesc())
        test_disks = dom_xml.xpath('//devices/disk')
        assert len(test_disks) > 0

        request = pb.DomainModifyReq(
            uuid=self.uuid,
            type=pb.OPERATION_TYPE_MOUNT,
            json_data=json.dumps({'devices': {"disk": [{
                "dev": "hda",
                "properties": {
                    "source": "/tmp/test_mount.iso"
                }
            }]}}))
        try:
            res = self.stub.ModifyDomain(request, timeout=10)
        except Exception:
            pass

        dom = self.conn.lookupByUUIDString(self.uuid)
        dom_xml = etree.XML(dom.XMLDesc())

        assert len(dom_xml.xpath('//devices/disk/source[@file="/tmp/test_mount.iso"]')) > 0
        assert pb.LIBVIRT_ERR_OK == res.code
        assert res.err_msg is ''
        envoy.run(">/tmp/test_mount.iso")

    def test_modify_umount(self):
        dom = self.conn.lookupByUUIDString(self.uuid)
        dom_xml = etree.XML(dom.XMLDesc())
        test_disks = dom_xml.xpath('//devices/disk')
        assert len(test_disks) > 0

        request = pb.DomainModifyReq(
            uuid=self.uuid,
            type=pb.OPERATION_TYPE_UMOUNT,
            json_data=json.dumps({'devices': {"disk": [{
                "dev": "hda"
            }]}}))
        try:
            res = self.stub.ModifyDomain(request, timeout=10)
        except Exception:
            pass

        dom = self.conn.lookupByUUIDString(self.uuid)
        dom_xml = etree.XML(dom.XMLDesc())
        disks = dom_xml.xpath('//devices/disk')
        assert len(disks) > 0
        assert len(dom_xml.xpath('//devices/disk/target[@dev="hda"]')) > 0
        for disk_xml in disks:
            if len(disk_xml.xpath('./target[@dev="hda"]')) > 0:
                assert len(disk_xml.xpath('./source')) == 0
        assert pb.LIBVIRT_ERR_OK == res.code
        assert res.err_msg is ''

    def test_modify_delete_network(self):
        dom = self.conn.lookupByUUIDString(self.uuid)
        dom_xml = etree.XML(dom.XMLDesc())
        test_interfaces = dom_xml.xpath('//devices/interface')
        assert len(test_interfaces) > 0

        request = pb.DomainModifyReq(
            uuid=self.uuid,
            type=pb.OPERATION_TYPE_DELETE,
            json_data=json.dumps({'devices': {"interface": [{
                "dev": "88:54:00:c8:ed:00"
            }]}}))
        try:
            res = self.stub.ModifyDomain(request, timeout=10)
        except Exception:
            pass

        dom = self.conn.lookupByUUIDString(self.uuid)
        dom_xml = etree.XML(dom.XMLDesc())
        interfaces = dom_xml.xpath('//devices/interface')
        assert len(test_interfaces) - 1 == len(interfaces)
        assert pb.LIBVIRT_ERR_OK == res.code
        assert res.err_msg is ''

    def test_modify_add_network(self):
        dom = self.conn.lookupByUUIDString(self.uuid)
        dom_xml = etree.XML(dom.XMLDesc())
        test_interfaces = dom_xml.xpath('//devices/interface')
        assert len(test_interfaces) > 0

        request = pb.DomainModifyReq(
            uuid=self.uuid,
            type=pb.OPERATION_TYPE_ADD,
            json_data=json.dumps({'devices': {"interface": [{
                "dev": "52:54:00:c4:d3:b2",
                "properties": {
                    "type": "bridge",
                    "source": "vswitch0",
                    "model_type": "virtio",
                    "driver_name": "vhost"
                }
            }]}}))
        try:
            res = self.stub.ModifyDomain(request, timeout=10)
        except Exception:
            pass

        dom = self.conn.lookupByUUIDString(self.uuid)
        dom_xml = etree.XML(dom.XMLDesc())
        interfaces = dom_xml.xpath('//devices/interface')
        assert len(test_interfaces) + 1 == len(interfaces)
        assert pb.LIBVIRT_ERR_OK == res.code
        assert res.err_msg is ''

    def test_modify_add_multi_network(self):
        dom = self.conn.lookupByUUIDString(self.uuid)
        dom_xml = etree.XML(dom.XMLDesc())
        test_interfaces = dom_xml.xpath('//devices/interface')
        assert len(test_interfaces) > 0

        request = pb.DomainModifyReq(
            uuid=self.uuid,
            type=pb.OPERATION_TYPE_ADD,
            json_data=json.dumps({'devices': {"interface": [{
                "dev": "52:54:00:c4:d3:b2",
                "properties": {
                    "type": "bridge",
                    "source": "vswitch0",
                    "model_type": "virtio",
                    "driver_name": "vhost"
                }
            }, {
                "dev": "52:54:00:c8:ed:c8",
                "properties": {
                    "type": "bridge",
                    "source": "vswitch0",
                    "model_type": "virtio",
                    "driver_name": "vhost"
                }
            }]}}))
        try:
            res = self.stub.ModifyDomain(request, timeout=10)
        except Exception:
            pass

        dom = self.conn.lookupByUUIDString(self.uuid)
        dom_xml = etree.XML(dom.XMLDesc())
        interfaces = dom_xml.xpath('//devices/interface')
        assert len(test_interfaces) + 2 == len(interfaces)
        addresses = []
        macs = dom_xml.xpath('//devices/interface/mac')
        for c in macs:
            addresses.append(c.get('address'))
        assert "52:54:00:c8:ed:c8" in addresses
        assert "52:54:00:c4:d3:b2" in addresses
        assert pb.LIBVIRT_ERR_OK == res.code
        assert res.err_msg is ''

    def test_modify_update_network_mac(self):
        request = pb.DomainModifyReq(
            uuid=self.uuid,
            type=pb.OPERATION_TYPE_UPDATE,
            json_data=json.dumps({'devices': {"interface": [{
                "dev": "88:54:00:c8:ed:00",
                "properties": {
                    "mac": "52:54:00:c4:d3:b2"
                }
            }]}}))
        try:
            res = self.stub.ModifyDomain(request, timeout=10)
        except Exception:
            pass

        dom = self.conn.lookupByUUIDString(self.uuid)
        dom_xml = etree.XML(dom.XMLDesc())
        mac = dom_xml.xpath('//devices/interface/mac[@address="52:54:00:c4:d3:b2"]')
        assert len(mac) > 0
        assert "52:54:00:c4:d3:b2" == mac[0].attrib['address']
        assert pb.LIBVIRT_ERR_OK == res.code
        assert res.err_msg is ''

    def teardown(self):
        super(TestCaseModifyDomain, self).teardown()
