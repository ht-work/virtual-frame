import os

import libvirt

from . import virt_agent_pb2 as pb


BIN_QEMU_IMG = '/usr/bin/qemu-img'
CPU_THREDSHOLD = 0.9
MEMORY_THREDSHOLD = 8 * 1024 * 1024  # KiB


def base_name(file_name):
    return os.path.basename(file_name)


def dir_name(file_name):
    return os.path.dirname(file_name)


def full_name(dir_name, base_name):
    return os.path.join(dir_name, base_name)


def generate_backend_error_code(libvirt_code):
    codes = {
        libvirt.VIR_ERR_OK: pb.LIBVIRT_ERR_OK,
        libvirt.VIR_ERR_INTERNAL_ERROR: pb.LIBVIRT_ERR_INTERNAL_ERROR,
        libvirt.VIR_ERR_NO_CONNECT: pb.LIBVIRT_ERR_NO_CONNECT,
        libvirt.VIR_ERR_INVALID_CONN: pb.LIBVIRT_ERR_NO_CONNECT,
        libvirt.VIR_ERR_OPERATION_FAILED: pb.LIBVIRT_ERR_OPERATION_FAILED,
        libvirt.VIR_ERR_XML_ERROR: pb.LIBVIRT_ERR_XML_ERROR,
        libvirt.VIR_ERR_XML_DETAIL: pb.LIBVIRT_ERR_XML_ERROR,
        libvirt.VIR_ERR_DOM_EXIST: pb.LIBVIRT_ERR_DOM_EXIST,
        libvirt.VIR_ERR_INVALID_NETWORK: pb.LIBVIRT_ERR_INVALID_NETWORK,
        libvirt.VIR_ERR_NO_DOMAIN: pb.LIBVIRT_ERR_NO_DOMAIN,
        libvirt.VIR_ERR_AUTH_FAILED: pb.LIBVIRT_ERR_AUTH_FAILED,
        libvirt.VIR_ERR_OPERATION_TIMEOUT: pb.LIBVIRT_ERR_OPERATION_TIMEOUT,
        libvirt.VIR_ERR_OPERATION_ABORTED: pb.LIBVIRT_ERR_OPERATION_ABORTED,
        libvirt.VIR_ERR_OPERATION_UNSUPPORTED: pb.LIBVIRT_ERR_OPERATION_UNSUPPORTED,
        libvirt.VIR_ERR_RESOURCE_BUSY: pb.LIBVIRT_ERR_RESOURCE_BUSY
    }
    return codes.get(libvirt_code, pb.LIBVIRT_ERR_INTERNAL_ERROR)


def generate_backend_domain_state(libvirt_state):
    states = {
        libvirt.VIR_DOMAIN_NOSTATE: "nostate",
        libvirt.VIR_DOMAIN_RUNNING: "running",
        libvirt.VIR_DOMAIN_BLOCKED: "blocked",
        libvirt.VIR_DOMAIN_PAUSED: "paused",
        libvirt.VIR_DOMAIN_SHUTDOWN: "shutdown",
        libvirt.VIR_DOMAIN_SHUTOFF: "shutoff",
        libvirt.VIR_DOMAIN_CRASHED: "crashed",
        libvirt.VIR_DOMAIN_PMSUSPENDED: "pmsuspended"
    }
    return states.get(libvirt_state, "unknown")
