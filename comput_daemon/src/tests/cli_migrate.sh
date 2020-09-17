#!/bin/bash
xml="
<domain type='kvm'>
  <name>test_2a32b91c-46a3-41ee-a709-8a5c2a0c4b2b</name>
  <uuid>2a32b91c-46a3-41ee-a709-8a5c2a0c4b2b</uuid>
  <title>test_domain_title</title>
  <metadata/>
  <memory unit='KiB'>2048000</memory>
  <currentMemory unit='KiB'>2048000</currentMemory>
  <vcpu placement='static'>1</vcpu>
  <resource>
    <partition>/machine</partition>
  </resource>
  <os>
    <type arch='x86_64' machine='pc-i440fx-4.0'>hvm</type>
    <boot dev='cdrom'/>
    <boot dev='hd'/>
    <boot dev='network'/>
  </os>
  <features>
    <acpi/>
    <apic/>
    <pae/>
    <hap state='on'/>
  </features>
  <cpu>
    <topology sockets='1' cores='1' threads='1'/>
  </cpu>
  <clock offset='localtime'/>
  <on_poweroff>destroy</on_poweroff>
  <on_reboot>restart</on_reboot>
  <on_crash>destroy</on_crash>
  <pm>
    <suspend-to-mem enabled='no'/>
    <suspend-to-disk enabled='no'/>
  </pm>
  <devices>
    <emulator>/usr/bin/qemu-system-x86_64</emulator>
    <disk type='file' device='disk'>
      <driver name='qemu' type='qcow2'/>
      <source file='/vms/images/test_2a32b91c-46a3-41ee-a709-8a5c2a0c4b2b.qcow2'/>
      <target dev='vda' bus='virtio'/>
      <address type='pci' domain='0x0000' bus='0x00' slot='0x07' function='0x0'/>
    </disk>
    <disk type='file' device='disk'>
      <driver name='qemu' type='qcow2'/>
      <source file='/vms/images/test_2a32b91c-46a3-41ee-a709-8a5c2a0c4b2b_2.qcow2'/>
      <target dev='vdb' bus='virtio'/>
      <address type='pci' domain='0x0000' bus='0x00' slot='0x0a' function='0x0'/>
    </disk>
    <controller type='usb' index='0' model='piix3-uhci'>
      <alias name='usb'/>
      <address type='pci' domain='0x0000' bus='0x00' slot='0x01' function='0x2'/>
    </controller>
    <controller type='usb' index='1' model='ehci'>
      <alias name='usb1'/>
      <address type='pci' domain='0x0000' bus='0x00' slot='0x03' function='0x0'/>
    </controller>
    <controller type='usb' index='2' model='nec-xhci'>
      <alias name='usb2'/>
      <address type='pci' domain='0x0000' bus='0x00' slot='0x04' function='0x0'/>
    </controller>
    <controller type='ide' index='0'>
      <alias name='ide'/>
      <address type='pci' domain='0x0000' bus='0x00' slot='0x01' function='0x1'/>
    </controller>
    <controller type='pci' index='0' model='pci-root'>
      <alias name='pci.0'/>
    </controller>
    <controller type='pci' index='1' model='pci-bridge'>
      <model name='pci-bridge'/>
      <target chassisNr='1'/>
      <alias name='pci.1'/>
      <address type='pci' domain='0x0000' bus='0x00' slot='0x1f' function='0x0'/>
    </controller>
    <controller type='scsi' index='0' model='virtio-scsi'>
      <alias name='scsi0'/>
      <address type='pci' domain='0x0000' bus='0x00' slot='0x05' function='0x0'/>
    </controller>
    <interface type='bridge'>
      <mac address='52:54:00:c4:d3:b2'/>
      <source bridge='vs1'/>
      <target dev='vnet0'/>
      <model type='virtio'/>
      <driver name='vhost'/>
      <address type='pci' domain='0x0000' bus='0x00' slot='0x06' function='0x0'/>
    </interface>
    <serial type='pty'>
      <source path='/dev/pts/4'/>
      <target type='isa-serial' port='0'>
        <model name='isa-serial'/>
      </target>
      <alias name='serial0'/>
    </serial>
    <console type='pty' tty='/dev/pts/4'>
      <source path='/dev/pts/4'/>
      <target type='serial' port='0'/>
      <alias name='serial0'/>
    </console>
    <input type='mouse' bus='ps2'>
      <alias name='input0'/>
    </input>
    <input type='keyboard' bus='ps2'>
      <alias name='input1'/>
    </input>
    <input type='tablet' bus='usb'>
      <alias name='input2'/>
      <address type='usb' bus='0' port='2'/>
    </input>
    <graphics type='vnc' port='5901' autoport='yes' listen='0.0.0.0'>
      <listen type='address' address='0.0.0.0'/>
    </graphics>
    <video>
      <model type='virtio' vram='65536' heads='1' primary='yes'/>
      <alias name='video0'/>
      <address type='pci' domain='0x0000' bus='0x00' slot='0x02' function='0x0'/>
    </video>
    <hub type='usb'>
      <alias name='hub0'/>
      <address type='usb' bus='0' port='1'/>
    </hub>
    <memballoon model='virtio'>
      <alias name='balloon0'/>
      <address type='pci' domain='0x0000' bus='0x00' slot='0x08' function='0x0'/>
    </memballoon>
  </devices>
  <seclabel type='dynamic' model='dac' relabel='yes'>
    <label>+0:+0</label>
    <imagelabel>+0:+0</imagelabel>
  </seclabel>
</domain>
"

function T1() {
    echo "---------------------------------------------"
    echo "在线迁移主机和存储, 两块磁盘，包括内存快照, 磁盘快照, base镜像(同一路径)"
    echo "---------------------------------------------"
    live_env
    backingfile
    snapshot
    migrate_base
}

function T2() {
    echo "---------------------------------------------"
    echo "virsh在线迁移主机和存储, 两块磁盘，包括base镜像(同一路径)"
    echo "---------------------------------------------"
    live_env
    backingfile
    virsh dumpxml test_2a32b91c-46a3-41ee-a709-8a5c2a0c4b2b >/tmp/t3.xml
    virsh migrate test_2a32b91c-46a3-41ee-a709-8a5c2a0c4b2b qemu+ssh://bogon/system --live --copy-storage-inc --verbose  --xml /tmp/t3.xml
}

function T3() {
    echo "---------------------------------------------"
    echo "在线迁移主机和存储, 两块磁盘，包括内存快照, 磁盘快照, base镜像(任意路径)"
    echo "---------------------------------------------"
    live_env
    backingfile
    snapshot
    migrate_base_change_path
}

function T4() {
    echo "---------------------------------------------"
    echo "离线迁移主机和存储, 两块磁盘，包括内存快照, 磁盘快照, base镜像(任意路径)"
    echo "---------------------------------------------"
    offline_env
    backingfile
    snapshot
    migrate_base
}

function T5() {
    echo "---------------------------------------------"
    echo "在线迁移CentOS主机和存储, 包括多个内存快照, 磁盘快照,raw格式base，scsi设备，base镜像(任意)"
    echo "---------------------------------------------"
    centos_env 
    backingfile_centos
    snapshot_centos
    #migrate_centos
    migrate_base_change_path_centos
}

function snapshot_centos(){
    # do ssh echo t > t.txt
    # ip=`virsh domifaddr centos7|grep 192 |awk -F' ' '{ print $4 }'|awk -F'/' '{ print $1 }'`
    # ssh-copy-id root@$ip
    # ssh root@$ip "echo t> t.txt"
    snapshot_live
    snapshot_diskonly
}

function snapshot_live(){
    uuid=`virsh domuuid centos7`
    virt_agent_cli snapshot-create -d $uuid --snapshot_type live --snapshot_name sn1_live
    virt_agent_cli snapshot-create -d $uuid --snapshot_type live --snapshot_name sn2_live
    virt_agent_cli snapshot-create -d $uuid --snapshot_type live --snapshot_name sn3_live
    virt_agent_cli snapshot-create -d $uuid --snapshot_type live --snapshot_name sn4_live
}

function snapshot_diskonly(){
    uuid=`virsh domuuid centos7`
    virt_agent_cli snapshot-create -d $uuid --snapshot_type diskonly --snapshot_name sn1_diskonly
    virt_agent_cli snapshot-create -d $uuid --snapshot_type diskonly --snapshot_name sn2_diskonly
    virt_agent_cli snapshot-create -d $uuid --snapshot_type diskonly --snapshot_name sn3_diskonly
    virt_agent_cli snapshot-create -d $uuid --snapshot_type diskonly --snapshot_name sn4_diskonly
}

function backingfile_centos() {
    virsh snapshot-create-as  centos7  --disk-only base1 --no-metadata
    virsh snapshot-create-as  centos7  --disk-only top --no-metadata
}

function migrate_base_change_path_centos() {
    uuid=`virsh domuuid centos7`
    virt_agent_cli migrate -d $uuid --time_out 300 --postcopy true  --destination test_migration_host --destination_json '''{
    "devices": {
            "disk":[
            {
                "dev":"sda",
                "properties":{
                    "source":"/vms/images/centos7.top"
                },
                "migrate_backingfiles": [
                {
                    "filename": "/vms/images/centos7.qcow2",
                    "dst_filename": "/vms/images/centos7.qcow2"
                },
                {
                    "filename": "/vms/images/centos7.base1",
                    "dst_filename": "/vms/images/centos7.base1"
                },
                {
                    "filename": "/vms/images/centos7.raw",
                    "dst_filename": "/vms/images/centos7.raw"
                }]
            },
            {
                "dev":"vda",
                "properties":{
                    "source":"/var/lib/libvirt/images/centos7_2.top"
                },
                "migrate_backingfiles": [
                {
                    "filename": "/vms/images/centos7_2.qcow2",
                    "dst_filename": "/var/lib/libvirt/images/centos7_2.qcow2"
                },
                {
                    "filename": "/vms/images/centos7_2.base1",
                    "dst_filename": "/var/lib/libvirt/images/centos7_2.base1"
                }]
            }]
        }
    }'''
}
function define(){
    echo $xml > /tmp/t_migration.xml
    virsh define /tmp/t_migration.xml >/dev/null 2>&1
    rm -f /tmp/t_migration.xml
}

function create_image(){
    qemu-img create -f qcow2 /vms/images/test_2a32b91c-46a3-41ee-a709-8a5c2a0c4b2b.qcow2 1M >/dev/null 2>&1
    qemu-img create -f qcow2 /vms/images/test_2a32b91c-46a3-41ee-a709-8a5c2a0c4b2b_2.qcow2 1M >/dev/null 2>&1
}

function start() {
    virsh start test_2a32b91c-46a3-41ee-a709-8a5c2a0c4b2b >/dev/null 2>&1
}

function snapshot() {
    virt_agent_cli snapshot-create -d 2a32b91c-46a3-41ee-a709-8a5c2a0c4b2b  --snapshot_type live --snapshot_name sn1_live
    virt_agent_cli snapshot-create -d 2a32b91c-46a3-41ee-a709-8a5c2a0c4b2b  --snapshot_type diskonly --snapshot_name sn2_diskonly
}

function backingfile() {
    virsh snapshot-create-as  2a32b91c-46a3-41ee-a709-8a5c2a0c4b2b  --disk-only base1 --no-metadata
    virsh snapshot-create-as  2a32b91c-46a3-41ee-a709-8a5c2a0c4b2b  --disk-only top --no-metadata
}

function snapshot_offline() {
    virt_agent_cli snapshot-create -d 2a32b91c-46a3-41ee-a709-8a5c2a0c4b2b  --snapshot_type diskonly --snapshot_name sn1_diskonly
}

function migrate() {
    virt_agent_cli migrate -d 2a32b91c-46a3-41ee-a709-8a5c2a0c4b2b --time_out 300 --postcopy true  --destination test_migration_host --destination_json '''{
    "devices": {
        "disk":[
        {
            "dev":"vda",
            "properties":{
                "source":"/vms/images/test_2a32b91c-46a3-41ee-a709-8a5c2a0c4b2b.qcow2"
            }
        }, 
        {
            "dev":"vdb",
            "properties":{
                "source":"/vms/images/test_2a32b91c-46a3-41ee-a709-8a5c2a0c4b2b_2.qcow2"
            }
        }
        ]
   }
}'''
}

function migrate_centos() {
    uuid=`virsh domuuid centos7`
    virt_agent_cli migrate -d $uuid --time_out 300 --postcopy true  --destination test_migration_host --destination_json '''{
    "devices": {
        "disk":[
        {
            "dev":"vda",
            "properties":{
                "source":"/vms/images/centos7.qcow2"
            }
        }
        ]
   }
}'''
}

function migrate_base_change_path() {
    virt_agent_cli migrate -d 2a32b91c-46a3-41ee-a709-8a5c2a0c4b2b --time_out 300 --postcopy true  --destination test_migration_host --destination_json '''{
    "devices": {
            "disk":[
            {
                "dev":"vda",
                "properties":{
                    "source":"/vms/images/test_2a32b91c-46a3-41ee-a709-8a5c2a0c4b2b.top"
                },
                "migrate_backingfiles": [
                {
                    "filename": "/vms/images/test_2a32b91c-46a3-41ee-a709-8a5c2a0c4b2b.qcow2",
                    "dst_filename": "/vms/images/test_2a32b91c-46a3-41ee-a709-8a5c2a0c4b2b.qcow2"
                },
                {
                    "filename": "/vms/images/test_2a32b91c-46a3-41ee-a709-8a5c2a0c4b2b.base1",
                    "dst_filename": "/vms/images/test_2a32b91c-46a3-41ee-a709-8a5c2a0c4b2b.base1"
                }]
            },
            {
                "dev":"vdb",
                "properties":{
                    "source":"/var/lib/libvirt/images/test_2a32b91c-46a3-41ee-a709-8a5c2a0c4b2b_2.top"
                },
                "migrate_backingfiles": [
                {
                    "filename": "/vms/images/test_2a32b91c-46a3-41ee-a709-8a5c2a0c4b2b_2.qcow2",
                    "dst_filename": "/var/lib/libvirt/images/test_2a32b91c-46a3-41ee-a709-8a5c2a0c4b2b_2.qcow2"
                },
                {
                    "filename": "/vms/images/test_2a32b91c-46a3-41ee-a709-8a5c2a0c4b2b_2.base1",
                    "dst_filename": "/var/lib/libvirt/images/test_2a32b91c-46a3-41ee-a709-8a5c2a0c4b2b_2.base1"
                }]
            }]
        }
    }'''
}

function migrate_base() {
    virt_agent_cli migrate -d 2a32b91c-46a3-41ee-a709-8a5c2a0c4b2b --time_out 300 --postcopy true  --destination test_migration_host --destination_json '''{
    "devices": {
            "disk":[
            {
                "dev":"vda",
                "properties":{
                    "source":"/vms/images/test_2a32b91c-46a3-41ee-a709-8a5c2a0c4b2b.top"
                },
                "migrate_backingfiles": [
                {
                    "filename": "/vms/images/test_2a32b91c-46a3-41ee-a709-8a5c2a0c4b2b.qcow2",
                    "dst_filename": "/vms/images/test_2a32b91c-46a3-41ee-a709-8a5c2a0c4b2b.qcow2"
                },
                {
                    "filename": "/vms/images/test_2a32b91c-46a3-41ee-a709-8a5c2a0c4b2b.base1",
                    "dst_filename": "/vms/images/test_2a32b91c-46a3-41ee-a709-8a5c2a0c4b2b.base1"
                }]
            },
            {
                "dev":"vdb",
                "properties":{
                    "source":"/vms/images/test_2a32b91c-46a3-41ee-a709-8a5c2a0c4b2b_2.top"
                },
                "migrate_backingfiles": [
                {
                    "filename": "/vms/images/test_2a32b91c-46a3-41ee-a709-8a5c2a0c4b2b_2.qcow2",
                    "dst_filename": "/vms/images/test_2a32b91c-46a3-41ee-a709-8a5c2a0c4b2b_2.qcow2"
                },
                {
                    "filename": "/vms/images/test_2a32b91c-46a3-41ee-a709-8a5c2a0c4b2b_2.base1",
                    "dst_filename": "/vms/images/test_2a32b91c-46a3-41ee-a709-8a5c2a0c4b2b_2.base1"
                }]
            }]
        }
    }'''
}

function live_env() {
    clean
    define
    create_image
    start
}

function offline_env() {
    clean
    define
    create_image
}

function centos_env() {
    clean
    cp -f /root/centos7.raw /vms/images
    qemu-img create -f qcow2 -b /vms/images/centos7.raw /vms/images/centos7.qcow2
    qemu-img create -f qcow2 /vms/images/centos7_2.qcow2 1G
    virsh define ~/centos.xml
    virsh start centos7
}

function clean() {
    ssh root@test_migration_host  /root/cleandomains.sh >/dev/null 2>&1
    /root/cleandomains.sh >/dev/null 2>&1
}

function main() {
    case $1 in
        1)
            T1
            ;;
        2)
            T2
            ;;
        3)
            T3
            ;;
        4)
            T4
            ;;
        5)
            T5
            ;;
        all)
            T1
            T2
            T3
            T4
            T5
            ;;
        clean)
            clean
            ;;
        live)
            live_env
            ;;
        offline)
            offline_env
            ;;
        centos)
            centos_env
            ;;
        snapshot)
            snapshot
            ;;
        snapshot-offline)
            snapshot_offline
            ;;
        backingfile)
            backingfile
            ;;
        migrate)
            migrate
            ;;
        migrate-base)
            migrate_base
            ;;
        migrate-centos)
            migrate_centos
            ;;
        migrate-base-centos)
            migrate_base_change_path_centos
            ;;
        backingfile-centos)
            backingfile_centos
            ;;
        snapshot-centos)
            snapshot_centos
            ;;
        snapshot-live)
            snapshot_live
            ;;
        snapshot-diskonly)
            snapshot_diskonly
            ;;
        -h|--help|help)
            echo "Usage: cli.sh [ 1|2|3|all|clean|live|offline|snapshot|backingfile|snapshot-offline|migrate|migrate-base|snapshot-centos|snapshot-live|snapshot-diskonly|migrate-centos|backingfile-centos|migrate-base-centos ]"
            ;;
        *)
            T1
            ;;
    esac
}

main $@
