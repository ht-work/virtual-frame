#!/usr/bin/env python
# encoding: utf-8
import grpc
import uuid
import pytest
import logging
import libvirt
import envoy

from virt_agent import virt_agent_pb2 as pb
from virt_agent import virt_agent_pb2_grpc as pb_grpc


class TestCaseBase():
    def setup(self):
        """Setup and teardown for each test case to support parrallel tests."""
        try:
            self.channel = grpc.insecure_channel("127.0.0.1:9100")
            self.stub = pb_grpc.VirtAgentStub(self.channel)
        except grpc.RpcError as e:
            assert 0
        try:
            self.conn = libvirt.open('qemu:///system')
        except libvirt.libvirtError:
            assert 0

    def teardown(self):
        """Tear down all test resources."""
        self.channel.close()
        self.conn.close()


class TestCaseDomainBase(TestCaseBase):
    """
        Setup: Create a domain & grpc channel
        Teardown: Delete a domain & grpc channel
    """

    def setup(self):
        """Setup and teardown for each test case to support parrallel tests.
    """
        super(TestCaseDomainBase, self).setup()
        envoy.run("touch /vms/images/test_base.iso")
        envoy.run("qemu-img create -f qcow2 /vms/images/test_base.qcow2 1M")

        self.uuid = str(uuid.uuid4())
        self.name = self.uuid
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
                                    "cores":"1",
                                    "sockets":"1"
                                },
                                "clock": {
                                    "offset":"localtime"
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
                                      },
                                      {
                                        "dev":"vda",
                                        "properties": {
                                            "type":"file",
                                            "device":"disk",
                                            "driver_type":"qcow2",
                                            "driver_name":"qemu",
                                            "source":"/vms/images/test_base.qcow2",
                                            "target_bus":"virtio"
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
                                    }]
                                }}"""
        request = pb.DomainCreateReq(os_type='linux', json_data=self.json_template % (self.name, self.uuid))
        try:
            res = self.stub.CreateDomain(request, timeout=10)
        except Exception:
            assert 0

        assert pb.LIBVIRT_ERR_OK == res.code
        assert '' == res.err_msg

    def teardown(self):
        """Tear down all test resources."""
        request = pb.DomainDeleteReq(uuid=self.uuid)
        try:
            res = self.stub.DeleteDomain(request, timeout=10)
        except grpc.RpcError as e:
            assert 0

        assert ((pb.LIBVIRT_ERR_OK == res.code) or (pb.VIRT_AGENT_ERR_INVALID_UUID == res.code))

        super(TestCaseDomainBase, self).teardown()
        envoy.run('rm -f /vms/images/test_base.iso')
        envoy.run('rm -f /vms/images/test_base.qcow2')
