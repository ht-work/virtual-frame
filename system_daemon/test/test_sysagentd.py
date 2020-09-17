import sys
import copy
import os
import time
import socket
import logging
import grpc
import pytest
from google.protobuf import empty_pb2 as empty_pb

sys.path.insert(0, '..')
import sysagent.sysagent_pb2
import sysagent.sysagent_pb2_grpc
from sysagent.util import ExternalConfig as ExCfg


logging.basicConfig(level=logging.INFO)


class TestSysagentd(object):
    channel = None
    stub = None
    local_ip = socket.gethostbyname(socket.gethostname())
    remote1_ip = local_ip
    remote2_ip = local_ip

    @classmethod
    def setup_class(cls):
        try:
            conf = ExCfg('../data/sysagentd.cfg')
            port = conf.ConfigGet('global', 'port')
        except Exception as e:
            logging.error(e)

        cls.channel = grpc.insecure_channel(cls.local_ip + ':' + port)
        cls.stub = sysagent.sysagent_pb2_grpc.SysAgentStub(cls.channel)
        logging.info('sysagent grpc channel create ok!')

    @classmethod
    def teardown_class(cls):
        cls.channel.close()
        logging.info('sysagent grpc channel close ok!')

    def test_ConnectHost(self):
        response = self.stub.ConnectHost(
            sysagent.sysagent_pb2.HostConnectRequest(manager_ip='6.6.6.6',
                                                     name='root',
                                                     passwd='a@#F4r^%S&D'))
        assert response.errno == sysagent.util_pb2.SYS_USER_PASSWD

    def test_GetHostInfo(self):
        response = self.stub.GetHostInfo(
            sysagent.sysagent_pb2.HostInfoGetRequest())

        logging.info('host_ip          : %s' % response.body.host_ip)
        logging.info('host_name        : %s' % response.body.host_name)
        logging.info('host_arch        : %s' % response.body.host_arch)
        logging.info('host_module      : %s' % response.body.host_module)
        logging.info('cpu_module       : %s' % response.body.cpu_module)
        logging.info('cpu_speed        : %s' % response.body.cpu_speed)
        logging.info('cpu_rate         : %s' % response.body.cpu_rate)
        logging.info('mem_total        : %s' % response.body.mem_total)
        logging.info('mem_free         : %s' % response.body.mem_free)
        logging.info('ver_inner        : %s' % response.body.ver_inner)
        logging.info('ver_outer        : %s' % response.body.ver_outer)
        logging.info('time_now         : %s' % response.body.time_now)
        logging.info('time_up          : %s' % response.body.time_up)
        logging.info('cpu_sockets         : %s' % response.body.cpu_sockets)
        logging.info('cpu_cores_per_socket: %s' % response.body.cpu_cores_per_socket)
        logging.info('cpu_threads_per_core: %s' % response.body.cpu_threads_per_core)

        assert response.errno == sysagent.util_pb2.OK

    def test_SyncHostInfo(self):
        lists = []
        host = sysagent.sysagent_pb2.HostInfoSyncRequest.Host()
        host.hostname = 'test1234'
        host.ip = '1.2.3.4'
        lists.append(copy.deepcopy(host))
        host.hostname = 'test5678'
        host.ip = '5.6.7.8'
        lists.append(copy.deepcopy(host))
        response = self.stub.SyncHostInfo(
            sysagent.sysagent_pb2.HostInfoSyncRequest(lists=lists, deletes=lists))
        assert response.errno == sysagent.util_pb2.OK

        lists.clear()
        host.hostname = 'e34%,*&ds*@&a#$34'
        host.ip = '1.2.3.4'
        lists.append(copy.deepcopy(host))
        response = self.stub.SyncHostInfo(
            sysagent.sysagent_pb2.HostInfoSyncRequest(lists=lists))
        assert response.errno == sysagent.util_pb2.SYS_INVAL

        lists.clear()
        host.hostname = 'test7890'
        host.ip = '1.#$H^*op^d$(2'
        lists.append(copy.deepcopy(host))
        response = self.stub.SyncHostInfo(
            sysagent.sysagent_pb2.HostInfoSyncRequest(lists=lists))
        assert response.errno == sysagent.util_pb2.SYS_INVAL

    def test_FileClient(self):
        # prepare test data
        file_in = "/tmp/in.test"
        file_out = "/tmp/out.test"
        fd = open(file_in, "wb+")
        fd.write(os.urandom(512))
        fd.close()

        # start server
        server_req = sysagent.sysagent_pb2.FileServerStartRequest(server_ip=self.local_ip,
                                                                  path=file_out,
                                                                  operation="put")
        server_response = self.stub.StartFileServer(request=server_req)
        assert server_response.errno == sysagent.util_pb2.OK
        assert server_response.server_port
        assert server_response.job_id

        logging.info('file server port: %d' % server_response.server_port)
        logging.info('file server job id: %s' % server_response.job_id)

        # wait server ready
        times = 10
        while times > 0:
            time.sleep(1)
            req_queryjob = sysagent.sysagent_pb2.JobQueryRequest(job_id=server_response.job_id)
            response_queryjob = self.stub.QueryJob(request=req_queryjob)
            if response_queryjob.body.status == sysagent.util_pb2.JOBSTATUS_PROCESSING:
                break
            times -= 1
        assert response_queryjob.body.status == sysagent.util_pb2.JOBSTATUS_PROCESSING

        # start client
        client_req = sysagent.sysagent_pb2.FileClientStartRequest(server_ip=self.local_ip,
                                                                  server_port=server_response.server_port,
                                                                  local_path=file_in,
                                                                  remote_path=file_out,
                                                                  operation="put")
        client_response = self.stub.StartFileClient(request=client_req)
        assert client_response.errno == sysagent.util_pb2.OK
        assert client_response.job_id
        logging.info('file client job id: %s' % client_response.job_id)

        # wait client finish success
        times = 10
        while times > 0:
            time.sleep(1)
            req_queryjob = sysagent.sysagent_pb2.JobQueryRequest(job_id=client_response.job_id)
            response_queryjob = self.stub.QueryJob(request=req_queryjob)
            if response_queryjob.body.status == sysagent.util_pb2.JOBSTATUS_FINISHED_SUCCESSFULLY:
                break
            times -= 1
        assert response_queryjob.body.status == sysagent.util_pb2.JOBSTATUS_FINISHED_SUCCESSFULLY

        # querry server job status: success
        req_queryjob = sysagent.sysagent_pb2.JobQueryRequest(job_id=server_response.job_id)
        response_queryjob = self.stub.QueryJob(request=req_queryjob)
        assert response_queryjob.body.status == sysagent.util_pb2.JOBSTATUS_FINISHED_SUCCESSFULLY

        # delete jobs: only delete job id in cache list
        req_deljob = sysagent.sysagent_pb2.JobDeleteRequest(job_id=server_response.job_id)
        response_deljob = self.stub.DeleteJob(request=req_deljob)
        assert response_deljob.errno == sysagent.util_pb2.OK

        req_deljob = sysagent.sysagent_pb2.JobDeleteRequest(job_id=client_response.job_id)
        response_deljob = self.stub.DeleteJob(request=req_deljob)
        assert response_deljob.errno == sysagent.util_pb2.OK

        # delete test data
        os.remove(file_in)
        assert os.path.exists(file_out)
        os.remove(file_out)

    def test_FileTransimt(self):
        file_in = "/tmp/in.test"
        file_out = "/tmp/out.test"
        fd = open(file_in, "wb+")
        fd.write(os.urandom(512))
        fd.close()

        req = sysagent.sysagent_pb2.FileTransmitRequest(remote_ip=self.remote2_ip, remote_path=file_out,
                                                        local_ip=self.local_ip, local_path=file_in,
                                                        grpc_ip=self.remote2_ip)

        response = self.stub.FileTransmit(request=req)

        assert response.errno == sysagent.util_pb2.OK
        assert response.job_id

        logging.info("file transmit job id: %s" % response.job_id)

        times = 10
        while times > 0:
            req_queryjob = sysagent.sysagent_pb2.JobQueryRequest(job_id=response.job_id)
            response_queryjob = self.stub.QueryJob(request=req_queryjob)
            if response_queryjob.body.status == sysagent.util_pb2.JOBSTATUS_FINISHED_SUCCESSFULLY:
                break
            times -= 1
            time.sleep(1)
        assert response_queryjob.body.status == sysagent.util_pb2.JOBSTATUS_FINISHED_SUCCESSFULLY

        # only delet job id in cache list
        req_deljob = sysagent.sysagent_pb2.JobDeleteRequest(job_id=response.job_id)
        response_deljob = self.stub.DeleteJob(request=req_deljob)
        assert response_deljob.errno == sysagent.util_pb2.OK

        os.remove(file_in)
        if self.local_ip == self.remote2_ip:
            assert os.path.exists(file_out)
            os.remove(file_out)

    def _PreCheckAndSetMode(self, mode):
        req = sysagent.sysagent_pb2.HostModeSetRequest(mode=mode)
        response = self.stub.SetHostMode(request=req)
        assert response.errno == sysagent.util_pb2.OK

        req = empty_pb.Empty()
        response = self.stub.GetHostMode(request=req)
        assert response.errno == sysagent.util_pb2.OK
        assert response.mode == mode

    def test_SetHostMode(self):
        # record current mode
        req = empty_pb.Empty()
        response = self.stub.GetHostMode(request=req)
        assert response.errno == sysagent.util_pb2.OK
        cur_mode = response.mode

        # test set nomal mode
        self._PreCheckAndSetMode("normal")

        # test set maintenance mode
        self._PreCheckAndSetMode("maintenance")

        # set original mode
        self._PreCheckAndSetMode(cur_mode)

    @pytest.mark.skip(reason="no need to shutdown/reboot host")
    def test_ShutdownHost(self):
        # in normal mode, cannot reboot or shutdown
        self._PreCheckAndSetMode("normal")
        req = sysagent.sysagent_pb2.HostShutdownRequest(shut_type="shutdown")
        response = self.stub.ShutdownHost(request=req)
        assert response.errno == sysagent.util_pb2.SYS_FAIL

        # in maintenance mode, reboot and shutdown will success
        self._PreCheckAndSetMode("maintenance")
        req = sysagent.sysagent_pb2.HostShutdownRequest(shut_type="reboot")
        response = self.stub.ShutdownHost(request=req)
        assert response.errno == sysagent.util_pb2.OK
