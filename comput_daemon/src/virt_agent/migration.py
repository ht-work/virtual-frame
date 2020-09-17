import logging
import traceback
import time
import json
import envoy
from lxml import etree

import libvirt

from . import virt_agent_pb2 as pb
from . import virt_agent_exception
from . import xml_util
from . import rpcapi
from . import utils


def is_job_complete(dom, path, flags=0):
    try:
        status = dom.blockJobInfo(path=path, flags=flags)
        if status['end'] != 0 and status['cur'] == status['end']:
            return True
    except libvirt.libvirtError as e:
        logging.error('Get block job info failed, libvirt error(%d): %s' % (e.get_error_code(), e.get_error_message()))
    return False


def block_commit(dom, tmp_info):
    '''tmp_info:
        {
            'vda':{
                'base':'/vms/images/b_1.img',
                'tmp':'/vms/images/tmp_1'
            },
            'vdb':{
                'base':'/vms/images/b_2.img',
                'tmp':'/vms/images/tmp_2'
            }
        }
    '''
    commit_flags = 0
    commit_flags |= libvirt.VIR_DOMAIN_BLOCK_COMMIT_ACTIVE
    abort_flags = 0
    abort_flags |= libvirt.VIR_DOMAIN_BLOCK_JOB_ABORT_PIVOT
    for c, d in tmp_info.items():
        dom.blockCommit(disk=c, base=d['base'],
                        top=d['tmp'], flags=commit_flags)
        while not is_job_complete(dom, d['tmp']):
            time.sleep(0.5)
        dom.blockJobAbort(disk=c, flags=abort_flags)
        envoy.run('rm -f %s' % d['tmp'])


def rebase_images(disk):
    '''disk is an element of destination_json
    {
        "dev":"sda",
        "properties":{
               "source":"/vms/images/t.img"
        },
        "migrate_backingfiles": [{
            "filename": /vms/images/b1.img,
            "dst_filename": /var/lib/libvirt/images/b1.img
        }]
    }
    '''
    backingfile_info = {}
    cmd = envoy.run('%s info %s --output=json' % (utils.BIN_QEMU_IMG, disk['properties']['source']))
    if cmd.std_err != '':
        logging.error("Prepare migration failed: %s" % cmd.std_err)
        raise virt_agent_exception.VirtAgentException(err_msg=cmd.std_err)
    disk_info = json.loads(cmd.std_out)
    if 'migrate_backingfiles' in disk:
        for b in disk['migrate_backingfiles']:
            ''' Save backingfile info '''
            cmd = envoy.run('%s info %s --output=json' % (utils.BIN_QEMU_IMG, b['dst_filename']))
            if cmd.std_err != '':
                logging.error("Prepare migration failed: %s" % cmd.std_err)
                raise virt_agent_exception.VirtAgentException(err_msg=cmd.std_err)
            std_out = json.loads(cmd.std_out)
            if 'backing-filename' in std_out:
                backingfile_info[std_out['filename']] = std_out['backing-filename']

            ''' Rebase disk '''
            if b['dst_filename'] == b['filename']:
                continue
            if b['filename'] == disk_info['backing-filename']:
                cmd = envoy.run(
                    '%s rebase -u -b %s %s' % (utils.BIN_QEMU_IMG, b['dst_filename'],
                                               disk['properties']['source']))
                if cmd.std_err != '':
                    logging.error("Prepare migration failed: %s" % cmd.std_err)
                    raise virt_agent_exception.VirtAgentException(err_msg=cmd.std_err)
        for b in disk['migrate_backingfiles']:
            ''' Rebase backingfiles'''
            if b['dst_filename'] == b['filename']:
                continue
            for c in backingfile_info:
                if b['filename'] == backingfile_info[c]:
                    cmd = envoy.run(
                        '%s rebase -u -b %s %s' % (utils.BIN_QEMU_IMG, b['dst_filename'], c))
                    if cmd.std_err != '':
                        logging.error("Prepare migration failed: %s" % cmd.std_err)
                        raise virt_agent_exception.VirtAgentException(err_msg=cmd.std_err)


def check_migration_target_cpu(dest_ip, migrate_cpu):
    '''
        check if destination host can migration:
        cpu used < utils.CPU_THREDSHOLD
    '''
    host_info = rpcapi.get_host_info(dest_ip)
    cpu_rate = float(host_info.body.cpu_rate)
    sockets = float(host_info.body.cpu_sockets)
    cores = float(host_info.body.cpu_cores_per_socket)
    threads = float(host_info.body.cpu_threads_per_core)
    cpu_total = sockets * cores * threads
    if float(migrate_cpu) / float(cpu_total) + float(cpu_rate) > utils.CPU_THREDSHOLD:
        return False

    return True


def check_migration_target_memory(dest_ip, migrate_memory):
    '''
        check if destination host can migration:
        memory free > utils.MEMORY_THREDSHOLD
    '''
    host_info = rpcapi.get_host_info(dest_ip)
    mem_free = int(host_info.body.mem_free)
    mem_total = int(host_info.body.mem_total)
    if int(int(mem_total) - int(mem_free) - int(migrate_memory)) < utils.MEMORY_THREDSHOLD:
        return False
    return True


def check_migration_disks(dest_ip, dom, migrate_devs, dst_disks, migrate_backingfiles, dst_backingfiles):
    local_backingfiles = []
    local_disks = []
    local_pools = []
    remote_pools = []
    remote_pool_files = {}
    dst_pools = []
    md5_check_base_images = {}
    copy_base_images = []
    migrate_disks = []
    local_devs = []
    pools_to_allocalte = {}
    disk_outputs = {}
    backingfile_outputs = {}

    dom_xml = etree.XML(dom.XMLDesc())
    dom_info = xml_util.XmlManagerDomain()
    dom_info.parse(dom_xml)
    disks = dom_info.get_devices(devtype='disk')
    for disk in disks:
        if disk.source is None:
            continue
        if disk.device == 'cdrom':
            continue
        local_disks.append(disk.source)
        local_pool = utils.dir_name(disk.source)
        local_pools.append(local_pool)

        cmd = envoy.run('%s info %s --output=json' % (utils.BIN_QEMU_IMG, disk.source))
        if cmd.std_err != '':
            logging.error(cmd.std_err)
            raise virt_agent_exception.VirtAgentMigrationException(
                err_msg=cmd.std_err, err_code=pb.VIRT_AGENT_ERR_MIGRATION_GET_IMAGE_INFO_FAILED)
        info = json.loads(cmd.std_out)
        disk_outputs[disk.source] = info
        while 'backing-filename' in info:
            local_backingfiles.append(info['backing-filename'])
            cmd = envoy.run('%s info %s --output=json' % (utils.BIN_QEMU_IMG, info['backing-filename']))
            if cmd.std_err != '':
                logging.error(cmd.std_err)
                raise virt_agent_exception.VirtAgentMigrationException(
                    err_msg=cmd.std_err, err_code=pb.VIRT_AGENT_ERR_MIGRATION_GET_IMAGE_INFO_FAILED)
            backingfile_outputs[info['backing-filename']] = info
            info = json.loads(cmd.std_out)
        local_devs.append(disk.target_dev)
        if disk.target_dev in migrate_devs:
            migrate_disks.append(disk.source)

    for dst_disk in dst_disks:
        dst_pool = utils.dir_name(dst_disk)
        filename = ""
        if dst_pool not in dst_pools:
            dst_pools.append(dst_pool)
            for migrate_disk in migrate_disks:
                if utils.base_name(migrate_disk) == utils.base_name(dst_disk):
                    filename = migrate_disk
            if filename not in disk_outputs.keys():
                err_msg = 'Request migate disk %s is not used by current domain' % filename
                logging.error(err_msg)
                raise virt_agent_exception.VirtAgentMigrationException(
                    err_msg=err_msg, err_code=pb.VIRT_AGENT_ERR_MIGRATION_DISK_NOT_IN_USE)
            size = int(disk_outputs[filename]['actual-size']) / 1024
            if utils.dir_name(dst_disk) not in pools_to_allocalte:
                pools_to_allocalte[utils.dir_name(dst_disk)] = size
            else:
                pools_to_allocalte[utils.dir_name(dst_disk)] = int(pools_to_allocalte[utils.dir_name(dst_disk)]) + size

    for dst_backingfile in dst_backingfiles:
        dst_pool = utils.dir_name(dst_backingfile)
        filename = ""
        if dst_pool not in dst_pools:
            dst_pools.append(dst_pool)
            for migrate_backingfile in migrate_backingfiles:
                if utils.base_name(migrate_backingfile) == utils.base_name(dst_backingfile):
                    filename = migrate_backingfile
            if filename not in backingfile_outputs.keys():
                err_msg = 'Request migate backingfile %s is not used by current domain' % filename
                logging.error(err_msg)
                raise virt_agent_exception.VirtAgentMigrationException(
                    err_msg=err_msg, err_code=pb.VIRT_AGENT_ERR_MIGRATION_DISK_NOT_IN_USE)
            size = int(backingfile_outputs[filename]['actual-size']) / 1024
            if utils.dir_name(dst_backingfile) not in pools_to_allocalte:
                pools_to_allocalte[utils.dir_name(dst_backingfile)] = size
            else:
                pools_to_allocalte[utils.dir_name(dst_backingfile)] = int(
                    pools_to_allocalte[utils.dir_name(dst_backingfile)]) + size

    '''
        rpcapi call store-agent
        collect pools and files in each pool
    '''
    remote_pools = rpcapi.list_pools(dest_ip)
    for pool in remote_pools:
        path = pool.mount
        files = rpcapi.list_files_in_pool(dest_ip, pool.name)
        remote_pool_files[path] = files

    ''' Condition 1:
        storages(path changed) must be migrate to destination
    '''
    for disk in local_disks:
        if disk not in dst_disks:
            if utils.dir_name(disk) not in remote_pool_files.keys():
                logging.error("Disk %s must be migrated because it's not visable to destination" % disk)
                raise virt_agent_exception.VirtAgentMigrationException(
                    err_code=pb.VIRT_AGENT_ERR_MIGRATION_NON_SHARED_STORAGE_UNMIGRATED)
            if utils.base_name(disk) not in remote_pool_files[utils.dir_name(disk)]:
                # check if in requested dst_disks list
                in_req_list = False
                for dst_disk in dst_disks:
                    if utils.base_name(disk) == utils.base_name(dst_disk):
                        in_req_list = True
                        break
                if not in_req_list:
                    logging.error("Disk %s must be migrated because it's not visable to destination" % disk)
                    raise virt_agent_exception.VirtAgentMigrationException(
                        err_code=pb.VIRT_AGENT_ERR_MIGRATION_NON_SHARED_STORAGE_UNMIGRATED)
    for backingfile in local_backingfiles:
        if backingfile not in dst_backingfiles:
            if utils.dir_name(backingfile) not in remote_pool_files.keys():
                logging.error("Backingfile %s must be migrated because it's not visable to destination" % backingfile)
                raise virt_agent_exception.VirtAgentMigrationException(
                    err_code=pb.VIRT_AGENT_ERR_MIGRATION_NON_SHARED_STORAGE_UNMIGRATED)
            if utils.base_name(backingfile) not in remote_pool_files[utils.dir_name(backingfile)]:
                # check if in requested dst_disks list
                in_req_list = False
                for dst_backingfile in dst_backingfiles:
                    if utils.base_name(backingfile) == utils.base_name(dst_backingfile):
                        in_req_list = True
                        break
                if not in_req_list:
                    logging.error(
                        "Backinfile %s must be migrated because it's not visable to destination" %
                        backingfile)
                    raise virt_agent_exception.VirtAgentMigrationException(
                        err_code=pb.VIRT_AGENT_ERR_MIGRATION_NON_SHARED_STORAGE_UNMIGRATED)

    ''' Condition 2:
        migrate paths must be visible to destination
    '''
    for dst_pool in dst_pools:
        if dst_pool not in remote_pool_files.keys():
            logging.error('Request pool %s is not visable to desition' % dst_pool)
            raise virt_agent_exception.VirtAgentMigrationException(
                err_code=pb.VIRT_AGENT_ERR_MIGRATION_NO_SUCH_DST_STORAGE_POOL)

    ''' Condition 3
        disk must be in use by current domain
    '''
    for migrate_dev in migrate_devs:
        if migrate_dev not in local_devs:
            err_msg = 'Request migate disk %s is not used by current domain' % migrate_dev
            logging.error(err_msg)
            raise virt_agent_exception.VirtAgentMigrationException(err_msg=err_msg,
                                                                   err_code=pb.VIRT_AGENT_ERR_MIGRATION_DISK_NOT_IN_USE)

    ''' Condition 4
        backingfile must be in use by current domain
    '''
    for migrate_backingfile in migrate_backingfiles:
        if migrate_backingfile not in local_backingfiles:
            err_msg = 'Request migate backingfile %s is not used by current domain' % migrate_backingfile
            logging.error(err_msg)
            raise virt_agent_exception.VirtAgentMigrationException(
                err_msg=err_msg, err_code=pb.VIRT_AGENT_ERR_MIGRATION_BACKINGFILE_NOT_IN_USE)

    ''' Condition 5
        top image must not be in destination pool with the same name
    '''
    for dst_file in migrate_disks:
        if dst_file in remote_pool_files[utils.dir_name(dst_file)]:
            raise virt_agent_exception.VirtAgentMigrationException(
                err_code=pb.VIRT_AGENT_ERR_MIGRATION_DISK_NAME_CONFLICT_IN_DST_STORAGE_POOL)

    ''' Condition 6
        backingfiles must check md5 if with the same name in destination pool
        backingfile copy to remote if not in destination pool
    '''
    for dst_backingfile in dst_backingfiles:
        if utils.base_name(dst_backingfile) not in remote_pool_files[utils.dir_name(dst_backingfile)]:
            copy_base_images.append(migrate_backingfile)
            continue
        for migrate_backingfile in migrate_backingfiles:
            if utils.base_name(dst_backingfile) == utils.base_name(migrate_backingfile):
                md5_check_base_images[migrate_backingfile] = dst_backingfile

    ''' Condition 7
        remote_pools must have enough space
    '''
    for pool in remote_pools:
        if pool.mount in pools_to_allocalte:
            pool.allocatedsize = str(int(pool.allocatedsize) + int(pools_to_allocalte[pool.mount]))
            pool.availablesize = str(int(pool.availablesize) - int(pools_to_allocalte[pool.mount]))
            if float(pool.allocatedsize) / float(pool.totalsize) > 0.9:
                raise virt_agent_exception.VirtAgentMigrationException(
                    err_code=pb.VIRT_AGENT_ERR_MIGRATION_NO_SPACE_LEFT_AT_DESTINATION)

    ''' Condition 8
        check md5
    '''
    for s, d in md5_check_base_images:
        cmd = envoy.run('md5sum %s' % s)
        s_md5 = cmd.std_out.partition(' ')[0]
        d_md5 = rpcapi.get_md5(dest_ip, d)
        logging.info(s_md5)
        logging.info(d_md5)
        if s_md5 != d_md5:
            logging.error('Md5 of %s, %s not matched' % s, d)
            raise virt_agent_exception.VirtAgentMigrationException(
                err_code=pb.VIRT_AGENT_ERR_MIGRATION_BACKINGFILE_MD5_CHECK_ERROR)

    return copy_base_images


def check_can_migrate(opaque):
    '''
        destination_json e.g:
        {
            "devices": {
                "disk":[{
                    "dev":"sda",
                    "properties":{
                        "source":"new path"
                    }
                    "migrate_backingfiles": [{
                        "filename": string,
                        "dst_filename": string
                    }]
              }]
           }
        }
    '''
    connection_pool = opaque['connection_pool']
    uuid = opaque['dom_id']
    dest_ip = opaque['destination']
    destination_json = opaque['destination_json']
    migrate_devs = []
    dst_disks = []
    migrate_backingfiles = []
    dst_backingfiles = []

    try:
        conn = connection_pool.get()
        if conn is None:
            logging.error('failed to get libvirt connection')
            raise virt_agent_exception.VirtAgentLibvirtException('failed to get libvirt connection')
        dom = conn.lookupByUUIDString(uuid)
        dom_xml = etree.XML(dom.XMLDesc())
        dom_info = xml_util.XmlManagerDomain()
        dom_info.parse(dom_xml)

        if dom.isActive():
            check_migration_target_cpu(dest_ip, dom_info.vcpu.num)
            check_migration_target_memory(dest_ip, dom_info.memory)
        if destination_json != '':
            for disk in destination_json['devices']['disk']:
                migrate_devs.append(disk['dev'])
                dst_disks.append(disk['properties']['source'])
                if 'migrate_backingfiles' in disk:
                    for backingfile in disk['migrate_backingfiles']:
                        migrate_backingfiles.append(backingfile['filename'])
                        dst_backingfiles.append(backingfile['dst_filename'])
            check_migration_disks(dest_ip, dom, migrate_devs, dst_disks, migrate_backingfiles, dst_backingfiles)
    except libvirt.libvirtError as e:
        logging.error(traceback.format_exc())
        raise virt_agent_exception.VirtAgentLibvirtException(e)
    finally:
        if conn:
            connection_pool.put(conn)

    return
