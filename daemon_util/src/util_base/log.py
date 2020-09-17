#!/usr/bin/env python
# encoding: utf-8

import logging
import logging.handlers


def Loginit(filepath=None, loglevel='debug'):
    levels = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL
    }
    if not isinstance(loglevel, str):
        raise TypeError("loglevel need string")

    llvl = loglevel.upper()
    if llvl not in levels:
        raise Exception("invalid log level: %s" % (loglevel))

    log_handler = logging.handlers.WatchedFileHandler(filename=filepath,
                                                      mode='a',
                                                      encoding='utf-8',
                                                      delay=False)

    fmt = logging.Formatter('%(asctime)s %(filename)s(%(funcName)s)[line:%(lineno)d][pid: %(process)d]'
                            '[tid: %(thread)d] %(levelname)s: %(message)s')
    log_handler.setFormatter(fmt)
    logger = logging.getLogger()
    logger.addHandler(log_handler)
    logger.setLevel(levels[loglevel.upper()])


def __test_func(lvl):
    Loginit("test.log", lvl)

    logging.debug("debug message for %s" % lvl)
    logging.info("info message for %s" % lvl)
    logging.warn("warning message for %s" % lvl)
    logging.error("error message for %s" % lvl)


def __test():
    __test_func("INFO")


if __name__ == "__main__":
    __test()
