#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import queue
import traceback
import threading
import json

from concurrent.futures import ThreadPoolExecutor
from storeagent import worker_job
from storeagent import store_util_pb2 as util_pb2
from storeagent.store_exception import StoreJobException
from storeagent import worker_notify


class Worker(object):
    def __init__(self, size=5):
        self.__size = size
        self.__main_thread = None
        self.__cond = threading.Condition()
        self.__job_q = queue.Queue()

        # for job query and delete
        self.__job_cache_lock = threading.Lock()
        self.__job_cache = {}

        self.__worker_notify = None

    def __worker(self):
        while True:
            job = self.__job_q.get()
            err_code = 0
            try:
                job.run()
                job.set_job_status(util_pb2.JOBSTATUS_FINISHED_SUCCESSFULLY)
                job.set_process(100)
            except StoreJobException as e:
                job.set_job_status(util_pb2.JOBSTATUS_FINISHED_FAILED)
                logging.critical(traceback.format_exc())
                logging.critical(e)
                err_code = e.err_code
            except Exception as e:
                job.set_job_status(util_pb2.JOBSTATUS_FINISHED_FAILED)
                logging.critical(traceback.format_exc())
                logging.critical(e)
                err_code = util_pb2.STORE_INVALID_ERROR
            finally:
                # job notify
                if job.need_notify:
                    logging.debug('job(%s) notify now, err code %d' %
                                  (job.job_id, err_code))
                    # no lock here. Though requests if not thread-safety, RestfulNotifier is thread-safety.
                    # In __init__, it just save uri , no any session information.
                    # In Notify, it provide a full evoke of an http post, so it support concurrent evoking.
                    # If there is a new implement of Notifier, it must provide thread-safety 'Notify'.
                    if self.__worker_notify:
                        notify_data = {}
                        notify_data['job_id'] = job.job_id
                        notify_data['status'] = job.get_job_status()
                        notify_data['process'] = job.get_process()
                        notify_data['err_code'] = err_code
                        self.__worker_notify.Notify(str(json.dumps(notify_data)))

    def __create_thread_pool(self):
        with ThreadPoolExecutor(max_workers=self.__size) as executor:
            for i in range(self.__size):
                executor.submit(self.__worker)

    def run(self):
        self.__main_thread = threading.Thread(target=self.__create_thread_pool,
                                              name='worker pool main thread',
                                              daemon=True)
        self.__main_thread.start()

    def init_notifier(self):
        # TODO, demo now
        self.__worker_notify = worker_notify.RestfulNotifier('http://localhost:8080/test/api/notify')

    def add_job(self, jobs, opaque=None, need_notify=False):
        assert isinstance(jobs, worker_job.JobType)

        logging.debug(self.__job_q.qsize())
        job = worker_job.Jobs(jobs, opaque, need_notify)
        if job.need_cache:
            with self.__job_cache_lock:
                if job.job_id in self.__job_cache.keys():
                    logging.error('invalid job_id %s' % (job.job_id))
                self.__job_cache[job.job_id] = job
                logging.info('job_id %s current cache size %d' %
                             (job.job_id, len(self.__job_cache)))
        self.__job_q.put(job)
        job.set_job_status(util_pb2.JOBSTATUS_SUBMITTED)
        return job.job_id

    def del_job(self, job_id):
        with self.__job_cache_lock:
            logging.info('job_id %s current cache size %d' %
                         (job_id, len(self.__job_cache)))
            if job_id in self.__job_cache.keys():
                self.__job_cache.pop(job_id)
            else:
                err_msg = ('failed to find job(%s) in job cache' % job_id)
                logging.error(err_msg)
                raise StoreJobException(err_msg, err_code=util_pb2.STORE_NOT_FOUND)

    def query_job(self, job_id):
        with self.__job_cache_lock:
            logging.info('job_id %s current cache size %d' %
                         (job_id, len(self.__job_cache)))
            if job_id in self.__job_cache.keys():
                job = self.__job_cache[job_id]
                return (job.get_job_status(), job.get_process())
            else:
                err_msg = ('failed to find job(%s) in job cache' % job_id)
                logging.error(err_msg)
                raise StoreJobException(err_msg, err_code=util_pb2.STORE_NOT_FOUND)
