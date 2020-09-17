#!/usr/bin/python3
# -*- coding: utf-8 -*-
# used by server
import logging
import traceback
import sys

from . import exception
from . import ncpapi as api


def Server(server_ip, server_port):
    logging.debug("server %s:%s", server_ip, server_port)

    remote_target = None
    local_target = None
    ret = 0

    try:
        remote_target, local_target = api.GetServerTarget(server_ip, server_port)
        api.ServerRun(remote_target, local_target)

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
