package device

import (
	"exporter/config"
	. "exporter/httptool"
	. "exporter/models"
	"fmt"
	"sync"
)

var allDevMap sync.Map

//云主机
const DeviceType_VM string = "f5f6b15cc48a43a1b02467f0bfcfbeae"

//X86服务器，包括宿主机和裸金属
const DeviceType_X86 string = "85a802f297a24b2e9c9ec58dd15846b7"

//KVM宿主机
// const NodeType_KVM_Host string = "宿主机"
const NodeType_KVM_Host string = "计算节点"

//裸金属
const NodeType_BM string = "计算节点"

// 根据相关的信息判断设备的类型
func _updateDeviceType(info *ResourceInfo) {
	if info.DeviceType == DeviceType_VM {
		info.Type = GetVMType()
	} else {
		if info.NodeTypeName == NodeType_KVM_Host {
			info.Type = GetPhysicalServerType()
		} else {
			info.Type = GetBareMetalType()
		}
	}
}

func UpdateDeviceCMDB(devId string) {
	info := GetDeviceCMDBById(devId)
	if info == nil {
		//fetch the CMDB data from net
		info, err := QueryDeviceCMDB(devId)
		if err == nil && info != nil {
			_updateDeviceType(info)
			if config.IsDebug() {
				debugText(fmt.Sprintf("device info: %+v\n", *info))
			}
			_updateDeviceCMDB(devId, info)
		}
	}
}

func _updateDeviceCMDB(devId string, info *ResourceInfo) {
	//如果存在则不做任何处理，如果不存在则插入记录
	allDevMap.LoadOrStore(devId, info)
}

func GetDeviceCMDBById(devId string) *ResourceInfo {
	v, ok := allDevMap.Load(devId)
	if ok && v != nil {
		return v.(*ResourceInfo)
	} else {
		return nil
	}
}
