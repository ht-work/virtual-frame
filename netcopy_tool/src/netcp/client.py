#!/usr/bin/python3
# -*- coding: utf-8 -*-
import logging
import traceback
import sys

from . import exception
from . import ncpapi as api


def Client(server_ip, server_port, operation, local_file, remote_file):
    logging.debug("server %s:%s local file %s remote file %s operation %s",
                  server_ip, server_port, local_file, remote_file, operation)

    remote_target = None
    local_target = None
    ret = 0

    try:
        remote_target, local_target = api.GetClientTarget(server_ip, server_port, operation,
                                                          local_file, remote_file)
        api.ClientRun(remote_target, local_target)

    except exception.NetCopyEOF as e:
        logging.info(e)
        logging.info('finished')
    except exception.NetCopyError as e:
        logging.error(e)
        logging.error('interrupted')
        logging.error(traceback.format_exc())
        ret = -1
    except Exception:
        logging.error(traceback.format_exc())
        ret = -2
    finally:
        api.PutTarget(remote_target, local_target)
        sys.exit(ret)
