import sys
import time
import logging

sys.path.insert(0, '..')
from sysagent import util_pb2 as u_pb2
from sysagent.worker import Worker
from sysagent.worker_job import JobType


logging.basicConfig(level=logging.INFO)


class TestWork(object):
    work = None

    @classmethod
    def setup_class(cls):
        cls.work = Worker()

    @classmethod
    def teardown_class(cls):
        pass

    def test_job_TEST(self):
        job_id = self.work.add_job(JobType.TEST, 'This is a job test')
        count = 0
        while count < 5:
            count = count + 1
            time.sleep(0.1)
            logging.info('TEST(%s) job process: %s' % (job_id, self.work.query_job(job_id)))
        assert self.work.query_job(job_id) == (u_pb2.JOBSTATUS_SUBMITTED, 0)
        self.work.del_job(job_id)
        try:
            self.work.query_job(job_id)
        except Exception as e:
            assert e.err_code == u_pb2.SYS_NOTFOUND
