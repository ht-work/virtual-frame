#!/usr/bin/python3
# -*- coding: utf-8 -*-
import struct
from zlib import crc32


DEFAULT_CRC = 10
VERSION = 1
CRRCHECK = False

'''
packet format description:
! big endian
I = total size of this packet
4s = HEAD
5I = version + head_size + packet_type + path_size  + crc_code
%ds = path
'''
FORMAT_BASE_MSG = '!I4s5I%ds'
FORMAT_BASE_MSG_FIXED = '!I4s5I'
FORMAT_BASE_MSG_FIXED_LENGTH = struct.calcsize(FORMAT_BASE_MSG_FIXED)

# Q = file_size 2**63
FORMAT_HEAD_APPEND = '!Q'
FORMAT_HEAD_MSG = FORMAT_BASE_MSG + 'Q'

# Q = offset, %ds = data
FORMAT_DATA_MSG = FORMAT_BASE_MSG + 'Q%ds'

# %ds = md5_code
FORMAT_END_MSG = FORMAT_BASE_MSG + '%ds'

FORMAT_REQUEST_APPEND = '!2I'
FORMAT_REQUEST_MSG = FORMAT_BASE_MSG + '2I'

# 2I = response_type + error_code
FORMAT_RESPONSE_APPEND = '!2I'
FORMAT_RESPONSE_MSG = FORMAT_BASE_MSG + '2I'

# I = count of blank block
FORMAT_BLANK_MSG = FORMAT_BASE_MSG + 'I'

PACKET_TYPE_INVAID = 0
PACKET_TYPE_HEAD = 1
PACKET_TYPE_DATA = 2
PACKET_TYPE_END = 3
PACKET_TYPE_REQUEST = 4
PACKET_TYPE_RESPONSE = 5
PACKET_TYPE_BLANK = 6


class BaseMsg():
    def __init__(self, path, packet_type, data_size):
        global VERSION
        '''
        path: target file path
        packet_type:
        data_size:
        '''
        self.head = "HEAD"
        self.path = path
        self.path_size = len(self.path)
        self.head_size = FORMAT_BASE_MSG_FIXED_LENGTH + len(self.path)
        self.packet_type = packet_type
        self.total_size = self.head_size + data_size
        self.version = VERSION
        self.crc_code = GetCrcCode(bytes(self.head.encode("utf-8")), self.version, self.head_size,
                                   self.packet_type, self.path_size, self.total_size)


class HeadMsg(BaseMsg):
    def __init__(self, file_size, file_path):
        # self.file_size = os.path.getsize(target.path)
        self.file_size = file_size
        data_size = struct.calcsize(FORMAT_HEAD_APPEND)
        super().__init__(file_path, PACKET_TYPE_HEAD, data_size)

    def Pack(self):
        return struct.pack(FORMAT_HEAD_MSG % len((self.path),),
                           self.total_size,
                           bytes(self.head.encode("utf-8")),
                           self.version,
                           self.head_size,
                           self.packet_type,
                           self.path_size,
                           self.crc_code,
                           bytes(self.path.encode("utf-8")),
                           self.file_size)


class BlankMsg(BaseMsg):
    def __init__(self, file_path, size):
        self.blank_count = size
        data_size = struct.calcsize('!I')
        super().__init__(file_path, PACKET_TYPE_BLANK, data_size)

    def Pack(self):
        return struct.pack(FORMAT_BLANK_MSG % len((self.path),),
                           self.total_size,
                           bytes(self.head.encode("utf-8")),
                           self.version,
                           self.head_size,
                           self.packet_type,
                           self.path_size,
                           self.crc_code,
                           bytes(self.path.encode("utf-8")),
                           self.blank_count)


class DataMsg(BaseMsg):
    offset = ''
    data = ''

    def __init__(self, file_path, offset, data):
        self.offset = offset
        self.data = bytes(data)
        data_size = struct.calcsize('!Q') + len(self.data)
        super().__init__(file_path, PACKET_TYPE_DATA, data_size)

    def Pack(self):
        return struct.pack(FORMAT_DATA_MSG % (len((self.path),), len((self.data),)),
                           self.total_size,
                           bytes(self.head.encode("utf-8")),
                           self.version,
                           self.head_size,
                           self.packet_type,
                           self.path_size,
                           self.crc_code,
                           bytes(self.path.encode("utf-8")),
                           self.offset,
                           self.data)


class EndMsg(BaseMsg):
    def __init__(self, file_path, md5):
        self.md5_code = md5
        data_size = len(self.md5_code)
        super().__init__(file_path, PACKET_TYPE_END, data_size)

    def Pack(self):
        return struct.pack(FORMAT_END_MSG % (len((self.path),), len((self.md5_code),)),
                           self.total_size,
                           bytes(self.head.encode("utf-8")),
                           self.version,
                           self.head_size,
                           self.packet_type,
                           self.path_size,
                           self.crc_code,
                           bytes(self.path.encode("utf-8")),
                           bytes(self.md5_code.encode("utf-8")))

REQUEST_READ = 1
REQUEST_WRITE = 2


class RequestMsg(BaseMsg):
    def __init__(self, src, operation=REQUEST_READ, enable_verify=True):
        self.operation = operation
        self.enable_verify = 1 if enable_verify else 0
        super().__init__(src, PACKET_TYPE_REQUEST, struct.calcsize(FORMAT_REQUEST_APPEND))

    def Pack(self):
        return struct.pack(FORMAT_REQUEST_MSG % len((self.path), ),
                           self.total_size,
                           bytes(self.head.encode("utf-8")),
                           self.version,
                           self.head_size,
                           self.packet_type,
                           self.path_size,
                           self.crc_code,
                           bytes(self.path.encode("utf-8")),
                           self.operation,
                           self.enable_verify)

RESPONSE_TYPE_OK = 0
RESPONSE_TYPE_ERROR = 1

RESPONSE_ERROR_CODE_OK = 0
RESPONSE_ERROR_TARGET_FILE_NOT_EXIST = 1


class ResponseMsg(BaseMsg):
    def __init__(self, file_path, response_type, error_code):
        self.response_type = response_type
        self.error_code = error_code
        data_size = struct.calcsize(FORMAT_RESPONSE_APPEND)
        dest_path = file_path
        super().__init__(dest_path, PACKET_TYPE_RESPONSE, data_size)

    def Pack(self):
        return struct.pack(FORMAT_RESPONSE_MSG % len((self.path),),
                           self.total_size,
                           bytes(self.head.encode("utf-8")),
                           self.version,
                           self.head_size,
                           self.packet_type,
                           self.path_size,
                           self.crc_code,
                           bytes(self.path.encode("utf-8")),
                           self.response_type,
                           self.error_code)


def PackMsg(msg):
    return msg.Pack()


def UnpackBase(pkt):
    total_size, head, version, head_size, pkt_type, path_size, crc_code, = \
        struct.unpack(FORMAT_BASE_MSG_FIXED, pkt[:FORMAT_BASE_MSG_FIXED_LENGTH])
    local_crc = GetCrcCode(head, version, head_size, pkt_type, path_size, total_size)
    return head, version, pkt_type, crc_code, local_crc


def UnpackHead(pkt):
    # skip totle_size(I), head(4s), version(I), head_size(I), packet_type(I)
    offset = struct.calcsize('!I4s3I')
    # path size is 'unsigned int'(I)
    path_size, = struct.unpack('!I', pkt[offset: offset + struct.calcsize('!I')])
    # skip totle_size(I), head(4s), version(I), head_size(I), packet_type(I), path_size(I), crc_code(I)
    path, file_size, = struct.unpack('!%dsQ' % path_size, pkt[struct.calcsize('!I4s5I'):])
    return path, file_size


def UnpackData(pkt):
    head_size = GetHeadSize(pkt)
    data_size = GetDataSize(pkt)
    offset, = struct.unpack('!Q', pkt[head_size: head_size + struct.calcsize('!Q')])
    data, =  struct.unpack('!%ds' % data_size, pkt[head_size + struct.calcsize('!Q'):])
    return offset, data


def UnpackBlank(pkt):
    head_size = GetHeadSize(pkt)
    count, = struct.unpack('!I', pkt[head_size:])
    return count


def UnpackEnd(pkt):
    head_size = GetHeadSize(pkt)
    endsize = GetEndSize(pkt)
    md5_code, = struct.unpack('!%ds' % endsize, pkt[head_size:])
    return md5_code


def UnpackRequest(pkt):
    head_size = GetHeadSize(pkt)
    path_size = head_size - FORMAT_BASE_MSG_FIXED_LENGTH
    path, operation, enable_verify = struct.unpack('!%ds2I' % path_size, pkt[FORMAT_BASE_MSG_FIXED_LENGTH:])
    return path, operation, bool(enable_verify)


def UnpackResponse(pkt):
    response_type, error_code, = struct.unpack('!2I', pkt[-struct.calcsize('!2I'):])
    return response_type, error_code


def GetHeadSize(pkt):
    # skip total_size(I), head(4s), version(I)
    offset = struct.calcsize('!I4sI')
    head_size, = struct.unpack('!I', pkt[offset: offset + struct.calcsize('!I')])
    return head_size


def GetTotalSize(pkt):
    offset = 0
    total_size, = struct.unpack('!I', pkt[offset:offset + struct.calcsize('!I')])
    return total_size


def GetDataSize(pkt):
    return GetTotalSize(pkt) - GetHeadSize(pkt) - struct.calcsize('!Q')


def GetEndSize(pkt):
    return GetTotalSize(pkt) - GetHeadSize(pkt)


def GetCrcCode(head, version, head_size, pkt_type, path_size, total_size):
    if CRRCHECK is True:
        pkt = struct.pack('!4s5I', head, version, head_size, pkt_type, path_size, total_size)
        crc_code = crc32(pkt)
    else:
        crc_code = DEFAULT_CRC
    return crc_code


def GetPktType(pkt):
    offset = struct.calcsize('!I4s2I')
    pkt_type, = struct.unpack('!I', pkt[offset:offset + struct.calcsize('!I')])
    return pkt_type


def PktToString(pkt_type):
    str_dict = {
            PACKET_TYPE_INVAID: 'invalid',
            PACKET_TYPE_HEAD: 'head',
            PACKET_TYPE_DATA: 'data',
            PACKET_TYPE_END: 'end',
            PACKET_TYPE_REQUEST: 'request',
            PACKET_TYPE_RESPONSE: 'response',
            PACKET_TYPE_BLANK: 'blank'}

    return str_dict.get(pkt_type, 'invalid type')
