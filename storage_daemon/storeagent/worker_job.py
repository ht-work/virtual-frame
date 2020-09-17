#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import uuid
import enum
import time
import threading

from storeagent import store_util_pb2 as util_pb2
from storeagent import store_driver as driver


def _do_test(opaque, job=None):
    logging.info('test job')
    logging.info(opaque)
    time.sleep(0.1)
    logging.info('done')


def CreateFullVolHandler(opaque, job=None):
    logging.info(opaque)
    driver.QemuCreateFullVol(opaque, job)


@enum.unique
class JobType(enum.Enum):
    TEST = {'func': _do_test}
    CREATE_FULL_VOL = {'func': CreateFullVolHandler}


# internal job no need to cache it
_NO_CACHE_LIST = [
    JobType.TEST]


# job definition
class Jobs(object):
    def __init__(self, job_type, opaque=None, need_notify=False):
        assert isinstance(job_type, JobType)

        self.__type = job_type
        self.__opaque = opaque

        # _job_id is readonly variable
        self.__job_id = str(uuid.uuid4())

        # job_status, err_code, process must be protected by this lock
        self.__lock = threading.Lock()
        self.__job_status = util_pb2.JOBSTATUS_CREATED
        self.__err_code = 0
        self.__process = 0

        # __need_notify is a readonly variable
        self.__need_notify = need_notify

        # __need_cache is a readonly variable
        self.__need_cache = False if (job_type in _NO_CACHE_LIST) else True

    def run(self):
        logging.debug(self.__type)
        self.set_job_status(util_pb2.JOBSTATUS_PROCESSING)
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
