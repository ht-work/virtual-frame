#!/usr/bin/env python
# encoding: utf-8

import pytest
import time
from util_base.sys_util import cat, echo
from util_base.sys_util import check_passwd
import traceback

def _genrandstr(size = 10):
    import string
    import random

    return ''.join(random.choices(string.ascii_letters + string.digits, k = size))

class TestCase:
    def test_file_op(self):
        import tempfile
        import os

        (lvl, tmp) = tempfile.mkstemp(prefix=__name__, text=True)

        randstr = _genrandstr(120)
        echo(tmp, randstr)
        c = cat(tmp)
        print(randstr)
        print(c)
        if c.strip() == randstr:
            print("ok")
            assert 1
        else:
            print("not match")
            assert 0

        if os.path.isfile(tmp):
            os.remove(tmp)

    def test_check_password(self):
        result_dict = {
            '1q2w3e' : True,
            '1q2w3e4r' : False,
            '1q2w@3e4r' : False,
            'qwe@123' : False,
            'asuifdasif' : False,
            '' : False,
            None : False,
            11024 : False,
        }
        for k in result_dict:
            if result_dict[k] != check_passwd(user='root', pwd=k):
                assert 0

        assert check_passwd(user='rootabc', pwd='') is False

        assert 1
