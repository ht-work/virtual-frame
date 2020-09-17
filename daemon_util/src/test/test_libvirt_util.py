#!/usr/bin/env python
# encoding: utf-8

import pytest
from util_base import libvirt_util
import threading
import concurrent
from concurrent import futures
from concurrent.futures import ThreadPoolExecutor, wait, ALL_COMPLETED, FIRST_COMPLETED
import time
import traceback

__running = 1

def _libvirt_util_do_test(connectpool, index):
    import random
    global __running

    while __running:
        conn = None
        try:
            conn = connectpool.get()
            if conn:
                print(conn.getVersion())

        except libvirt.libvirtError as e:
            print("%s"%(e.get_error_message()))
            assert 0
        finally:
            if conn:
                connectpool.put(conn)

        time.sleep(random.randint(5, 10))

def _libvirt_util_timer_handler():
    global __running
    print("time up")
    __running = 0

def _genrandstr(size = 10):
    import string
    import random

    return ''.join(random.choices(string.ascii_letters + string.digits, k = size))

class TestCase:
    def test_libvirt_util(self):
        try:
            cp = libvirt_util.ConnectionPool()

            timer = threading.Timer(30, _libvirt_util_timer_handler)
            timer.start()

            worker = 20
            executer = ThreadPoolExecutor(max_workers = worker)
            all_task = [executer.submit(_libvirt_util_do_test, cp, i) for i in range(worker)]
            wait(all_task, return_when = ALL_COMPLETED)

            print("finished")
            assert 1
        except KeyboardInterrupt:
            __running = 0
