"""driver
"""
import os
import sys
import pathlib
import re
import threading
import socket
import platform
import dmidecode
import psutil
import time
import grpc
import logging
import uptime
import fileinput
import traceback
import envoy
import copy

from netcp import ncpapi as api
from netcp.exception import NetCopyEOF
from netcp.exception import NetCopyError

from util_base.sys_util import GlobalConfig
from util_base.sys_util import HostMode
from util_base.sys_util import HostModeToString
# from virt_agent import virt_agent_pb2_grpc
# from virt_agent import virt_agent_pb2
# from store_agent import store_agent_pb2_grpc
# from store_agent import store_agent_pb2
import sysagent.worker
from sysagent.util import ExternalConfig as ExCfg
import sysagent.util as util
from sysagent import exception as exp
from sysagent import util_pb2 as u_pb2
from sysagent import sysagent_pb2 as s_pb2
from sysagent import worker_job as wj

_VERSION_FILE = '/etc/version'
_MANAGER_FILE = '/etc/vap/manager.cfg'
_HOSTS_FILE = '/etc/hosts'

_FILE_SERVER_PORT_LOCK = threading.Lock()
_FILE_SERVER_PORT_DIC = {}

_GLOBAL_HOST_MODE_LOCK = threading.Lock()
_GLOBAL_HOST_MODE = HostMode.UNKNOWN

SYS_AGENT_PORT = 0
VIRT_AGENT_PORT = 0
STORE_AGENT_PORT = 0


class HostManager(object):
    __lock = threading.Lock()

    def __init__(self):
        global _MANAGER_FILE
        with self.__lock:
            if not os.path.isfile(_MANAGER_FILE):
                dir_name = os.path.dirname(_MANAGER_FILE)
                if not os.path.isdir(dir_name):
                    os.makedirs(dir_name)
                pathlib.Path(_MANAGER_FILE).touch()
            self.__conf = ExCfg(_MANAGER_FILE)

    def set_ip(self, ip):
        with self.__lock:
            self.__conf.ConfigSet(section='manager', key='ip', value=ip)

    def get_ip(self):
        with self.__lock:
            return self.__conf.ConfigGet(section='manager', key='ip')


class HostCapability(object):
    __host_arch = platform.machine()
    __dmi_dict = dmidecode.parse()

    # update once in a while
    __cpu_rate = '0.0'
    __cpu_rate_lock = threading.Lock()

    # cpu_sockets * cpu_cores_per_socket
    __cpu_physical = psutil.cpu_count(logical=False)

    # cpu_sockets * cpu_cores_per_socket * cpu_threads_per_core
    __cpu_logical = psutil.cpu_count(logical=True)

    def __init__(self):
        self.__host_name = socket.gethostname()
        self.__host_ip = socket.gethostbyname(self.__host_name)

    @property
    def host_name(self):
        return self.__host_name

    @property
    def host_ip(self):
        return self.__host_ip

    @property
    def host_arch(self):
        return self.__host_arch

    @property
    def host_module(self):
        host_module_info = []
        for key1 in self.__dmi_dict.keys():
            json_dict = self.__dmi_dict[key1]
            if 'DMIName' in json_dict and json_dict['DMIName'] == 'System Information':
                if 'Manufacturer' in json_dict:
                    host_module_info.append(json_dict['Manufacturer'])
                if 'Product Name' in json_dict:
                    host_module_info.append(json_dict['Product Name'])

        return ' '.join(host_module_info)

    @property
    def cpu_counts(self):
        sockets = 0
        cores_per_socket = 0
        threads_per_core = 0
        for key1 in self.__dmi_dict.keys():
            json_dict = self.__dmi_dict[key1]
            if 'DMIName' in json_dict and json_dict['DMIName'] == 'Processor Information':
                sockets = sockets + 1

        if sockets != 0:
            cores_per_socket = self.__cpu_physical // sockets

        if self.__cpu_physical != 0:
            threads_per_core = self.__cpu_logical // self.__cpu_physical

        return str(sockets), str(cores_per_socket), str(threads_per_core)

    @property
    def cpu_module(self):
        for key1 in self.__dmi_dict.keys():
            json_dict = self.__dmi_dict[key1]
            if 'DMIName' in json_dict and json_dict['DMIName'] == 'Processor Information':
                if 'Version' in json_dict:
                    return json_dict['Version']
        return ''

    @property
    def cpu_speed(self):
        for key1 in self.__dmi_dict.keys():
            json_dict = self.__dmi_dict[key1]
            if 'DMIName' in json_dict and json_dict['DMIName'] == 'Processor Information':
                if 'Current Speed' in json_dict:
                    return json_dict['Current Speed']
        return ''

    @property
    def cpu_rate(self):
        rate = '0.0'
        with self.__cpu_rate_lock:
            rate = self.__cpu_rate
        return rate

    @property
    def version(self):
        global _VERSION_FILE
        ver_inner = '0'
        ver_outer = '0'
        if not os.path.exists(_VERSION_FILE):
            logging.error('No such file or directory: %s' % _VERSION_FILE)
            return ver_inner, ver_outer

        line = []
        with open(_VERSION_FILE, 'r', encoding='utf-8') as f:
            # read first line and split with space
            # version file as below :
            # V100R001B01D001 V1.1 E0101 Enterprise 23058
            # Build 2018-01-01 01:01:01, RELEASE SOFTWARE
            line = f.readline().split()
        if line:
            ver_inner = line[0]
            ver_outer = line[1] + '-' + line[2]
        else:
            raise exp.InvalidValueException(err_code=u_pb2.SYS_INVAL,
                                            err_msg='Version parse error: %s' % line)

        return ver_inner, ver_outer

    @property
    def mem_info(self):
        mem = psutil.virtual_memory()
        return str(mem.total), str(mem.free)

    @property
    def time_now(self):
        return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())

    @property
    def time_up(self):
        up = uptime.uptime()
        parts = []
        days, up = up // 86400, up % 86400
        if days:
            parts.append('%d day%s' % (days, 's' if days != 1 else ''))
        hours, up = up // 3600, up % 3600
        if hours:
            parts.append('%d hour%s' % (hours, 's' if hours != 1 else ''))
        if up or not parts:
            parts.append('%.2f seconds' % up)
        return ', '.join(parts)

    @classmethod
    def update_cpu_rate(cls):
        rate = str(psutil.cpu_percent(2))
        with cls.__cpu_rate_lock:
            cls.__cpu_rate = rate


def HostCpuPercentJob(job):
    while True:
        try:
            HostCapability.update_cpu_rate()
        except Exception as e:
            logging.error(e)
        time.sleep(1)


class HostName():
    __lock = threading.Lock()

    def add(self, hostname, ip):
        with self.__lock:
            global _HOSTS_FILE
            for line in fileinput.input(_HOSTS_FILE, inplace=1):
                if fileinput.isfirstline():
                    sys.stdout.write(ip + ' ' + hostname + '\n')
                pattern = re.compile(r'([0-9])(.*)(\s+)%s$' % hostname)
                if not pattern.match(line.strip()):
                    sys.stdout.write(line)

    def delete(self, hostname):
        with self.__lock:
            global _HOSTS_FILE
            for line in fileinput.input(_HOSTS_FILE, inplace=1):
                pattern = re.compile(r'([0-9])(.*)(\s+)%s$' % hostname)
                if not pattern.match(line.strip()):
                    sys.stdout.write(line)


def AcquirePort(ip):
    # Pick one available port for server to bind
    is_available = False
    test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    test_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    global _FILE_SERVER_PORT_LOCK
    global _FILE_SERVER_PORT_DIC
    with _FILE_SERVER_PORT_LOCK:
        for port in _FILE_SERVER_PORT_DIC:
            if not _FILE_SERVER_PORT_DIC[port]:
                try:
                    test_socket.bind((ip, port))
                    is_available = True
                    _FILE_SERVER_PORT_DIC[port] = True
                    break
                except socket.error as e:
                    logging.info(e)

    test_socket.close()

    if not is_available:
        err_msg = "no available port for file transmit server"
        logging.error(err_msg)
        raise exp.NoAvailablePortException(err_msg)

    logging.info("pick port:%d" % (port))

    return port


def ReleaseFileserverPort(port):
    global _FILE_SERVER_PORT_LOCK
    global _FILE_SERVER_PORT_DIC
    with _FILE_SERVER_PORT_LOCK:
        _FILE_SERVER_PORT_DIC[port] = False


def RunLocalFileServer(opaque, job=None):
    logging.info("ncp-server -i %s -p %d" % (opaque['server_ip'], opaque['server_port']))

    try:
        remote_target, local_target = api.GetServerTarget(opaque['server_ip'], opaque['server_port'])
        if job:
            while True:
                api.ServerProcess(remote_target, local_target)
                job.set_process(round(local_target.GetOffset * 100 / local_target.GetFileSize))
        else:
            api.ServerRun(remote_target, local_target)
    except NetCopyEOF as e:
        logging.info(e)
        logging.info("file transmit server run success.")
    except (NetCopyError, Exception) as e:
        logging.error(e)
        logging.error('file transmit server interrupted')
        logging.error(traceback.format_exc())
        # server run failed.
        if opaque["operation"] == "put" and os.path.exists(opaque["path"]):
            logging.info("file transmit server failed. delete file %s" % (opaque["path"]))
            os.remove(opaque["path"])

        err_msg = "file transmit server run failed."
        raise exp.FileTransFailException(err_msg=err_msg)
    finally:
        api.PutTarget(remote_target, local_target)
        ReleaseFileserverPort(opaque['server_port'])


def RunLocalFileClient(opaque, job=None):
    logging.info("ncp-client -o %s -i %s -p %d -l %s -r %s -e" % (opaque['operation'],
                 opaque['server_ip'], opaque['server_port'], opaque["local_path"], opaque["remote_path"]))

    try:
        remote_target, local_target = api.GetClientTarget(opaque['server_ip'],  opaque['server_port'],
                                                          opaque['operation'], opaque["local_path"],
                                                          opaque["remote_path"])
        if job:
            while True:
                api.ClientProcess(remote_target, local_target)
                job.set_process(round(local_target.GetOffset * 100 / local_target.GetFileSize))
        else:
            api.ClientRun(remote_target, local_target)
    except NetCopyEOF as e:
        logging.info(e)
        logging.info('file transmit client run success.')
    except (NetCopyError, Exception) as e:
        logging.error(e)
        logging.error('file transmit client run interrupted')
        logging.error(traceback.format_exc())
        # client run failed.
        if opaque["operation"] == "get" and os.path.exists(opaque["local_path"]):
            logging.info("file transmit client failed. delete file %s" % (opaque["local_path"]))
            os.remove(opaque["local_path"])

        err_msg = "file transmit client run fialed."
        raise exp.FileTransFailException(err_msg=err_msg)
    finally:
        api.PutTarget(remote_target, local_target)


def StartFileTransServer(job):
    opaque = job.get_opaque()
    RunLocalFileServer(opaque, job)


def StartFileTransClient(job):
    opaque = job.get_opaque()
    RunLocalFileClient(opaque, job)


def StartFileTransimt(job):
    opaque = job.get_opaque()
    TransmitFile(opaque)


def StartLocalFileServer(opaque, need_notify=False):
    """
    start local file transmit client
    :param opaque:{"server_ip": server_ip
                   "server_port": server_port
                   "operation": operation
                   "path": path}
    :param need_notify
    :return: server_job_id
             server port
    """
    port = 0
    server_job_id = 0
    server_ip = opaque["server_ip"]
    port = AcquirePort(server_ip)

    server_info = {}
    server_info["server_ip"] = opaque["server_ip"]
    server_info["server_port"] = port
    server_info["operation"] = opaque["operation"]
    server_info["path"] = opaque["path"]

    worker_thd = sysagent.worker.worker_threading
    server_job_id = worker_thd.add_job(wj.JobType.STARTFILESERVER, server_info, need_notify)

    return server_job_id, port


def StartLocalFileClient(opaque, need_notify=False):
    """
    start local file transmit client
    :param opaque: {"local_path": local_path,
                    "remote_path": remote_path,
                    "server_ip": server_ip,
                    "server_port": server_port,
                    "operation": operation}
    :param need_notify
    :return: client_job_id
    """
    worker_thd = sysagent.worker.worker_threading

    client_info = {}
    client_info["local_path"] = opaque["local_path"]
    client_info["remote_path"] = opaque["remote_path"]
    client_info["server_ip"] = opaque["server_ip"]
    client_info["server_port"] = opaque["server_port"]
    client_info["operation"] = opaque["operation"]

    return worker_thd.add_job(wj.JobType.STARTFILECLIENT, client_info, need_notify)


def StartRemoteFileServer(opaque):
    """
    start remote file transmit server
    :param opaque:{"grpc_ip":grpc_ip,
                   "server_ip":server_ip
                   "operation":operation
                   "path":path
                   }
    :return: job_id, server_port
    """
    global SYS_AGENT_PORT
    try:
        with grpc.insecure_channel(opaque["grpc_ip"] + ':' + str(SYS_AGENT_PORT)) as channel:
            stub = sysagent.sysagent_pb2_grpc.SysAgentStub(channel)
            req = s_pb2.FileServerStartRequest(server_ip=opaque["server_ip"],
                                               operation=opaque["operation"],
                                               path=opaque["path"],
                                               need_notify=False)
            reply = stub.StartFileServer(request=req)
    except grpc.RpcError as e:
        err_msg = "grpc error. start remote file server failed"
        logging.error(err_msg, e)
        raise exp.RemoteRequestFailException(err_msg)

    if reply.errno != u_pb2.OK:
        err_msg = "start remote file server failed!"
        logging.error(err_msg)
        raise exp.RemoteRequestFailException(err_msg)

    return reply.job_id, reply.server_port


def StartRemoteFileClient(opaque):
    """
    start remote file transmit client
    :param opaque:{"local_path": request.local_path, "remote_path": request.remote_path,
                   "server_ip": server_ip, "server_port": server_port,
                   "operation": "get", "remote_ip":remote_ip}
    :return: job_id
    """
    global SYS_AGENT_PORT
    try:
        with grpc.insecure_channel(opaque["grpc_ip"] + ':' + str(SYS_AGENT_PORT)) as channel:
            stub = sysagent.sysagent_pb2_grpc.SysAgentStub(channel)
            req = s_pb2.FileClientStartRequest(remote_path=opaque["remote_path"], local_path=opaque["local_path"],
                                               server_ip=opaque["server_ip"], server_port=opaque["server_port"],
                                               operation=opaque["operation"], need_notify=False)
            reply = stub.StartFileClient(request=req)
    except grpc.RpcError as e:
        err_msg = "grpc error. start remote file client failed"
        logging.error(err_msg, e)
        raise exp.RemoteRequestFailException(err_msg)

    if reply.errno != u_pb2.OK:
        err_msg = "start remote file client fialed!"
        logging.error(err_msg)
        raise exp.RemoteRequestFailException(err_msg)

    return reply.job_id


def QueryRemoteJob(remote_ip, job_id):
    global SYS_AGENT_PORT
    try:
        with grpc.insecure_channel(remote_ip + ':' + str(SYS_AGENT_PORT)) as channel:
            stub = sysagent.sysagent_pb2_grpc.SysAgentStub(channel)
            req = s_pb2.JobQueryRequest(job_id=job_id)
            reply = stub.QueryJob(request=req)
    except grpc.RpcError as e:
        err_msg = "grpc error. query remote job failed"
        logging.error(err_msg, e)
        raise exp.RemoteRequestFailException(err_msg)

    if reply.errno != u_pb2.OK:
        err_msg = "query remote job status failed!"
        logging.error(err_msg)
        raise exp.RemoteRequestFailException(err_msg)

    return reply.body.status, reply.body.process


def DeleteRemoteJob(remote_ip, job_id):
    global SYS_AGENT_PORT
    try:
        with grpc.insecure_channel(remote_ip + ':' + str(SYS_AGENT_PORT)) as channel:
            stub = sysagent.sysagent_pb2_grpc.SysAgentStub(channel)
            req = s_pb2.JobDeleteRequest(job_id=job_id)
            reply = stub.DeleteJob(request=req)
    except grpc.RpcError as e:
        err_msg = "grpc error. delete remote job failed"
        logging.error(err_msg, e)
        raise exp.RemoteRequestFailException(err_msg)

    if reply.errno != u_pb2.OK:
        err_msg = "delete remote job failed!"
        logging.errno(err_msg)
        raise exp.RemoteRequestFailException(err_msg)


def WaitRemoteServerReady(remote_ip, job_id):
    while True:
        status, process = QueryRemoteJob(remote_ip, job_id)
        if status == u_pb2.JOBSTATUS_PROCESSING:
            time.sleep(0.3)
            break
        else:
            time.sleep(0.2)
    return


def WaitLocalServerReady(job_id):
    while True:
        worker_thd = sysagent.worker.worker_threading
        status, process = worker_thd.query_job(job_id)
        if status == u_pb2.JOBSTATUS_PROCESSING:
            time.sleep(0.3)
            break
        else:
            time.sleep(0.2)
    return


def WaitRemoteJobFinish(remote_ip, remote_job_id):
    status = u_pb2.JOBSTATUS_FINISHED_SUCCESSFULLY
    while True:
        status, process = QueryRemoteJob(remote_ip, remote_job_id)
        if status == u_pb2.JOBSTATUS_FINISHED_SUCCESSFULLY or status == u_pb2.JOBSTATUS_FINISHED_FAILED:
            logging.info("remote job finished. job=%s" % (remote_job_id))
            break
        else:
            time.sleep(0.1)

    return status


def WaitLocalJobFinish(local_job_id):
    worker_thd = sysagent.worker.worker_threading
    status = u_pb2.JOBSTATUS_FINISHED_SUCCESSFULLY
    while True:
        status, process = worker_thd.query_job(local_job_id)
        if status == u_pb2.JOBSTATUS_FINISHED_SUCCESSFULLY or status == u_pb2.JOBSTATUS_FINISHED_FAILED:
            logging.info("local job finished. job=%s" % (local_job_id))
            break
        else:
            time.sleep(0.1)

    return status


def StartTransmitFile(request):
    opaque = {}
    opaque["local_path"] = request.local_path
    opaque["remote_path"] = request.remote_path
    opaque["local_ip"] = request.local_ip
    opaque["remote_ip"] = request.remote_ip
    opaque["grpc_ip"] = request.grpc_ip

    worker_thd = sysagent.worker.worker_threading

    return worker_thd.add_job(wj.JobType.STARTTRANSMITFILE, opaque, request.need_notify)


def TransmitFile(opaque):
    is_client = True
    if is_client:
        # local is client
        server_ip = opaque["remote_ip"]
        server_info = {}
        server_info["server_ip"] = server_ip
        server_info["grpc_ip"] = opaque["grpc_ip"]
        server_info["operation"] = "put"
        server_info["path"] = opaque["remote_path"]

        job_server_id, server_port = StartRemoteFileServer(server_info)
        try:
            WaitRemoteServerReady(opaque["grpc_ip"], job_server_id)

            client_info = {}
            client_info["server_ip"] = server_ip
            client_info["server_port"] = server_port
            client_info["local_path"] = opaque["local_path"]
            client_info["remote_path"] = opaque["remote_path"]
            client_info["operation"] = "put"

            RunLocalFileClient(client_info)
            status = WaitRemoteJobFinish(opaque["grpc_ip"], job_server_id)
            if status != u_pb2.JOBSTATUS_FINISHED_SUCCESSFULLY:
                err_msg = "file transmit remote server process failed!"
                raise exp.FileTransFailException(err_msg=err_msg)
        finally:
            DeleteRemoteJob(opaque["grpc_ip"], job_server_id)
    else:
        # local is server
        server_ip = opaque["local_ip"]
        server_info = {}
        server_info["server_ip"] = server_ip
        server_info["operation"] = "get"
        server_info["path"] = opaque["local_path"]

        job_server_id, server_port = StartLocalFileServer(server_info)
        WaitLocalServerReady(job_server_id)

        client_info = {}
        client_info["local_path"] = opaque["local_path"]
        client_info["remote_path"] = opaque["remote_path"]
        client_info["server_ip"] = server_ip
        client_info["server_port"] = server_port
        client_info["operation"] = "get"
        client_info["grpc_ip"] = opaque["grpc_ip"]

        job_client_id = StartRemoteFileClient(client_info)
        try:
            status = WaitLocalJobFinish(job_server_id)
            if status != u_pb2.JOBSTATUS_FINISHED_SUCCESSFULLY:
                err_msg = "file transmit local server process failed!"
                raise exp.FileTransFailException(err_msg=err_msg)

            status = WaitRemoteJobFinish(opaque["grpc_ip"], job_client_id)
            if status != u_pb2.JOBSTATUS_FINISHED_SUCCESSFULLY:
                err_msg = "file transmit remote client process failed!"
                raise exp.FileTransFailException(err_msg=err_msg)
        finally:
            DeleteRemoteJob(opaque["grpc_ip"], job_client_id)

    return


def _SysPreCheckAndSetMode(mode):
    host_mode = GetSysHostMode()
    if host_mode == HostMode.NORMAL:
        if mode == HostMode.MAINTENANCE:
            # switch mode from normal to maintenance
            worker_thd = sysagent.worker.worker_threading
            if not worker_thd.is_own_jobs():
                logging.info("set host mode from normal to maintenance success")
                SetSysHostMode(mode)
            else:
                err_code = u_pb2.SYS_PRECHECK_SET_FAIL
                err_msg = "there is at least 1 running job, cannot set MAINTENANCE mode."
                raise exp.HostModeException(err_msg, err_code)
    elif host_mode == HostMode.MAINTENANCE:
        if mode == HostMode.NORMAL:
            # switch mode from maintenance to normal
            logging.info("set host mode from maintenance to normal success")
            SetSysHostMode(HostMode.NORMAL)


def _VirtPreCheckAndSetMode(mode):
    pass


def _VirtGetHostMode():
    pass


def _StorePreCheckAndSetMode(mode):
    pass


def _StoreGetHostMode():
    pass


def _PreCheckAndSetHostMode(mode):
    _SysPreCheckAndSetMode(mode)
    _VirtPreCheckAndSetMode(mode)
    _StorePreCheckAndSetMode(mode)


def _SetGlobalCfgHostMode(mode):
    try:
        conf = GlobalConfig()
        conf.SetConfigHostMode(mode)
    except Exception:
        err_code = u_pb2.SYS_CFGMODE_FAIL
        err_msg = "set host mode to global config file failed"
        raise exp.HostModeException(err_msg, err_code)


def GetSysHostMode():
    global _GLOBAL_HOST_MODE
    global _GLOBAL_HOST_MODE_LOCK

    mode = HostMode.UNKNOWN

    with _GLOBAL_HOST_MODE_LOCK:
        mode = copy.deepcopy(_GLOBAL_HOST_MODE)

    return mode


def SetSysHostMode(mode):
    global _GLOBAL_HOST_MODE
    global _GLOBAL_HOST_MODE_LOCK

    with _GLOBAL_HOST_MODE_LOCK:
        _GLOBAL_HOST_MODE = mode


def _CheckAgentsHostMode(mode):
    pass


def PreCheckAndSetHostMode(mode):
    host_mode = GetSysHostMode()
    if host_mode == mode:
        logging.info("no need to set mode. current mode:%s" % (HostModeToString(mode)))
        return
    old_mode = host_mode
    try:
        # 1.notity other agents change into specified mode
        _PreCheckAndSetHostMode(mode)
        # 2.write new mode into global config file
        _SetGlobalCfgHostMode(mode)
        # 3.recheck other agents to ensure the mode right
        _CheckAgentsHostMode(mode)
    except exp.HostModeException as e:
        logging.error(e.err_msg)
        if e.err_code == u_pb2.SYS_SETMODE_FAIL or e.err_code == u_pb2.SYS_CFGMODE_FAIL:
            # check or set new mode failed, all agents rollback to old mode.
            _PreCheckAndSetHostMode(old_mode)
        elif e.err_code == u_pb2.SYS_RECHECKMODE_FAIL:
            # check or set new mode failed, all agents and global config file both rollback to old mode.
            _SetGlobalCfgHostMode(old_mode)
            _PreCheckAndSetHostMode(old_mode)

        err_code = u_pb2.SYS_SETMODE_FAIL
        raise exp.HostModeException(err_code=err_code)


def HostShutdown(job):
    opaque = job.get_opaque()
    shut_type = opaque['shut_type']
    if shut_type == util.SHUTDOWN:
        cmd = util.CMD_SHUTDOWN
    elif shut_type == util.REBOOT:
        cmd = util.CMD_REBOOT + ' -p'
    logging.info(cmd)
    ret = envoy.run(cmd)
    if ret.status_code:
        # shutdown failed
        err_msg = "shutdown/reboot host failed"
        raise exp.SystemOperationException(err_msg)
    else:
        # shutdown success
        logging.info("shutdown/reboot success")


def Shutdown(shut_type):
    if shut_type not in (util.SHUTDOWN, util.REBOOT):
        err_msg = "not support operation: %s" % shut_type
        err_code = u_pb2.SYS_INVAL
        raise exp.SystemOperationException(err_code=err_code, err_msg=err_msg)

    if GetSysHostMode() == HostMode.MAINTENANCE:
        # only in maintenance mode, can host shutdown or reboot
        worker_thd = sysagent.worker.worker_threading
        shut_info = {}
        shut_info["shut_type"] = shut_type
        worker_thd.add_job(wj.JobType.SHUTDOWN, shut_info)
    else:
        err_msg = "current mode is not MAINTENANCE, cannot shutdown/reboot."
        raise exp.SystemOperationException(err_msg=err_msg)
