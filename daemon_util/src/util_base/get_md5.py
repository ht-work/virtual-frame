#!/usr/bin/env python
# encoding: utf-8

import os
import logging
import hashlib
import argparse
import directio

from util_base.exception import Md5Exception
_BLOCK_SIZE = 1024 * 1024     # 1M


def GetFileMd5(filepath):
    if filepath is None:
        err_msg = 'invalid input'
        raise Md5Exception(err_msg=err_msg, err_code=-1)

    path = os.path.abspath(filepath)
    if not os.path.exists(path):
        err_msg = '%s: No such file or directory' % path
        raise Md5Exception(err_msg=err_msg, err_code=-2)

    logging.info("start to cal file mad5. name: %s." % (path))
    md5_str = None

    try:
        filesize = os.path.getsize(path)
        fd = os.open(path, os.O_RDONLY | os.O_DIRECT)
        offset = 0
        md5 = hashlib.md5()
        global _BLOCK_SIZE
        while offset + _BLOCK_SIZE <= filesize:
            data = directio.read(fd, _BLOCK_SIZE)
            md5.update(data)
            offset += _BLOCK_SIZE
    except Exception as e:
        err_msg = 'directio error. %s' % e
        raise Md5Exception(err_msg=err_msg, err_code=-3)
    finally:
        os.close(fd)

    if offset == filesize:
        logging.info("finish to cal file mad5. name: %s md5: %s" % (path, md5.hexdigest().strip()))
        return md5.hexdigest().strip()

    try:
        with open(path, "rb") as fd:
            fd.seek(offset)
            data = fd.read(_BLOCK_SIZE)
            md5.update(data)
            md5_str = md5.hexdigest().strip()
            logging.info("finish to cal file mad5. name: %s md5: %s" % (path, md5_str))
            return md5_str
    except Exception as e:
        err_msg = 'file read error. %s' % e
        raise Md5Exception(err_msg=err_msg, err_code=-4)


def main():
    '''
    Return: 0: success
            -1: invalid input
            -2: file not exit
            -3: directio error
            -4: file read error
            -5: unknown errors
    '''
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--path', type=str, help='file path to be calculated')
    args = parser.parse_args()

    try:
        md5 = GetFileMd5(args.path)
        print(md5)
        return 0
    except Md5Exception as e:
        print(e.err_msg)
        return e.err_code
    except Exception as e:
        logging.error('%s' % e)
        print('calculate file md5 failed.')
        return -5


if __name__ == '__main__':
    main()
