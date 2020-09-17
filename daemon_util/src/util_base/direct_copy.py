#!/usr/bin/python3
# -*- coding: utf-8 -*-
import os
import sys
import re
import argparse
import directio
import logging

from util_base.exception import DirectcopyException


def get_bytes(size_string):
    try:
        size_string = size_string.lower().replace(',', '')
        if size_string.isdigit():
            return int(size_string)

        if size_string[-1] != 'b':
            size_string = size_string + 'b'

        size = re.search(r'^(\d+)[a-z]i?b$', size_string).groups()[0]
        suffix = re.search(r'^\d+([kmgtp])i?b$', size_string).groups()[0]
        shft = suffix.translate(str.maketrans('kmgtp', '12345')) + '0'
    except AttributeError:
        raise DirectcopyException('Invalid Input')
    except Exception:
        raise DirectcopyException('Translate Bytes')

    return int(size) << int(shft)


def copy(src, dst, bs, is_verbose):
    if bs % 512 != 0:
        raise DirectcopyException('bs(%d) must be a multiple of a 512' % bs)

    if not os.path.isfile(src):
        raise DirectcopyException('%s: No such file' % src)
    src_file = src

    if os.path.isdir(dst):
        dst_dir = dst
        dst_file_name = os.path.basename(src)
    else:
        if os.path.islink(dst):
            raise DirectcopyException('%s is link to %s' % (dst, os.path.realpath(dst)))
        dst_dir = os.path.dirname(dst)
        if not dst_dir:
            dst_dir = '.'
        dst_file_name = os.path.basename(dst)

    if not os.path.exists(dst_dir):
        raise DirectcopyException('%s: No such directory' % dst_dir)
    dst_file = os.path.join(dst_dir, dst_file_name)

    if os.path.abspath(src_file) == os.path.abspath(dst_file):
        raise DirectcopyException("'%s' and '%s' are the same file" % (src_file, dst_file))

    src_file_size = os.path.getsize(src_file)

    if is_verbose is True:
        logging.info('Source file: %s(%d bytes)' % (src_file, src_file_size))
        logging.info('Destination file: %s' % dst_file)

    count = src_file_size // bs
    last_size = src_file_size % bs
    if is_verbose is True:
        logging.info('Calculate %s -> bs:%d, count:%d, last_size:%d' %
                     (src_file, bs, count, last_size))

    if os.path.isfile(dst_file):
        if is_verbose is True:
            logging.info("Remove regular file '%s'" % dst_file)
        os.remove(dst_file)

    try:
        if is_verbose is True:
            logging.info("Create file '%s'" % dst_file)
        src_fd = os.open(src_file, os.O_RDONLY | os.O_DIRECT)
        dst_fd = os.open(dst_file, os.O_WRONLY | os.O_DIRECT | os.O_CREAT)
        for i in range(0, count):
            data = directio.read(src_fd, bs)
            directio.write(dst_fd, data)
    except Exception as e:
        raise DirectcopyException('directio %s' % e)
    finally:
        os.close(src_fd)
        os.close(dst_fd)

    try:
        with open(src_file, 'rb') as src_fo, open(dst_file, 'ab+') as dst_fo:
            src_fo.seek(count*bs, 0)
            dst_fo.seek(0, 2)
            data = src_fo.read(last_size)
            dst_fo.write(data)
    except Exception as e:
        raise DirectcopyException('file io %s' % e)

    try:
        src_file_mode = oct(os.stat(src_file).st_mode)[-3:]
        if is_verbose is True:
            logging.info("Chmod '%s' '%s'" % (src_file_mode, dst_file))
        os.chmod(dst_file, int(src_file_mode, 8))
    except Exception as e:
        raise DirectcopyException('file mode %s' % e)


def main():
    logging.basicConfig(level=logging.INFO, format='%(levelname)s %(message)s')
    usage = '''direct-copy [-h] [-s SRC] [-d DST] [-b BS] [-v]'''
    epilog = '''example:
  direct-copy <src> <dst>
  direct-copy <src> <dst> <bs>
  direct-copy --src <src> --dst <dst> --bs <bs> --verbose'''

    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter,
                                     usage=usage,
                                     epilog=epilog)

    parser.add_argument('-s', '--src', type=str, help='read from FILE')
    parser.add_argument('-d', '--dst', type=str, help='write to FILE')
    parser.add_argument('-b', '--bs', type=str, help='convert BYTES bytes at a time')
    parser.add_argument('-v', '--verbose', action='store_true', help='explain what is being done')

    parser.add_argument('srcfile', type=str, nargs='?', help='same to [-s SRC] but without key')
    parser.add_argument('dstfile', type=str, nargs='?', help='same to [-d DST] but without key')
    parser.add_argument('bsval', type=str, nargs='?', default='512', help='same to [-b BS] but without key')

    args = parser.parse_args()

    try:
        if args.srcfile:
            src_file = args.srcfile
        if args.dstfile:
            dst_file = args.dstfile
        if args.bsval:
            bs_bytes = get_bytes(args.bsval)

        verbose = False
        if args.src:
            src_file = args.src
        if args.dst:
            dst_file = args.dst
        if args.bs:
            bs_bytes = get_bytes(args.bs)
        if args.verbose:
            verbose = True

        if src_file and dst_file and bs_bytes:
            copy(src_file, dst_file, bs_bytes, verbose)
            sys.exit(0)
        else:
            logging.error('Invalid Input')
            sys.exit(1)
    except UnboundLocalError:
        logging.error('Invalid Input')
        sys.exit(1)
    except DirectcopyException as e:
        logging.error('%s' % e.err_msg)
        sys.exit(1)
    except Exception as e:
        logging.error('%s' % e)
        sys.exit(1)


if __name__ == '__main__':
    main()
