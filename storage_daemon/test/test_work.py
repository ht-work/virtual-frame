#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import time
import logging

from storeagent import store_util_pb2 as util_pb2
from storeagent.worker import Worker
from storeagent.worker_job import JobType
from storeagent.store_exception import StoreJobException


logging.basicConfig(level=logging.INFO)


class TestWork(object):
    work = None

    @classmethod
    def setup_class(cls):
        cls.work = Worker()
        cls.work.run()

    @classmethod
    def teardown_clas(cls):
        pass

    def test_job_TEST(self):
        job_id = self.work.add_job(JobType.TEST, 'This is a job test')
        count = 0
        while count < 5:
            count = count + 1
            time.sleep(0.1)
            #logging.info('TEST(%s) job process: %s' % (job_id, self.work.query_job(job_id)))
        #assert self.work.query_job(job_id) == (util_pb2.JOBSTATUS_FINISHED_SUCCESSFULLY, 100)
        #self.work.del_job(job_id)
        try:
            self.work.query_job(job_id)
        except StoreJobException as e:
            assert e.err_code == util_pb2.STORE_NOT_FOUND
