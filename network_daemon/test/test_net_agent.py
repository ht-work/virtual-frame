from __future__ import print_function
import logging
import grpc
import json
import paramiko

logging.basicConfig(level=logging.INFO)

from net_agent import NicManager_pb2
from net_agent import NicManager_pb2_grpc
from net_agent import OvsManager_pb2
from net_agent import OvsManager_pb2_grpc
from net_agent import UpLinkManager_pb2
from net_agent import UpLinkManager_pb2_grpc
from net_agent import AclManager_pb2
from net_agent import AclManager_pb2_grpc
from net_agent import QosManager_pb2
from net_agent import QosManager_pb2_grpc
from net_agent import ErrNo_pb2
from net_agent import net_agent_util as util
from net_agent import net_agentd_exception

'''
Before performing the test, you must ensure that the environment of the machine under test meets the requirements.
The following items are needed:
machine_ip:  This is the IP address of the machine being tested.
machine_user:  This is the user name of the machine being tested.
machine_passwd:  This is the user password of the machine being tested.
phy_nic_1:  This is the phyical NIC of the machine being tested.
phy_nic_2:  This is another phyical NIC of the machine being tested.

Because need to test link aggregation, so must have two free physical NICs.

In addition, the test process needs to remotely log in to the test machine through ssh,
so the machine_user and machine_passwd are also required.
'''
machine_ip = "192.168.15.12"
machine_user = "root"
machine_passwd = "1q2w3e"

phy_nic_1 = "enp0s8"
phy_nic_2 = "enp0s9"

virtual_nic_1 = "tap0"


def login_remote_machine(ip, user, passwd):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ip, 22, user, passwd)

    return ssh


def execute_remote_machine_cmd(ssh, cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    if stderr.read().decode() != "":
        raise net_agentd_exception.NetAgentException("execute_remote_machine_cmd %s failed", cmd)
    else:
        return stdout.read().decode()


def quit_remote_machine(ssh):
    ssh.close()


class TestNicManager(object):
    channel = None
    nic_stub = None
    nic = phy_nic_1

    if nic == "":
        raise net_agentd_exception.NetAgentException("nic is null")

    @classmethod
    def setup_class(cls):
        try:
            conf = util.ExternalConfig('../net_agent.cfg')
            port = conf.ConfigGet('global', 'port')
        except Exception as e:
            logging.error(e)

        cls.channel = grpc.insecure_channel(machine_ip + ':' + port)
        cls.nic_stub = NicManager_pb2_grpc.NicManagerStub(cls.channel)
        logging.info('TestNicManager@net_agent grpc channel create ok!')

    @classmethod
    def teardown_class(cls):
        cls.channel.close()
        logging.info('TestNicManager@net_agent grpc channel close ok!')

    def test_QueryNicList(self):
        response = self.nic_stub.QueryNicList(NicManager_pb2.NicListQueryRequest(
            host_name='you', nic_type=NicManager_pb2.NicListQueryRequest.ALL_PHY_NIC))
        assert response.errno == ErrNo_pb2.SYS_OK

        response = self.nic_stub.QueryNicList(NicManager_pb2.NicListQueryRequest(
            host_name='you', nic_type=NicManager_pb2.NicListQueryRequest.FREE_PHY_NIC))
        assert response.errno == ErrNo_pb2.SYS_OK

        response = self.nic_stub.QueryNicList(NicManager_pb2.NicListQueryRequest(
            host_name='you', nic_type=NicManager_pb2.NicListQueryRequest.VIRTUAL_NIC))
        assert response.errno == ErrNo_pb2.SYS_OK

    def test_QueryNicInfo(self):
        response = self.nic_stub.QueryNicInfo(NicManager_pb2.NicInfoQueryRequest(nic_names=[self.nic]))
        assert response.nic_infos[0].errno == ErrNo_pb2.SYS_OK

    def test_QueryPacketStat(self):
        query_nic_info_response = self.nic_stub.QueryNicInfo(NicManager_pb2.NicInfoQueryRequest(nic_names=[self.nic]))
        mac_addr = query_nic_info_response.nic_infos[0].mac_address
        response = self.nic_stub.QueryPacketStat(NicManager_pb2.PacketStatQueryRequest(mac_addrs=[mac_addr]))
        assert response.packet_stats[0].errno == ErrNo_pb2.SYS_OK

        response = self.nic_stub.QueryPacketStat(NicManager_pb2.PacketStatQueryRequest(
            mac_addrs=["Z6:33:db:0f:e0:4c"]))
        assert response.packet_stats[0].errno == ErrNo_pb2.SYS_FAIL

    def test_ModifyNic(self):
        query_nic_info_response = self.nic_stub.QueryNicInfo(NicManager_pb2.NicInfoQueryRequest(nic_names=[self.nic]))
        driver_name = query_nic_info_response.nic_infos[0].driver_name
        mtu = "1899"
        response = self.nic_stub.ModifyNic(NicManager_pb2.NicModifyRequest(
            nic_name=self.nic, driver_name=driver_name, mtu=mtu))
        assert response.errno == ErrNo_pb2.SYS_OK

    def test_StartNic(self):
        response = self.nic_stub.StartNic(NicManager_pb2.NicModifyRequest(nic_name=self.nic))
        assert response.errno == ErrNo_pb2.SYS_OK

    def test_StopNic(self):
        response = self.nic_stub.StopNic(NicManager_pb2.NicModifyRequest(nic_name=self.nic))
        assert response.errno == ErrNo_pb2.SYS_OK


class TestOtherManager(object):
    channel = None
    ovs_stub = None
    uplink_stub = None
    uplink_nic_1 = phy_nic_1
    uplink_nic_2 = phy_nic_2
    switch_name = "test_other"

    @classmethod
    def create_default_vswitch(cls):
        vswitch_conf = OvsManager_pb2.vSwitchConf()
        vswitch_conf.vswitch_name = cls.switch_name
        vswitch_conf.mode = OvsManager_pb2.vSwitchConf.VEB
        vswitch_conf.is_multicast = False

        response = cls.ovs_stub.AddvSwitch(OvsManager_pb2.vSwitchAddRequest(vswitch_conf=vswitch_conf))

        if response == ErrNo_pb2.SYS_FAIL:
            raise net_agentd_exception.NetAgentException("create default vswitch failed")

    @classmethod
    def destroy_default_vswitch(cls):
        response = cls.ovs_stub.DelvSwitch(OvsManager_pb2.vSwitchDelRequest(vswitch_name=cls.switch_name))
        if response == ErrNo_pb2.SYS_FAIL:
            raise net_agentd_exception.NetAgentException("del default vswitch failed")

    @classmethod
    def setup_class(cls):
        try:
            conf = util.ExternalConfig('../net_agent.cfg')
            port = conf.ConfigGet('global', 'port')
        except Exception as e:
            logging.error(e)

        cls.channel = grpc.insecure_channel(machine_ip + ':' + port)
        logging.info('TestOtherManager@net_agent grpc channel create ok!')

        cls.ovs_stub = OvsManager_pb2_grpc.OvsManagerStub(cls.channel)
        cls.uplink_stub = UpLinkManager_pb2_grpc.UpLinkManagerStub(cls.channel)

        cls.create_default_vswitch()
        logging.info('create default vswitch %s ok!' % cls.switch_name)

    @classmethod
    def teardown_class(cls):
        cls.destroy_default_vswitch()
        logging.info('del default vswitch %s ok!' % cls.switch_name)

        cls.channel.close()
        logging.info('TestOtherManager@net_agent grpc channel close ok!')

    def test_QueryvSwitchList(self):
        response = self.ovs_stub.QueryvSwitchList(OvsManager_pb2.vSwitchListQueryRequest(host_name='me'))
        logging.info('TestOtherManager:vswitch list: %s!', response.vswitch_names)
        logging.info('TestOtherManager:errno: %d!', response.errno)
        assert response.errno == ErrNo_pb2.SYS_OK

    def test_AddvSwitch_DelvSwitch(self):
        vswitch_name = "test_tmp"

        vswitch_conf = OvsManager_pb2.vSwitchConf()
        vswitch_conf.vswitch_name = vswitch_name
        vswitch_conf.mode = OvsManager_pb2.vSwitchConf.VEB
        vswitch_conf.is_multicast = False
        response = self.ovs_stub.AddvSwitch(OvsManager_pb2.vSwitchAddRequest(vswitch_conf=vswitch_conf))
        assert response.errno == ErrNo_pb2.SYS_OK

        '''repeated add same name vswitch'''
        response = self.ovs_stub.AddvSwitch(OvsManager_pb2.vSwitchAddRequest(vswitch_conf=vswitch_conf))
        assert response.errno == ErrNo_pb2.SYS_FAIL

        response = self.ovs_stub.DelvSwitch(OvsManager_pb2.vSwitchDelRequest(vswitch_name=vswitch_name))
        assert response.errno == ErrNo_pb2.SYS_OK

    def test_ModifyvSwitch(self):
        vswitch_conf = OvsManager_pb2.vSwitchConf()
        vswitch_conf.vswitch_name = self.switch_name
        vswitch_conf.mode = OvsManager_pb2.vSwitchConf.VEB
        vswitch_conf.is_multicast = True
        response = self.ovs_stub.ModifyvSwitch(OvsManager_pb2.vSwitchModifyRequest(vswitch_conf=vswitch_conf))
        assert response.errno == ErrNo_pb2.SYS_OK

    def test_QueryvSwitchInfo(self):
        response = self.ovs_stub.QueryvSwitchInfo(OvsManager_pb2.vSwitchInfoQueryRequest(
            vswitch_names=[self.switch_name]))
        logging.info('QueryvSwitchInfo:vswitch_name: %s', response.vswitch_infos[0].vswitch_conf.vswitch_name)
        logging.info('QueryvSwitchInfo:mode: %d', response.vswitch_infos[0].vswitch_conf.mode)
        logging.info('QueryvSwitchInfo:is_multicast: %d', response.vswitch_infos[0].vswitch_conf.is_multicast)
        logging.info('QueryvSwitchInfo:is_link: %d', response.vswitch_infos[0].is_link)
        logging.info('QueryvSwitchInfo:errno: %d', response.vswitch_infos[0].errno)
        assert response.vswitch_infos[0].errno == ErrNo_pb2.SYS_OK

        response = self.ovs_stub.QueryvSwitchInfo(OvsManager_pb2.vSwitchInfoQueryRequest(
            vswitch_names=[]))
        if len(response.vswitch_infos) == 0:
            assert 1

        response = self.ovs_stub.QueryvSwitchInfo(OvsManager_pb2.vSwitchInfoQueryRequest(
            vswitch_names=["fail@vswitch"]))
        if len(response.vswitch_infos) == 0:
            assert 1

    def test_SetInternalNicParam(self):
        response = self.ovs_stub.SetInternalNicParam(OvsManager_pb2.InternalNicParamSetRequest(
            vswitch_name=self.switch_name,
            internal_nic_name=self.switch_name,
            vlan="256",
            mtu="1718",
            ip_addr="192.168.25.12",
            netmask="255.255.255.0",
            gateway="192.168.25.23"))
        assert response.errno == ErrNo_pb2.SYS_OK

        response = self.ovs_stub.SetInternalNicParam(OvsManager_pb2.InternalNicParamSetRequest(
            vswitch_name=self.switch_name,
            internal_nic_name=self.switch_name,
            vlan="5000",
            mtu="1718",
            ip_addr="192.168.25.12",
            netmask="255.255.255.0",
            gateway="192.168.25.23"))
        assert response.errno == ErrNo_pb2.SYS_FAIL

        response = self.ovs_stub.SetInternalNicParam(OvsManager_pb2.InternalNicParamSetRequest(
            vswitch_name=self.switch_name,
            internal_nic_name=self.switch_name,
            vlan="256",
            mtu="10890",
            ip_addr="192.168.25.12",
            netmask="255.255.255.0",
            gateway="192.168.25.23"))
        assert response.errno == ErrNo_pb2.SYS_FAIL

        response = self.ovs_stub.SetInternalNicParam(OvsManager_pb2.InternalNicParamSetRequest(
            vswitch_name=self.switch_name,
            internal_nic_name=self.switch_name,
            vlan="256",
            mtu="1718",
            ip_addr="342.168.25.12",
            netmask="255.255.255.0",
            gateway="192.168.25.23"))
        assert response.errno == ErrNo_pb2.SYS_FAIL

        response = self.ovs_stub.SetInternalNicParam(OvsManager_pb2.InternalNicParamSetRequest(
            vswitch_name=self.switch_name,
            internal_nic_name=self.switch_name,
            vlan="256",
            mtu="1718",
            ip_addr="192.168.25.12",
            netmask="255.200.255.0",
            gateway="192.168.25.23"))
        assert response.errno == ErrNo_pb2.SYS_FAIL

        response = self.ovs_stub.SetInternalNicParam(OvsManager_pb2.InternalNicParamSetRequest(
            vswitch_name=self.switch_name,
            internal_nic_name=self.switch_name,
            vlan="256",
            mtu="1718",
            ip_addr="192.168.25.12",
            netmask="255.255.255.0",
            gateway="192.378.25.23"))
        assert response.errno == ErrNo_pb2.SYS_FAIL

    def test_ClearInternalNicParam(self):
        response = self.ovs_stub.ClearInternalNicParam(OvsManager_pb2.InternalNicParamClearRequest(
            vswitch_name=self.switch_name,
            internal_nic_name=self.switch_name))
        assert response.errno == ErrNo_pb2.SYS_OK

    def test_GetInternalNicParam(self):
        response = self.ovs_stub.GetInternalNicParam(OvsManager_pb2.InternalNicParamGetRequest(
            vswitch_name=self.switch_name,
            internal_nic_name=self.switch_name))
        logging.info('GetInternalNicParam:vswitch_name: %s', response.vswitch_name)
        logging.info('GetInternalNicParam:internal_nic_name: %s', response.internal_nic_name)
        logging.info('GetInternalNicParam:vlan: %s', response.vlan)
        logging.info('GetInternalNicParam:mtu: %s', response.mtu)
        logging.info('GetInternalNicParam:ip_addr: %s', response.ip_addr)
        logging.info('GetInternalNicParam:netmask: %s', response.netmask)
        logging.info('GetInternalNicParam:gateway: %s', response.gateway)
        logging.info('GetInternalNicParam:errno: %d', response.errno)
        assert response.errno == ErrNo_pb2.SYS_OK

    def test_AddUpLink_DelUpLink(self):
        uplink_conf = UpLinkManager_pb2.UpLinkConf()
        uplink_conf.nic_names.append(self.uplink_nic_1)
        response = self.uplink_stub.AddUpLink(UpLinkManager_pb2.UpLinkAddRequest(
            vswitch_name=self.switch_name,
            uplink_conf=uplink_conf))
        assert response.errno == ErrNo_pb2.SYS_OK

        response = self.uplink_stub.DelUpLink(UpLinkManager_pb2.UpLinkDelRequest(
            vswitch_name=self.switch_name))
        assert response.errno == ErrNo_pb2.SYS_OK

        uplink_conf = UpLinkManager_pb2.UpLinkConf()
        uplink_conf.nic_names.append(self.uplink_nic_1)
        uplink_conf.nic_names.append(self.uplink_nic_2)
        uplink_conf.bond_name = 'juhe'
        uplink_conf.lacp = True
        uplink_conf.bond_mode = UpLinkManager_pb2.UpLinkConf.BALANCE_SLB
        response = self.uplink_stub.AddUpLink(UpLinkManager_pb2.UpLinkAddRequest(
            vswitch_name=self.switch_name,
            uplink_conf=uplink_conf))
        assert response.errno == ErrNo_pb2.SYS_OK

        response = self.uplink_stub.DelUpLink(UpLinkManager_pb2.UpLinkDelRequest(
            vswitch_name=self.switch_name))
        assert response.errno == ErrNo_pb2.SYS_OK

        uplink_conf = UpLinkManager_pb2.UpLinkConf()
        uplink_conf.nic_names.append(self.uplink_nic_1)
        uplink_conf.nic_names.append(self.uplink_nic_2)
        uplink_conf.bond_name = 'juhe'
        uplink_conf.lacp = True
        uplink_conf.bond_mode = UpLinkManager_pb2.UpLinkConf.BALANCE_TCP
        response = self.uplink_stub.AddUpLink(UpLinkManager_pb2.UpLinkAddRequest(
            vswitch_name=self.switch_name,
            uplink_conf=uplink_conf))
        assert response.errno == ErrNo_pb2.SYS_OK

        response = self.uplink_stub.DelUpLink(UpLinkManager_pb2.UpLinkDelRequest(
            vswitch_name=self.switch_name))
        assert response.errno == ErrNo_pb2.SYS_OK

        uplink_conf = UpLinkManager_pb2.UpLinkConf()
        uplink_conf.nic_names.append(self.uplink_nic_1)
        uplink_conf.nic_names.append(self.uplink_nic_2)
        uplink_conf.bond_name = 'juhe'
        uplink_conf.lacp = True
        uplink_conf.bond_mode = UpLinkManager_pb2.UpLinkConf.ACTIVE_BACKUP
        response = self.uplink_stub.AddUpLink(UpLinkManager_pb2.UpLinkAddRequest(
            vswitch_name=self.switch_name,
            uplink_conf=uplink_conf))
        assert response.errno == ErrNo_pb2.SYS_FAIL

        uplink_conf = UpLinkManager_pb2.UpLinkConf()
        uplink_conf.nic_names.append(self.uplink_nic_1)
        uplink_conf.nic_names.append(self.uplink_nic_2)
        uplink_conf.bond_name = 'juhe'
        uplink_conf.lacp = False
        uplink_conf.bond_mode = UpLinkManager_pb2.UpLinkConf.ACTIVE_BACKUP
        response = self.uplink_stub.AddUpLink(UpLinkManager_pb2.UpLinkAddRequest(
            vswitch_name=self.switch_name,
            uplink_conf=uplink_conf))
        assert response.errno == ErrNo_pb2.SYS_OK

        response = self.uplink_stub.DelUpLink(UpLinkManager_pb2.UpLinkDelRequest(
            vswitch_name=self.switch_name))
        assert response.errno == ErrNo_pb2.SYS_OK

        uplink_conf = UpLinkManager_pb2.UpLinkConf()
        uplink_conf.nic_names.append(self.uplink_nic_1)
        uplink_conf.nic_names.append(self.uplink_nic_2)
        uplink_conf.bond_name = 'juhe'
        uplink_conf.lacp = False
        uplink_conf.bond_mode = UpLinkManager_pb2.UpLinkConf.BALANCE_SLB
        response = self.uplink_stub.AddUpLink(UpLinkManager_pb2.UpLinkAddRequest(
            vswitch_name=self.switch_name,
            uplink_conf=uplink_conf))
        assert response.errno == ErrNo_pb2.SYS_OK

        response = self.uplink_stub.DelUpLink(UpLinkManager_pb2.UpLinkDelRequest(
            vswitch_name=self.switch_name))
        assert response.errno == ErrNo_pb2.SYS_OK

    def test_ModifyUpLink(self):
        uplink_conf = UpLinkManager_pb2.UpLinkConf()
        uplink_conf.nic_names.append(self.uplink_nic_1)
        response = self.uplink_stub.AddUpLink(UpLinkManager_pb2.UpLinkModifyRequest(
            vswitch_name=self.switch_name,
            uplink_conf=uplink_conf))
        assert response.errno == ErrNo_pb2.SYS_OK

        uplink_conf = UpLinkManager_pb2.UpLinkConf()
        uplink_conf.nic_names.append(self.uplink_nic_1)
        uplink_conf.nic_names.append(self.uplink_nic_2)
        uplink_conf.bond_name = 'juhe'
        uplink_conf.lacp = True
        uplink_conf.bond_mode = UpLinkManager_pb2.UpLinkConf.BALANCE_SLB
        response = self.uplink_stub.ModifyUpLink(UpLinkManager_pb2.UpLinkModifyRequest(
            vswitch_name=self.switch_name,
            uplink_conf=uplink_conf))
        assert response.errno == ErrNo_pb2.SYS_OK

        uplink_conf = UpLinkManager_pb2.UpLinkConf()
        uplink_conf.nic_names.append(self.uplink_nic_1)
        uplink_conf.nic_names.append(self.uplink_nic_2)
        uplink_conf.bond_name = 'juhe'
        uplink_conf.lacp = True
        uplink_conf.bond_mode = UpLinkManager_pb2.UpLinkConf.BALANCE_TCP
        response = self.uplink_stub.ModifyUpLink(UpLinkManager_pb2.UpLinkModifyRequest(
            vswitch_name=self.switch_name,
            uplink_conf=uplink_conf))
        assert response.errno == ErrNo_pb2.SYS_OK

        uplink_conf = UpLinkManager_pb2.UpLinkConf()
        uplink_conf.nic_names.append(self.uplink_nic_1)
        uplink_conf.nic_names.append(self.uplink_nic_2)
        uplink_conf.bond_name = 'juhe'
        uplink_conf.lacp = False
        uplink_conf.bond_mode = UpLinkManager_pb2.UpLinkConf.ACTIVE_BACKUP
        response = self.uplink_stub.ModifyUpLink(UpLinkManager_pb2.UpLinkModifyRequest(
            vswitch_name=self.switch_name,
            uplink_conf=uplink_conf))
        assert response.errno == ErrNo_pb2.SYS_OK

        uplink_conf = UpLinkManager_pb2.UpLinkConf()
        uplink_conf.nic_names.append(self.uplink_nic_1)
        uplink_conf.nic_names.append(self.uplink_nic_2)
        uplink_conf.bond_name = 'juhe'
        uplink_conf.lacp = False
        uplink_conf.bond_mode = UpLinkManager_pb2.UpLinkConf.BALANCE_SLB
        response = self.uplink_stub.ModifyUpLink(UpLinkManager_pb2.UpLinkModifyRequest(
            vswitch_name=self.switch_name,
            uplink_conf=uplink_conf))
        assert response.errno == ErrNo_pb2.SYS_OK

        response = self.uplink_stub.DelUpLink(UpLinkManager_pb2.UpLinkDelRequest(
            vswitch_name=self.switch_name))
        assert response.errno == ErrNo_pb2.SYS_OK


class TestAclManager(object):
    channel = None
    ovs_stub = None
    acl_stub = None
    nic_stub = None
    ssh = None
    acl_nic = virtual_nic_1
    switch_name = "test_acl"
    filter_name = "acl_test"

    @classmethod
    def create_default_vswitch(cls):
        vswitch_conf = OvsManager_pb2.vSwitchConf()
        vswitch_conf.vswitch_name = cls.switch_name
        vswitch_conf.mode = OvsManager_pb2.vSwitchConf.VEB
        vswitch_conf.is_multicast = False

        response = cls.ovs_stub.AddvSwitch(OvsManager_pb2.vSwitchAddRequest(vswitch_conf=vswitch_conf))

        if response == ErrNo_pb2.SYS_FAIL:
            raise net_agentd_exception.NetAgentException("create default vswitch failed")

    @classmethod
    def destroy_default_vswitch(cls):
        response = cls.ovs_stub.DelvSwitch(OvsManager_pb2.vSwitchDelRequest(vswitch_name=cls.switch_name))
        if response == ErrNo_pb2.SYS_FAIL:
            raise net_agentd_exception.NetAgentException("del default vswitch failed")

    @classmethod
    def create_default_acl_file(cls):
        rules = []

        acl_rule1 = AclManager_pb2.AclRule()
        acl_rule1.protocol = "UDP"
        acl_rule1.src_ip = "192.168.25.13"
        acl_rule1.action = "accept"
        rules.append(acl_rule1)
        response = cls.acl_stub.AddAclFile(AclManager_pb2.AclFileAddRequest(
            filter_name=cls.filter_name,
            acl_rules=rules,
            in_default_action="accept",
            out_default_action="accept",
            filter_type=AclManager_pb2.FILTER_BY_IP))

        if response == ErrNo_pb2.SYS_FAIL:
            raise net_agentd_exception.NetAgentException("create default acl file failed")

    @classmethod
    def destroy_default_acl_file(cls):
        response = cls.acl_stub.DelAclFile(AclManager_pb2.AclFileDelRequest(filter_name=cls.filter_name))
        if response == ErrNo_pb2.SYS_FAIL:
            raise net_agentd_exception.NetAgentException("del default acl file failed")

    @classmethod
    def setup_class(cls):
        try:
            conf = util.ExternalConfig('../net_agent.cfg')
            port = conf.ConfigGet('global', 'port')
        except Exception as e:
            logging.error(e)

        cls.channel = grpc.insecure_channel(machine_ip + ':' + port)
        logging.info('TestAclManager@net_agent grpc channel create ok!')

        cls.ovs_stub = OvsManager_pb2_grpc.OvsManagerStub(cls.channel)
        cls.nic_stub = NicManager_pb2_grpc.NicManagerStub(cls.channel)
        cls.acl_stub = AclManager_pb2_grpc.AclManagerStub(cls.channel)

        cls.create_default_vswitch()
        cls.create_default_acl_file()
        logging.info('create default vswitch %s ok!' % cls.switch_name)

        cls.ssh = login_remote_machine(machine_ip, machine_user, machine_passwd)
        logging.info('login %s machine success!' % machine_ip)

        execute_remote_machine_cmd(cls.ssh, "ip tuntap add %s mode tap" % cls.acl_nic)
        execute_remote_machine_cmd(cls.ssh, "%s add-port %s %s" % (util.OVS_VSCTL_CMD, cls.switch_name, cls.acl_nic))

    @classmethod
    def teardown_class(cls):
        cls.destroy_default_vswitch()
        cls.destroy_default_acl_file()
        logging.info('del default vswitch %s ok!' % cls.switch_name)

        cls.channel.close()
        logging.info('TestAclManager@net_agent grpc channel close ok!')

        execute_remote_machine_cmd(cls.ssh, "ip tuntap del %s mode tap" % cls.acl_nic)
        quit_remote_machine(cls.ssh)
        logging.info('quit %s machine success!' % machine_ip)

    def test_AddAclFile_DelAclFile(self):
        rules = []
        acl_rule0 = AclManager_pb2.AclRule()
        acl_rule0.protocol = "ALL"
        acl_rule0.src_ip = "192.168.25.10"
        acl_rule0.src_port = "58"
        acl_rule0.src_mask = "255.255.255.0"
        acl_rule0.action = "drop"
        rules.append(acl_rule0)
        acl_rule1 = AclManager_pb2.AclRule()
        acl_rule1.protocol = "UDP"
        acl_rule1.src_ip = "192.168.25.13"
        acl_rule1.action = "accept"
        rules.append(acl_rule1)
        response = self.acl_stub.AddAclFile(AclManager_pb2.AclFileAddRequest(
            filter_name="acl_test_0",
            acl_rules=rules,
            in_default_action="accept",
            out_default_action="accept",
            filter_type=AclManager_pb2.FILTER_BY_IP))

        assert response.errno == ErrNo_pb2.SYS_OK

        response = self.acl_stub.AddAclFile(AclManager_pb2.AclFileAddRequest(
            filter_name="acl_test_0",
            acl_rules=rules,
            in_default_action="accept",
            out_default_action="accept",
            filter_type=AclManager_pb2.FILTER_BY_IP))

        assert response.errno == ErrNo_pb2.SYS_FAIL

        response = self.acl_stub.DelAclFile(AclManager_pb2.AclFileDelRequest(filter_name="acl_test_0"))
        assert response.errno == ErrNo_pb2.SYS_OK

        response = self.acl_stub.AddAclFile(AclManager_pb2.AclFileAddRequest(
            filter_name="acl_test_0",
            acl_rules=rules,
            in_default_action="adf",
            out_default_action="accept",
            filter_type=AclManager_pb2.FILTER_BY_IP))

        assert response.errno == ErrNo_pb2.SYS_FAIL

        response = self.acl_stub.AddAclFile(AclManager_pb2.AclFileAddRequest(
            filter_name="acl_test_0",
            acl_rules=rules,
            in_default_action="accept",
            out_default_action="adf",
            filter_type=AclManager_pb2.FILTER_BY_IP))

        assert response.errno == ErrNo_pb2.SYS_FAIL

    def test_ModifyAclFile(self):
        rules = []

        acl_rule1 = AclManager_pb2.AclRule()
        acl_rule1.protocol = "TCP"
        acl_rule1.src_ip = "192.168.25.13"
        acl_rule1.action = "accept"
        rules.append(acl_rule1)
        response = self.acl_stub.ModifyAclFile(AclManager_pb2.AclFileModifyRequest(
            filter_name=self.filter_name,
            acl_rules=rules,
            in_default_action="accept",
            out_default_action="accept",
            filter_type=AclManager_pb2.FILTER_BY_IP))

        assert response.errno == ErrNo_pb2.SYS_OK

    def test_QueryAclFile(self):
        response = self.acl_stub.QueryAclFile(AclManager_pb2.AclFileQueryRequest(filter_name=self.filter_name))
        logging.info('QueryAclFile:filter_name: %s', response.filter_name)
        logging.info('QueryAclFile:filter_type: %d', response.filter_type)
        logging.info('QueryAclFile:in_default_action: %s', response.in_default_action)
        logging.info('QueryAclFile:out_default_action: %s', response.out_default_action)
        for acl_rule in response.acl_rules:
            logging.info('QueryAclFile:priority: %s', acl_rule.priority)
            logging.info('QueryAclFile:direction: %d', acl_rule.direction)
            logging.info('QueryAclFile:src_ip: %s', acl_rule.src_ip)
            logging.info('QueryAclFile:src_port: %s', acl_rule.src_port)
            logging.info('QueryAclFile:src_mask: %s', acl_rule.src_mask)
            logging.info('QueryAclFile:src_mac: %s', acl_rule.src_mac)
            logging.info('QueryAclFile:src_mac_mask: %s', acl_rule.src_mac_mask)
            logging.info('QueryAclFile:dst_ip: %s', acl_rule.dst_ip)
            logging.info('QueryAclFile:dst_port: %s', acl_rule.dst_port)
            logging.info('QueryAclFile:dst_mask: %s', acl_rule.dst_mask)
            logging.info('QueryAclFile:dst_mac: %s', acl_rule.dst_mac)
            logging.info('QueryAclFile:dst_mac_mask: %s', acl_rule.dst_mac_mask)
            logging.info('QueryAclFile:action: %s', acl_rule.action)
            logging.info('-----------------------------------------')
        logging.info('QueryAclFile:errno: %d', response.errno)
        assert response.errno == ErrNo_pb2.SYS_OK

    def test_AttachAcl_DetachAcl(self):
        response = self.nic_stub.QueryNicInfo(NicManager_pb2.NicInfoQueryRequest(nic_names=[self.acl_nic]))
        assert response.nic_infos[0].errno == ErrNo_pb2.SYS_OK
        mac_addr = response.nic_infos[0].mac_address

        response = self.acl_stub.AttachAcl(AclManager_pb2.AclAttachRequest(
            vswitch_name=self.switch_name,
            tap_name=self.acl_nic,
            mac_addr=mac_addr,
            filter_name=self.filter_name))

        assert response.errno == ErrNo_pb2.SYS_OK

        response = self.acl_stub.DetachAcl(AclManager_pb2.AclDetachRequest(
            vswitch_name=self.switch_name,
            tap_name=self.acl_nic,
            mac_addr=mac_addr,
            filter_name=self.filter_name))

        assert response.errno == ErrNo_pb2.SYS_OK


class TestQosManager(object):
    channel = None
    ovs_stub = None
    qos_stub = None
    nic_stub = None
    ssh = None
    qos_nic = virtual_nic_1
    switch_name = "test_qos"
    qos_name = "qos_test"

    @classmethod
    def create_default_vswitch(cls):
        vswitch_conf = OvsManager_pb2.vSwitchConf()
        vswitch_conf.vswitch_name = cls.switch_name
        vswitch_conf.mode = OvsManager_pb2.vSwitchConf.VEB
        vswitch_conf.is_multicast = False

        response = cls.ovs_stub.AddvSwitch(OvsManager_pb2.vSwitchAddRequest(vswitch_conf=vswitch_conf))

        if response == ErrNo_pb2.SYS_FAIL:
            raise net_agentd_exception.NetAgentException("create default vswitch failed")

    @classmethod
    def destroy_default_vswitch(cls):
        response = cls.ovs_stub.DelvSwitch(OvsManager_pb2.vSwitchDelRequest(vswitch_name=cls.switch_name))
        if response == ErrNo_pb2.SYS_FAIL:
            raise net_agentd_exception.NetAgentException("del default vswitch failed")

    @classmethod
    def create_default_qos_file(cls):
        qos_rules = {
            "rules": [
                {"direction": "in", "average": "1000", "peak": "1000", "burst": "2000"},
                {"direction": "out", "average": "1800", "peak": "1000", "burst": "3000"}
            ]
        }
        qos_rules_json = json.dumps(qos_rules)

        response = cls.qos_stub.AddQosFile(QosManager_pb2.QosFileAddRequest(
            qos_name=cls.qos_name,
            qos_rules=qos_rules_json))

        if response == ErrNo_pb2.SYS_FAIL:
            raise net_agentd_exception.NetAgentException("create default qos file failed")

    @classmethod
    def destroy_default_qos_file(cls):
        response = cls.qos_stub.DelQosFile(QosManager_pb2.QosFileDelRequest(qos_name=cls.qos_name))
        if response == ErrNo_pb2.SYS_FAIL:
            raise net_agentd_exception.NetAgentException("del default qos file failed")

    @classmethod
    def setup_class(cls):
        try:
            conf = util.ExternalConfig('../net_agent.cfg')
            port = conf.ConfigGet('global', 'port')
        except Exception as e:
            logging.error(e)

        cls.channel = grpc.insecure_channel(machine_ip + ':' + port)
        logging.info('TestAclManager@net_agent grpc channel create ok!')

        cls.ovs_stub = OvsManager_pb2_grpc.OvsManagerStub(cls.channel)
        cls.nic_stub = NicManager_pb2_grpc.NicManagerStub(cls.channel)
        cls.qos_stub = QosManager_pb2_grpc.QosManagerStub(cls.channel)

        cls.create_default_vswitch()
        cls.create_default_qos_file()
        logging.info('create default vswitch %s ok!' % cls.switch_name)

        cls.ssh = login_remote_machine(machine_ip, machine_user, machine_passwd)
        logging.info('login %s machine success!' % machine_ip)

        execute_remote_machine_cmd(cls.ssh, "ip tuntap add %s mode tap" % cls.qos_nic)
        execute_remote_machine_cmd(cls.ssh, "%s add-port %s %s" % (util.OVS_VSCTL_CMD, cls.switch_name, cls.qos_nic))

    @classmethod
    def teardown_class(cls):
        cls.destroy_default_vswitch()
        cls.destroy_default_qos_file()
        logging.info('del default vswitch %s ok!' % cls.switch_name)

        cls.channel.close()
        logging.info('TestAclManager@net_agent grpc channel close ok!')

        execute_remote_machine_cmd(cls.ssh, "ip tuntap del %s mode tap" % cls.qos_nic)
        quit_remote_machine(cls.ssh)
        logging.info('quit %s machine success!' % machine_ip)

    def test_AddQosFile_DelQosFile(self):
        qos_rules = {
            "rules": [
                {"direction": "in", "average": "1000", "peak": "1000", "burst": "2000"},
                {"direction": "out", "average": "1800", "peak": "1000", "burst": "3000"}
            ]
        }
        qos_rules_json = json.dumps(qos_rules)

        response = self.qos_stub.AddQosFile(QosManager_pb2.QosFileAddRequest(
            qos_name="qos_test_0",
            qos_rules=qos_rules_json))

        assert response.errno == ErrNo_pb2.SYS_OK

        response = self.qos_stub.AddQosFile(QosManager_pb2.QosFileAddRequest(
            qos_name="qos_test_0",
            qos_rules=qos_rules_json))

        assert response.errno == ErrNo_pb2.SYS_FAIL

        response = self.qos_stub.DelQosFile(QosManager_pb2.QosFileDelRequest(qos_name="qos_test_0"))
        assert response.errno == ErrNo_pb2.SYS_OK

    def test_ModifyQosFile(self):
        qos_rules = {
            "rules": [
                {"direction": "in", "average": "1000", "peak": "1000", "burst": "2000"},
                {"direction": "in", "average": "2400", "peak": "1000", "burst": "6000"}
            ]
        }
        qos_rules_json = json.dumps(qos_rules)

        response = self.qos_stub.ModifyQosFile(QosManager_pb2.QosFileModifyRequest(
            qos_name=self.qos_name,
            qos_rules=qos_rules_json))

        assert response.errno == ErrNo_pb2.SYS_FAIL

    def test_QueryQosFile(self):
        response = self.qos_stub.QueryQosFile(QosManager_pb2.QosFileQueryRequest(qos_name=self.qos_name))
        logging.info('QueryQosFile:qos_name: %s', response.qos_name)

        qos_rules_json = json.loads(response.qos_rules)["rules"]

        for qos_rule_json in qos_rules_json:
            logging.info('QueryQosFile:direction: %s', qos_rule_json["direction"])
            logging.info('QueryQosFile:average: %s', qos_rule_json["average"])
            logging.info('QueryQosFile:peak: %s', qos_rule_json["peak"])
            logging.info('QueryQosFile:burst: %s', qos_rule_json["burst"])
            logging.info('-----------------------------------------')
        logging.info('QueryQosFile:errno: %d', response.errno)
        assert response.errno == ErrNo_pb2.SYS_OK

    def test_AttachQos_DetachQos(self):
        response = self.nic_stub.QueryNicInfo(NicManager_pb2.NicInfoQueryRequest(nic_names=[self.qos_nic]))
        assert response.nic_infos[0].errno == ErrNo_pb2.SYS_OK
        mac_addr = response.nic_infos[0].mac_address

        response = self.qos_stub.AttachQos(QosManager_pb2.QosAttachRequest(
            vswitch_name=self.switch_name,
            tap_name=self.qos_nic,
            qos_name=self.qos_name))

        assert response.errno == ErrNo_pb2.SYS_OK

        response = self.qos_stub.DetachQos(QosManager_pb2.QosDetachRequest(
            vswitch_name=self.switch_name,
            tap_name=self.qos_nic,
            qos_name=self.qos_name))

        assert response.errno == ErrNo_pb2.SYS_OK