#!/usr/bin/env python
# encoding: utf-8
import logging

from . import target


def GetServerTarget(server_ip, server_port):
    remote_target = target.SocketTarget(server_ip, server_port, server_mode=True)
    data = remote_target.ServerRead()
    logging.info(data)
    local_target = target.FileTarget(data.msg_data['file_path'], data.msg_data['ops'])

    return remote_target, local_target


def GetClientTarget(server_ip, server_port, operation, local_file, remote_file):
    if (operation == 'get'):
        remote_ops = target.TargetOps.READ
        local_ops = target.TargetOps.WRITE
    else:
        remote_ops = target.TargetOps.WRITE
        local_ops = target.TargetOps.READ

    remote_target = target.SocketTarget(server_ip, server_port, remote_file, remote_ops, True)
    local_target = target.FileTarget(local_file, local_ops)

    return remote_target, local_target


def ServerProcess(remote_target, local_target):
    local_target.ServerWrite(remote_target.ServerRead())
    remote_target.ServerWrite(local_target.ServerRead())


def ServerRun(remote_target, local_target):
    while True:
        ServerProcess(remote_target, local_target)


def ClientProcess(remote_target, local_target):
    remote_target.ClientWrite(local_target.ClientRead())
    local_target.ClientWrite(remote_target.ClientRead())


def ClientRun(remote_target, local_target):
    while True:
        ClientProcess(remote_target, local_target)


def PutTarget(remote_target, local_target):
    if remote_target:
        remote_target.close()
    if local_target:
        local_target.close()
