import sys
import logging
sys.path.insert(0, '..')
import sysagent.util_pb2
import sysagent.exception


logging.basicConfig(level=logging.DEBUG)


class TestException(object):
    def test_SysagentException(self):
        err_code = sysagent.util_pb2.SYS_FAIL
        err_msg = None
        exp = sysagent.exception.SysagentException()

        logging.info('exp.err_code :%d' % exp.err_code)
        assert exp.err_code == err_code
        logging.info('exp.err_msg :%s' % exp.err_msg)
        assert exp.err_msg == err_msg
