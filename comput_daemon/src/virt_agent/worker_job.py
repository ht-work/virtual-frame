#!/usr/bin/env python
# encoding: utf-8

import uuid
import logging
import time
import traceback
import threading
import enum

from . import libvirt_driver
from . import virt_agent_pb2 as pb

LIBVIRT_EVENT_CONNECTING = False
LIBVIRT_EVENT_CONNECTING_LOCK = threading.Lock()


def _do_test(opaque, job=None):
    logging.info('test job')
    logging.info(opaque)
    time.sleep(10)
    logging.info('done')


def LibvirtEventConnCloseHandler(param, job=None):
    global LIBVIRT_EVENT_CONNECTING
    global LIBVIRT_EVENT_CONNECTING_LOCK

    try:
        logging.debug('enter')
        assert ('conn' in param)
        assert ('libvirt_event' in param)
        libvirt_event = param['libvirt_event']
        assert isinstance(libvirt_event, libvirt_driver.LibvirtEvent)
        if not libvirt_event.check_conn(param['conn']):
            logging.debug('not libvirt event conn')
            return

        with LIBVIRT_EVENT_CONNECTING_LOCK:
            if LIBVIRT_EVENT_CONNECTING:
                logging.info('connecting, exit')
                return

            LIBVIRT_EVENT_CONNECTING = True

        cnt = 0

        libvirt_event.disable()

        while (not libvirt_event.isEnabled()):
            libvirt_event.enable()
            cnt += 1
            time.sleep(1)

        logging.info('libvirt_event get new connection(retry %d)' % (cnt))
        with LIBVIRT_EVENT_CONNECTING_LOCK:
            LIBVIRT_EVENT_CONNECTING = False
    except Exception as e:
        logging.error(traceback.format_exc())
        logging.error(e)


def LibvirtDomainEventHandler(opaque, job=None):
    # vm booted set acl and qos
    logging.info(opaque)


def LibvirtDomainSnapshotCreateHandler(opaque, job=None):
    logging.debug(opaque)
    libvirt_driver.DomainSnapshotCreate(opaque, job)


def LibvirtDomainSnapshotDeleteHandler(opaque, job=None):
    logging.debug(opaque)
    libvirt_driver.DomainSnapshotDelete(opaque, job)


def LibvirtDomainStartHandler(opaque, job=None):
    logging.debug(opaque)
    libvirt_driver.DomainStart(opaque, job)


def LibvirtDomainStopHandler(opaque, job=None):
    logging.debug(opaque)
    libvirt_driver.DomainStop(opaque, job)


def LibvirtDomainMigrateHandler(opaque, job=None):
    logging.debug(opaque)
    libvirt_driver.DomainMigrate(opaque, job)


def LibvirtDomainMigrateMonitorHandler(opaque, job=None):
    logging.debug(opaque)
    libvirt_driver.DomainMigrateMonitor(opaque, job)


def LibvirtFinishMigrationHandler(opaque, job=None):
    logging.debug(opaque)
    libvirt_driver.FinishMigration(opaque, job)


@enum.unique
class JobType(enum.Enum):
    TEST = {'func': _do_test}
    LIBVIRT_EVENT_CONN_CLOSED = {'func': LibvirtEventConnCloseHandler}
    LIBVIRT_DOMAIN_EVENT = {'func': LibvirtDomainEventHandler}
    LIBVIRT_SNAPSHOT_CREATE = {'func': LibvirtDomainSnapshotCreateHandler}
    LIBVIRT_SNAPSHOT_DELETE = {'func': LibvirtDomainSnapshotDeleteHandler}
    LIBVIRT_DOMAIN_START = {'func': LibvirtDomainStartHandler}
    LIBVIRT_DOMAIN_STOP = {'func': LibvirtDomainStopHandler}
    LIBVIRT_DOMAIN_MIGRATE = {'func': LibvirtDomainMigrateHandler}
    LIBVIRT_DOMAIN_MIGRATE_MONITOR = {'func': LibvirtDomainMigrateMonitorHandler}
    LIBVIRT_FINISH_MIGRATION = {'func': LibvirtFinishMigrationHandler}


# internal job no need to cache it
_NO_CACHE_LIST = [
    JobType.TEST,
    JobType.LIBVIRT_EVENT_CONN_CLOSED,
    JobType.LIBVIRT_DOMAIN_EVENT,
    JobType.LIBVIRT_DOMAIN_MIGRATE_MONITOR]


# job definition #
class Jobs(object):
    def __init__(self, job_type, opaque=None, need_notify=False):
        assert isinstance(job_type, JobType)

        self.__type = job_type
        self.__opaque = opaque

        # __job_id is a readonly variable
        self.__job_id = str(uuid.uuid4())

        # job_status, err_code, process must be protected by this lock
        self.__lock = threading.Lock()
        self.__job_status = pb.JOBSTATUS_CREATED
        self.__err_code = 0
        self.__process = 0

        # __need_notify is a readonly variable
        self.__need_notify = need_notify

        # __need_cache is a readonly variable
        self.__need_cache = False if (job_type in _NO_CACHE_LIST) else True

    def run(self):
        logging.debug(self.__type)
        self.set_job_status(pb.JOBSTATUS_PROCESSING)
        return self.__type.value['func'](self.__opaque, self)

    @property
    def job_id(self):
        return self.__job_id

    @property
    def need_notify(self):
        return self.__need_notify

    @property
    def need_cache(self):
        return self.__need_cache

    def set_job_status(self, status):
        with self.__lock:
            self.__job_status = status

    def get_job_status(self):
        with self.__lock:
            return self.__job_status

    def set_err_code(self, err_code):
        with self.__lock:
            self.__err_code = err_code

    def get_err_code(self):
        with self.__lock:
            return self.__err_code

    def set_process(self, process):
        with self.__lock:
            self.__process = process

    def get_process(self):
        with self.__lock:
            return self.__process
