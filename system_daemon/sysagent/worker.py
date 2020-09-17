#!/usr/bin/env python
# encoding: utf-8
import threading
from concurrent.futures import ThreadPoolExecutor
import logging
import queue
import json
import traceback

from sysagent import worker_job
from sysagent import exception as exp
from sysagent import util_pb2 as u_pb2
from sysagent import worker_notify


worker_threading = None


def StartWork():
    global worker_threading
    try:
        if not worker_threading:
            worker_threading = Worker()
            worker_threading.add_job(worker_job.JobType.HOSTCPUPERCENT)
            worker_threading.init_notifier()
            worker_threading.run()
    except Exception as e:
        logging.error(e)
        logging.error(traceback.format_exc())


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
                job.set_job_status(u_pb2.JOBSTATUS_FINISHED_SUCCESSFULLY)
                job.set_process(100)
            except Exception as e:
                job.set_job_status(u_pb2.JOBSTATUS_FINISHED_FAILED)
                logging.error(e)
                logging.error(traceback.format_exc())
                err_code = u_pb2.SYS_FAIL
            finally:
                # job notify
                if job.need_notify:
                    logging.debug('job(%s) notify now, error code %d' % (job.job_id, err_code))
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
        self.__worker_notify = worker_notify.RestfulNotifier('http://localhost:8086/test/api/notify')

    def add_job(self, job, opaque=None, need_notify=False):
        assert isinstance(job, worker_job.JobType)

        logging.debug(self.__job_q.qsize())
        job = worker_job.Jobs(job, opaque, need_notify)
        if job.need_cache:
            with self.__job_cache_lock:
                if job.job_id in self.__job_cache.keys():
                    logging.error("invalid job_id %s" % (job.job_id))
                self.__job_cache[job.job_id] = job
                logging.info("job_id %s current cache size %d" % (job.job_id, len(self.__job_cache)))
        self.__job_q.put(job)
        job.set_job_status(u_pb2.JOBSTATUS_SUBMITTED)
        return job.job_id

    def del_job(self, job_id):
        with self.__job_cache_lock:
            logging.info("job_id %s current cache size %d" % (job_id, len(self.__job_cache)))
            if job_id in self.__job_cache.keys():
                self.__job_cache.pop(job_id)
            else:
                err_msg = 'failed to find job(%s) in job cache' % (job_id)
                logging.error(err_msg)
                raise exp.SysagentJobException(err_msg=err_msg, err_code=u_pb2.SYS_NOTFOUND)

    def query_job(self, job_id):
        with self.__job_cache_lock:
            logging.info("job_id %s current cache size %d" % (job_id, len(self.__job_cache)))
            if job_id in self.__job_cache.keys():
                job = self.__job_cache[job_id]
                return (job.get_job_status(), job.get_process())
            else:
                err_msg = 'failed to find job(%s) in job cache' % (job_id)
                logging.error(err_msg)
                raise exp.SysagentJobException(err_msg=err_msg, err_code=u_pb2.SYS_NOTFOUND)

    def is_own_jobs(self):
        with self.__job_cache_lock:
            return True if (len(self.__job_cache) != 0) else False
