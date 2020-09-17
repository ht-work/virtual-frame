import os
import logging
import traceback
import time

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

from net_agent import NicManager
from net_agent import OvsManager
from net_agent import UpLinkManager
from net_agent import AclManager
from net_agent import QosManager

from net_agent import net_agent_util as util
from net_agent import net_agentd_exception


class nic_manager(NicManager_pb2_grpc.NicManagerServicer):
    def QueryNicList(self, request, context):
        errno = ErrNo_pb2.SYS_FAIL
        nic_names = []
        type = [NicManager_pb2.NicListQueryRequest.ALL_PHY_NIC,
                NicManager_pb2.NicListQueryRequest.FREE_PHY_NIC,
                NicManager_pb2.NicListQueryRequest.VIRTUAL_NIC]

        while True:
            if request.nic_type not in type:
                break

            try:
                nic_names = NicManager.get_nic_list(request.nic_type)
                errno = ErrNo_pb2.SYS_OK
            except net_agentd_exception.NetAgentException:
                logging.error(traceback.format_exc())
                logging.error("QueryNicList failed")

            break

        return NicManager_pb2.NicListQueryReply(nic_names=nic_names, errno=errno)

    def QueryNicInfo(self, request, context):
        nic_infos = []

        for nic_name in request.nic_names:
            class_net_path = os.path.join(util.SYS_CLASS_NET, nic_name)
            if os.path.exists(class_net_path):
                try:
                    nic_object = NicManager.NicHandle(nic_name)
                    nic_info = NicManager_pb2.NicInfo()

                    nic_info.nic_name = nic_name
                    nic_info.description = nic_object.get_description()
                    nic_info.mac_address = nic_object.get_mac_address()
                    nic_info.speed = nic_object.get_speed()
                    nic_info.operstate = nic_object.get_operstate()
                    nic_info.mtu = nic_object.get_mtu()
                    nic_info.driver_name = nic_object.get_driver_name()
                    nic_info.numa = nic_object.get_numa()
                    nic_info.nic_address = nic_object.get_nic_address()
                    nic_info.carrier = nic_object.get_carrier()
                    nic_info.duplex = nic_object.get_duplex()

                    nic_info.errno = ErrNo_pb2.SYS_OK
                except net_agentd_exception.NetAgentException:
                    nic_info.errno = ErrNo_pb2.SYS_FAIL
                    logging.error("%s QueryNicList failed" % nic_name)

                nic_infos.append(nic_info)

            else:
                logging.error("%s doesnt exist" % nic_name)

        return NicManager_pb2.NicInfoQueryReply(nic_infos=nic_infos)

    def QueryPacketStat(self, request, context):
        statistics_items = []

        for mac_addr in request.mac_addrs:
            statistics = NicManager_pb2.PacketStat()
            statistics_items.append(statistics)

            nic_name = NicManager.MacAddr2NicName(mac_addr)
            if nic_name == "":
                statistics.errno = ErrNo_pb2.SYS_FAIL
                continue

            class_net_path = os.path.join(util.SYS_CLASS_NET, nic_name)
            if not os.path.exists(class_net_path):
                statistics.errno = ErrNo_pb2.SYS_FAIL
                continue

            try:
                nic_object = NicManager.NicHandle(nic_name)
                statistics.tx_bytes = nic_object.get_tx_bytes()
                statistics.tx_packets = nic_object.get_tx_packets()
                statistics.tx_dropped = nic_object.get_tx_dropped()
                statistics.tx_errors = nic_object.get_tx_errors()
                statistics.rx_bytes = nic_object.get_rx_bytes()
                statistics.rx_packets = nic_object.get_rx_packets()
                statistics.rx_dropped = nic_object.get_rx_dropped()
                statistics.rx_errors = nic_object.get_rx_errors()

                statistics.errno = ErrNo_pb2.SYS_OK
            except net_agentd_exception.NetAgentException:
                statistics.errno = ErrNo_pb2.SYS_FAIL
                logging.error("%s QueryPacketStat failed" % nic_name)

        return NicManager_pb2.PacketStatQueryReply(
                                   packet_stats=statistics_items)

    def ModifyNic(self, request, context):
        errno = ErrNo_pb2.SYS_FAIL

        class_net_path = os.path.join(util.SYS_CLASS_NET, request.nic_name)
        if request.nic_name == "":
            errno = ErrNo_pb2.SYS_FAIL
            return NicManager_pb2.NicModifyReply(errno=errno)
        else:
            if not os.path.exists(class_net_path):
                errno = ErrNo_pb2.SYS_FAIL
                return NicManager_pb2.NicModifyReply(errno=errno)

        nic_object = NicManager.NicHandle(request.nic_name)

        if request.driver_name != "":
            try:
                raw_device = nic_object.get_raw_device()
                new_driver_path = nic_object.get_driver_path_by_driver_name(request.driver_name)
                nic_object.detach_driver()
                nic_object.attach_driver(new_driver_path, raw_device)
                errno = ErrNo_pb2.SYS_OK
            except net_agentd_exception.NetAgentException:
                logging.error(traceback.format_exc())
                logging.error('changer driver failed %s' % request.nic_name)
                errno = ErrNo_pb2.SYS_FAIL
            time.sleep(1)

        if request.mtu != "":
            try:
                nic_object.set_mtu(request.mtu)
                new_mtu = nic_object.get_mtu()
                if new_mtu == request.mtu:
                    errno = ErrNo_pb2.SYS_OK
                else:
                    errno = ErrNo_pb2.SYS_FAIL

            except:
                logging.error(traceback.format_exc())
                logging.error('set mtu failed %s' % request.nic_name)
                errno = ErrNo_pb2.SYS_FAIL

        return NicManager_pb2.NicModifyReply(errno=errno)

    def StartNic(self, request, context):
        errno = ErrNo_pb2.SYS_FAIL

        try:
            nic_object = NicManager.NicHandle(request.nic_name)
            nic_object.start_nic()
            errno = ErrNo_pb2.SYS_OK
        except:
            logging.error(traceback.format_exc())
            logging.error("StartNic failed")

        return NicManager_pb2.NicStartReply(errno=errno)

    def StopNic(self, request, context):
        errno = ErrNo_pb2.SYS_FAIL

        try:
            nic_object = NicManager.NicHandle(request.nic_name)
            nic_object.stop_nic()
            errno = ErrNo_pb2.SYS_OK
        except:
            logging.error(traceback.format_exc())
            logging.error("StopNic failed")

        return NicManager_pb2.NicStopReply(errno=errno)


class ovs_manager(OvsManager_pb2_grpc.OvsManagerServicer):
    def QueryvSwitchList(self, request, context):
        errno = ErrNo_pb2.SYS_FAIL
        vswitch_names = []

        try:
            vswitch_names = OvsManager.get_vswitch_list()
            errno = ErrNo_pb2.SYS_OK
        except net_agentd_exception.NetAgentException:
            logging.error(traceback.format_exc())
            logging.error("QueryvSwitchList failed")

        return OvsManager_pb2.vSwitchListQueryReply(vswitch_names=vswitch_names, errno=errno)

    def QueryvSwitchInfo(self, request, context):
        vswitch_infos = []

        for vswitch_name in request.vswitch_names:
            ovs_object = OvsManager.OvsHandle(vswitch_name)
            if ovs_object.is_vswitch_exist() is True:
                try:
                    vswitch_info = OvsManager_pb2.vSwitchInfo()
                    vswitch_info.vswitch_conf.vswitch_name = vswitch_name
                    vswitch_info.vswitch_conf.mode = ovs_object.get_mode()
                    vswitch_info.vswitch_conf.is_multicast = ovs_object.get_vswitch_multicast()
                    vswitch_info.is_link = ovs_object.is_vswitch_link()
                    vswitch_info.errno = ErrNo_pb2.SYS_OK
                except net_agentd_exception.NetAgentException:
                    vswitch_infos.errno = ErrNo_pb2.SYS_FAIL
                    logging.error(traceback.format_exc())
                    logging.error("%s QueryvSwitchInfo failed" % vswitch_name)

                vswitch_infos.append(vswitch_info)
            else:
                logging.error("Query: br %s doesnt exist" % vswitch_name)

        return OvsManager_pb2.vSwitchInfoQueryReply(vswitch_infos=vswitch_infos)

    def AddvSwitch(self, request, context):
        retval = ErrNo_pb2.SYS_FAIL

        ovs_object = OvsManager.OvsHandle(request.vswitch_conf.vswitch_name)
        if ovs_object.is_vswitch_exist() is False:
            try:
                ovs_object.create_vswitch()
                ovs_object.generate_conf_file()
                if request.vswitch_conf.is_multicast:
                    ovs_object.set_vswitch_multicast(request.vswitch_conf.is_multicast)
                retval = ErrNo_pb2.SYS_OK
            except net_agentd_exception.NetAgentException:
                logging.error(traceback.format_exc())
                logging.error("create br %s failed" % request.vswitch_conf.vswitch_name)
        else:
            logging.error("Add: br %s already exist" % request.vswitch_conf.vswitch_name)

        return OvsManager_pb2.vSwitchAddReply(errno=retval)

    def DelvSwitch(self, request, context):
        errno = ErrNo_pb2.SYS_FAIL

        ovs_object = OvsManager.OvsHandle(request.vswitch_name)
        if ovs_object.is_vswitch_exist() is True:
            try:
                ovs_object.destroy_vswitch()
                ovs_object.remove_conf_file()
                errno = ErrNo_pb2.SYS_OK
            except net_agentd_exception.NetAgentException:
                logging.error(traceback.format_exc())
                logging.error("destroy br %s failed" % request.vswitch_name)
        else:
            logging.error("Del: br %s doesnt exist" % request.vswitch_name)

        return OvsManager_pb2.vSwitchAddReply(errno=errno)

    def ModifyvSwitch(self, request, context):
        retval = ErrNo_pb2.SYS_FAIL

        ovs_object = OvsManager.OvsHandle(request.vswitch_conf.vswitch_name)
        if ovs_object.is_vswitch_exist() is True:
            try:
                if request.vswitch_conf.is_multicast:
                    ovs_object.set_vswitch_multicast(request.vswitch_conf.is_multicast)
                retval = ErrNo_pb2.SYS_OK

            except net_agentd_exception.NetAgentException:
                logging.error(traceback.format_exc())
                logging.error("Modify br %s failed" % request.vswitch_name)
        else:
            logging.error("Modify: br %s doesnt exist" % request.vswitch_conf.vswitch_name)

        return OvsManager_pb2.vSwitchAddReply(errno=retval)

    def SetInternalNicParam(self, request, context):
        old_vlan = ""
        old_mtu = ""
        old_ip = ""
        old_netmask = ""
        operate_success = []
        errno = ErrNo_pb2.SYS_FAIL

        ovs_object = OvsManager.OvsHandle(request.vswitch_name, request.internal_nic_name)
        if ovs_object.is_vswitch_exist() is True:
            try:
                '''make sure internal_nic status is up'''
                ovs_object.start_nic()
                if request.vlan:
                    old_vlan = ovs_object.get_vlan()
                    ovs_object.set_vlan(request.vlan)
                    operate_success.append("vlan")
                if request.mtu:
                    old_mtu = ovs_object.get_mtu()
                    ovs_object.set_mtu(request.mtu)
                    operate_success.append("mtu")
                if request.ip_addr:
                    old_ip = ovs_object.get_ip()
                    old_netmask = ovs_object.get_netmask()
                    ovs_object.set_ip_netmask(request.ip_addr, request.netmask)
                    operate_success.append("ip_addr")
                if request.gateway:
                    ovs_object.set_gateway(request.gateway)
                    operate_success.append("gateway")
                errno = ErrNo_pb2.SYS_OK

            except net_agentd_exception.NetAgentException:
                if "ip_addr" in operate_success:
                    ovs_object.set_ip_netmask(old_ip, old_netmask)
                if "mtu" in operate_success:
                    ovs_object.set_mtu(old_mtu)
                if "vlan" in operate_success:
                    ovs_object.set_vlan(old_vlan)

                logging.error(traceback.format_exc())
                logging.error("SetInternalNicParam br %s vnic %s failed" % (request.vswitch_name,
                                                                            request.internal_nic_name))
        else:
            logging.error("SetInternalNicParam: br %s doesnt exist" % request.vswitch_name)

        return OvsManager_pb2.InternalNicParamSetReply(errno=errno)

    def ClearInternalNicParam(self, request, context):
        errno = ErrNo_pb2.SYS_FAIL

        ovs_object = OvsManager.OvsHandle(request.vswitch_name, request.internal_nic_name)
        if ovs_object.is_vswitch_exist() is True:
            try:
                ovs_object.clear_ip()
                ovs_object.save_conf_file_item("IPADDR", "")
                ovs_object.save_conf_file_item("NETMASK", "")
                ovs_object.save_conf_file_item("GATEWAY", "")
                errno = ErrNo_pb2.SYS_OK

            except net_agentd_exception.NetAgentException:
                logging.error(traceback.format_exc())
                logging.error("ClearInternalNicParam br %s vnic %s failed" % (request.vswitch_name,
                                                                              request.internal_nic_name))
        else:
            logging.error("ClearInternalNicParam: br %s doesnt exist" % request.vswitch_name)

        return OvsManager_pb2.InternalNicParamClearReply(errno=errno)

    def GetInternalNicParam(self, request, context):
        vlan = ""
        mtu = ""
        ip_addr = ""
        net_mask = ""
        gate_way = ""
        errno = ErrNo_pb2.SYS_FAIL

        ovs_object = OvsManager.OvsHandle(request.vswitch_name, request.internal_nic_name)
        if ovs_object.is_vswitch_exist() is True:
            try:
                vlan = ovs_object.get_vlan()
                mtu = ovs_object.get_mtu()
                ip_addr = ovs_object.get_ip()
                net_mask = ovs_object.get_netmask()
                gate_way = ovs_object.get_gateway()
                errno = ErrNo_pb2.SYS_OK

            except net_agentd_exception.NetAgentException:
                logging.error(traceback.format_exc())
                logging.error("Modify br %s failed" % request.vswitch_name)
        else:
            logging.error("Modify: br %s doesnt exist" % request.vswitch_name)

        return OvsManager_pb2.InternalNicParamGetReply(vswitch_name=request.vswitch_name,
                                                       internal_nic_name=request.internal_nic_name,
                                                       vlan=vlan,
                                                       mtu=mtu,
                                                       ip_addr=ip_addr,
                                                       netmask=net_mask,
                                                       gateway=gate_way,
                                                       errno=errno)


class uplink_manager(UpLinkManager_pb2_grpc.UpLinkManagerServicer):
    def AddUpLink(self, request, context):
        retval = ErrNo_pb2.SYS_FAIL

        uplink_object = UpLinkManager.UpLinkHandle(request.vswitch_name)
        try:
            uplink_port_name = uplink_object.get_uplink_port_name()
            if uplink_port_name == "":
                if request.uplink_conf.nic_names.__len__() == 0:
                    logging.error("AddUpLink: br %s has no uplink port" % request.vswitch_name)
                if request.uplink_conf.nic_names.__len__() == 1:
                    uplink_object.set_single_uplink_port(request.uplink_conf.nic_names[0])

                if request.uplink_conf.nic_names.__len__() > 1:
                    uplink_object.set_bond_uplink_port(request.uplink_conf)

                retval = ErrNo_pb2.SYS_OK
            else:
                logging.error("uplink port %s already exist" % uplink_port_name)
        except Exception:
            retval = ErrNo_pb2.SYS_FAIL
            logging.error(traceback.format_exc())

        return UpLinkManager_pb2.UpLinkAddReply(errno=retval)

    def DelUpLink(self, request, context):
        retval = ErrNo_pb2.SYS_FAIL

        try:
            uplink_object = UpLinkManager.UpLinkHandle(request.vswitch_name)
            uplink_port_name = uplink_object.get_uplink_port_name()
            uplink_object.remove_port(uplink_port_name)
            retval = ErrNo_pb2.SYS_OK
            logging.info("del uplink port %s success" % uplink_port_name)
        except Exception:
            logging.error(traceback.format_exc())
            logging.error("del %s uplink port failed" % request.vswitch_name)

        return UpLinkManager_pb2.UpLinkDelReply(errno=retval)

    def ModifyUpLink(self, request, context):
        retval = ErrNo_pb2.SYS_FAIL

        uplink_object = UpLinkManager.UpLinkHandle(request.vswitch_name)
        try:
            uplink_port_name = uplink_object.get_uplink_port_name()
            if uplink_port_name != "":
                uplink_object.remove_port(uplink_port_name)
                if request.uplink_conf.nic_names.__len__() == 0:
                    logging.error("ModifyUpLink: %s have no phy nic" % request.vswitch_name)
                if request.uplink_conf.nic_names.__len__() == 1:
                    uplink_object.set_single_uplink_port(request.uplink_conf.nic_names[0])
                    retval = ErrNo_pb2.SYS_OK
                if request.uplink_conf.nic_names.__len__() > 1:
                    uplink_object.set_bond_uplink_port(request.uplink_conf)
                    retval = ErrNo_pb2.SYS_OK
            else:
                logging.error("ModifyUpLink: have no uplink port")
        except Exception:
            retval = ErrNo_pb2.SYS_FAIL
            logging.critical(traceback.format_exc())

        return UpLinkManager_pb2.UpLinkModifyReply(errno=retval)


class acl_manager(AclManager_pb2_grpc.AclManagerServicer):
    def AttachAcl(self, request, context):
        errno = ErrNo_pb2.SYS_FAIL
        acl_object = AclManager.AclHandle(request.vswitch_name,
                                          request.filter_name)

        while True:
            if acl_object.is_vswitch_exist() is False:
                logging.error("AddAcl: br %s doesnt exist" % request.vswitch_name)
                break

            if not os.path.exists(os.path.join(util.NET_AGENT_CONF_DIR, request.filter_name + '.xml')):
                logging.error("AttachAcl: acl_rules file doesnt exist")
                break

            try:
                ofport = acl_object.iface_to_ofport(request.tap_name)
                acl_object.attach_rules(ofport)
            except:
                logging.critical(traceback.format_exc())
                logging.error("AddAcl: br %s del old Acl %s failed" % (request.vswitch_name, request.filter_name))
                break

            errno = ErrNo_pb2.SYS_OK
            break

        return AclManager_pb2.AclAttachReply(errno=errno)

    def DetachAcl(self, request, context):
        errno = ErrNo_pb2.SYS_FAIL
        acl_object = AclManager.AclHandle(request.vswitch_name,
                                          request.filter_name)

        while True:
            if not os.path.exists(os.path.join(util.NET_AGENT_CONF_DIR, request.filter_name + '.xml')):
                logging.error("DelAcl: old acl_rules file doesn,t exist")
                break

            if acl_object.is_vswitch_exist() is False:
                logging.error("DelAcl: br %s doesnt exist" % request.vswitch_name)
                break

            try:
                ofport = acl_object.iface_to_ofport(request.tap_name)
                acl_object.detach_rules(ofport)
            except:
                logging.error("DelAcl: br %s del old Acl %s failed" % (request.vswitch_name, request.filter_name))
                break

            errno = ErrNo_pb2.SYS_OK
            break

        return AclManager_pb2.AclDetachReply(errno=errno)

    def AddAclFile(self, request, context):
        errno = ErrNo_pb2.SYS_FAIL

        if not os.path.exists(os.path.join(util.NET_AGENT_CONF_DIR, request.filter_name + '.xml')):
            try:
                AclManager.generate_acl_rules_file(request.filter_type,
                                                   request.filter_name,
                                                   request.in_default_action,
                                                   request.out_default_action,
                                                   request.acl_rules)
                errno = ErrNo_pb2.SYS_OK
            except:
                logging.critical(traceback.format_exc())
                logging.error("AddAclFile: generate acl_rules file failed")
        else:
            logging.error("AddAclFile: acl_rules file already exist")

        return AclManager_pb2.AclFileAddReply(errno=errno)

    def ModifyAclFile(self, request, context):
        errno = ErrNo_pb2.SYS_FAIL

        if os.path.exists(os.path.join(util.NET_AGENT_CONF_DIR, request.filter_name + '.xml')):
            try:
                AclManager.generate_acl_rules_file(request.filter_type,
                                                   request.filter_name,
                                                   request.in_default_action,
                                                   request.out_default_action,
                                                   request.acl_rules)
                errno = ErrNo_pb2.SYS_OK
            except:
                logging.error("ModifyAclFile: modify acl_rules file failed")
        else:
            logging.error("ModifyAclFile: acl_rules doesnt exist")

        return AclManager_pb2.AclFileModifyReply(errno=errno)

    def DelAclFile(self, request, context):
        errno = ErrNo_pb2.SYS_FAIL

        path = os.path.join(util.NET_AGENT_CONF_DIR, request.filter_name + '.xml')
        if AclManager.remove_acl_rules_file(path) is True:
            errno = ErrNo_pb2.SYS_OK

        return AclManager_pb2.AclFileDelReply(errno=errno)

    def QueryAclFile(self, request, context):
        errno = ErrNo_pb2.SYS_FAIL

        try:
            filter_name = AclManager.get_filter_name(request.filter_name)
            filter_type = AclManager.get_filter_type(request.filter_name)
            in_default_action = AclManager.get_in_default_action(request.filter_name)
            out_default_action = AclManager.get_out_default_action(request.filter_name)
            filter_rules = AclManager.get_filter_rules(request.filter_name)
            errno = ErrNo_pb2.SYS_OK
        except:
            logging.critical(traceback.format_exc())
            logging.error("%s QueryAclFile failed" % request.filter_name)

        return AclManager_pb2.AclFileQueryReply(acl_rules=filter_rules,
                                                filter_name=filter_name,
                                                filter_type=filter_type,
                                                in_default_action=in_default_action,
                                                out_default_action=out_default_action,
                                                errno=errno)


class qos_manager(QosManager_pb2_grpc.QosManagerServicer):
    def AttachQos(self, request, context):
        errno = ErrNo_pb2.SYS_FAIL
        qos_object = QosManager.QosHandle(request.vswitch_name,
                                          request.qos_name)

        while True:
            if not os.path.exists(os.path.join(util.NET_AGENT_QOS_CONF_DIR, request.qos_name + '.xml')):
                logging.error("AttachQos: qos_rules file %s doesn,t exist" % request.qos_name)
                break

            if qos_object.is_vswitch_exist() is False:
                logging.error("AttachQos: br %s doesnt exist" % request.vswitch_name)
                break

            try:
                qos_object.attach_rules(request.tap_name)
            except:
                logging.critical(traceback.format_exc())
                logging.error("AttachQos: br %s attach qos %s failed" % (request.vswitch_name, request.qos_name))
                break

            errno = ErrNo_pb2.SYS_OK
            break

        return QosManager_pb2.QosAttachReply(errno=errno)

    def DetachQos(self, request, context):
        errno = ErrNo_pb2.SYS_FAIL
        qos_object = QosManager.QosHandle(request.vswitch_name,
                                          request.qos_name)

        while True:
            if not os.path.exists(os.path.join(util.NET_AGENT_QOS_CONF_DIR, request.qos_name + '.xml')):
                logging.error("DetachQos: qos_rules file %s doesn,t exist" % request.qos_name)
                break

            if qos_object.is_vswitch_exist() is False:
                logging.error("DetachQos: br %s doesnt exist" % request.vswitch_name)
                break

            try:
                qos_object.detach_rules(request.tap_name)
            except:
                logging.critical(traceback.format_exc())
                logging.error("DetachQos: br %s detach qos %s failed" % (request.vswitch_name, request.qos_name))
                break

            errno = ErrNo_pb2.SYS_OK
            break

        return QosManager_pb2.QosDetachReply(errno=errno)

    def AddQosFile(self, request, context):
        errno = ErrNo_pb2.SYS_FAIL

        if not os.path.exists(os.path.join(util.NET_AGENT_QOS_CONF_DIR, request.qos_name + '.xml')):
            try:
                QosManager.generate_qos_rules_file(request.qos_name,
                                                   request.qos_rules)
                errno = ErrNo_pb2.SYS_OK
            except:
                logging.critical(traceback.format_exc())
                logging.error("AddQosFile: generate qos_rules file failed")
        else:
            logging.error("AddQosFile: qos_rules file already exist")

        return QosManager_pb2.QosFileAddReply(errno=errno)

    def ModifyQosFile(self, request, context):
        errno = ErrNo_pb2.SYS_FAIL

        if os.path.exists(os.path.join(util.NET_AGENT_QOS_CONF_DIR, request.qos_name + '.xml')):
            try:
                QosManager.generate_qos_rules_file(request.qos_name,
                                                   request.qos_rules)
                errno = ErrNo_pb2.SYS_OK
            except:
                logging.critical(traceback.format_exc())
                logging.error("ModifyQosFile: modify qos_rules file failed")
        else:
            logging.error("ModifyQosFile: qos_rules file %s doesnt exist" % request.qos_name)

        return QosManager_pb2.QosFileModifyReply(errno=errno)

    def DelQosFile(self, request, context):
        errno = ErrNo_pb2.SYS_FAIL

        try:
            path = os.path.join(util.NET_AGENT_QOS_CONF_DIR, request.qos_name + '.xml')
            QosManager.remove_qos_rules_file(path)
            errno = ErrNo_pb2.SYS_OK
        except:
            logging.critical(traceback.format_exc())
            logging.error("DelQosFile: del qos file %s failed" % request.qos_name)

        return QosManager_pb2.QosFileDelReply(errno=errno)

    def QueryQosFile(self, request, context):
        errno = ErrNo_pb2.SYS_FAIL

        try:
            qos_name = request.qos_name
            qos_rules = QosManager.get_qos_rules_to_json(request.qos_name)
            errno = ErrNo_pb2.SYS_OK
        except:
            logging.critical(traceback.format_exc())
            logging.error("QueryQosFile: query qos file %s failed" % request.qos_name)

        return QosManager_pb2.QosFileQueryReply(qos_name=qos_name,
                                                qos_rules=qos_rules,
                                                errno=errno)


def add_to_server(sub_server):
    NicManager_pb2_grpc.add_NicManagerServicer_to_server(nic_manager(), sub_server)
    OvsManager_pb2_grpc.add_OvsManagerServicer_to_server(ovs_manager(), sub_server)
    UpLinkManager_pb2_grpc.add_UpLinkManagerServicer_to_server(
                                                     uplink_manager(), sub_server)
    AclManager_pb2_grpc.add_AclManagerServicer_to_server(acl_manager(), sub_server)
    QosManager_pb2_grpc.add_QosManagerServicer_to_server(qos_manager(), sub_server)
