import logging
import grpc
import time

from . import virt_agent_pb2 as pb
from . import virt_agent_pb2_grpc as pb_grpc
from . import virt_agentd
from . import virt_agent_exception
from sysagent import sysagent_pb2 as syspb
from sysagent import sysagent_pb2_grpc as syspb_grpc
from sysagent import util_pb2 as sysutilpb
from sysagent.util import ExternalConfig
'''
from storeagent import pools_pb2 as storepb
from storeagent import pools_pb2_grpc as storepb_grpc
'''
from storeagent.store_util import StoreAgentConfig

sysagent_conf = ExternalConfig('/etc/vap/sysagentd.cfg')
sysagent_port = sysagent_conf.ConfigGet('global', 'port')

storeagent_conf = StoreAgentConfig('/etc/vap/storeagent.cfg')
storeagent_port = storeagent_conf.GetServicePort()


def finish_migration(dest_ip, uuid, snap_xmls, tmp_info):
    finish_res = None
    res = None
    logging.info('Finish migration...')
    try:
        with grpc.insecure_channel("%s:%d" % (dest_ip, virt_agentd.VIRT_AGENT_CONF.GetServicePort())) as channel:
            stub = pb_grpc.VirtAgentStub(channel)
            request = pb.FinishMigrationReq(uuid=uuid, snap_xmls=snap_xmls, tmp_info=tmp_info)
            finish_res = stub.FinishMigration(request, timeout=10)
        while True:
            with grpc.insecure_channel("%s:%d" % (dest_ip, virt_agentd.VIRT_AGENT_CONF.GetServicePort())) as channel:
                stub = pb_grpc.VirtAgentStub(channel)
                request = pb.QueryJobReq(job_id=finish_res.job_id)
                res = stub.QueryJob(request, timeout=10)
                if res.status == pb.JOBSTATUS_FINISHED_FAILED:
                    raise virt_agent_exception.VirtAgentMigrationException(err_msg='Finish migration failed')
                if res.status == pb.JOBSTATUS_FINISHED_SUCCESSFULLY:
                    break
                time.sleep(0.5)

    except grpc.RpcError as e:
        logging.info('connecting to virt_agentd failed')
        raise virt_agent_exception.VirtAgentRPCApiCallException(e)

    return res


def revert_migration(dest_ip, uuid, destination_josn, remote_tmp_info):
    res = None
    logging.info('Revert migration...')
    try:
        with grpc.insecure_channel("%s:%d" % (dest_ip, virt_agentd.VIRT_AGENT_CONF.GetServicePort())) as channel:
            stub = pb_grpc.VirtAgentStub(channel)
            request = pb.RevertMigrationReq(
                uuid=uuid,
                destination_json=destination_josn,
                tmp_info=remote_tmp_info)
            res = stub.RevertMigration(request, timeout=10)
    except grpc.RpcError as e:
        logging.info('connecting to virt_agentd failed')
        raise virt_agent_exception.VirtAgentRPCApiCallException(e)

    return res


def get_host_info(dest_ip):
    res = None
    try:
        with grpc.insecure_channel("%s:%s" % (dest_ip, sysagent_port)) as channel:
            stub = syspb_grpc.SysAgentStub(channel)
            request = syspb.HostInfoGetRequest()
            res = stub.GetHostInfo(request, timeout=10)
    except grpc.RpcError as e:
        logging.info('connecting to virt_agentd failed')
        raise virt_agent_exception.VirtAgentRPCApiCallException(e)

    return res


def prepare_migration(dest_ip, live, destination_json, tmp_info):
    res = None
    logging.info('Prepare migration...')
    try:
        with grpc.insecure_channel("%s:%d" % (dest_ip, virt_agentd.VIRT_AGENT_CONF.GetServicePort())) as channel:
            stub = pb_grpc.VirtAgentStub(channel)
            request = pb.PrepareMigrationReq(live=live, destination_json=destination_json, tmp_info=tmp_info)
            res = stub.PrepareMigration(request, timeout=10)
    except grpc.RpcError as e:
        logging.info('connecting to virt_agentd failed')
        raise virt_agent_exception.VirtAgentRPCApiCallException(e)

    return res


def copy_image(dest_ip, dest_path, local_ip, local_path):
    res = None
    logging.info('Copy image %s:%s to %s:%s' % (local_ip, local_path, dest_ip, dest_path))
    try:
        with grpc.insecure_channel("%s:%s" % (local_ip, sysagent_port)) as channel:
            stub = syspb_grpc.SysAgentStub(channel)
            request = syspb.FileTransmitRequest(
                local_ip=local_ip,
                local_path=local_path,
                remote_ip=dest_ip,
                remote_path=dest_path,
                grpc_ip=dest_ip,
                need_notify=False)
            res = stub.FileTransmit(request, timeout=10)
            ''' proccess timeout outside '''
        while True:
            with grpc.insecure_channel("%s:%s" % (local_ip, sysagent_port)) as channel:
                stub = syspb_grpc.SysAgentStub(channel)
                req_queryjob = syspb.JobQueryRequest(job_id=res.job_id)
                res_queryjob = stub.QueryJob(request=req_queryjob)
                if res_queryjob.body.status == sysutilpb.JOBSTATUS_FINISHED_SUCCESSFULLY:
                    break
                if res_queryjob.body.status == sysutilpb.JOBSTATUS_FINISHED_FAILED:
                    raise virt_agent_exception.VirtAgentMigrationException(
                        err_msg='Copy image job status is FAILED',
                        err_code=pb.VIRT_AGENT_ERR_MIGRATION_COPY_IMAGE_ERROR)
                time.sleep(0.5)
    except grpc.RpcError as e:
        logging.info('connecting to virt_agentd failed')
        raise virt_agent_exception.VirtAgentRPCApiCallException(e)

    return res


class DataStoreInfo():
    def __init__(self, name, totalsize, allocatedsize, availablesize, mount):
        self.name = name
        self.totalsize = totalsize
        self.allocatedsize = allocatedsize
        self.availablesize = availablesize
        self.mount = mount


def list_pools(dest_ip):
    '''
    res = None
    try:
        with grpc.insecure_channel("%s:%s" % (dest_ip, storeagent_port)) as channel:
            stub = storepb_grpc.StoreAgentStub(channel)
            request = storepb.ListPoolsRequest()
            res = stub.ListPools(request, timeout=10)
    except grpc.RpcError:
        logging.info('connecting to store_agent failed')
        raise
    return res
    '''
    response = []
    info = DataStoreInfo(
        name="test_pool_1",
        totalsize="104857600",
        allocatedsize="52428800",
        availablesize="52428800",
        mount="/vms/images")
    response.append(info)
    info = DataStoreInfo(
        name="test_pool_2",
        totalsize="104857600",
        allocatedsize="52428800",
        availablesize="52428800",
        mount="/var/lib/libvirt/images")
    response.append(info)

    return response


def list_files_in_pool(dest_ip, pool_name):
    '''
    res = None
    try:
        with grpc.insecure_channel("%s:%s" % (dest_ip, storeagent_port)) as channel:
            stub = storepb_grpc.StoreAgentStub(channel)
            request = storepb.ListPoolFilesRequest(pool_name)
            res = stub.ListPoolFiles(request, timeout=10)
    except grpc.RpcError:
        logging.info('connecting to store_agent failed')
        raise
    return res
    '''

    return ['test_image.qcow2', 'test_base_image.qcow2']


def get_md5(dest_ip, filename):
    '''
    res = None
    try:
        with grpc.insecure_channel("%s:%s" % (dest_ip, storeagent_port)) as channel:
            stub = storepb_grpc.StoreAgentStub(channel)
            request = storepb.MD5Request(filename)
            res = stub.MD5(request, timeout=10)
    except grpc.RpcError:
        logging.info('connecting to store_agent failed')
        raise
    return res
    '''

    return 'aa7f0f51a507ac780b2f37a1cfa8db58xxx'
