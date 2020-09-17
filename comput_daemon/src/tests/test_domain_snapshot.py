#!/usr/bin/env python
# encoding: utf-8

import uuid
import time
import envoy
import grpc

from virt_agent import virt_agent_pb2 as pb
from virt_agent import virt_agent_pb2_grpc as pb_grpc

import base


class TestCaseDomainSnapshot(base.TestCaseDomainBase):
    def setup(self):
        super(TestCaseDomainSnapshot, self).setup()
        self.snap_name = 'snap-%s' % (str(uuid.uuid4()))

    def _create_snapshot(self, with_memory=False, no_need_notify=True):
        request = pb.SnapshotCreateReq(
            dom_uuid=self.uuid,
            name=self.snap_name,
            with_memory=with_memory,
            no_need_notify=no_need_notify)
        try:
            res = self.stub.CreateSnapshot(request, timeout=10)
        except grpc.RpcError as e:
            assert 0
        return res

    def _delete_snapshots(self, snaps, with_memory=False, no_need_notify=True):
        request = pb.SnapshotDeleteReq(dom_uuid=self.uuid, names=snaps, no_need_notify=no_need_notify)
        try:
            res = self.stub.DeleteSnapshot(request, timeout=10)
        except grpc.RpcError as e:
            assert 0
        return res

    def _list_snapshots(self):
        request = pb.SnapshotListReq(dom_uuid=self.uuid)
        try:
            res = self.stub.ListSnapshot(request, timeout=10)
        except grpc.RpcError as e:
            assert 0

        return res

    def test_snapshot_create_offline(self):
        res = self._create_snapshot()
        assert pb.LIBVIRT_ERR_OK == res.code

        cmd = envoy.run('virsh snapshot-list --domain %s' % self.uuid)
        assert self.snap_name in cmd.std_out

        envoy.run('virsh snapshot-delete --domain %s %s' % (self.uuid, self.snap_name))

    def test_snapshot_delete_snapshots(self):
        snaps = []
        snap_num = 2
        while(snap_num > 0):
            snap_num = snap_num - 1
            self.snap_name = 'snap-%s' % (str(uuid.uuid4()))
            res = self._create_snapshot()
            assert pb.LIBVIRT_ERR_OK == res.code
            snaps.append(self.snap_name)
        # wait for snapshot create
        time.sleep(1)
        res = self._delete_snapshots(snaps=snaps)
        # wait for snapshot delete
        time.sleep(1)
        assert pb.LIBVIRT_ERR_OK == res.code

    def teardown(self):
        super(TestCaseDomainSnapshot, self).teardown()
