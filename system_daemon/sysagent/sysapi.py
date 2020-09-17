#!/usr/bin/python3
# -*- coding: utf-8 -*-
import logging
import subprocess
import traceback
import sysagent.sysagent_pb2
import sysagent.sysagent_pb2_grpc
import sysagent.util_pb2

from util_base.sys_util import HostModeToString
from util_base.sys_util import StringToHostMode

import sysagent.worker
from sysagent.util import Verify
from sysagent.util import ExternalSysUtil as ExUtil
from sysagent.driver import HostName
from sysagent.driver import HostManager as HostMgr
from sysagent.driver import HostCapability as HostCap
from sysagent.driver import StartLocalFileClient as StartLocalFileClient
from sysagent.driver import StartLocalFileServer as StartLocalFileServer
from sysagent.driver import StartTransmitFile as StartTransmitFile
from sysagent.driver import PreCheckAndSetHostMode
from sysagent.driver import GetSysHostMode
from sysagent.driver import Shutdown
from sysagent import exception as exp


class SysAgent(sysagent.sysagent_pb2_grpc.SysAgentServicer):
    """SysAgent API"""

    def ConnectHost(self, request, context):
        """Connect Host
        :param request: request information.
                        request.manager_ip: The manager ip
                        request.name: The name of user
                        request.passwd: The password of user
        :returns: util_pb2.OK successfully
                  util_pb2.SYS_INVAL invalid argument
                  util_pb2.SYS_USER_PASSWD user or password failed
                  util_pb2.SYS_AGAIN connect repeated
        """
        ret = sysagent.util_pb2.OK
        logging.info('connect ip: %s' % request.manager_ip)

        while True:
            body = sysagent.sysagent_pb2.HostConnectReply.msg()
            body.is_managed = False
            # check ip
            if not Verify.is_ipv4_valid(request.manager_ip):
                logging.error('ip formal error: %s' % request.manager_ip)
                ret = sysagent.util_pb2.SYS_INVAL
                break

            # check name and password
            if request.name != 'root':
                logging.error('permission denied, user must be root')
                ret = sysagent.util_pb2.SYS_PERMISSION
                break
            if not ExUtil.CheckPasswd(request.name, request.passwd):
                logging.error('wrong user or password')
                ret = sysagent.util_pb2.SYS_USER_PASSWD
                break

            # check config file
            host_mgr = HostMgr()
            ip = host_mgr.get_ip()
            if not ip:
                host_mgr.set_ip(request.manager_ip)
            else:
                if request.force:
                    host_mgr.set_ip(request.manager_ip)
                else:
                    body.is_managed = True
                    body.manager_ip = ip
                    logging.warn('%s has been connected' % ip)
                    ret = sysagent.util_pb2.SYS_AGAIN
            break

        return sysagent.sysagent_pb2.HostConnectReply(body=body, errno=ret)

    def DisConnectHost(self, request, context):
        """DisConnect Host
        :param request: request information
                        request.manager_ip: The manager ip
        :returns: util_pb2.OK successfully
                  util_pb2.SYS_NOTFOUND no manager ip connected
                  util_pb2.SYS_NOTMATCH manager ip is not matched
        """
        ret = sysagent.util_pb2.OK
        logging.info('manager ip: %s.' % request.manager_ip)

        # check config file
        host_mgr = HostMgr()
        ip = host_mgr.get_ip()
        if not ip:
            logging.error('manager ip is not found')
            ret = sysagent.util_pb2.SYS_NOTFOUND
        else:
            if ip == request.manager_ip:
                host_mgr.set_ip('')
            else:
                logging.error('manager ip %s is not match with %s.' %
                              (ip, request.manager_ip))
                ret = sysagent.util_pb2.SYS_NOTMATCH

        return sysagent.sysagent_pb2.HostDisConnectReply(errno=ret)

    def ModifyHostPasswd(self, request, context):
        """Modify password of user for host
        :param request: request information
                        request.name: user name
                        request.passwd: password of user name
                        request.passwd_new: new password of user name
        :returns: util_pb2.OK successfully
                  util_pb2.SYS_NOTFOUND user name not found
                  util_pb2.SYS_USER_PASSWD user password error
                  util_pb2.SYS_FAIL modify password error
        """
        ret = sysagent.util_pb2.OK
        logging.info('user name:%s .' % request.name)

        while True:
            # check user name
            if not len(request.name):
                logging.error('user name is null')
                ret = sysagent.util_pb2.SYS_INVAL
                break
            name = request.name + ':'
            with open('/etc/passwd') as f:
                lines = f.readlines()
                if 0 not in [c.strip().find(name) for c in lines]:
                    logging.error('user name(%s) not found.' %
                                  request.name)
                    ret = sysagent.util_pb2.SYS_NOTFOUND
                    break

            # check user name and password
            if not request.force:
                if not ExUtil.CheckPasswd(request.name, request.passwd):
                    logging.error('wrong user or password')
                    ret = sysagent.util_pb2.SYS_USER_PASSWD
                    break

            # modify password
            if not len(request.passwd_new):
                logging.error('new password is null')
                ret = sysagent.util_pb2.SYS_INVAL
                break
            cmd = ['passwd', '--stdin']
            cmd.append(request.name)
            passwd = request.passwd_new
            p = subprocess.Popen(cmd,
                                 stdin=subprocess.PIPE,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 shell=False)
            out, err = p.communicate(input=passwd.encode('utf-8'))
            if err:
                logging.error('modify password: %s.' % err)
                ret = sysagent.util_pb2.SYS_FAIL
            break

        return sysagent.sysagent_pb2.HostDisConnectReply(errno=ret)

    def GetVersion(self, request, context):
        """Get Version
        :param request: None
        :returns: util_pb2.OK successfully
                  util_pb2.SYS_NOTFOUND file not found
                  util_pb2.SYS_INVAL invalid arument
                  util_pb2.SYS_FAIL failed
        """
        errno = sysagent.util_pb2.OK
        body = sysagent.sysagent_pb2.VersionGetReply.msg()
        try:
            host_cap = HostCap()
            body.inner, body.outer = host_cap.version
        except (exp.InvalidValueException, exp.FileNotFoundException) as e:
            logging.error('%s' % e.err_msg)
            errno = e.err_code
        except Exception as e:
            logging.error('%s' % e)
            logging.error(traceback.format_exc())
            errno = sysagent.util_pb2.SYS_FAIL
        return sysagent.sysagent_pb2.VersionGetReply(body=body, errno=errno)

    def GetHostInfo(self, request, context):
        """Get host information
        :param request: None
        :returns: util_pb2.OK successfully
                  util_pb2.SYS_NOTFOUND file not found
                  util_pb2.SYS_INVAL invalid arument
                  util_pb2.SYS_FAIL failed
        """
        errno = sysagent.util_pb2.OK
        body = sysagent.sysagent_pb2.HostInfoGetReply.msg()
        try:
            host_cap = HostCap()
            body.host_ip = host_cap.host_ip
            body.host_name = host_cap.host_name
            body.host_arch = host_cap.host_arch
            body.host_module = host_cap.host_module
            body.cpu_sockets, body.cpu_cores_per_socket, body.cpu_threads_per_core = host_cap.cpu_counts
            body.cpu_module = host_cap.cpu_module
            body.cpu_speed = host_cap.cpu_speed
            body.cpu_rate = host_cap.cpu_rate
            body.mem_total, body.mem_free = host_cap.mem_info
            body.ver_inner, body.ver_outer = host_cap.version
            body.time_now = host_cap.time_now
            body.time_up = host_cap.time_up
        except (exp.InvalidValueException, exp.FileNotFoundException) as e:
            logging.error('%s' % e.err_msg)
            errno = e.err_code
            logging.error(traceback.format_exc())
        except Exception as e:
            errno = sysagent.util_pb2.SYS_FAIL
            logging.error('%s', e)
            logging.error(traceback.format_exc())
        return sysagent.sysagent_pb2.HostInfoGetReply(body=body, errno=errno)

    def SyncHostInfo(self, request, context):
        """Synchronize host information
        :param request: request information.
                        request.lists: The list of host information to sync
                        request.deletes: The list of host information to delete
        :returns: util_pb2.OK successfully
                  util_pb2.SYS_INVAL invalid argument
        """
        errno = sysagent.util_pb2.OK
        host_name = HostName()
        for host in request.lists:
            if Verify.is_hostname_valid(host.hostname) and Verify.is_ipv4_valid(host.ip):
                host_name.add(host.hostname, host.ip)
            else:
                errno = sysagent.util_pb2.SYS_INVAL
                logging.info('hostname or ip invalid: %s %s.' % (host.hostname, host.ip))

        for host in request.deletes:
            if Verify.is_hostname_valid(host.hostname):
                host_name.delete(host.hostname)
            else:
                errno = sysagent.util_pb2.SYS_INVAL
                logging.info('hostname invalid: %s.' % host.hostname)

        return sysagent.sysagent_pb2.HostInfoSyncReply(errno=errno)

    def BeatHeart(self, request, context):
        """Heart beat
        :param request: request information.
                        request.manager_ip: The manager ip
        :returns: util_pb2.OK successfully
                  util_pb2.SYS_INVAL invalid argument
                  util_pb2.SYS_NOTFOUND no manager ip connected
                  util_pb2.SYS_NOTMATCH manager ip is not matched
        """
        errno = sysagent.util_pb2.OK
        logging.info('heart beat ip: %s' % request.manager_ip)

        host_mgr = HostMgr()
        ip = host_mgr.get_ip()
        if not ip:
            logging.error('manager ip is not found')
            errno = sysagent.util_pb2.SYS_NOTFOUND
        else:
            if ip != request.manager_ip:
                logging.error('manager ip %s is not match with %s.' %
                              (ip, request.manager_ip))
                errno = sysagent.util_pb2.SYS_NOTMATCH

        return sysagent.sysagent_pb2.HeartBeatReply(errno=errno)

    def QueryJob(self, request, context):
        """Query a job
        :param request: request information.
                        request.job_id: The uuid of job
        :returns: util_pb2.OK successfully
                  util_pb2.SYS_NOTFOUND The uuid of job not found
                  util_pb2.SYS_FAIL failed
        """
        errno = sysagent.util_pb2.OK
        body = sysagent.sysagent_pb2.JobQueryReply.msg()

        try:
            worker_thd = sysagent.worker.worker_threading
            job_tup = worker_thd.query_job(request.job_id)
            logging.info(job_tup)
            body.job_id = request.job_id
            body.status = job_tup[0]
            body.process = job_tup[1]
        except exp.SysagentJobException as e:
            errno = e.err_code
            logging.error('%s' % e.err_msg)
            logging.error(traceback.format_exc())
        except Exception as e:
            errno = sysagent.util_pb2.SYS_FAIL
            logging.error('%s', e)
            logging.error(traceback.format_exc())
        return sysagent.sysagent_pb2.JobQueryReply(body=body, errno=errno)

    def DeleteJob(self, request, context):
        """Delete a job
        :param request: request information.
                        request.job_id: The uuid of job
        :returns: util_pb2.OK successfully
                  util_pb2.SYS_NOTFOUND The uuid of job not found
                  util_pb2.SYS_FAIL failed
        """
        errno = sysagent.util_pb2.OK

        try:
            worker_thd = sysagent.worker.worker_threading
            worker_thd.del_job(request.job_id)
        except exp.SysagentJobException as e:
            errno = e.err_code
            logging.error('%s' % e.err_msg)
            logging.error(traceback.format_exc())
        except Exception as e:
            errno = sysagent.util_pb2.SYS_FAIL
            logging.error('%s', e)
            logging.error(traceback.format_exc())
        return sysagent.sysagent_pb2.JobDeleteReply(errno=errno)

    def FileTransmit(self, request, context):
        """Start file transmit
        :param request: request infomation.
                        request.local_ip
                        request.local_path
                        request.remote_ip
                        request.remote_path
                        request.grpc_ip
                        request.need_notify
        :returns util_pb2.OK successfully
                 util_pb2.SYS_FAIL failed
        """
        try:
            job_id = StartTransmitFile(request)
            errno = sysagent.util_pb2.OK
        except (exp.NoAvailablePortException, exp.RemoteRequestFailException,
                exp.SysagentJobException, exp.FileTransFailException) as e:
            errno = sysagent.util_pb2.SYS_FAIL
            logging.error(e.err_msg)
            logging.error(traceback.format_exc())

        return sysagent.sysagent_pb2.FileTransmitReply(job_id=job_id, errno=errno)

    def StartFileServer(self, request, context):
        try:
            server_info = {}
            server_info["server_ip"] = request.server_ip
            server_info["operation"] = request.operation
            server_info["path"] = request.path

            server_job_id, port = StartLocalFileServer(server_info, request.need_notify)
            errno = sysagent.util_pb2.OK
            server_port = port
            job_id = server_job_id
        except exp.NoAvailablePortException as e:
            errno = sysagent.util_pb2.SYS_FAIL
            server_port = 0
            job_id = "ffffffff-ffff-ffff-ffff-ffffffffffff"
            logging.error(e.err_msg)

        return sysagent.sysagent_pb2.FileServerStartReply(errno=errno, job_id=job_id, server_port=server_port)

    def StartFileClient(self, request, context):
        client_info = {}
        client_info["local_path"] = request.local_path
        client_info["remote_path"] = request.remote_path
        client_info["server_ip"] = request.server_ip
        client_info["server_port"] = request.server_port
        client_info["operation"] = request.operation

        client_job_id = StartLocalFileClient(client_info, request.need_notify)
        job_id = client_job_id
        errno = sysagent.util_pb2.OK

        return sysagent.sysagent_pb2.FileClientStartReply(errno=errno, job_id=job_id)

    def SetHostMode(self, request, context):
        """SetHostMode
        :param request: request
                        request.mode: unknown, normal or maintenance
        :returns errno:
                util_pb2.OK, successfully
                util_pb2.SYS_FAIL, failed
        """
        mode_str = request.mode
        logging.info("precheck and set mode start: %s" % (mode_str))
        mode = StringToHostMode(mode_str)
        try:
            PreCheckAndSetHostMode(mode)
            errno = sysagent.util_pb2.OK
        except exp.HostModeException as e:
            logging.error(e.err_msg)
            logging.error(traceback.format_exc())
            errno = sysagent.util_pb2.SYS_FAIL

        return sysagent.sysagent_pb2.HostModeSetReply(errno=errno)

    def GetHostMode(self, request, context):
        """GetHostMode
        :param request: empty
        :returns errno:
                util_pb2.OK, successfully
                util_pb2.SYS_FAIL, failed
        :returns mode: unknown, normal or maintenance
        """
        mode_str = HostModeToString(GetSysHostMode())
        errno = sysagent.util_pb2.OK
        return sysagent.sysagent_pb2.HostModeGetReply(errno=errno, mode=mode_str)

    def ShutdownHost(self, request, context):
        """ShutdownHost
        :param request: request information.
                        request.shut_type: ('shutdown', 'reboot')
        :returns: util_pb2.OK successfully
                  util_pb2.SYS_FAIL failed
        """
        try:
            Shutdown(request.shut_type)
            errno = sysagent.util_pb2.OK
        except exp.SystemOperationException as e:
            errno = sysagent.util_pb2.SYS_FAIL
            logging.error(e.err_msg)

        return sysagent.sysagent_pb2.HostShutdownReply(errno=errno)


def add_to_server(s):
    sysagent.sysagent_pb2_grpc.add_SysAgentServicer_to_server(SysAgent(), s)
