#!/usr/bin/env python
# encoding: utf-8

import logging
import enum
import socket
import os
import struct
import hashlib
import directio

from . import exception
from . import protocol


MD5_CHECK_ENABLE = True


@enum.unique
class TargetStatus(enum.Enum):
    INVALID = 0
    INIT = 1
    INIT_FILE = 2
    PROCESSING = 3
    FINISHED = 4


@enum.unique
class TargetOps(enum.Enum):
    READ = 1
    WRITE = 2


@enum.unique
class TargetMsgType(enum.Enum):
    INVALID = 0
    OK = 1
    ERROR = 2


def RecvMsg(fd):
    packet_size = struct.calcsize("!I")
    head = RecvAllData(fd, packet_size)
    data_size, = struct.unpack("!I", head)
    pkt = RecvAllData(fd, data_size - packet_size)
    pkt = head + pkt
    return pkt


def RecvAllData(fd, total_len):
    recv_len = 0
    sys_int = 65535
    total_data = bytes()
    while (recv_len < total_len):
        recv_size = total_len - recv_len
        if (recv_size > sys_int):
            recv_size = sys_int
        sock_data = fd.recv(recv_size)
        recv_len += len(sock_data)
        total_data += sock_data
    return total_data


def CreateEmptyFile(fd, size):
    if (size > 0):
        os.ftruncate(fd, size)


def IsAllZero(data, max_size):
    data_len = len(data)
    if (data_len < max_size):
        return False

    i = 0
    size = 512

    while(i + size < data_len):
        j = int.from_bytes(data[i:i+size], 'big')
        if (j != 0):
            return False
        i += size

    if (data[i:] == bytes(data_len - i)):
        return True

    return False


class TargetMsg:
    def __init__(self, msg_type=TargetMsgType.INVALID, msg_data=None):
        self.msg_type = msg_type
        self.msg_data = msg_data

    def __str__(self):
        return 'type %s data %s' % (self.msg_type, self.msg_data)


class Target(object):
    def __init__(self):
        self._status = TargetStatus.INIT
        self._md5 = hashlib.md5()

    def SetStatus(self, status):
        if status.value > self._status.value:
            logging.info('%s -> %s' % (self._status, status))
            self._status = status

    def GetStatus(self):
        logging.debug("current status: %s" % (self._status))
        return self._status

    def _SockRead(self):
        data = RecvMsg(self._sock)
        head, version, pkt_type, crc_code, local_crc = protocol.UnpackBase(data)
        logging.debug('head: %s, version: %d, pkt_type: %s, crc_code: %d, local_crc: %d.',
                      bytes.decode(head), version, protocol.PktToString(pkt_type), crc_code, local_crc)
        return (data, pkt_type)

    def _SockWrite(self, request):
        logging.debug('pkt_type %s' % (protocol.PktToString(request.packet_type)))
        self._sock.sendall(protocol.PackMsg(request))

    def SockRead(self, data):
        pass

    def SockWrite(self, data):
        if self._ops == TargetOps.WRITE:
            # 'get' server / 'put' client
            if self.GetStatus() == TargetStatus.PROCESSING:
                msg_data = data.msg_data
                if 'data' in msg_data:
                    offset = msg_data['offset']
                    fdata = msg_data['data']
                    pro_msg = protocol.DataMsg(self._file_path, offset, fdata)
                    self._SockWrite(pro_msg)
                elif 'hole_size' in msg_data:
                    pro_msg = protocol.BlankMsg(self._file_path, msg_data['hole_size'])
                    self._SockWrite(pro_msg)
                elif 'blank' not in msg_data:
                    self.SetStatus(TargetStatus.FINISHED)
                    if MD5_CHECK_ENABLE:
                        md5 = msg_data['md5']
                        logging.info('md5: %s' % (md5.hexdigest()))
                    else:
                        md5 = self._md5
                    end_msg = protocol.EndMsg(self._file_path, md5.hexdigest())
                    self._SockWrite(end_msg)
                    raise exception.NetCopyEOF('finished type 0', 0)

    def _FileRead(self, size):
        if isinstance(self._fd, int):
            data = directio.read(self._fd, size)
        else:
            data = self._fd.read(size)
        if data == b'':
            # send end msg
            logging.info('eof')
            self.SetStatus(TargetStatus.FINISHED)
        elif MD5_CHECK_ENABLE:
            self._md5.update(data)
        return data

    def _FileWrite(self, msg_data):
        data = msg_data['data']
        offset = msg_data['offset']
        # 'get' client/ 'put' server, last piece of file
        if self._file_size < offset + self._block_size:
            self._SwitchOpenMethord()

        if isinstance(self._fd, int):
            os.lseek(self._fd, offset, 0)
            directio.write(self._fd, data)
        else:
            self._fd.seek(offset, 0)
            self._fd.write(data)

    def FileWrite(self, data):
        if self._ops == TargetOps.WRITE:
            # 'put' server or 'get' client
            msg_type = data.msg_type
            msg_data = data.msg_data
            logging.debug(msg_data)
            if self.GetStatus() == TargetStatus.INIT:
                if msg_type == TargetMsgType.OK:
                    if 'file_size' in msg_data:
                        CreateEmptyFile(self._fd, msg_data['file_size'])
                        self._file_size = msg_data['file_size']
                        self.SetStatus(TargetStatus.PROCESSING)
                else:
                    raise exception.NetCopyError('error msg_type %s' % (msg_type))
            elif self.GetStatus() == TargetStatus.PROCESSING:
                if msg_type == TargetMsgType.OK:
                    if 'data' in msg_data:
                        self._FileWrite(msg_data)

    def FileRead(self):
        if self._ops == TargetOps.WRITE:
            # 'put' server/ 'get' client
            return TargetMsg(TargetMsgType.OK)
        elif self._ops == TargetOps.READ:
            # 'get' server/ 'put' client
            if self._file_size != 0 and self._file_size < self._offset + self._block_size:
                # 'put' client/ 'get' server, last piece of file
                self._SwitchOpenMethord()

            # on server read from file
            data = self._FileRead(self._block_size)

            msg_data = {}
            msg_data['offset'] = self._offset
            if data:
                if IsAllZero(data, self._block_size):
                    # if md5 verify is disable, there is no need no send BlankMsg
                    if MD5_CHECK_ENABLE:
                        msg_data['hole_size'] = len(data)
                    else:
                        msg_data['blank'] = True
                else:
                    msg_data['data'] = data
                self._offset += len(data)
            if MD5_CHECK_ENABLE:
                msg_data['md5'] = self._md5
            return TargetMsg(TargetMsgType.OK, msg_data)

    def _SwitchOpenMethord(self):
        if isinstance(self._fd, int):
            os.close(self._fd)
            if self._ops == TargetOps.WRITE:
                self._fd = open(self._file_path, "rb+")
            else:
                self._fd = open(self._file_path, "rb")
            self._fd.seek(self._offset)

    def UnpackData(self, data):
        offset, fdata = protocol.UnpackData(data)
        msg_data = {}
        msg_data['offset'] = offset
        msg_data['data'] = fdata
        if MD5_CHECK_ENABLE:
            self._md5.update(fdata)
        return TargetMsg(TargetMsgType.OK, msg_data)

    def UnpackBlank(self, data):
        hole_size = protocol.UnpackBlank(data)
        msg_data = {}
        msg_data['hole_size'] = hole_size
        self._md5.update(bytes(hole_size))
        return TargetMsg(TargetMsgType.OK, msg_data)

    def MD5Verify(self, data, type_value):
        global MD5_CHECK_ENABLE

        if not MD5_CHECK_ENABLE:
            raise exception.NetCopyEOF('finished type %s' % (type_value), 0)

        local_md5_str = self._md5.hexdigest().strip()
        logging.info('local md5  %s' % (local_md5_str))
        remote_md5_str = protocol.UnpackEnd(data).decode('utf-8').strip()
        logging.info('remote md5 %s' % (remote_md5_str))
        if remote_md5_str == local_md5_str:
            raise exception.NetCopyEOF('finished type %s' % (type_value), 0)
        else:
            raise exception.NetCopyEOF('md5 verify failed, local %s remote %s %s' %
                                       (local_md5_str, remote_md5_str, type_value), 0)

    def close(self):
        pass


class SocketTarget(Target):
    def __init__(self, ip, port, file_path=None, operation=TargetOps.READ, enable_verify=False, server_mode=False):
        global MD5_CHECK_ENABLE

        self.__ip = ip
        self.__port = port
        self._file_path = file_path
        self._ops = operation
        self.__is_server = server_mode
        super().__init__()
        MD5_CHECK_ENABLE = enable_verify

        if (self.__is_server):
            self.__server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.__server.bind((ip, port))
            self.__server.listen(1)
            self._sock, addr = self.__server.accept()
        else:
            self._sock = socket.socket()
            self._sock.connect((ip, port))

    def ClientWrite(self, data):
        global MD5_CHECK_ENABLE
        if self.GetStatus() == TargetStatus.INIT:
            if self._ops == TargetOps.WRITE:
                # 'put' client
                # send request from client to server, 'put' start here
                request = protocol.RequestMsg(self._file_path, protocol.REQUEST_WRITE, MD5_CHECK_ENABLE)
                super()._SockWrite(request)
                logging.info('send request')

                # send head
                logging.debug(data)
                head_msg = protocol.HeadMsg(data.msg_data['file_size'], self._file_path)
                super()._SockWrite(head_msg)
                logging.info('send head')
            elif self._ops == TargetOps.READ:
                # 'get' client
                # send request from client to server, 'get' start here
                request = protocol.RequestMsg(self._file_path, protocol.REQUEST_READ, MD5_CHECK_ENABLE)
                super()._SockWrite(request)
                logging.info('send request')
        else:
            super().SockWrite(data)

    def ServerWrite(self, data):
        super().SockWrite(data)

    def ClientRead(self):
        if self._ops == TargetOps.WRITE:
            # 'put' client
            if self.GetStatus() == TargetStatus.INIT:
                data, pkt_type = super()._SockRead()
                response_type, error_code = protocol.UnpackResponse(data)
                logging.debug("responde_type %d, error_code %d", response_type, error_code)
                if response_type == protocol.RESPONSE_TYPE_OK and error_code == protocol.RESPONSE_ERROR_CODE_OK:
                    # init done, begin to received data
                    self.SetStatus(TargetStatus.PROCESSING)
                    return TargetMsg(TargetMsgType.OK)
                else:
                    err_msg = 'response type: %d, error code: %d' % (response_type, error_code)
                    logging.error(err_msg)
                    raise exception.NetCopyError(err_msg)
            elif self.GetStatus() == TargetStatus.PROCESSING:
                return TargetMsg(TargetMsgType.OK)

        elif self._ops == TargetOps.READ:
            # 'get' client
            data, pkt_type = super()._SockRead()
            if self.GetStatus() == TargetStatus.INIT:
                if pkt_type == protocol.PACKET_TYPE_HEAD:
                    file_path, file_size = protocol.UnpackHead(data)
                    logging.info("file_path %s, file_size %d", file_path, file_size)
                    msg_data = {}
                    msg_data['file_size'] = file_size
                    self.SetStatus(TargetStatus.PROCESSING)
                    return TargetMsg(TargetMsgType.OK, msg_data)
                elif pkt_type == protocol.PACKET_TYPE_RESPONSE:
                    response_type, error_code = protocol.UnpackResponse(data)
                    logging.debug("responde_type %d, error_code %d", response_type, error_code)
                    if response_type != protocol.RESPONSE_TYPE_OK or error_code != protocol.RESPONSE_ERROR_CODE_OK:
                        raise exception.NetCopyError('response error, response type %d, error code: %d' %
                                                     (response_type, error_code))
                else:
                    err_msg = 'invaid pkt_type %s' % (protocol.PktToString(pkt_type))
                    logging.error(err_msg)
                    raise exception.NetCopyEOF(err_msg)
            elif self.GetStatus() == TargetStatus.PROCESSING:
                if pkt_type == protocol.PACKET_TYPE_DATA:
                    return super().UnpackData(data)
                elif pkt_type == protocol.PACKET_TYPE_BLANK:
                    return super().UnpackBlank(data)
                elif pkt_type == protocol.PACKET_TYPE_END:
                    # reach end of file
                    logging.info('receive end msg')
                    res_msg = protocol.ResponseMsg(self._file_path, protocol.RESPONSE_TYPE_OK,
                                                   protocol.RESPONSE_ERROR_CODE_OK)
                    super()._SockWrite(res_msg)
                    self.SetStatus(TargetStatus.FINISHED)
                    super().MD5Verify(data, 'get')
                else:
                    logging.error('invalid pkt_type %s' % (protocol.PktToString(pkt_type)))

        return TargetMsg(TargetMsgType.INVALID, 'SocketTarget:ClientRead')

    def ServerRead(self):
        global MD5_CHECK_ENABLE
        if self.GetStatus() == TargetStatus.INIT:
            # comman init
            data, pkt_type = super()._SockRead()
            # waiting request, detecting operation mode
            path, operation, enable_verify = protocol.UnpackRequest(data)
            self._file_path = bytes.decode(path)
            if operation == protocol.REQUEST_READ:
                self._ops = TargetOps.WRITE
            if operation == protocol.REQUEST_WRITE:
                self._ops = TargetOps.READ
            logging.info(self._ops)
            MD5_CHECK_ENABLE = enable_verify
            logging.info('%s md5 verify' % ('enable' if MD5_CHECK_ENABLE else 'disable'))
            if self._ops == TargetOps.WRITE:
                # send head
                if os.path.isfile(self._file_path):
                    msg = protocol.HeadMsg(os.path.getsize(self._file_path), self._file_path)
                    super()._SockWrite(msg)
                    self.SetStatus(TargetStatus.PROCESSING)
                else:
                    msg = protocol.ResponseMsg(self._file_path, protocol.RESPONSE_TYPE_ERROR,
                                               protocol.RESPONSE_ERROR_TARGET_FILE_NOT_EXIST)
                    super()._SockWrite(msg)
                    raise exception.NetCopyError('%s is not found' % (self._file_path))
            else:
                # waiting head
                self.SetStatus(TargetStatus.INIT_FILE)
            msg_data = {}
            msg_data['file_path'] = self._file_path
            msg_data['ops'] = TargetOps.READ if self._ops is TargetOps.WRITE else TargetOps.WRITE
            return TargetMsg(TargetMsgType.OK, msg_data)

        if self._ops == TargetOps.WRITE:
            # 'get' server
            if self.GetStatus() == TargetStatus.PROCESSING:
                return TargetMsg(TargetMsgType.OK)
            elif self.GetStatus() == TargetStatus.FINISHED:
                data, pkt_type = super()._SockRead()
                logging.debug(protocol.PktToString(pkt_type))
                if pkt_type != protocol.PACKET_TYPE_RESPONSE:
                    raise exception.NetCopyError('invalid pkt_type %s' % (protocol.PktToString(pkt_type)))

                response_type, error_code = protocol.UnpackResponse(data)
                logging.debug('responde_type %d, error_code %d', response_type, error_code)
                if response_type == protocol.RESPONSE_TYPE_OK and error_code == protocol.RESPONSE_ERROR_CODE_OK:
                    # finished succesfully
                    raise exception.NetCopyEOF('finished type 2', 0)
                else:
                    raise exception.NetCopyError('responde_type %d, error_code %d' % (response_type, error_code))
        elif self._ops == TargetOps.READ:
            # 'put' server
            data, pkt_type = super()._SockRead()
            if self.GetStatus() == TargetStatus.INIT_FILE:
                # get head first
                if pkt_type != protocol.PACKET_TYPE_HEAD:
                    raise exception.NetCopyError('invalid pkt_type: %s' % (protocol.PktToString(pkt_type)))
                file_path, file_size = protocol.UnpackHead(data)
                logging.info("file_path %s, file_size %d", file_path, file_size)
                msg_data = {}
                msg_data['file_size'] = file_size
                res_msg = protocol.ResponseMsg(self._file_path, protocol.RESPONSE_TYPE_OK,
                                               protocol.RESPONSE_ERROR_CODE_OK)
                super()._SockWrite(res_msg)
                self.SetStatus(TargetStatus.PROCESSING)
                return TargetMsg(TargetMsgType.OK, msg_data)
            if self.GetStatus() == TargetStatus.PROCESSING:
                if pkt_type == protocol.PACKET_TYPE_DATA:
                    return super().UnpackData(data)
                elif pkt_type == protocol.PACKET_TYPE_BLANK:
                    return super().UnpackBlank(data)
                elif pkt_type == protocol.PACKET_TYPE_END:
                    # reach end of file
                    logging.info('receive end msg')
                    self.SetStatus(TargetStatus.FINISHED)
                    super().MD5Verify(data, 'put')
                else:
                    err_msg = 'invalid pkt_type %s' % (protocol.PktToString(pkt_type))
                    logging.error(err_msg)
                    raise exception.NetCopyError(err_msg)

        return TargetMsg(TargetMsgType.INVALID, 'SocketTarget:ServerRead')

    def close(self):
        logging.info('close')
        self._sock.close()
        if self.__is_server:
            self.__server.close()


class FileTarget(Target):
    def __init__(self, file_path, operation=TargetOps.READ):
        self._file_path = file_path
        self._ops = operation
        logging.info(operation)
        if operation == TargetOps.WRITE:
            self._fd = os.open(file_path, os.O_WRONLY | os.O_DIRECT | os.O_CREAT)
            self._file_size = 0
        if operation == TargetOps.READ:
            self._fd = os.open(file_path, os.O_RDONLY | os.O_DIRECT)
            self._file_size = os.path.getsize(file_path)
        super().__init__()
        # 1M
        self._block_size = 1024 * 1024
        self._offset = 0

    @property
    def GetFileSize(self):
        return self._file_size

    @property
    def GetOffset(self):
        return self._offset

    def ClientWrite(self, data):
        if self._ops == TargetOps.READ:
            # 'put' client
            if self.GetStatus() == TargetStatus.INIT:
                if data.msg_type == TargetMsgType.OK:
                    self.SetStatus(TargetStatus.PROCESSING)
                    return None

        return super().FileWrite(data)

    def ServerWrite(self, data):
        return super().FileWrite(data)

    def ClientRead(self):
        if self._ops == TargetOps.READ and self.GetStatus() == TargetStatus.INIT:
            # 'put' mode, send file size to server
            msg_data = {}
            msg_data['file_size'] = self._file_size
            return TargetMsg(TargetMsgType.OK, msg_data)

        return super().FileRead()

    def ServerRead(self):
        return super().FileRead()

    def close(self):
        if isinstance(self._fd, int):
            os.close(self._fd)
        else:
            self._fd.close()
