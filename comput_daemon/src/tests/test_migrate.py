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


class TestCaseMigrateDomain(base.TestCaseDomainBase):
    """
        Need a destination host and ssh-copy-id:
            1. echo 1.2.3.4 test_migration_host  >> /etc/hosts
            2. ssh-copy-id root@test_migration_host
            3. modify qemu+tls into qemu+ssh in libvirt_driver.py
    """

    def setup(self):
        super(TestCaseMigrateDomain, self).setup()
        cmd = envoy.run('ping test_migration_host -c 3')
        if cmd.std_err != '':
            print('Test host for migration not found: ', cmd.str_err)
            return

        self.has_env = True
        self._uuid = str(uuid.uuid4())
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
                                        "dev":"vda",
                                        "properties": {
                                            "type":"file",
                                            "device":"disk",
                                            "driver_type":"qcow2",
                                            "driver_name":"qemu",
                                            "source":"/vms/images/test_%s.qcow2",
                                            "target_bus":"virtio"
                                        }
                                    }],
                                    "interface": [{
                                        "dev":"52:54:00:c4:d3:b2",
                                        "properties": {
                                            "type": "network",
                                            "source": "default",
                                            "model_type":"virtio",
                                            "driver_name":"vhost"
                                        }
                                    }]
                                }}"""

        cmd = envoy.run('qemu-img create -f qcow2 /vms/images/test_%s.qcow2 1M' % self._uuid)
        if cmd.std_err != '':
            return

        request = pb.DomainCreateReq(
            os_type='linux', json_data=self.json_template %
            (self._uuid, self._uuid, self._uuid))
        try:
            res = self.stub.CreateDomain(request, timeout=10)
        except Exception:
            assert 0

        cmd = envoy.run('virsh start test_%s' % self._uuid)
        if cmd.std_err != '':
            print(cmd.std_err)
            return
        # wait for domain start
        assert pb.LIBVIRT_ERR_OK == res.code
        assert '' == res.err_msg

    def test_migrate_domain_online(self):
        if not self.has_env:
            return

        _job_id = -1
        dom_ref = None
        request = pb.DomainMigrateReq(
            uuid=self._uuid,
            destination="test_migration_host",
            no_need_notify=True,
            postcopy=True,
            time_out=300)
        try:
            res = self.stub.MigrateDomain(request, timeout=10)
            _job_id = res.job_id
        except Exception:
            assert 0

            assert self.conn is not None
        try:
            dom_ref = self.conn.lookupByUUIDString(self._uuid)
        except libvirt.libvirtError as e:
            assert libvirt.VIR_ERR_NO_DOMAIN == e.get_error_code()

        assert pb.LIBVIRT_ERR_OK == res.code
        assert '' == res.err_msg

        start = time.time()
        while True:
            try:
                res = self.stub.QueryJob(request=pb.QueryJobReq(job_id=_job_id), timeout=10)
            except Exception:
                assert 0
            assert res.code == 0
            assert time.time() - start < 8
            if res.process == 100:
                break
            time.sleep(0.5)

        try:
            res = self.stub.ListDomains(request=empty_pb.Empty(), timeout=10)
        except Exception:
            assert 0

        assert self._uuid not in res.domains
        assert self.uuid in res.domains

    def test_migrate_domain_offline_shared_storage(self):
        if not self.has_env:
            return

        cmd = envoy.run('virsh destroy test_%s' % self._uuid)
        if cmd.std_err != '':
            print(cmd.std_err)
            return

        cmd = envoy.run('ssh root@test_migration_host qemu-img create -f qcow2  1M test_%s' % self._uuid)
        if cmd.std_err != '':
            print(cmd.std_err)
            return

        _job_id = -1
        dom_ref = None
        request = pb.DomainMigrateReq(
            uuid=self._uuid,
            destination="test_migration_host",
            no_need_notify=True,
            postcopy=True,
            time_out=300)
        try:
            res = self.stub.MigrateDomain(request, timeout=10)
            _job_id = res.job_id
        except Exception:
            assert 0

            assert self.conn is not None
        try:
            dom_ref = self.conn.lookupByUUIDString(self._uuid)
        except libvirt.libvirtError as e:
            assert libvirt.VIR_ERR_NO_DOMAIN == e.get_error_code()

        assert pb.LIBVIRT_ERR_OK == res.code
        assert '' == res.err_msg

        start = time.time()
        while True:
            try:
                res = self.stub.QueryJob(request=pb.QueryJobReq(job_id=_job_id), timeout=10)
            except Exception:
                assert 0
            assert res.code == 0
            assert time.time() - start < 5
            if res.process == 100:
                break
            time.sleep(0.5)

        try:
            res = self.stub.ListDomains(request=empty_pb.Empty(), timeout=10)
        except Exception:
            assert 0

        assert self._uuid not in res.domains
        assert self.uuid in res.domains

    def test_migrate_domain_offline_non_shared_storage(self):
        if not self.has_env:
            return

        cmd = envoy.run('virsh destroy test_%s' % self._uuid)
        if cmd.std_err != '':
            print(cmd.std_err)
            return

        _job_id = -1
        dom_ref = None
        request = pb.DomainMigrateReq(
            uuid=self._uuid,
            destination="test_migration_host",
            no_need_notify=True,
            postcopy=True,
            time_out=300,
            destination_json=json.dumps({"devices": {"disk": [{
                "dev": "vda",
                "properties": {
                    "source": "/var/lib/libvirt/images/test_" + self._uuid + ".qcow2"
                }
            }]}}))
        try:
            res = self.stub.MigrateDomain(request, timeout=10)
            _job_id = res.job_id
        except Exception:
            assert 0

        assert self.conn is not None
        try:
            dom_ref = self.conn.lookupByUUIDString(self._uuid)
        except libvirt.libvirtError as e:
            assert libvirt.VIR_ERR_NO_DOMAIN == e.get_error_code()

        assert pb.LIBVIRT_ERR_OK == res.code
        assert '' == res.err_msg

        start = time.time()
        while True:
            try:
                res = self.stub.QueryJob(request=pb.QueryJobReq(job_id=_job_id), timeout=10)
            except Exception:
                assert 0
            assert res.code == 0
            assert time.time() - start < 10
            if res.process == 100:
                break
            time.sleep(0.5)

        try:
            res = self.stub.ListDomains(request=empty_pb.Empty(), timeout=10)
        except Exception:
            assert 0

        assert self._uuid not in res.domains
        assert self.uuid in res.domains

    def test_migrate_domain_online_non_shared_storage(self):
        if not self.has_env:
            return

        _job_id = -1
        dom_ref = None
        request = pb.DomainMigrateReq(
            uuid=self._uuid,
            destination="test_migration_host",
            no_need_notify=True,
            postcopy=True,
            time_out=300,
            destination_json=json.dumps({"devices": {"disk": [{
                "dev": "vda",
                "properties": {
                    "source": "/var/lib/libvirt/images/test_" + self._uuid + ".qcow2"
                }
            }]}}))
        try:
            res = self.stub.MigrateDomain(request, timeout=10)
            _job_id = res.job_id
        except Exception:
            assert 0

        assert self.conn is not None
        try:
            dom_ref = self.conn.lookupByUUIDString(self._uuid)
        except libvirt.libvirtError as e:
            assert libvirt.VIR_ERR_NO_DOMAIN == e.get_error_code()

        assert pb.LIBVIRT_ERR_OK == res.code
        assert '' == res.err_msg

        start = time.time()
        while True:
            try:
                res = self.stub.QueryJob(request=pb.QueryJobReq(job_id=_job_id), timeout=10)
            except Exception:
                assert 0
            assert res.code == 0
            assert time.time() - start < 15
            if res.process == 100:
                break
            time.sleep(0.5)

        try:
            res = self.stub.ListDomains(request=empty_pb.Empty(), timeout=10)
        except Exception:
            assert 0

        assert self._uuid not in res.domains
        assert self.uuid in res.domains

    def test_migrate_domain_online_non_shared_disk_snapshots(self):
        if not self.has_env:
            return

        cmd = envoy.run('qemu-img snapshot -c test_snap_disk_%s /vms/images/test_%s.qcow2' % (self._uuid, self._uuid))
        assert cmd.std_err == ''

        _job_id = -1
        dom_ref = None
        request = pb.DomainMigrateReq(
            uuid=self._uuid,
            destination="test_migration_host",
            no_need_notify=True,
            postcopy=True,
            time_out=300,
            destination_json=json.dumps({"devices": {"disk": [{
                "dev": "vda",
                "properties": {
                    "source": "/var/lib/libvirt/images/test_" + self._uuid + ".qcow2"
                }
            }]}}))
        try:
            res = self.stub.MigrateDomain(request, timeout=10)
            _job_id = res.job_id
        except Exception:
            assert 0

        assert self.conn is not None
        try:
            dom_ref = self.conn.lookupByUUIDString(self._uuid)
        except libvirt.libvirtError as e:
            assert libvirt.VIR_ERR_NO_DOMAIN == e.get_error_code()

        assert pb.LIBVIRT_ERR_OK == res.code
        assert '' == res.err_msg

        start = time.time()
        while True:
            try:
                res = self.stub.QueryJob(request=pb.QueryJobReq(job_id=_job_id), timeout=10)
            except Exception:
                assert 0
            assert res.code == 0
            assert time.time() - start < 15
            if res.process == 100:
                break
            time.sleep(0.5)

        try:
            res = self.stub.ListDomains(request=empty_pb.Empty(), timeout=10)
        except Exception:
            assert 0

        assert self._uuid not in res.domains
        assert self.uuid in res.domains

    def test_migrate_domain_offline_non_shared_disk_snapshots(self):
        if not self.has_env:
            return

        cmd = envoy.run('qemu-img snapshot -c test_snap_disk_%s /vms/images/test_%s.qcow2' % (self._uuid, self._uuid))
        assert cmd.std_err == ''
        cmd = envoy.run('virsh destroy %s' % self._uuid)
        assert cmd.std_err == ''

        _job_id = -1
        dom_ref = None
        request = pb.DomainMigrateReq(
            uuid=self._uuid,
            destination="test_migration_host",
            no_need_notify=True,
            postcopy=True,
            time_out=300,
            destination_json=json.dumps({"devices": {"disk": [{
                "dev": "vda",
                "properties": {
                    "source": "/var/lib/libvirt/images/test_" + self._uuid + ".qcow2"
                }
            }]}}))
        try:
            res = self.stub.MigrateDomain(request, timeout=10)
            _job_id = res.job_id
        except Exception:
            assert 0

        assert self.conn is not None
        try:
            dom_ref = self.conn.lookupByUUIDString(self._uuid)
        except libvirt.libvirtError as e:
            assert libvirt.VIR_ERR_NO_DOMAIN == e.get_error_code()

        assert pb.LIBVIRT_ERR_OK == res.code
        assert '' == res.err_msg

        start = time.time()
        while True:
            try:
                res = self.stub.QueryJob(request=pb.QueryJobReq(job_id=_job_id), timeout=10)
            except Exception:
                assert 0
            assert res.code == 0
            assert time.time() - start < 15
            if res.process == 100:
                break
            time.sleep(0.5)

        try:
            res = self.stub.ListDomains(request=empty_pb.Empty(), timeout=10)
        except Exception:
            assert 0

        assert self._uuid not in res.domains
        assert self.uuid in res.domains

    def test_migrate_domain_online_with_snapshots(self):
        if not self.has_env:
            return
        cmd = envoy.run('virsh snapshot-create-as --domain test_%s xxx' % self._uuid)
        assert cmd.std_err == ''
        cmd = envoy.run('virsh snapshot-create-as --domain test_%s yyy' % self._uuid)
        assert cmd.std_err == ''
        cmd = envoy.run('virsh snapshot-list --domain test_%s' % self._uuid)
        assert 'xxx' in cmd.std_out
        assert 'yyy' in cmd.std_out

        _job_id = -1
        dom_ref = None
        request = pb.DomainMigrateReq(
            uuid=self._uuid,
            destination="test_migration_host",
            no_need_notify=True,
            postcopy=True,
            time_out=300,
            destination_json=json.dumps({
                "devices": {
                    "disk": [{
                        "dev": "vda",
                        "properties": {
                            "source": "/var/lib/libvirt/images/test_" + self._uuid + ".qcow2"
                        }
                    }]}}))
        try:
            res = self.stub.MigrateDomain(request, timeout=10)
            _job_id = res.job_id
        except Exception:
            assert 0

            assert self.conn is not None
        try:
            dom_ref = self.conn.lookupByUUIDString(self._uuid)
        except libvirt.libvirtError as e:
            assert libvirt.VIR_ERR_NO_DOMAIN == e.get_error_code()

        assert pb.LIBVIRT_ERR_OK == res.code
        assert '' == res.err_msg

        start = time.time()
        while True:
            try:
                res = self.stub.QueryJob(request=pb.QueryJobReq(job_id=_job_id), timeout=10)
            except Exception:
                assert 0
            assert res.code == 0
            assert time.time() - start < 10
            if res.process == 100:
                break
            time.sleep(0.5)

        try:
            res = self.stub.ListDomains(request=empty_pb.Empty(), timeout=10)
        except Exception:
            assert 0
        cmd = envoy.run('ssh root@test_migration_host virsh snapshot-list test_%s' % self._uuid)
        assert cmd.std_err == ''
        assert 'xxx' in cmd.std_out
        assert 'yyy' in cmd.std_out
        assert self._uuid not in res.domains
        assert self.uuid in res.domains

    def test_migrate_domain_offline_with_snapshots(self):
        if not self.has_env:
            return
        cmd = envoy.run('virsh destroy test_%s' % self._uuid)
        assert cmd.std_err == ''
        test_size = '2048000'
        request = pb.DomainModifyReq(uuid=self._uuid, type=pb.OPERATION_TYPE_UPDATE,
                                     json_data=json.dumps({'memory': test_size}))
        try:
            res = self.stub.ModifyDomain(request, timeout=10)
        except Exception:
            assert 0
        cmd = envoy.run('virsh snapshot-create-as --domain test_%s xxx' % self._uuid)
        assert cmd.std_err == ''
        assert cmd.std_err == ''
        cmd = envoy.run('virsh snapshot-create-as --domain test_%s yyy' % self._uuid)
        assert cmd.std_err == ''
        cmd = envoy.run('virsh snapshot-list --domain test_%s' % self._uuid)
        assert 'xxx' in cmd.std_out
        assert 'yyy' in cmd.std_out
        cmd = envoy.run('virsh start test_%s' % self._uuid)
        assert cmd.std_err == ''

        _job_id = -1
        dom_ref = None
        request = pb.DomainMigrateReq(
            uuid=self._uuid,
            destination="test_migration_host",
            no_need_notify=True,
            postcopy=True,
            time_out=300)
        try:
            res = self.stub.MigrateDomain(request, timeout=10)
            _job_id = res.job_id
        except Exception:
            assert 0

            assert self.conn is not None
        try:
            dom_ref = self.conn.lookupByUUIDString(self._uuid)
        except libvirt.libvirtError as e:
            assert libvirt.VIR_ERR_NO_DOMAIN == e.get_error_code()

        assert pb.LIBVIRT_ERR_OK == res.code
        assert '' == res.err_msg

        start = time.time()
        while True:
            try:
                res = self.stub.QueryJob(request=pb.QueryJobReq(job_id=_job_id), timeout=10)
            except Exception:
                assert 0
            assert res.code == 0
            assert time.time() - start < 15
            if res.process == 100:
                break
            time.sleep(0.5)

        try:
            res = self.stub.ListDomains(request=empty_pb.Empty(), timeout=10)
        except Exception:
            assert 0
        cmd = envoy.run('ssh root@test_migration_host virsh snapshot-list test_%s' % self._uuid)
        assert cmd.std_err == ''
        assert 'xxx' in cmd.std_out
        assert 'yyy' in cmd.std_out
        cmd = envoy.run('ssh root@test_migration_host virsh snapshot-dumpxml test_%s yyy' % self._uuid)
        assert test_size in cmd.std_out
        assert self._uuid not in res.domains
        assert self.uuid in res.domains

   def test_migrate_domain_online_copy_base_images(self):
       if not self.has_env:
           return

       cmd = envoy.run('mv /vms/images/test_%s.qcow2 /vms/images/test_%s_base0.qcow2' % (self._uuid, self._uuid))
       assert cmd.std_err == ''
       cmd = envoy.run(
           'qemu-img create -b /vms/images/test_%s_base0.qcow2 -f qcow2 /vms/images/test_%s.qcow2 1M' %
           (self._uuid, self._uuid))

       time.sleep(1)
       _job_id = -1
       dom_ref = None
       request = pb.DomainMigrateReq(
           uuid=self._uuid,
           destination="test_migration_host",
           no_need_notify=True,
           postcopy=True,
           time_out=300,
           destination_json=json.dumps({"devices": {"disk": [{
               "dev": "vda",
               "properties": {
                   "source": "/vms/images/test_" + self._uuid + ".qcow2"
               },
               "migrate_backingfiles": [{
                   "filename": "/vms/images/test_" + self._uuid + "_base0.qcow2",
                   "dst_filename": "/var/lib/libvirt/images/test_" + self._uuid + "_base0.qcow2"
               }]
           }]}}))
       try:
           res = self.stub.MigrateDomain(request, timeout=10)
           _job_id = res.job_id
       except Exception:
           assert 0

       assert self.conn is not None
       try:
           dom_ref = self.conn.lookupByUUIDString(self._uuid)
       except libvirt.libvirtError as e:
           assert libvirt.VIR_ERR_NO_DOMAIN == e.get_error_code()

       assert pb.LIBVIRT_ERR_OK == res.code
       assert '' == res.err_msg

       start = time.time()
       while True:
           try:
               res = self.stub.QueryJob(request=pb.QueryJobReq(job_id=_job_id), timeout=10)
           except Exception:
               assert 0
           assert res.code == 0
           assert time.time() - start < 15
           if res.process == 100:
               break
           time.sleep(0.5)

       try:
           res = self.stub.ListDomains(request=empty_pb.Empty(), timeout=10)
       except Exception:
           assert 0

       cmd = envoy.run(
           'ssh root@test_migration_host ls /var/lib/libvirt/images/test_%s_base0.qcow2' %
           (self._uuid))
       assert cmd.std_err == ''
       assert '/var/lib/libvirt/images/test_%s_base0.qcow2' % (self._uuid) in cmd.std_out
       cmd = envoy.run(
           'file /vms/images/test_%s_base0.qcow2' %
           (self._uuid))
       assert cmd.std_err == ''
       assert self._uuid not in res.domains
       assert self.uuid in res.domains

    def test_migrate_domain_online_with_external_snapshots(self):
        if not self.has_env:
            return

        cmd = envoy.run(
            'virsh snapshot-create-as  /vms/images/test_%s.qcow2 external_snapshot --disk-only' %
            (self._uuid))
        assert cmd.std_err == ''
        dom_ref = None
        request = pb.DomainMigrateReq(
            uuid=self._uuid,
            destination="test_migration_host",
            no_need_notify=True,
            postcopy=True,
            time_out=300,
            destination_json=json.dumps({"devices": {"disk": [{
                "dev": "vda",
                "properties": {
                    "source": "/vms/images/test_" + self._uuid + ".external_snapshot"
                },
                "migrate_backingfiles": [{
                    "filename": "/vms/images/test_" + self._uuid + ".qcow2",
                    "dst_filename": "/var/lib/libvirt/images/test_" + self._uuid + ".qcow2"
                }]
            }]}}))
        try:
            res = self.stub.MigrateDomain(request, timeout=10)
            _job_id = res.job_id
        except Exception:
            assert 0

        assert self.conn is not None
        try:
            dom_ref = self.conn.lookupByUUIDString(self._uuid)
        except libvirt.libvirtError as e:
            assert libvirt.VIR_ERR_NO_DOMAIN == e.get_error_code()

        assert pb.LIBVIRT_ERR_OK == res.code
        assert '' == res.err_msg

        start = time.time()
        while True:
            try:
                res = self.stub.QueryJob(request=pb.QueryJobReq(job_id=_job_id), timeout=10)
            except Exception:
                assert 0
            assert res.code == 0
            assert time.time() - start < 15
            if res.process == 100:
                break
            time.sleep(0.5)

        try:
            res = self.stub.ListDomains(request=empty_pb.Empty(), timeout=10)
        except Exception:
            assert 0

        cmd = envoy.run(
            'ssh root@test_migration_host ls /var/lib/libvirt/images/test_%s_base0.qcow2' %
            (self._uuid))
        assert cmd.std_err == ''
        assert '/var/lib/libvirt/images/test_%s_base0.qcow2' % (self._uuid) in cmd.std_out
        cmd = envoy.run(
            'file /vms/images/test_%s_base0.qcow2' %
            (self._uuid))
        assert cmd.std_err == ''
        assert self._uuid not in res.domains
        assert self.uuid in res.domains

    def teardown(self):
        #        envoy.run('rm -f /vms/images/test_%s.qcow2' % self._uuid)
        super(TestCaseMigrateDomain, self).teardown()


class TestCaseFinishMigration(base.TestCaseDomainBase):
    def setup(self):
        super(TestCaseFinishMigration, self).setup()
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
                                    "disk":[
                                        {
                                            "dev":"vda",
                                            "properties": {
                                                "type":"file",
                                                "device":"disk",
                                                "driver_type":"qcow2",
                                                "driver_name":"qemu",
                                                "source":"/vms/images/test_%s_1.qcow2",
                                                "target_bus":"virtio"
                                            }
                                        },
                                        {
                                            "dev":"vdb",
                                            "properties": {
                                                "type":"file",
                                                "device":"disk",
                                                "driver_type":"qcow2",
                                                "driver_name":"qemu",
                                                "source":"/vms/images/test_%s_2.qcow2",
                                                "target_bus":"virtio"
                                            }

                                    }],
                                    "interface": [{
                                        "dev":"52:54:00:c4:d3:b2",
                                        "properties": {
                                            "type": "network",
                                            "source": "default",
                                            "model_type":"virtio",
                                            "driver_name":"vhost"
                                        }
                                    }]
                                }}"""
        self._uuid = str(uuid.uuid4())
        request = pb.DomainCreateReq(
            os_type='linux', json_data=self.json_template %
            (self._uuid, self._uuid, self._uuid, self._uuid))
        try:
            res = self.stub.CreateDomain(request, timeout=10)
        except Exception:
            assert 0

        cmd = envoy.run('qemu-img create -f qcow2 /vms/images/test_%s_1.qcow2 1M' % self._uuid)
        if cmd.std_err != '':
            return
        cmd = envoy.run('qemu-img create -f qcow2 /vms/images/test_%s_2.qcow2 1M' % self._uuid)
        if cmd.std_err != '':
            return

        cmd = envoy.run('virsh start test_%s' % self._uuid)
        if cmd.std_err != '':
            return

    def test_finish_migration(self):
        cmd = envoy.run('virsh snapshot-create-as test_%s --disk-only ttt ' % self._uuid)
        assert cmd.std_err == ''
        dom = self.conn.lookupByUUIDString(self._uuid)
        snap = dom.snapshotLookupByName('ttt')
        snap_xml = snap.getXMLDesc()
        cmd = envoy.run('virsh snapshot-delete test_%s --metadata ttt ' % self._uuid)
        assert cmd.std_err == ''
        cmd = envoy.run('virsh snapshot-create-as test_%s --disk-only tmp --no-metadata' % self._uuid)
        assert cmd.std_err == ''

        cmd = envoy.run('virsh snaphost-list test_%s' % self._uuid)
        assert 'ttt' not in cmd.std_out
        cmd = envoy.run('ls /vms/images/test_%s_1.tmp' % self._uuid)
        assert cmd.std_err == ''
        assert 'tmp' in cmd.std_out
        cmd = envoy.run('virsh dumpxml test_%s' % self._uuid)
        assert 'ttt' in cmd.std_out
        assert 'tmp' in cmd.std_out

        tmp_info = {
            'vda': {
                'base': '/vms/images/test_%s_1.ttt' % self._uuid,
                'tmp': '/vms/images/test_%s_1.tmp' % self._uuid
            },
            'vdb': {
                'base': '/vms/images/test_%s_2.ttt' % self._uuid,
                'tmp': '/vms/images/test_%s_2.tmp' % self._uuid
            }
        }
        cmd = envoy.run('ls /vms/images/test_%s_2.tmp' % self._uuid)
        assert cmd.std_err == ''
        assert 'tmp' in cmd.std_out
        snap_xmls = []
        snap_xmls.append(snap_xml)
        request = pb.FinishMigrationReq(uuid=self._uuid, snap_xmls=snap_xmls, tmp_info=json.dumps(tmp_info))
        try:
            res = self.stub.FinishMigration(request, timeout=10)
        except Exception:
            assert 0

        cmd = envoy.run('virsh dumpxml test_%s' % self._uuid)
        assert 'ttt' in cmd.std_out
        assert 'tmp' not in cmd.std_out
        cmd = envoy.run('ls /vms/images/test_%s_1.tmp' % self._uuid)
        assert cmd.std_err != ''
        cmd = envoy.run('ls /vms/images/test_%s_2.tmp' % self._uuid)
        assert cmd.std_err != ''

    def teardown(self):
        super(TestCaseFinishMigration, self).teardown()


class TestCaseCopyImage(base.TestCaseDomainBase):
    def setup(self):
        super(TestCaseCopyImage, self).setup()
        cmd = envoy.run('ping test_migration_host -c 3')
        if cmd.std_err != '':
            print('Test host for migration not found: ', cmd.str_err)
            return
        self.has_env = True
        envoy.run('qemu-img create -f qcow2 /tmp/test_copy_image.qcow2 1024')
        self.local_ip = socket.gethostbyname(socket.gethostname())

    def test_copy_images(self):
        if not self.has_env:
            return
        try:
            with grpc.insecure_channel("test_migration_host:6020") as channel:
                stub = sysagent_pb2_grpc.SysAgentStub(channel)
                request = sysagent_pb2.HostInfoGetRequest()
                res = stub.GetHostInfo(request, timeout=10)
                remote_ip = res.body.host_ip

            with grpc.insecure_channel("localhost:6020") as channel:
                stub = sysagent_pb2_grpc.SysAgentStub(channel)
                request = sysagent_pb2.HostInfoGetRequest()
                res = stub.GetHostInfo(request, timeout=10)
                local_ip = res.body.host_ip
                request = sysagent_pb2.FileTransmitRequest(
                    local_ip=local_ip,
                    local_path='/tmp/test_copy_image.qcow2',
                    remote_ip=remote_ip,
                    remote_path='/tmp/test_copy_image.qcow2',
                    grpc_ip=remote_ip)
                res = stub.FileTransmit(request, timeout=10)
                assert res.errno == util_pb2.OK
                assert res.job_id
                timeout = 10
                while timeout > 0:
                    req_queryjob = sysagent_pb2.JobQueryRequest(job_id=res.job_id)
                    res_queryjob = stub.QueryJob(request=req_queryjob)
                    if res_queryjob.body.status == util_pb2.JOBSTATUS_FINISHED_SUCCESSFULLY:
                        break
                    timeout -= 1
                    time.sleep(1)
                assert res_queryjob.body.status == util_pb2.JOBSTATUS_FINISHED_SUCCESSFULLY
        # cmd = envoy.run('ssh root@test_migration_host ls /tmp/test_copy_image.qcow2')
        except Exception as e:
            print(e)
            assert 0

        ''' TODO assert ok'''
        # assert cmd.std_err == ''

    def teardown(self):
        super(TestCaseCopyImage, self).teardown()


class TestCaseGetHostInfo(base.TestCaseBase):
    def setup(self):
        super(TestCaseGetHostInfo, self).setup()
        cmd = envoy.run('ping test_migration_host -c 3')
        if cmd.std_err != '':
            print('Test host for migration not found: ', cmd.str_err)
            return
        self.has_env = True

    def test_get_host_info(self):
        if not self.has_env:
            return

        try:
            with grpc.insecure_channel("test_migration_host:6020") as channel:
                stub = sysagent_pb2_grpc.SysAgentStub(channel)
                request = sysagent_pb2.HostInfoGetRequest()
                res = stub.GetHostInfo(request, timeout=10)
                assert res.body is not None
                assert res.body.host_ip != ''
                assert res.body.cpu_speed != ''
                assert res.body.cpu_module != ''
                assert int(res.body.cpu_sockets) != 0
      #          assert int(res.body.cpu_cores_per_socket) != 0
                assert int(res.body.cpu_threads_per_core) != 0
                assert float(res.body.cpu_rate) != 0.0
                assert int(res.body.mem_total) != 0
                assert int(res.body.mem_free) != 0
                assert float(res.body.mem_free) / float(res.body.mem_total) > 0
                assert float(res.body.mem_free) / float(res.body.mem_total) < 1
        except grpc.RpcError:
            print('connecting to virt_agentd failed')
            assert 0

    def teardown(self):
        super(TestCaseGetHostInfo, self).teardown()


class TestCasePrecheckMigration(base.TestCaseDomainBase):
    """
        Need a destination host and ssh-copy-id:
            1. echo 1.2.3.4 test_migration_host  >> /etc/hosts
            2. ssh-copy-id root@test_migration_host
            3. modify qemu+tls into qemu+ssh in libvirt_driver.py
    """

    def setup(self):
        super(TestCasePrecheckMigration, self).setup()
        cmd = envoy.run('ping test_migration_host -c 3')
        if cmd.std_err != '':
            print('Test host for migration not found: ', cmd.str_err)
            return

        self.has_env = True
        self._uuid = str(uuid.uuid4())
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
                                        "dev":"vda",
                                        "properties": {
                                            "type":"file",
                                            "device":"disk",
                                            "driver_type":"qcow2",
                                            "driver_name":"qemu",
                                            "source":"/vms/images/test_%s.qcow2",
                                            "target_bus":"virtio"
                                        }
                                    }],
                                    "interface": [{
                                        "dev":"52:54:00:c4:d3:b2",
                                        "properties": {
                                            "type": "network",
                                            "source": "default",
                                            "model_type":"virtio",
                                            "driver_name":"vhost"
                                        }
                                    }]
                                }}"""

        cmd = envoy.run('qemu-img create -f qcow2 /vms/images/test_base_%s.qcow2 1M' % self._uuid)
        if cmd.std_err != '':
            return

        cmd = envoy.run(
            'qemu-img create -f qcow2 -b /vms/images/test_base_%s.qcow2 /vms/images/test_%s.qcow2 1M' %
            (self._uuid, self._uuid))
        if cmd.std_err != '':
            return

        request = pb.DomainCreateReq(
            os_type='linux', json_data=self.json_template %
            (self._uuid, self._uuid, self._uuid))
        try:
            res = self.stub.CreateDomain(request, timeout=10)
        except Exception:
            assert 0
        assert pb.LIBVIRT_ERR_OK == res.code
        assert '' == res.err_msg

        cmd = envoy.run('virsh start test_%s' % self._uuid)
        if cmd.std_err != '':
            print(cmd.std_err)
            return
        sys_res = None
        try:
            with grpc.insecure_channel("test_migration_host:6020") as channel:
                stub = sysagent_pb2_grpc.SysAgentStub(channel)
                request = sysagent_pb2.HostInfoGetRequest()
                sys_res = stub.GetHostInfo(request, timeout=10)
        except grpc.RpcError:
            print('connecting to sys-agentd failed')
            assert 0
        self.remote_ip = sys_res.body.host_ip

    def test_precheck_migration(self):
        request = pb.MigrationPrecheckReq(uuid=self._uuid,
                                          destination=self.remote_ip,
                                          destination_json=json.dumps({"devices": {"disk": [{"dev": "vda",
                                                                                             "properties": {"source": "/vms/images/test_" + self._uuid + ".qcow2"},
                                                                                             "migrate_backingfiles": [{"filename": "/vms/images/test_base_" + self._uuid + ".qcow2",
                                                                                                                       "dst_filename": "/var/lib/libvirt/images/test_base_" + self._uuid + ".qcow2"}]}]}}))
        try:
            res = self.stub.PrecheckMigration(request, timeout=10)
        except Exception:
            assert 0

        assert pb.LIBVIRT_ERR_OK == res.code
        assert '' == res.err_msg

    def test_precheck_migration_test_check_md5(self):
        request = pb.MigrationPrecheckReq(uuid=self._uuid,
                                          destination=self.remote_ip,
                                          destination_json=json.dumps({"devices": {"disk": [{"dev": "vda",
                                                                                             "properties": {"source": "/vms/images/test_" + self._uuid + ".qcow2"},
                                                                                             "migrate_backingfiles": [{"filename": "/vms/images/test_base_" + self._uuid + ".qcow2",
                                                                                                                       "dst_filename": "/var/lib/libvirt/images/test_base_" + self._uuid + ".qcow2"}]}]}}))
        try:
            res = self.stub.PrecheckMigration(request, timeout=10)
        except Exception:
            assert 0

        assert pb.LIBVIRT_ERR_OK == res.code
        assert '' == res.err_msg

#    def test_precheck_migration_test_check_md5_error(self):
#        cmd = envoy.run(
#            'ssh root@test_migration_host qemu-img create -f qcow2 /var/lib/libvirt/images/test_base_md5err_%s.qcow2 2M' %
#            self._uuid)
#        assert cmd.std_err == ''
#        cmd = envoy.run(
#            'qemu-img create -f qcow2 /vms/images/test_base_md5err_%s.qcow2 1M' %
#            self._uuid)
#        assert cmd.std_err == ''
#        request = pb.MigrationPrecheckReq(uuid=self._uuid,
#                                          destination=self.remote_ip,
#                                          destination_json=json.dumps({"devices": {"disk": [{"dev": "vda",
#                                                                                             "properties": {"source": "/vms/images/test_" + self._uuid + ".qcow2"},
#                                                                                             "migrate_backingfiles": [{"filename": "/vms/images/test_base_md5err_" + self._uuid + ".qcow2",
#                                                                                                                       "dst_filename": "/var/lib/libvirt/images/test_base_md5err_" + self._uuid + ".qcow2"}]}]}}))
#        try:
#            res = self.stub.PrecheckMigration(request, timeout=10)
#        except Exception:
#            assert 0
#
#        assert pb.LIBVIRT_ERR_OK == res.code
#        assert '' == res.err_msg
#
#    def test_precheck_migration_test_check_no_space_left(self):
#        cmd = envoy.run(
#            'qemu-img create -f qcow2 /vms/images/test_base_no_space_%s.qcow2 1M' %
#            self._uuid)
#        assert cmd.std_err == ''
#        request = pb.MigrationPrecheckReq(uuid=self._uuid,
#                                          destination=self.remote_ip,
#                                          destination_json=json.dumps({"devices": {"disk": [{"dev": "vda",
#                                                                                             "properties": {"source": "/vms/images/test_" + self._uuid + ".qcow2"},
#                                                                                             "migrate_backingfiles": [{"filename": "/vms/images/test_base_no_space_" + self._uuid + ".qcow2",
#                                                                                                                       "dst_filename": "/var/lib/libvirt/images/test_base_no_space_" + self._uuid + ".qcow2"}]}]}}))
#        try:
#            res = self.stub.PrecheckMigration(request, timeout=10)
#        except Exception:
#            assert 0
#
#        assert pb.LIBVIRT_ERR_OK == res.code
#        assert '' == res.err_msg
#
    def teardown(self):
        envoy.run('rm -f /vms/images/test_%s.qcow2' % self._uuid)
        super(TestCasePrecheckMigration, self).teardown()

class TestCasePrepareMigration(base.TestCaseDomainBase):
    def setup(self):
        super(TestCasePrepareMigration, self).setup()
        cmd = envoy.run('ping test_migration_host -c 3')
        if cmd.std_err != '':
            print('Test host for migration not found: ', cmd.str_err)
            return

        self.has_env = True
        cmd = envoy.run('qemu-img create -f qcow2 /vms/images/test_prepare_1_%s.qcow2 1M' % self.uuid)
        if cmd.std_err != '':
            return
        cmd = envoy.run('qemu-img create -f qcow2 /vms/images/test_prepare_2_%s.qcow2 1M' % self.uuid)
        if cmd.std_err != '':
            return

    def test_prepare_migration(self):
        request = pb.PrepareMigrationReq(
            disks=[
                '/vms/images/test_prepare_1_' +
                self.uuid + '.qcow2',
                '/vms/images/test_prepare_2_' +
                self.uuid + '.qcow2'])
        try:
            res = self.stub.PrepareMigration(request, timeout=10)
        except Exception:
            assert 0

        assert pb.LIBVIRT_ERR_OK == res.code
        assert len(json.loads(res.disk_info)) == 2
        assert '/vms/images/test_prepare_1_%s.qcow2' % self.uuid in res.disk_info
        assert '/vms/images/test_prepare_2_%s.qcow2' % self.uuid in res.disk_info

    def teardown(self):
        envoy.run('rm -f /vms/images/test_prepare_1_%s.qcow2' % self.uuid)
        envoy.run('rm -f /vms/images/test_prepare_2_%s.qcow2' % self.uuid)
        super(TestCasePrepareMigration, self).teardown()
