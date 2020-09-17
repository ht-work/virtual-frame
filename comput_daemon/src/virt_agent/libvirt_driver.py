#!/usr/bin/env python
# encoding: utf-8

import logging
import traceback
import threading
import time
from lxml import etree
import enum
import os
import json
import envoy

import libvirt
from util_base.libvirt_util import ConnectionPool
from util_base.libvirt_util import Description
from util_base.exception import XMLParseException
from util_base.lxml_util import XMLGetAttribueByXPath

from . import virt_agent_pb2 as pb
from . import virt_agent_exception
from . import xml_util
from . import virt_agentd
from . import worker_job
from . import rpcapi
from . import utils
from . import migration

DOM_EVENTS = Description(
    ("Defined", ("Added", "Updated", "Renamed", "Snapshot")),
    ("Undefined", ("Removed", "Renamed")),
    ("Started", ("Booted", "Migrated", "Restored", "Snapshot", "Wakeup")),
    ("Suspended", ("Paused", "Migrated", "IOError", "Watchdog", "Restored", "Snapshot", "API error",
                   "Postcopy", "Postcopy failed")),
    ("Resumed", ("Unpaused", "Migrated", "Snapshot", "Postcopy")),
    ("Stopped", ("Shutdown", "Destroyed", "Crashed", "Migrated", "Saved", "Failed", "Snapshot", "Daemon")),
    ("Shutdown", ("Finished", "On guest request", "On host request")),
    ("PMSuspended", ("Memory", "Disk")),
    ("Crashed", ("Panicked",)),
)


class LibvirtEvent(object):
    def __init__(self, connection_pool):
        assert isinstance(connection_pool, ConnectionPool)

        self.__connection_pool = connection_pool
        self.__conn_lock = threading.Lock()
        self.__domain_event_cb = None
        self.__domain_event_opaque = None
        self.__dom_event_id = []

    def check_conn(self, conn):
        logging.debug(self.__conn)
        with self.__conn_lock:
            return (conn is self.__conn)

    def isEnabled(self):
        return (not self.check_conn(None))

    def enable(self):
        with self.__conn_lock:
            try:
                self.__conn = self.__connection_pool.get()
                if self.__conn:
                    self.__dom_event_id.clear()
                    evid = self.__conn.domainEventRegisterAny(None, libvirt.VIR_DOMAIN_EVENT_ID_LIFECYCLE,
                                                              self.__domain_event_handler, None)
                    self.__dom_event_id.append(evid)
                    evid = self.__conn.domainEventRegisterAny(None, libvirt.VIR_DOMAIN_EVENT_ID_REBOOT,
                                                              self.__domain_event_reboot_handler, None)
                    self.__dom_event_id.append(evid)

            except libvirt.libvirtError:
                logging.error(traceback.format_exc())

    def disable(self):
        if self.__conn:
            with self.__conn_lock:
                try:
                    for evid in self.__dom_event_id:
                        self.__conn.domainEventDeregisterAny(evid)

                    self.__connection_pool.put(self.__conn)
                except libvirt.libvirtError:
                    pass
                self.__conn = None

    def __domain_event_handler(self, conn, dom, event, detail, opaque):
        '''
        DO NOT long delayed operation here.
        It is recommended to adding job to worker.
        '''
        logging.info("Domain %s(%s) %s %s" % (dom.name(), dom.ID(),
                                              DOM_EVENTS[event],
                                              DOM_EVENTS[event][detail]))
        self.run_domain_event_cb(conn, dom, event, detail)

    def __domain_event_reboot_handler(self, conn, dom, opaque):
        logging.info("Domain %s(%s)" % (dom.name(), dom.ID()))

    def register_domain_event_cb(self, cb, opaque=None):
        self.__domain_event_cb = cb
        self.__domain_event_opaque = opaque

    def run_domain_event_cb(self, conn, dom, event, detail):
        if self.__domain_event_cb is None:
            return

        self.__domain_event_cb(conn, dom, event, detail, self.__domain_event_opaque)


def GetDomainXMLRoot(dom):
    '''
        return lxml.etree root node, which indicates the whole VM.
    '''
    ret = None
    try:
        ret = etree.XML(dom.XMLDesc())
    except (libvirt.libvirtError, etree.LxmlError):
        logging.error(traceback.format_exc())
    finally:
        return ret


class Domain(object):
    def __init__(self, uuid):
        self.__name = None
        self.__uuid = uuid
        self.__lock = threading.Lock()

    @property
    def lock(self):
        return self.__lock

    @property
    def name(self):
        return self.__name

    @name.setter
    def name(self, name):
        self.__name = name

    @property
    def uuid(self):
        return self.__uuid

    @uuid.setter
    def uuid(self, uuid):
        assert isinstance(uuid, str)
        self.__uuid = uuid


class DomainList(object):
    def __init__(self):
        self.__domain_list = {}
        self.__lock = threading.Lock()

    @property
    def lock(self):
        return self.__lock

    def append(self, domain):
        assert isinstance(domain, Domain)

        if not self.__lock.locked():
            raise virt_agent_exception.VirtAgentLockException('the caller must hold DomainList lock')

        with domain.lock:
            if domain.uuid in self.__domain_list:
                raise virt_agent_exception.VirtAgentInvalidException('domain(%s) already in domain list' % domain.uuid)
            else:
                self.__domain_list[domain.uuid] = domain

    def get(self, uuid_str):
        if not self.__lock.locked():
            raise virt_agent_exception.VirtAgentLockException('the caller must hold DomainList lock')

        if not (uuid_str in self.__domain_list):
            raise virt_agent_exception.VirtAgentInvalidException('invalid domain uuid')

        return self.__domain_list[uuid_str]

    def pop(self, uuid_str):
        if not self.__lock.locked():
            raise virt_agent_exception.VirtAgentLockException('the caller must hold DomainList lock')

        if not (uuid_str in self.__domain_list):
            raise virt_agent_exception.VirtAgentInvalidException('invalid domain uuid')

        return self.__domain_list.pop(uuid_str)

    def exists(self, uuid_str):
        if not self.__lock.locked():
            raise virt_agent_exception.VirtAgentLockException('the caller must hold DomainList lock')

        if not (uuid_str in self.__domain_list):
            return False

        return True

    def len(self, uuid_str):
        if not self.__lock.locked():
            raise virt_agent_exception.VirtAgentLockException('the caller must hold DomainList lock')

        return len(self.__domain_list)

    def __iter__(self):
        if not self.__lock.locked():
            raise virt_agent_exception.VirtAgentLockException('the caller must hold DomainList lock')

        self.it = iter(self.__domain_list)
        return self

    def __next__(self):
        if not self.__lock.locked():
            raise virt_agent_exception.VirtAgentLockException('the caller must hold DomainList lock')

        return self.__domain_list[next(self.it)]


DOMAIN_LIST = DomainList()


def LibvirtJobRun(libvirt_connection_pool, func, opaque):
    try:
        conn = libvirt_connection_pool.get()
        if conn is None:
            logging.error('failed to get libvirt connection')
            raise virt_agent_exception.VirtAgentLibvirtException('failed to get libvirt connection')

        return func(conn, opaque)
    except libvirt.libvirtError as e:
        logging.error(e)
        logging.error(traceback.format_exc())
        raise virt_agent_exception.VirtAgentLibvirtException(e)
    finally:
        if conn:
            libvirt_connection_pool.put(conn)


@enum.unique
class SnapshotType(enum.Enum):
    OFFLINE_SNAPSHOT = 0
    ONLINE_SNAPSHOT_DISK_INTERNAL = 1
    ONLINE_SNAPSHOT_FULL_SYSTEM = 2


def _BuildSnapshotXML(domain, snapname, snapshot_type):
    '''
    offline snapshot template:
    <domainsnapshot>
      <name>snapname</name>
    </domainsnapshot>

    online disk internal snapshot:
    <domainsnapshot>
      <name>snap1</name>
      <memory snapshot='no'/>
    </domainsnapshot>

    online full system snapshot:
    <domainsnapshot>
      <name>snap1</name>
      <memory snapshot='external' file='/data/images/.snap/centos7.snap1'/>
      <disks>
        <disk name='sda' snapshot='internal'/>
        <disk name='hda' snapshot='no'/>
      </disks>
    </domainsnapshot>

    return xml string of snapshot
    '''
    snap_root = etree.Element('domainsnapshot')
    # basic snap info
    child_name = etree.Element('name')
    child_name.text = snapname
    snap_root.append(child_name)
    disk_xmls = None

    domain_xml = GetDomainXMLRoot(domain)

    # memory info
    if snapshot_type != SnapshotType.OFFLINE_SNAPSHOT:
        child_mem = etree.Element('memory')
        if snapshot_type == SnapshotType.ONLINE_SNAPSHOT_DISK_INTERNAL:
            child_mem.attrib['snapshot'] = 'no'
        elif snapshot_type == SnapshotType.ONLINE_SNAPSHOT_FULL_SYSTEM:
            child_mem.attrib['snapshot'] = 'external'
            disk_xmls = xml_util.GetDomainXMLElemDiskAll(domain_xml)
            err_msg = None
            for disk in disk_xmls:
                try:
                    disk_type = XMLGetAttribueByXPath(disk, './@type')
                    disk_device = XMLGetAttribueByXPath(disk, './@device')
                    # skip cdrom and floppy
                    if (disk_type != 'file') or (disk_device != 'disk'):
                        continue
                    disk_file = XMLGetAttribueByXPath(disk, './source[1]/@file')
                    # 'domain name + snapshot' name is unqiue in VAP cluster environment
                    mem_file = os.path.join(os.path.dirname(disk_file), '.snap', '%s.%s' % (domain.name(), snapname))
                    if os.path.exists(mem_file):
                        err_msg = '%s exists already' % (mem_file)
                        break
                    child_mem.set('file', mem_file)
                    break
                except XMLParseException as e:
                    logging.error(e.err_msg)

            if (err_msg is None) and ('file' not in child_mem.keys()):
                err_msg = 'failed to build file in "memory"'
            if err_msg is not None:
                logging.error(err_msg)
                raise virt_agent_exception.VirtAgentDomainXMLException(err_msg)

        snap_root.append(child_mem)

    # disk info
    if snapshot_type == SnapshotType.ONLINE_SNAPSHOT_FULL_SYSTEM:
        if not disk_xmls:
            disk_xmls = xml_util.GetDomainXMLElemDiskAll(domain_xml)

        child_disks = etree.Element('disks')
        for disk in disk_xmls:
            try:
                child_disk = etree.Element('disk')
                disk_type = XMLGetAttribueByXPath(disk, './@type')
                disk_device = XMLGetAttribueByXPath(disk, './@device')
                disk_name = XMLGetAttribueByXPath(disk, './target[1]/@dev')
                child_disk.set('name', disk_name)

                if (disk_type != 'file') or (disk_device != 'disk'):
                    # skip cdrom, floppy and non-file driver
                    child_disk.set('snapshot', 'no')
                elif disk.xpath('readonly'):
                    # skip readonly disk
                    child_disk.set('snapshot', 'no')
                else:
                    child_disk.set('snapshot', 'internal')

                child_disks.append(child_disk)
            except XMLParseException as e:
                logging.error(e.err_msg)
                raise virt_agent_exception.VirtAgentDomainXMLException(e.err_msg)

        snap_root.append(child_disks)

    return etree.tostring(snap_root, encoding='utf-8', method='xml').decode('utf-8')


def DomainStart(opaque, job=None):
    '''
    dom_id: UUID of domain
    connection_pool: libvirt connection pool.
    '''
    def func(conn, opaque):
        dom_id = opaque['dom_id']

        dom = conn.lookupByUUIDString(dom_id)
        if dom is None:
            err_msg = 'domain %s is not found' % dom_id
            logging.error(err_msg)
            raise virt_agent_exception.VirtAgentInvalidException(err_msg)
        dom.create()

    return LibvirtJobRun(opaque['connection_pool'], func, opaque)


def DomainStop(opaque, job=None):
    '''
    dom_id: UUID of domain
    force: force delete domain
    connection_pool: libvirt connection pool.
    '''
    def func(conn, opaque):
        dom_id = opaque['dom_id']
        force = opaque['force']

        dom = conn.lookupByUUIDString(dom_id)
        if dom is None:
            err_msg = 'domain %s is not found' % dom_id
            logging.error(err_msg)
            raise virt_agent_exception.VirtAgentInvalidException(err_msg)
        if force:
            dom.destroy()
        else:
            dom.shutdown()

    return LibvirtJobRun(opaque['connection_pool'], func, opaque)


def DomainMigrate(opaque, job=None):
    '''
    dom_id: UUID of domain
    connection_pool: libvirt connection pool.
    '''
    def _event_migrate_iteration_callback(conn, dom, iteration, opaque):
        if iteration == 2:
            dom.migrateStartPostCopy()

    def _migrate(conn, dom, dest_ip, postcopy, destination_json, remote_tmp_info):
        dest_uri = "qemu+ssh://%s/system" % dest_ip
        migration_flags = 0
        iter_event = -1
        migration_flags |= libvirt.VIR_MIGRATE_PERSIST_DEST
        migration_flags |= libvirt.VIR_MIGRATE_PEER2PEER
        migration_flags |= libvirt.VIR_MIGRATE_CHANGE_PROTECTION
        if not dom.isActive():
            migration_flags |= libvirt.VIR_MIGRATE_OFFLINE
        else:
            migration_flags |= libvirt.VIR_MIGRATE_LIVE
            migration_flags |= libvirt.VIR_MIGRATE_NON_SHARED_INC
            if postcopy:
                migration_flags |= libvirt.VIR_MIGRATE_POSTCOPY
                iter_event = conn.domainEventRegisterAny(
                    dom=dom,
                    eventID=libvirt.VIR_DOMAIN_EVENT_ID_MIGRATION_ITERATION,
                    cb=_event_migrate_iteration_callback,
                    opaque=None)

        dom_info = xml_util.XmlManagerDomain()
        dom_info.parse(GetDomainXMLRoot(dom))
        for c in destination_json['devices']['disk']:
            for d, e in remote_tmp_info.items():
                if c['dev'] == d:
                    c['properties']['source'] = e['tmp']

            if 'migrate_backingfiles' not in c:
                continue
            for d in dom_info.get_devices(devtype='disk'):
                if c['dev'] != d.target_dev:
                    continue
                for e in c['migrate_backingfiles']:
                    if e['filename'] == e['dst_filename']:
                        continue
                    d.change_backingfile(origin=e['filename'], target=e['dst_filename'])
        dom_info.update_properties(destination_json)
        try:
            dom.migrateToURI3(
                dconnuri=dest_uri,
                params={"destination_xml": dom_info.to_xml_str()},
                flags=migration_flags)
        except libvirt.libvirtError:
            raise
        finally:
            if iter_event != -1:
                conn.domainEventDeregisterAny(iter_event)

    def _backup_delete_snapshots(dom, destination_json):
        ''' Backup local snapshot xmls and delete '''
        local_snapshots = []
        remote_snapshots = []
        memory_snapshots = {}
        for snap_name in dom.snapshotListNames(flags=libvirt.VIR_DOMAIN_SNAPSHOT_LIST_TOPOLOGICAL):
            snap = dom.snapshotLookupByName(snap_name)
            snap_xml = snap.getXMLDesc()
            snap_info = xml_util.XmlManagerDomainSnapshot()
            snap_info.parse(snap_info.to_xml_tree(snap_xml))
            if snap_info.memory_snapshot == 'external':
                for c in destination_json['devices']['disk']:
                    if c['dev'] == snap_info.disks[0].name:
                        src_memory_file = snap_info.memory_file
                        snap_info.memory_file = utils.full_name(utils.dir_name(c['properties']['source']),
                                                                '.snap/' + utils.base_name(snap_info.memory_file))
                        memory_snapshots[src_memory_file] = snap_info.memory_file
            for d in snap_info.disks:
                if d.snapshot == 'internal':
                    continue
                if destination_json != '':
                    for c in destination_json['devices']['disk']:
                        if ['dev'] == d.name:
                            d.source_file = utils.full_name(
                                utils.dir_name(
                                    c['properties']['source']), utils.base_name(
                                    d.source_file))
            snap_info.domain.update_properties(destination_json)
            for c in destination_json['devices']['disk']:
                if 'migrate_backingfiles' not in c:
                    continue
                for d in snap_info.domain.get_devices(devtype='disk'):
                    if c['dev'] != d.target_dev:
                        continue
                    for e in c['migrate_backingfiles']:
                        if e['filename'] == e['dst_filename']:
                            continue
                        d.change_backingfile(origin=e['filename'], target=e['dst_filename'])
            snap_info.active = str(snap.isCurrent())
            remote_snapshots.append(snap_info.to_xml_str())
            local_snapshots.append(snap_xml)
        for snap_name in dom.snapshotListNames(flags=1024):
            snap = dom.snapshotLookupByName(snap_name)
            snap.delete(flags=libvirt.VIR_DOMAIN_SNAPSHOT_DELETE_METADATA_ONLY)

        return local_snapshots, remote_snapshots, memory_snapshots

    def _check_prepare_migration(dom, dest_ip, destination_json, local_tmp_info):
        '''tmp_info:
           {
               'vda': {
                   'base': '/vms/images/b_1.img',
                   'tmp': '/vms/images/tmp_1',
               },
               'vdb': {
                   'base': '/vms/images/b_2.img',
                   'tmp': '/vms/images/tmp_2',
               }
           }
        '''
        remote_tmp_info = {}
        live = True
        if not dom.isActive():
            live = False
        if destination_json == '':
            return remote_tmp_info

        ''' remote tmp info includes:
            1. disk path at remote host
            2. tmp disk path base on disk at remote host
        '''
        for c, d in local_tmp_info.items():
            for e in destination_json['devices']['disk']:
                if c == e['dev']:
                    remote_tmp_info[e['dev']] = {'base': e['properties']['source'], 'tmp': utils.full_name(
                        utils.dir_name(e['properties']['source']), utils.base_name(d['tmp']))}

        rpcapi.prepare_migration(dest_ip, live, json.dumps(destination_json), json.dumps(remote_tmp_info))

        return remote_tmp_info

    def _check_create_tmp_snapshot(dom):
        '''local_tmp_info
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
        if not dom.isActive():
            return

        snap_flags = 0
        snap_flags |= libvirt.VIR_DOMAIN_SNAPSHOT_CREATE_ATOMIC
        snap_flags |= libvirt.VIR_DOMAIN_SNAPSHOT_CREATE_DISK_ONLY
        snap_flags |= libvirt.VIR_DOMAIN_SNAPSHOT_CREATE_NO_METADATA
        snap_disks = []
        local_tmp_info = {}
        dom_info = xml_util.XmlManagerDomain()
        dom_info.parse(GetDomainXMLRoot(dom))

        index = 1
        for disk in dom_info.get_devices(devtype='disk'):
            if disk.device == 'cdrom':
                continue
            tmp_file = disk.source + '_' + str(index) + '_' + str(round(time.time() * 1000))
            snap_disks.append(
                xml_util.XmlManagerDomainSnapshotDisk(
                    name=disk.target_dev,
                    snapshot='external',
                    source_file=tmp_file,
                    driver_type=disk.driver_type))
            local_tmp_info[disk.target_dev] = {'base': disk.source, 'tmp': tmp_file}

        snap_info = xml_util.XmlManagerDomainSnapshot(
            name='tmp',
            state='disk-snapshot',
            memory_snapshot='no',
            creationTime=str(int(time.time())),
            disks=snap_disks,
            domain=dom_info)
        dom.snapshotCreateXML(snap_info.to_xml_str(), snap_flags)

        return local_tmp_info

    def _check_copy_images(dom, dom_info, dest_ip, destination_json, memory_snapshots):
        ''' Use destination_json to copy or migrate disks, format:
            {
                "devices": {
                    "disk":[{
                     "dev":"sda",
                     "properties":{
                            "source":"/vms/images/test.qcow2"
                        }
                     },
                     "migrate_backingfiles": [{
                         "filename": "/vms/images/test_base.qcow2",
                         "dst_filename": "/var/lib/libvirt/images/test_base.qcow2"
                    }]
                }
            }
        '''
        if destination_json == '':
            return

        host_info = rpcapi.get_host_info("localhost")
        local_ip = host_info.body.host_ip
        for c in destination_json['devices']['disk']:
            for disk in dom_info.get_devices(devtype='disk'):
                if disk.target_dev != c['dev'] or disk.device == 'cdrom':
                    continue
                rpcapi.copy_image(dest_ip=dest_ip, dest_path=c['properties']['source'],
                                  local_ip=local_ip, local_path=disk.source)

                if 'migrate_backingfiles' in c.keys():
                    for b in c['migrate_backingfiles']:
                        rpcapi.copy_image(dest_ip=dest_ip, dest_path=b['dst_filename'],
                                          local_ip=local_ip, local_path=b['filename'])

        for c, d in memory_snapshots.items():
            rpcapi.copy_image(dest_ip=dest_ip, dest_path=c, local_ip=local_ip, local_path=d)

    def _finish_migration(dom, dest_ip, remote_snapshots, remote_tmp_info):
        logging.info(remote_tmp_info)
        rpcapi.finish_migration(dest_ip=dest_ip, uuid=dom.UUIDString(),
                                snap_xmls=remote_snapshots, tmp_info=json.dumps(remote_tmp_info))
        dom.undefine()

    def _rollback(dom, local_snapshots, local_tmp_info, dest_ip, destination_json, remote_tmp_info):
        flags = 0
        flags |= libvirt.VIR_DOMAIN_SNAPSHOT_CREATE_ATOMIC
        flags |= libvirt.VIR_DOMAIN_SNAPSHOT_CREATE_REDEFINE

        migration.block_commit(dom, local_tmp_info)
        for snap_xml in local_snapshots:
            dom.snapshotCreateXML(snap_xml, flags)
        rpcapi.revert_migration(dest_ip, dom.UUIDString(), json.dumps(destination_json), json.dumps(remote_tmp_info))

    def func(conn, opaque):
        dom_id = opaque['dom_id']
        dest_ip = opaque['destination']
        postcopy = opaque['postcopy']
        destination_json = opaque['destination_json']
        local_snapshots = []
        remote_snapshots = []
        local_tmp_info = {}
        remote_tmp_info = {}

        dom = conn.lookupByUUIDString(dom_id)
        if dom is None:
            err_msg = 'domain %s is not found' % dom_id
            logging.error(err_msg)
            raise virt_agent_exception.VirtAgentInvalidException(err_msg)

        try:
            migration.check_can_migrate(opaque)
            local_snapshots, remote_snapshots, memory_snapshots = _backup_delete_snapshots(dom, destination_json)
            '''
                save dom info before snapshot
            '''
            dom_info = xml_util.XmlManagerDomain()
            dom_info.parse(GetDomainXMLRoot(dom))
            local_tmp_info = _check_create_tmp_snapshot(dom)
            _check_copy_images(dom, dom_info, dest_ip, destination_json, memory_snapshots)
            remote_tmp_info = _check_prepare_migration(dom, dest_ip, destination_json, local_tmp_info)
            _migrate(conn, dom, dest_ip, postcopy, destination_json, remote_tmp_info)
            _finish_migration(dom, dest_ip, remote_snapshots, remote_tmp_info)
        except virt_agent_exception.VirtAgentException:
            logging.error(traceback.format_exc())
            _rollback(dom, local_snapshots, local_tmp_info,
                      dest_ip, destination_json, remote_tmp_info)
            raise

    virt_agentd.WORKER.add_job(
        worker_job.JobType.LIBVIRT_DOMAIN_MIGRATE_MONITOR,
        opaque=opaque,
        need_notify=False)

    return LibvirtJobRun(opaque['connection_pool'], func, opaque)


def DomainMigrateMonitor(opaque, job=None):
    def _get_job_info(dom):
        info = None
        finished = False
        _percent = 0
        try:
            info = dom.jobStats()
            ''' Update progress only if current percent > previous percent '''
            if info is not None and info['type'] != libvirt.VIR_DOMAIN_JOB_NONE:
                if info['data_total'] != 0:
                    _percent = info['data_processed'] * 100 / info['data_total']
                if _percent > job.get_process():
                    job.set_process(_percent)
                if info['data_processed'] == info['data_total']:
                    finished = True
            ''' logging.info('[%.2f%%] %s' % (_percent, info)) '''
        except libvirt.libvirtError as ex:
            logging.info("Failed to get job info: %s", ex.get_error_message())
        return info, finished

    def func(conn, opaque):
        timeout = opaque['timeout']
        dom_id = opaque['dom_id']
        dom = conn.lookupByUUIDString(dom_id)
        if dom is None:
            err_msg = 'domain %s is not found' % dom_id
            logging.error(err_msg)
            raise virt_agent_exception.VirtAgentInvalidException(err_msg)

        start = time.time()
        while True:
            info, finished = _get_job_info(dom)
            if finished:
                break
            if info['type'] == libvirt.VIR_DOMAIN_JOB_NONE:
                pass
            elif info['type'] == libvirt.VIR_DOMAIN_JOB_UNBOUNDED:
                ''' suspend after timeout '''
                logging.info("Migration of domain %s is in progress", opaque['dom_id'])
                if (time.time() - start) > timeout:
                    dom.suspend()
                    logging.info("Migration of domain %s is timeout", opaque['dom_id'])
                    break
            elif info['type'] == libvirt.VIR_DOMAIN_JOB_COMPLETED:
                logging.info("Migration of domain %s is completed", opaque['dom_id'])
                break
            elif info['type'] == libvirt.VIR_DOMAIN_JOB_FAILED:
                logging.error("Migration of domain %s is failed", opaque['dom_id'])
                break
            else:
                logging.warning("Unexpected migration job type: %d",
                                info['type'])
            time.sleep(0.5)

    return LibvirtJobRun(opaque['connection_pool'], func, opaque)


def PrepareMigration(opaque):
    '''tmp_info:
       {
           'vda': {
               'base': '/vms/images/b_1.img',
               'tmp': '/vms/images/tmp_1',
           },
           'vdb': {
               'base': '/vms/images/b_2.img',
               'tmp': '/vms/images/tmp_2',
           }
       }
    '''
    live = opaque['live']
    destination_json = opaque['destination_json']
    tmp_info = opaque['tmp_info']

    index = 1
    for disk in destination_json['devices']['disk']:
        migration.rebase_images(disk)
        if live:
            cmd = envoy.run('%s info %s --output=json' % (utils.BIN_QEMU_IMG, disk['properties']['source']))
            if cmd.std_err != '':
                logging.error("Prepare migration failed: %s" % cmd.std_err)
                raise virt_agent_exception.VirtAgentException(err_msg=cmd.std_err)
            disk_info = json.loads(cmd.std_out)
            create_cmd = '%s create -f %s -b %s %s ' % (utils.BIN_QEMU_IMG,
                                                        disk_info['format'],
                                                        disk['properties']['source'],
                                                        tmp_info[disk['dev']]['tmp'])
            cmd = envoy.run(create_cmd)
            index = index + 1
            if cmd.std_err != '':
                logging.error("Prepare migration failed: %s" % cmd.std_err)
                raise virt_agent_exception.VirtAgentException(err_msg=cmd.std_err)


def PrecheckMigration(opaque):
    migration.check_can_migrate(opaque)


def FinishMigration(opaque, job):
    connection_pool = opaque['connection_pool']
    uuid = opaque['dom_id']
    snap_xmls = opaque['snap_xmls']
    tmp_info = opaque['tmp_info']

    try:
        conn = connection_pool.get()
        if conn is None:
            logging.error('failed to get libvirt connection')
            raise virt_agent_exception.VirtAgentLibvirtException('failed to get libvirt connection')
        dom = conn.lookupByUUIDString(uuid)
        migration.block_commit(dom, tmp_info)

        snap_flags = 0
        snap_flags |= libvirt.VIR_DOMAIN_SNAPSHOT_CREATE_ATOMIC
        snap_flags |= libvirt.VIR_DOMAIN_SNAPSHOT_CREATE_REDEFINE
        for snap_xml in snap_xmls:
            snap_info = xml_util.XmlManagerDomainSnapshot()
            snap_info.parse(snap_info.to_xml_tree(snap_xml))
            if snap_info.active == '1':
                snap_flags |= libvirt.VIR_DOMAIN_SNAPSHOT_CREATE_CURRENT
            dom.snapshotCreateXML(snap_xml, snap_flags)
    except libvirt.libvirtError as e:
        logging.error(traceback.format_exc())
        raise virt_agent_exception.VirtAgentLibvirtException(e)
    finally:
        if conn:
            connection_pool.put(conn)
    return


def RevertMigration(opaque):
    connection_pool = opaque['connection_pool']
    uuid = opaque['dom_id']
    destination_json = opaque['destination_json']
    tmp_info = opaque['tmp_info']

    try:
        conn = connection_pool.get()
        if conn is None:
            logging.error('failed to get libvirt connection')
            raise virt_agent_exception.VirtAgentLibvirtException('failed to get libvirt connection')
        dom = conn.lookupByUUIDString(uuid)
        # Delete snapshot metadatas
        for snap_name in dom.snapshotListNames():
            snap = dom.snapshotLookupByName(snap_name)
            snap.delete(flags=libvirt.VIR_DOMAIN_SNAPSHOT_DELETE_METADATA_ONLY)
        # Delete domain
        if dom.isActive():
            dom.destroy()
        dom.undefine()
        # Delete disks
        for disk in destination_json['disk']:
            envoy.run('rm -f %s' % disk['properties']['source'])
        # Remove tmp image
        for info in tmp_info.values():
            envoy.run('rm -f %s' % info['tmp'])
        ''' TODO: Delete memory-snapshot file '''

    except libvirt.libvirtError as e:
        logging.error('Revert migration failed, %s', e.get_error_message())
    finally:
        if conn:
            connection_pool.put(conn)

    return


def DomainSnapshotCreate(opaque, job=None):
    '''
    dom_id: UUID of domain
    snapshot_name: snapshot name to be created
    live_snapshot: for an active domain,
                   if live_snapshot is True, a full-system snapshot will be created, including disk internal snapshot
                   and memory external snapshot.
                   if live_snapshot is False, a diskonly snapshot will be created, including disk internal snapshot.
    connection_pool: libvirt connection pool.
    '''
    def func(conn, opaque):
        dom_id = opaque['dom_id']
        snapshot_name = opaque['snapshot_name']
        live_snapshot = opaque['live_snapshot']
        snapshot_flag = libvirt.VIR_DOMAIN_SNAPSHOT_CREATE_ATOMIC

        logging.debug('domain: %s snapshot: %s type: %s' % (dom_id, snapshot_name, live_snapshot))

        dom = conn.lookupByUUIDString(dom_id)

        if dom.isActive():
            logging.info('online snapshot. domain %s' % (dom.name()))
            if live_snapshot:
                snap_xml = _BuildSnapshotXML(dom, snapshot_name, SnapshotType.ONLINE_SNAPSHOT_FULL_SYSTEM)
                snapshot_flag |= libvirt.VIR_DOMAIN_SNAPSHOT_CREATE_LIVE
            else:
                snap_xml = _BuildSnapshotXML(dom, snapshot_name, SnapshotType.ONLINE_SNAPSHOT_DISK_INTERNAL)
            logging.info(snap_xml)
        else:
            logging.info('offline snapshot. domain %s' % (dom.name()))
            snap_xml = _BuildSnapshotXML(dom, snapshot_name, SnapshotType.OFFLINE_SNAPSHOT)
            logging.info(snap_xml)
            if live_snapshot:
                logging.warning('ignore live_snapshot flag for inactive domain')

        job.set_process(20)
        dom.snapshotCreateXML(snap_xml, snapshot_flag)
        job.set_process(80)

    return LibvirtJobRun(opaque['connection_pool'], func, opaque)


def DomainSnapshotDelete(opaque, job=None):
    '''
    dom_id: UUID of domain
    snapshot_names: snapshot name to be created
    connection_pool: libvirt connection pool.
    '''
    def func(conn, opaque):
        dom_id = opaque['dom_id']
        snapshot_names = opaque['snapshot_names']

        logging.debug('domain: %s snapshot: %s' % (dom_id, snapshot_names))

        dom = conn.lookupByUUIDString(dom_id)
        dom_snap_names = dom.snapshotListNames()
        for snapshot_name in snapshot_names:
            if snapshot_name not in dom_snap_names:
                err_msg = 'invalid snapshot name'
                logging.error(err_msg)
                raise virt_agent_exception.VirtAgentInvalidException(err_msg)
        job.set_process(20)
        for snapshot_name in snapshot_names:
            snap = dom.snapshotLookupByName(snapshot_name)
            snap.delete()
        job.set_process(80)

    return LibvirtJobRun(opaque['connection_pool'], func, opaque)


def DomainSnapshotList(opaque):
    '''
    dom_ids: UUID list of domain, if dom_ids is empty, check all
    connection_pool: libvirt connection pool.
    '''
    def func(conn, opaque):
        dom_ids = opaque['dom_ids']
        snap_list = []

        logging.debug('domains: %s' % (dom_ids))

        if not len(dom_ids):
            # get all domain if dom_ids is empty
            for dom in conn.listAllDomains():
                dom_ids.append(dom.UUIDString())

        for dom_id in dom_ids:
            snap_info = {}
            dom = conn.lookupByUUIDString(dom_id)
            snap_info['domain_uuid'] = dom.UUIDString()
            snap_info_list = []
            snap_info['snap_info'] = snap_info_list
            for snap_name in dom.snapshotListNames():
                snap = dom.snapshotLookupByName(snap_name)
                snap_detail = {}
                snap_detail['name'] = snap_name
                snap_detail['current'] = snap.isCurrent()
                snap_xml = etree.XML(snap.getXMLDesc())
                snap_detail['state'] = snap_xml.findtext('./state[1]')
                snap_detail['parent'] = snap_xml.findtext('./parent[1]/name[1]')
                snap_detail['create_time'] = snap_xml.findtext('./creationTime[1]')
                snap_info_list.append(snap_detail)

            snap_list.append(json.dumps(snap_info))

        logging.debug(snap_list)
        return snap_list

    return LibvirtJobRun(opaque['connection_pool'], func, opaque)


def DomainSnapshotRevert(opaque):
    '''
    dom_id: UUID of domain
    snapshot_name: snapshot name to be created
    connection_pool: libvirt connection pool.
    '''
    def func(conn, opaque):
        dom_id = opaque['dom_id']
        snapshot_name = opaque['snapshot_name']

        logging.debug('domain: %s snapshot: %s' % (dom_id, snapshot_name))

        dom = conn.lookupByUUIDString(dom_id)
        if snapshot_name not in dom.snapshotListNames():
            err_msg = 'invalid snapshot name'
            logging.error(err_msg)
            raise virt_agent_exception.VirtAgentInvalidException(err_msg)

        snap = dom.snapshotLookupByName(snapshot_name)
        dom.revertToSnapshot(snap)

    return LibvirtJobRun(opaque['connection_pool'], func, opaque)
