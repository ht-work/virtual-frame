#!/usr/bin/env python
# encoding: utf-8

import libvirt
from . import log
import logging
import threading
import concurrent
import time

CONNECTIONPOOL_MIN_SIZE = 2
CONNECTIONPOOL_MAX_SIZE = 5
CONNECTIONPOOL_KEEP_ALIVE_INTERVAL = 10
CONNECTIONPOOL_KEEP_ALIVE_COUNT = 5

eventLoopThread = None


class Description(object):
    __slots__ = ('desc', 'args')

    def __init__(self, *args, **kwargs):
        self.desc = kwargs.get('desc')
        self.args = args

    def __str__(self):  # type: () -> str
        return self.desc

    def __getitem__(self, item):  # type: (int) -> str
        try:
            data = self.args[item]
        except IndexError:
            return self.__class__(desc=str(item))

        if isinstance(data, str):
            return self.__class__(desc=data)
        elif isinstance(data, (list, tuple)):
            desc, args = data
            return self.__class__(*args, desc=desc)

        raise TypeError(args)


def _virEventLoopAIORun(loop):
    import asyncio
    asyncio.set_event_loop(loop)
    loop.run_forever()


def _virEventLoopNativeRun():
    while True:
        libvirt.virEventRunDefaultImpl()


def _virEventLoopAIOStart():
    global eventLoopThread
    import libvirtaio
    import asyncio
    loop = asyncio.new_event_loop()
    libvirtaio.virEventRegisterAsyncIOImpl(loop=loop)
    eventLoopThread = threading.Thread(target=_virEventLoopAIORun, args=(loop,), name="libvirtEventLoop")
    eventLoopThread.setDaemon(True)
    eventLoopThread.start()


def _virEventLoopNativeStart():
    global eventLoopThread
    libvirt.virEventRegisterDefaultImpl()
    eventLoopThread = threading.Thread(target=_virEventLoopNativeRun, name="libvirtEventLoop")
    eventLoopThread.setDaemon(True)
    eventLoopThread.start()


def _start_event_loop(enable_async=0):
    if enable_async:
        _virEventLoopAIOStart()
    else:
        _virEventLoopNativeStart()


class ConnectionPool(object):
    def __init__(self, minsize=CONNECTIONPOOL_MIN_SIZE,
                 maxsize=CONNECTIONPOOL_MAX_SIZE, url="qemu:///system",
                 close_cb=None):

        self.__minsize = minsize
        self.__maxsize = maxsize
        self.__url = url
        self.__conn_free_list = []
        self.__conn_free_lock = threading.Lock()
        self.__close_cb = close_cb

        _start_event_loop(1)

    def __get_new_connect(self):
        return libvirt.open(self.__url)

    def __size(self):
        with self.__conn_free_lock:
            return len(self.__conn_free_list)

    def __conn_isalive(self, conn):
        try:
            conn.getVersion()
            return True
        except libvirt.libvirtError:
            return False

    def __ConnectionCloseCallback(self, conn, reason, opaque):
        CONNECTION_EVENTS = Description("I/O Error", "End-of-file", "Keepalive", "Client")
        logging.error("%s closed: %s" % (conn, CONNECTION_EVENTS[reason]))
        if self.__close_cb is not None:
            self.__close_cb(conn, reason, opaque)

    def get(self):
        conn = None

        if self.__size() == 0:
            try:
                conn = self.__get_new_connect()
                logging.info("create new connection %s" % (conn))
                conn.setKeepAlive(CONNECTIONPOOL_KEEP_ALIVE_INTERVAL,
                                  CONNECTIONPOOL_KEEP_ALIVE_COUNT)
                conn.registerCloseCallback(self.__ConnectionCloseCallback, None)
            except libvirt.libvirtError as e:
                logging.error("%s" % (e.get_error_message()))
        else:
            with self.__conn_free_lock:
                conn = self.__conn_free_list.pop()
            if not self.__conn_isalive(conn):
                logging.info("free %s" % (conn))
                try:
                    conn.unregisterCloseCallback()
                    conn.close()
                except libvirt.libvirtError:
                    pass
                conn = None

        logging.debug("get connection %s" % (conn))
        return conn

    def put(self, conn):
        logging.debug("put connection %s" % (conn))
        need_free = False
        if (self.__conn_isalive(conn)):
            with self.__conn_free_lock:
                logging.debug("%d" % (len(self.__conn_free_list)))
                if (len(self.__conn_free_list) < self.__maxsize):
                    logging.debug("return %s" % (conn))
                    self.__conn_free_list.append(conn)
                else:
                    need_free = True
        else:
            # free conn
            need_free = True

        if need_free:
            logging.info("free %s" % (conn))
            conn.unregisterCloseCallback()
            conn.close()

__running = 1


def __do_test(connectpool, index):
    import random
    global __running

    while __running:
        conn = None
        logging.info("loop start %d" % (index))
        try:
            conn = connectpool.get()
            if conn:
                logging.info(conn.getVersion())
                # connectpool.put(conn)

        except libvirt.libvirtError as e:
            logging.error("%s" % (e.get_error_message()))
        finally:
            if conn:
                connectpool.put(conn)

        time.sleep(random.randint(40, 50))


def __run_test():
    global __running
    try:
        cp = ConnectionPool()

        worker = 20
        with concurrent.futures.ThreadPoolExecutor(max_workers=worker) as executer:
            for i in (range(worker)):
                executer.submit(__do_test, cp, i)

    except KeyboardInterrupt:
        __running = 0


def __main():
    # log.Loginit("/var/log/vap/libvirt_conn.log")
    log.Loginit("/var/log/vap/libvirt_conn.log", "info")
    __run_test()

if __name__ == "__main__":
    __main()
