#!/usr/bin/env python
# encoding: utf-8
from concurrent import futures
import logging
import grpc
import traceback
import time
import threading
import json
import argparse
import prettytable

import libvirt
from util_base import log
from util_base.sys_util import BaseConfig
from util_base.libvirt_util import ConnectionPool
from util_base.grpc_util import GrpcAbortReason
from util_base.grpc_util import ErrorCode as GrpcErrorCode

from . import virt_agent_pb2 as pb
from . import virt_agent_pb2_grpc as pb_grpc
from virt_agent.virt_agent_exception import VirtAgentException, VirtAgentLockException, VirtAgentInvalidException
from virt_agent.virt_agent_exception import VirtAgentDomainXMLException, VirtAgentJsonValidationException
from virt_agent.virt_agent_exception import VirtAgentJobException
from virt_agent import virt_agent_exception
from virt_agent.worker import Worker
from virt_agent.worker_job import JobType
from virt_agent import libvirt_driver
from virt_agent.libvirt_driver import LibvirtEvent, Domain, DOMAIN_LIST
from . import schema
from . import utils
from virt_agent import xml_util

# general
CONFIG_FILE = '/etc/vap/virt-agent.cfg'
VIRT_AGENT_CONF = None

# grpc
GRPC_STATISTIC_ENABLE = 0
# seconds
GRPC_STATISTIC_REPORT_CYCLE = 30

# libvirt
LIBVIRT_CONNECTION_POOL = None
LIBVIRT_EVENT = None

# worker
WORKER = None


class VirtAgentConfig(BaseConfig):
    def GetLibvirtPoolMaxWorker(self):
        size = self.Get('libvirt_pool_max')
        if size is None:
            # set 10 as default
            default_max = 10
            self.Set('libvirt_pool_max', str(default_max))
            return default_max
        else:
            max_worker = int(size)
            return max_worker

    def GetMaxWorker(self):
        size = self.Get('max_worker')
        if size is None:
            # set 5 as default
            max_worker = 5
            self.Set('max_worker', str(max_worker))
        else:
            max_worker = int(size)

        return max_worker


def LoadConfig():
    global VIRT_AGENT_CONF

    VIRT_AGENT_CONF = VirtAgentConfig(CONFIG_FILE)


def LogInit():
    global VIRT_AGENT_CONF

    log.Loginit(VIRT_AGENT_CONF.GetLogPath(), VIRT_AGENT_CONF.GetLogLevel())


class RequestHeaderValidatorInterceptor(grpc.ServerInterceptor):
    def __init__(self):
        self.__counter = {}
        self.__last_report = time.time()
        self.__statistic_lock = threading.Lock()

    def intercept_service(self, continuation, handler_call_details):
        global GRPC_STATISTIC_ENABLE
        global GRPC_STATISTIC_REPORT_CYCLE

        if GRPC_STATISTIC_ENABLE:
            with self.__statistic_lock:
                if handler_call_details.method not in self.__counter:
                    self.__counter[handler_call_details.method] = 1
                else:
                    self.__counter[handler_call_details.method] += 1

                if time.time() - self.__last_report > GRPC_STATISTIC_REPORT_CYCLE:
                    logging.info(self.__counter)
                    self.__last_report = time.time()

        return continuation(handler_call_details)


def virtAgentLibvirtConnCloseCB(conn, reason, opaque):
    global LIBVIRT_EVENT
    global WORKER

    logging.debug(conn)
    logging.debug(LIBVIRT_EVENT)
    # unregister all event cb
    # add a job to waiting for libvirtd is available and reconnect
    param = {}
    param['conn'] = conn
    param['libvirt_event'] = LIBVIRT_EVENT
    WORKER.add_job(JobType.LIBVIRT_EVENT_CONN_CLOSED, param)


def virtAgentDomainEventHandler(conn, dom, event, detail, opaque):
    WORKER.add_job(JobType.LIBVIRT_DOMAIN_EVENT, None)


class VirtAgentServicer(pb_grpc.VirtAgentServicer):
    def Echo(self, request, context):
        return pb.EchoRes(context=request.context)

    def HeartBeat(self, request, context):
        return pb.HeartBeatRes(hbid=request.hbid)

    def QueryJob(self, request, context):
        global WORKER
        job_id = request.job_id

        try:
            (status, process) = WORKER.query_job(job_id)
            return pb.QueryJobRes(code=pb.LIBVIRT_ERR_OK, job_id=job_id, status=status, process=process)
        except VirtAgentJobException as e:
            return pb.QueryJobRes(code=e.err_code)

    def DeleteJob(self, request, context):
        global WORKER
        job_id = request.job_id

        try:
            WORKER.del_job(job_id)
            return pb.DeleteJobRes(code=pb.LIBVIRT_ERR_OK)
        except VirtAgentJobException as e:
            return pb.DeleteJobRes(code=e.err_code)

    def GetLibvirtVersion(self, request, context):
        global LIBVIRT_CONNECTION_POOL
        conn = None

        try:
            conn = LIBVIRT_CONNECTION_POOL.get()
            if conn:
                vers = {}
                vers['libvirt'] = conn.getLibVersion()
                vers['qemu'] = conn.getVersion()
                return pb.GetLibvirtVersionRes(libvirt_version=json.dumps(vers))
            else:
                logging.warning("failed to get libvirt connection")
                exit_reason = GrpcAbortReason(GrpcErrorCode.LIBVIRT_CONNECTION_ERROR,
                                              'failed to get libvirt connection')
                context.abort(grpc.StatusCode.RESOURCE_EXHAUSTED, str(exit_reason))

        except libvirt.libvirtError as e:
            logging.error("%s" % (e.get_error_message()))
            exit_reason = GrpcAbortReason(GrpcErrorCode.LIBVIRT_CONNECTION_ERROR, 'libvirtd is unavailable')
            context.abort(grpc.StatusCode.RESOURCE_EXHAUSTED, str(exit_reason))
            # context.abort_with_status(status)
        finally:
            if conn:
                LIBVIRT_CONNECTION_POOL.put(conn)

    def PrecheckMode(self, request, context):
        return pb.PrecheckRes(code=pb.LIBVIRT_ERR_OK, result=True)

    def SetHostMode(self, request, context):
        return pb.SetHostModeRes(code=pb.LIBVIRT_ERR_OK)

    def GetHostMode(self, request, context):
        return pb.GetHostModeRes(code=pb.LIBVIRT_ERR_OK, mode='normal')

    def PrecheckAndSetHostMode(self, request, context):
        return pb.PrecheckAndSetHostModeRes(code=pb.LIBVIRT_ERR_OK)

    def CreateDomain(self, request, context):
        global LIBVIRT_CONNECTION_POOL
        conn = LIBVIRT_CONNECTION_POOL.get()
        json_data = json.loads(request.json_data)
        domain = Domain(uuid=json_data['uuid'])
        try:
            schema.validate(json_data)
        except VirtAgentJsonValidationException:
            return pb.DomainCreateRes(code=pb.VIRT_AGENT_ERR_JSON_INVALID,
                                      err_msg="json is invalid")

        try:
            with DOMAIN_LIST.lock:
                if DOMAIN_LIST.exists(uuid_str=json_data['uuid']):
                    return pb.DomainCreateRes(code=pb.VIRT_AGENT_ERR_INVALID_UUID,
                                              err_msg='UUID %s is already existed.' % json_data['uuid'])

            try:
                xml_manager = xml_util.XmlManagerDomain()
                xml_manager.parse_template(request.os_type)
                if 'devices' in json_data:
                    xml_manager.create_devices(json_data['devices'])
                xml_manager.update_properties(json_data)

            except VirtAgentDomainXMLException:
                logging.critical(traceback.format_exc())
                return pb.DomainCreateRes(code=pb.LIBVIRT_ERR_INTERNAL_ERROR,
                                          err_msg='Template xml is invalid.')
            if conn:
                conn.defineXML(xml_manager.to_xml_str())

            with DOMAIN_LIST.lock:
                DOMAIN_LIST.append(domain)

            return pb.DomainCreateRes(code=pb.LIBVIRT_ERR_OK)

        except libvirt.libvirtError as e:
            logging.error("%s" % (e.get_error_message()))
            return pb.DomainCreateRes(
                code=utils.generate_backend_error_code(
                    e.get_error_code()),
                err_msg=e.get_error_message())
        except VirtAgentLockException:
            logging.critical(traceback.format_exc())
            return pb.DomainCreateRes(code=pb.LIBVIRT_ERR_INTERNAL_ERROR, err_msg='Virt agent lock error.')
        except Exception:
            logging.critical(traceback.format_exc())
            return pb.DomainCreateRes(code=pb.LIBVIRT_ERR_INTERNAL_ERROR, err_msg='Unknown internal error.')
        finally:
            if conn:
                LIBVIRT_CONNECTION_POOL.put(conn)

    def DeleteDomain(self, request, context):
        global LIBVIRT_CONNECTION_POOL
        conn = LIBVIRT_CONNECTION_POOL.get()

        try:
            with DOMAIN_LIST.lock:
                if not DOMAIN_LIST.exists(request.uuid):
                    return pb.DomainDeleteRes(code=pb.VIRT_AGENT_ERR_INVALID_UUID,
                                              err_msg='UUID %s is not found in cache.' % request.uuid)

            if conn:
                domain_ref = conn.lookupByUUIDString(request.uuid)
                """TODO:
                    * Add test case of (domain_ref is None) and (uuid exists in DOMAIN_LIST).
                    * In this case, domain is manually undefined but not by virt_agentd.
                """
                if domain_ref:
                    domain_ref.undefine()

            with DOMAIN_LIST.lock:
                DOMAIN_LIST.pop(request.uuid)

            return pb.DomainDeleteRes(code=pb.LIBVIRT_ERR_OK)

        except libvirt.libvirtError as e:
            logging.error("%s" % (e.get_error_message()))
            return pb.DomainDeleteRes(
                code=utils.generate_backend_error_code(
                    e.get_error_code()),
                err_msg=e.get_error_message())
        except VirtAgentInvalidException:
            logging.critical(traceback.format_exc())
            return pb.DomainDeleteRes(code=pb.VIRT_AGENT_ERR_INVALID_UUID, err_msg='UUID is not found.')
        except VirtAgentLockException:
            logging.critical(traceback.format_exc())
            return pb.DomainDeleteRes(code=pb.LIBVIRT_ERR_INTERNAL_ERROR, err_msg='Virt agent lock error.')
        except Exception:
            logging.critical(traceback.format_exc())
            return pb.DomainDeleteRes(code=pb.LIBVIRT_ERR_INTERNAL_ERROR, err_msg='Unknown internal error.')
        finally:
            if conn:
                LIBVIRT_CONNECTION_POOL.put(conn)

    def ListDomains(self, request, context):
        global LIBVIRT_CONNECTION_POOL
        conn = LIBVIRT_CONNECTION_POOL.get()
        uuids = []

        try:
            if conn:
                domains = conn.listAllDomains(0)
                for domain in domains:
                    uuids.append(domain.UUIDString())
            return pb.DomainListRes(code=pb.LIBVIRT_ERR_OK, domains=uuids)
        except libvirt.libvirtError as e:
            logging.error("Libvirt error message: %s" % (e.get_error_message()))
            return pb.DomainDeleteRes(
                code=utils.generate_backend_error_code(
                    e.get_error_code()),
                err_msg=e.get_error_message())
        except Exception:
            logging.critical(traceback.format_exc())
            return pb.DomainDeleteRes(code=pb.LIBVIRT_ERR_INTERNAL_ERROR, err_msg='Unknown internal error.')
        finally:
            if conn:
                LIBVIRT_CONNECTION_POOL.put(conn)

    def GetDomainsState(self, request, context):
        global LIBVIRT_CONNECTION_POOL
        conn = LIBVIRT_CONNECTION_POOL.get()
        domain_states = []

        try:
            with DOMAIN_LIST.lock:
                for uuid in request.uuids:
                    if not DOMAIN_LIST.exists(uuid):
                        return pb.DomainsStateGetRes(code=pb.VIRT_AGENT_ERR_INVALID_UUID,
                                                     err_msg='UUID %s is not found in cache.' % uuid)

            if conn:
                for uuid in request.uuids:
                    domain_ref = conn.lookupByUUIDString(uuid)
                    state, _ = domain_ref.state()
                    domain_state = pb.DomainStateModel(uuid=uuid, state=utils.generate_backend_domain_state(state))
                    domain_states.append(domain_state)

            return pb.DomainsStateGetRes(code=pb.LIBVIRT_ERR_OK, states=domain_states)
        except libvirt.libvirtError as e:
            logging.error("Libvirt error message: %s" % (e.get_error_message()))
            return pb.DomainDeleteRes(
                code=utils.generate_backend_error_code(
                    e.get_error_code()),
                err_msg=e.get_error_message())
        except VirtAgentInvalidException:
            logging.critical(traceback.format_exc())
            return pb.DomainDeleteRes(code=pb.VIRT_AGENT_ERR_INVALID_UUID, err_msg='UUID is not found.')
        except VirtAgentLockException:
            logging.critical(traceback.format_exc())
            return pb.DomainDeleteRes(code=pb.LIBVIRT_ERR_INTERNAL_ERROR, err_msg='Virt agent lock error.')
        except Exception:
            logging.critical(traceback.format_exc())
            return pb.DomainDeleteRes(code=pb.LIBVIRT_ERR_INTERNAL_ERROR, err_msg='Unknown internal error.')
        finally:
            if conn:
                LIBVIRT_CONNECTION_POOL.put(conn)

    def DumpDomains(self, request, context):
        global LIBVIRT_CONNECTION_POOL
        conn = LIBVIRT_CONNECTION_POOL.get()
        _domains = []

        try:
            for uuid in request.uuids:
                with DOMAIN_LIST.lock:
                    if not DOMAIN_LIST.exists(uuid):
                        return pb.DomainsDumpRes(code=pb.VIRT_AGENT_ERR_INVALID_UUID,
                                                 err_msg='UUID %s is not found in cache.' % uuid)
                domain = conn.lookupByUUIDString(uuid)
                dom_xml = libvirt_driver.GetDomainXMLRoot(domain)
                xml_manager = xml_util.XmlManagerDomain()
                xml_manager.parse(dom_xml)
                _domains.append(json.dumps(xml_manager.to_dict()))

            return pb.DomainsDumpRes(code=pb.LIBVIRT_ERR_OK, domains=_domains)
        except libvirt.libvirtError as e:
            logging.error("Libvirt error message: %s" % (e.get_error_message()))
            return pb.DomainDeleteRes(
                code=utils.generate_backend_error_code(
                    e.get_error_code()),
                err_msg=e.get_error_message())
        except VirtAgentInvalidException:
            logging.critical(traceback.format_exc())
            return pb.DomainDeleteRes(code=pb.VIRT_AGENT_ERR_INVALID_UUID, err_msg='UUID is not found.')
        except VirtAgentLockException:
            logging.critical(traceback.format_exc())
            return pb.DomainDeleteRes(code=pb.LIBVIRT_ERR_INTERNAL_ERROR, err_msg='Virt agent lock error.')
        except Exception:
            logging.critical(traceback.format_exc())
            return pb.DomainDeleteRes(code=pb.LIBVIRT_ERR_INTERNAL_ERROR, err_msg='Unknown internal error.')
        finally:
            if conn:
                LIBVIRT_CONNECTION_POOL.put(conn)

    def ModifyDomain(self, request, context):
        global LIBVIRT_CONNECTION_POOL
        conn = LIBVIRT_CONNECTION_POOL.get()
        json_data = json.loads(request.json_data)

        try:
            with DOMAIN_LIST.lock:
                if not DOMAIN_LIST.exists(request.uuid):
                    return pb.DomainModifyRes(code=pb.VIRT_AGENT_ERR_INVALID_UUID,
                                              err_msg='UUID %s is not found in cache.' % request.uuid)

            if conn:
                domain_ref = conn.lookupByUUIDString(request.uuid)
                if domain_ref is None:
                    return pb.DomainModifyRes(code=pb.VIRT_AGENT_ERR_INVALID_UUID,
                                              err_msg='UUID %s is not found in cache.' % request.uuid)

            xml_manager = xml_util.XmlManagerDomain()
            xml_manager.parse(libvirt_driver.GetDomainXMLRoot(domain_ref))

            if request.type == pb.OPERATION_TYPE_ADD:
                xml_manager.create_devices(json_data['devices'])
            elif request.type == pb.OPERATION_TYPE_DELETE:
                xml_manager.del_devices(json_data['devices'])
            elif request.type == pb.OPERATION_TYPE_MOUNT:
                xml_manager.insert_cdrom(json_data['devices'])
            elif request.type == pb.OPERATION_TYPE_UMOUNT:
                xml_manager.eject_cdrom(json_data['devices'])
            elif request.type == pb.OPERATION_TYPE_UPDATE:
                xml_manager.update_properties(json_data)
            else:
                return pb.DomainModifyRes(code=pb.VIRT_AGENT_ERR_NOT_IMPLEMENTED,
                                          err_msg='operation type %s not supported.' % request.type)

            if conn:
                conn.defineXML(xml_manager.to_xml_str())

            return pb.DomainModifyRes(code=pb.LIBVIRT_ERR_OK)

        except libvirt.libvirtError as e:
            logging.error("%s" % (e.get_error_message()))
            return pb.DomainModifyRes(
                code=utils.generate_libvirt_error(
                    e.get_error_code()),
                err_msg=e.get_error_message())
        except VirtAgentInvalidException:
            logging.critical(traceback.format_exc())
            return pb.DomainModifyRes(code=pb.VIRT_AGENT_ERR_INVALID_UUID, err_msg='UUID is not found.')
        except VirtAgentLockException:
            logging.critical(traceback.format_exc())
            return pb.DomainModifyRes(code=pb.LIBVIRT_ERR_INTERNAL_ERROR, err_msg='Virt agent lock error.')
        except Exception:
            logging.critical(traceback.format_exc())
            return pb.DomainModifyRes(code=pb.LIBVIRT_ERR_INTERNAL_ERROR, err_msg='Unknown internal error.')
        finally:
            if conn:
                LIBVIRT_CONNECTION_POOL.put(conn)

    def StartDomain(self, request, context):
        global LIBVIRT_CONNECTION_POOL
        dom_id = request.uuid
        need_notify = not request.no_need_notify

        opaque = {}
        opaque['dom_id'] = dom_id
        opaque['connection_pool'] = LIBVIRT_CONNECTION_POOL
        job_id = WORKER.add_job(JobType.LIBVIRT_DOMAIN_START, opaque, need_notify)

        return pb.DomainStartRes(code=pb.LIBVIRT_ERR_OK, job_id=job_id)

    def StopDomain(self, request, context):
        global LIBVIRT_CONNECTION_POOL
        dom_id = request.uuid
        force = request.force
        need_notify = not request.no_need_notify

        opaque = {}
        opaque['dom_id'] = dom_id
        opaque['force'] = force
        opaque['connection_pool'] = LIBVIRT_CONNECTION_POOL
        job_id = WORKER.add_job(JobType.LIBVIRT_DOMAIN_STOP, opaque, need_notify)

        return pb.DomainStopRes(code=pb.LIBVIRT_ERR_OK, job_id=job_id)

    def MigrateDomain(self, request, context):
        global LIBVIRT_CONNECTION_POOL
        need_notify = not request.no_need_notify

        opaque = {}
        opaque['dom_id'] = request.uuid
        opaque['postcopy'] = request.postcopy
        opaque['connection_pool'] = LIBVIRT_CONNECTION_POOL
        opaque['timeout'] = request.time_out
        if request.destination != '':
            opaque['destination'] = request.destination
        if request.destination_json != '':
            opaque['destination_json'] = json.loads(request.destination_json)

        job_id = WORKER.add_job(JobType.LIBVIRT_DOMAIN_MIGRATE, opaque, need_notify)

        return pb.DomainMigrateRes(code=pb.LIBVIRT_ERR_OK, job_id=job_id)

    def CreateSnapshot(self, request, context):
        global LIBVIRT_CONNECTION_POOL
        dom_id = request.dom_uuid
        snapshot_name = request.name
        live_snapshot = request.with_memory
        need_notify = not request.no_need_notify

        logging.debug('domain: %s snapshot name: %s type: %s' %
                      (dom_id, snapshot_name, 'live snapshot' if (live_snapshot) else 'disk-only snapshot'))

        opaque = {}
        opaque['dom_id'] = dom_id
        opaque['snapshot_name'] = snapshot_name
        opaque['live_snapshot'] = live_snapshot
        opaque['connection_pool'] = LIBVIRT_CONNECTION_POOL
        job_id = WORKER.add_job(JobType.LIBVIRT_SNAPSHOT_CREATE, opaque, need_notify)

        return pb.SnapshotCreateRes(code=pb.LIBVIRT_ERR_OK, job_id=job_id)

    def DeleteSnapshot(self, request, context):
        global LIBVIRT_CONNECTION_POOL
        dom_id = request.dom_uuid
        snapshot_names = request.names
        need_notify = not request.no_need_notify

        logging.debug('domain: %s snapshot name: %s' % (dom_id, snapshot_names))

        opaque = {}
        opaque['dom_id'] = dom_id
        opaque['snapshot_names'] = snapshot_names
        opaque['connection_pool'] = LIBVIRT_CONNECTION_POOL
        job_id = WORKER.add_job(JobType.LIBVIRT_SNAPSHOT_DELETE, opaque, need_notify)

        return pb.SnapshotDeleteRes(code=pb.LIBVIRT_ERR_OK, job_id=job_id)

    def ListSnapshot(self, request, context):
        global LIBVIRT_CONNECTION_POOL
        dom_ids = request.dom_uuid

        logging.debug('domain: %s' % (dom_ids))

        opaque = {}
        opaque['dom_ids'] = dom_ids
        opaque['connection_pool'] = LIBVIRT_CONNECTION_POOL

        try:
            snapshot_info_list = libvirt_driver.DomainSnapshotList(opaque)
            return pb.SnapshotListRes(code=pb.LIBVIRT_ERR_OK, snapshot_info=snapshot_info_list)
        except VirtAgentException:
            return pb.SnapshotListRes(code=pb.LIBVIRT_ERR_INTERNAL_ERROR)

    def RevertSnapshot(self, request, context):
        global LIBVIRT_CONNECTION_POOL
        dom_id = request.dom_uuid
        snapshot_name = request.name

        logging.debug('domain: %s snapshot name: %s' % (dom_id, snapshot_name))

        opaque = {}
        opaque['dom_id'] = dom_id
        opaque['snapshot_name'] = snapshot_name
        opaque['connection_pool'] = LIBVIRT_CONNECTION_POOL

        try:
            libvirt_driver.DomainSnapshotRevert(opaque)
            return pb.SnapshotListRes(code=pb.LIBVIRT_ERR_OK)
        except VirtAgentException:
            return pb.SnapshotListRes(code=pb.LIBVIRT_ERR_INTERNAL_ERROR)

    def FinishMigration(self, request, context):
        global LIBVIRT_CONNECTION_POOL
        opaque = {}
        opaque['dom_id'] = request.uuid
        opaque['snap_xmls'] = request.snap_xmls
        opaque['tmp_info'] = json.loads(request.tmp_info)
        opaque['connection_pool'] = LIBVIRT_CONNECTION_POOL

        job_id = WORKER.add_job(JobType.LIBVIRT_FINISH_MIGRATION, opaque, need_notify=False)
        return pb.FinishMigrationRes(code=pb.LIBVIRT_ERR_OK, job_id=job_id)

    def PrecheckMigration(self, request, context):
        global LIBVIRT_CONNECTION_POOL
        opaque = {}
        opaque['dom_id'] = request.uuid
        opaque['destination'] = request.destination
        opaque['destination_json'] = json.loads(request.destination_json)
        opaque['connection_pool'] = LIBVIRT_CONNECTION_POOL

        try:
            libvirt_driver.PrecheckMigration(opaque)
        except virt_agent_exception.VirtAgentLibvirtException as e:
            logging.error("Libvirt exception  message: %s" % (e.get_error_message()))
            return pb.MigrationPrecheckRes(
                code=utils.generate_libvirt_error(
                    e.get_error_code()),
                err_msg=e.get_error_message())
        except virt_agent_exception.VirtAgentMigrationException as e2:
            return pb.MigrationPrecheckRes(code=e2.err_code(), err_msg=e2.err_msg())
        return pb.MigrationPrecheckRes(code=pb.LIBVIRT_ERR_OK)

    def PrepareMigration(self, request, context):
        global LIBVIRT_CONNECTION_POOL
        opaque = {}
        opaque['live'] = request.live
        opaque['destination_json'] = json.loads(request.destination_json)
        opaque['tmp_info'] = json.loads(request.tmp_info)

        try:
            libvirt_driver.PrepareMigration(opaque)
        except virt_agent_exception.VirtAgentException as e:
            return pb.PrepareMigrationRes(code=e.err_code(), err_msg=e.err_msg())
        return pb.PrepareMigrationRes(code=pb.LIBVIRT_ERR_OK)

    def RevertMigration(self, request, context):
        global LIBVIRT_CONNECTION_POOL
        opaque = {}
        opaque['dom_id'] = request.uuid
        opaque['destination_json'] = json.loads(request.destination_json)
        opaque['tmp_info'] = json.loads(request.tmp_info)
        opaque['connection_pool'] = LIBVIRT_CONNECTION_POOL

        try:
            libvirt_driver.RevertMigration(opaque)
        except libvirt.libvirtError as e:
            logging.error("Libvirt error message: %s" % (e.get_error_message()))
            return pb.RevertMigrationRes(
                code=utils.generate_libvirt_error(
                    e.get_error_code()),
                err_msg=e.get_error_message())
        return pb.RevertMigrationRes(code=pb.LIBVIRT_ERR_OK)


def initialize_domlist():
    conn = LIBVIRT_CONNECTION_POOL.get()
    try:
        if conn:
            domain_list = conn.listAllDomains(0)
    except libvirt.libvirtError as e:
        logging.error("Initilize domlist failed from libvirt, error message: %s" % (e.get_error_message()))
        exit(-1)
    except Exception:
        logging.critical(traceback.format_exc())
        exit(-1)
    finally:
        if conn:
            LIBVIRT_CONNECTION_POOL.put(conn)

    for domain in domain_list:
        uuid = domain.UUIDString()
        domain = Domain(uuid=uuid)
        with DOMAIN_LIST.lock:
            if not DOMAIN_LIST.exists(uuid):
                DOMAIN_LIST.append(domain)


def main():
    global VIRT_AGENT_CONF
    global LIBVIRT_CONNECTION_POOL
    global LIBVIRT_EVENT
    global WORKER

    try:
        LoadConfig()
        LogInit()
        logging.info('start')
        logging.info('listening on %d' % VIRT_AGENT_CONF.GetServicePort())
        logging.info('grpc worker %d' % VIRT_AGENT_CONF.GetGrpcWorkerSize())
        logging.info('libvirt pool max %d' % VIRT_AGENT_CONF.GetLibvirtPoolMaxWorker())
        logging.info('max worker %d' % VIRT_AGENT_CONF.GetMaxWorker())

        # worker
        WORKER = Worker(VIRT_AGENT_CONF.GetMaxWorker())
        WORKER.init_notifier()
        WORKER.run()

        # libvirt connection pool
        logging.info('start libvirt connection pool')
        LIBVIRT_CONNECTION_POOL = ConnectionPool(maxsize=VIRT_AGENT_CONF.GetLibvirtPoolMaxWorker(),
                                                 close_cb=virtAgentLibvirtConnCloseCB)

        # register event on LIBVIRT_EVENT
        LIBVIRT_EVENT = LibvirtEvent(LIBVIRT_CONNECTION_POOL)
        LIBVIRT_EVENT.register_domain_event_cb(virtAgentDomainEventHandler)
        LIBVIRT_EVENT.enable()

        # initialize DOMAIN_LIST
        initialize_domlist()

        # grpc
        header_check = RequestHeaderValidatorInterceptor()
        server = grpc.server(thread_pool=futures.ThreadPoolExecutor(max_workers=VIRT_AGENT_CONF.GetGrpcWorkerSize()),
                             interceptors=(header_check,))
        pb_grpc.add_VirtAgentServicer_to_server(VirtAgentServicer(), server)
        server.add_insecure_port('0.0.0.0:%d' % (VIRT_AGENT_CONF.GetServicePort()))
        server.start()

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            server.stop(0)

        LIBVIRT_EVENT.disable()
        logging.debug('stop')

    except Exception:
        logging.critical(traceback.format_exc())


def VACliClient(func, opaque):
    global VIRT_AGENT_CONF

    try:
        with grpc.insecure_channel("127.0.0.1:%d" % (VIRT_AGENT_CONF.GetServicePort())) as channel:
            stub = pb_grpc.VirtAgentStub(channel)
            func(stub, opaque)
    except grpc.RpcError:
        print('connecting to virt_agentd failed')


def VACliSnapshotCreate(args):
    def func(stub, args):
        finished = False
        request = pb.SnapshotCreateReq(dom_uuid=args.domain, name=args.snapshot_name,
                                       with_memory=True if args.snapshot_type == 'live' else False,
                                       no_need_notify=True)
        try:
            res = stub.CreateSnapshot(request, timeout=10)
            job_id = res.job_id
            while not finished:
                res = stub.QueryJob(pb.QueryJobReq(job_id=job_id), timeout=10)
                if res.code != pb.LIBVIRT_ERR_OK:
                    # retry after 1s
                    time.sleep(1)
                    continue
                if res.status == pb.JOBSTATUS_FINISHED_SUCCESSFULLY and res.process == 100:
                    print("snapshot create successfully")
                    finished = True
                if res.status == pb.JOBSTATUS_FINISHED_FAILED:
                    print("snapshot create failed")
                    finished = True
                time.sleep(1)
            res = stub.DeleteJob(pb.DeleteJobReq(job_id=job_id), timeout=10)
            if res.code != pb.LIBVIRT_ERR_OK:
                print('failed to delete job')
        except grpc.RpcError:
            print('connecting to virt_agentd failed')
        assert pb.LIBVIRT_ERR_OK == res.code

    VACliClient(func, args)


def VACliSnapshotDelete(args):
    def func(stub, args):
        finished = False
        request = pb.SnapshotDeleteReq(dom_uuid=args.domain, names=args.snapshot_names, no_need_notify=True)
        try:
            res = stub.DeleteSnapshot(request, timeout=10)
            job_id = res.job_id
            while not finished:
                res = stub.QueryJob(pb.QueryJobReq(job_id=job_id), timeout=10)
                if res.code != pb.LIBVIRT_ERR_OK:
                    # retry after 1s
                    time.sleep(1)
                    continue
                if res.status == pb.JOBSTATUS_FINISHED_SUCCESSFULLY and res.process == 100:
                    print("snapshot delete successfully")
                    finished = True
                if res.status == pb.JOBSTATUS_FINISHED_FAILED:
                    print("snapshot delete failed")
                    finished = True
                time.sleep(1)
            res = stub.DeleteJob(pb.DeleteJobReq(job_id=job_id), timeout=10)
            if res.code != pb.LIBVIRT_ERR_OK:
                print('failed to delete job')
        except grpc.RpcError:
            print('connecting to virt_agentd failed')
        assert pb.LIBVIRT_ERR_OK == res.code

    VACliClient(func, args)


def VACliSnapshotList(args):
    def func(stub, args):
        domlist = []
        if args.domain is not None:
            domlist.append(args.domain)
        request = pb.SnapshotListReq(dom_uuid=domlist)
        try:
            res = stub.ListSnapshot(request, timeout=10)
        except grpc.RpcError:
            print('connecting to virt_agentd failed')
        assert pb.LIBVIRT_ERR_OK == res.code
        tb = prettytable.PrettyTable()
        for info in res.snapshot_info:
            snap_info = json.loads(info)
            tb.field_names = ['domain uuid', 'snapshot name', 'state', 'parent', 'creation time', 'current']
            for snap_detail in snap_info['snap_info']:
                tb.add_row([snap_info['domain_uuid'], snap_detail['name'], snap_detail['state'],
                            snap_detail['parent'], time.ctime(int(snap_detail['create_time'])),
                            '*' if int(snap_detail['current']) else ''])
        print(tb)

    VACliClient(func, args)


def VACliSnapshotRevert(args):
    def func(stub, args):
        request = pb.SnapshotRevertReq(dom_uuid=args.domain, name=args.snapshot_name)
        try:
            res = stub.RevertSnapshot(request, timeout=10)
        except grpc.RpcError:
            print('connecting to virt_agentd failed')
        assert pb.LIBVIRT_ERR_OK == res.code
        print('revert successfully')

    VACliClient(func, args)


def VACliDomainStart(args):
    def func(stub, args):
        finished = False
        request = pb.DomainStartReq(uuid=args.domain, no_need_notify=True)
        try:
            res = stub.StartDomain(request, timeout=10)
            job_id = res.job_id
            while not finished:
                res = stub.QueryJob(pb.QueryJobReq(job_id=job_id), timeout=10)
                if res.code != pb.LIBVIRT_ERR_OK:
                    # retry after 1s
                    time.sleep(1)
                    continue
                if res.status == pb.JOBSTATUS_FINISHED_SUCCESSFULLY and res.process == 100:
                    print("domain start successfully")
                    finished = True
                if res.status == pb.JOBSTATUS_FINISHED_FAILED:
                    print("domain start failed")
                    finished = True
                time.sleep(1)
            res = stub.DeleteJob(pb.DeleteJobReq(job_id=job_id), timeout=10)
            if res.code != pb.LIBVIRT_ERR_OK:
                print('failed to delete job')
        except grpc.RpcError:
            print('connecting to virt_agentd failed')
        assert pb.LIBVIRT_ERR_OK == res.code

    VACliClient(func, args)


def VACliDomainStop(args):
    def func(stub, args):
        finished = False
        request = pb.DomainStopReq(uuid=args.domain, force=True, no_need_notify=True)
        res = None
        try:
            res = stub.StopDomain(request, timeout=10)
            job_id = res.job_id
            while not finished:
                res = stub.QueryJob(pb.QueryJobReq(job_id=job_id), timeout=10)
                if res.code != pb.LIBVIRT_ERR_OK:
                    # retry after 1s
                    time.sleep(1)
                    continue
                if res.status == pb.JOBSTATUS_FINISHED_SUCCESSFULLY and res.process == 100:
                    print("domain stop successfully")
                    finished = True
                if res.status == pb.JOBSTATUS_FINISHED_FAILED:
                    print("domain stop failed")
                    finished = True
                time.sleep(1)
            res = stub.DeleteJob(pb.DeleteJobReq(job_id=job_id), timeout=10)
            if res.code != pb.LIBVIRT_ERR_OK:
                print('failed to delete job')
        except grpc.RpcError:
            print('connecting to virt_agentd failed')
        assert pb.LIBVIRT_ERR_OK == res.code

    VACliClient(func, args)


def VACliDomainMigrate(args):
    def func(stub, args):
        finished = False
        request = pb.DomainMigrateReq(
            postcopy=args.postcopy,
            destination=args.destination,
            destination_json=args.destination_json,
            time_out=args.time_out,
            uuid=args.domain, no_need_notify=True)
        res = None
        try:
            res = stub.MigrateDomain(request, timeout=10)
            job_id = res.job_id
            while not finished:
                res = stub.QueryJob(pb.QueryJobReq(job_id=job_id), timeout=10)
                if res.code != pb.LIBVIRT_ERR_OK:
                    # retry after 1s
                    time.sleep(1)
                    continue
                if res.status == pb.JOBSTATUS_FINISHED_SUCCESSFULLY and res.process == 100:
                    print("domain migrate successfully")
                    finished = True
                if res.status == pb.JOBSTATUS_FINISHED_FAILED:
                    print("domain migrate failed")
                    finished = True
                time.sleep(1)
            res = stub.DeleteJob(pb.DeleteJobReq(job_id=job_id), timeout=10)
            if res.code != pb.LIBVIRT_ERR_OK:
                print('failed to delete job')
        except libvirt.libvirtError as e:
            print('libvirt error: %s' % e)
        except grpc.RpcError:
            print('connecting to virt_agentd failed')
        assert pb.LIBVIRT_ERR_OK == res.code

    VACliClient(func, args)


def main_cli():
    operation_list = {
        'snapshot-create': VACliSnapshotCreate,
        'snapshot-delete': VACliSnapshotDelete,
        'snapshot-list': VACliSnapshotList,
        'snapshot-revert': VACliSnapshotRevert,
        'domain-start': VACliDomainStart,
        'domain-stop': VACliDomainStop,
        'migrate': VACliDomainMigrate
    }
    parser = argparse.ArgumentParser()
    parser.add_argument('operation', type=str, choices=operation_list.keys(), help='operation on domain')
    parser.add_argument('-d', '--domain', type=str, help='domain name')
    parser.add_argument('--snapshot_name', type=str, help='snapshot name')
    parser.add_argument('--snapshot_names', type=str, nargs='+', help='snapshot names')
    parser.add_argument('--snapshot_type', type=str, choices=['live', 'diskonly'],
                        default='live', help='snapshot type, default: live')
    parser.add_argument('--destination', type=str, help='destination ip for migration')
    parser.add_argument('--destination_json', type=str, help='destination json migration')
    parser.add_argument('--postcopy', type=bool, help='postcopy or not')
    parser.add_argument('--time_out', type=int, help='time out')
    # parser.add_argument('-')
    args = parser.parse_args()

    if args.operation not in operation_list:
        raise VirtAgentException('invalid operation %s' % args.operation)

    try:
        LoadConfig()
        operation_list[args.operation](args)
    except Exception as e:
        print(e)
        print(traceback.format_exc())
