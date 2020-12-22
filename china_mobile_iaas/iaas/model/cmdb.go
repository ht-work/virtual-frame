package model

import "sync"

var DeviceType = map[string]string{
	"PhyServer": "1",
	"VirServer": "2",
}

type FullCmdbResp struct {
	Count int               `json:"totalSize"`
	Data  []FullCmdbContext `json:"data"`
}

type FullCmdbContext struct {
	DeviceId     string `json:"id"`
	DeviceName   string `json:"device_name"`
	Ip           string `json:"ip,omitempty"`
	IdcType      string `json:"idcType,omitempty"`
	IdcTypeName  string `json:"idcType_idc_name_name,omitempty"`
	DeviceType   string `json:"device_type"`
	Dept1        string `json:"department1"`
	Dept1Name    string `json:"department1_orgName_name,omitempty"`
	Dept2Name    string `json:"department2_orgName_name,omitempty"`
	Dept2        string `json:"department2"`
	BizSys       string `json:"bizSystem"`
	BizSysName   string `json:"bizSystem_bizSystem_name,omitempty"`
	DevTypeName  string `json:"device_type_dict_note_name,omitempty"`
	NodeTypeName string `json:"node_type_dict_note_name,omitempty"`
	CpuCoreNum   string `json:"cpu_core_number,omitempty"`
	CpuNum       string `json:"cpu_number,omitempty"`
	MemSize      string `json:"memory_size,omitempty"`
}

//type ResourcePool struct {
//	ResourcePoolId   string `gorm:"column:resource_pool_id"`
//	ResourcePoolName string `gorm:"column:resource_pool_name"`
//}

//func (*ResourcePool) TableName() string {
//	return `tb_resource_pool`
//}

type Resource struct {
	//ID         uint   `gorm:"column:id; not null; primary_key; AUTO_INCREMENT"`
	Id           string `gorm:"column:data_id" json:"id"`
	DeviceId     string `gorm:"column:device_id;primary_key;type:varchar(255)" json:"device_id,omitempty"`     //设备唯一ID，UUID字符串
	DeviceName   string `gorm:"column:device_name;type:varchar(255)" json:"device_name,omitempty"`             //设备名称
	DeviceIP     string `gorm:"column:device_ip;" json:"ip,omitempty"`                                         //管理IP地址，好几个IP字段，暂取这个吧
	DeviceType   string `gorm:"column:device_type" json:"device_type,omitempty"`                               //设备类型，uuid字符串
	BizSys       string `gorm:"column:biz_sys" json:"bizSystem,omitempty"`                                     //业务系统，uuid字符串
	BizSysName   string `gorm:"column:biz_sys_name" json:"bizSystem_bizSystem_name,omitempty"`                 //业务系统名称
	Dept1        string `gorm:"column:dept1" json:"department1,omitempty"`                                     //一级部门uuid
	Dept2        string `gorm:"column:dept2" json:"department2,omitempty"`                                     //二级部门uuid
	Dept1Name    string `gorm:"column:dept1_name;type:varchar(255)" json:"department1_orgName_name,omitempty"` //一级部门名称
	Dept2Name    string `gorm:"column:dept2_name;type:varchar(255)" json:"department2_orgName_name,omitempty"` //二级部门名称
	IdcType      string `gorm:"column:idc_type" json:"idcType,omitempty"`                                      //资源池uuid
	IdcTypeName  string `gorm:"column:idc_type_name;type:varchar(255)" json:"idcType_idc_name_name,omitempty"` //资源池名称
	DevTypeName  string `gorm:"column:dev_type_name" json:"device_type_dict_note_name,omitempty"`
	NodeTypeName string `gorm:"column:node_type_name" json:"node_type_dict_note_name,omitempty"`
	CpuCoreNum   string `gorm:"column:cpu_core_num" json:"cpu_core_number,omitempty"`
	CpuNum       string `gorm:"column:cpu_num" json:"cpu_number,omitempty"`
	MemSize      string `gorm:"column:mem_size" json:"memory_size,omitempty"`
}

type ResourceTenantBaseInfo struct {
	Dept2        string `gorm:"column:dept2" json:"department2"`
	Dept2Name    string `gorm:"column:dept2_name" json:"department2_orgName_name"`
	VCPU         float64 `gorm:"column:VCPU" json:"VCPU"`
	MEM          float64 `gorm:"column:MEM" json:"MEM"`
	VM           int64 `gorm:"column:VM" json:"VM"`
	BM           int64 `gorm:"column:BM" json:"BM"`
	PM           int64 `gorm:"column:PM" json:"PM"`
	AppCount     int64 `gorm:"column:app_count" json:"app_count"`
}

type ResourceBizSysBaseInfo struct {
	BizSysId        string `gorm:"column:biz_sys" json:"id"`
	VCPU         float64 `gorm:"column:VCPU" json:"VCPU"`
	MEM          float64 `gorm:"column:MEM" json:"MEM"`
	VM           int64 `gorm:"column:VM" json:"VM"`
	BM           int64 `gorm:"column:BM" json:"BM"`
	PM           int64 `gorm:"column:PM" json:"PM"`
}

type ResourcePoolBaseInfo struct {
	ResourcePoolId        string `gorm:"column:idc_type" json:"id"`
	VCPU         float64 `gorm:"column:VCPU" json:"VCPU"`
	MEM          float64 `gorm:"column:MEM" json:"MEM"`
	VM           int64 `gorm:"column:VM" json:"VM"`
	BM           int64 `gorm:"column:BM" json:"BM"`
	PM           int64 `gorm:"column:PM" json:"PM"`
}

func (*Resource) TableName() string {
	return `tb_resource`
}

type ResourceChange struct {
	ResourceId   string `json:"uuid"`
	ResourceName string `json:"name"`
	ChangeType   int    `json:"changeType"`
}

type PhySerChange struct {
	ChangeType  int    `json:"changeType"`
	ServerId    string `json:"id"`
	Ip          string `json:"ipmi_ip,omitempty"`
	DevType     string `json:"device_type"`
	DevName     string `json:"device_name"`
	Dept2Id     string `json:"department2"`
	Dept2Name   string `json:"department2_orgName_name"`
	Dept1Id     string `json:"department1"`
	Dept1Name   string `json:"department1_orgName_name"`
	BizSys      string `json:"bizSystem"`
	IdcType     string `json:"idcType"`
	IdcTypeName string `json:"idcType_idc_name_name"`
}

type VirSerChange struct {
	ChangeType   int    `json:"changeType"`
	Dept2Name    string `json:"department2_orgName_name,omitempty"`
	Dept2Id      string `json:"department2"`
	Dept1Name    string `json:"department1_orgName_name,omitempty"`
	Dept1Id      string `json:"department1"`
	DevTypeName  string `json:"device_type_dict_note_name"`
	DevTypeId    string `json:"device_type"`
	ProjName     string `json:"project_name,omitempty"`
	DevClassName string `json:"device_class_dict_note_name,omitempty"`
	DevName      string `json:"device_name,omitempty"`
	Id           string `json:"id"`
	BizSysName   string `json:"bizSystem_bizSystem_name,omitempty"`
	BizSysId     string `json:"bizSystem"`
	IdcName      string `json:"idcType_idc_name_name,omitempty"`
	IdcType      string `json:"idcType"`
	Ip           string `json:"ip"`
}

type Response struct {
	Data struct {
		ResourcePools []ResourceChange `json:"resourcePools"`
		Tenant        []ResourceChange `json:"tenant"`
		BizSys        []ResourceChange `json:"business"`
		//Resource      []ResourceChange `json:"resource"`
		VirServer []VirSerChange `json:"virtualServers"`
		PhyServer []PhySerChange `json:"physicalServers"`
	} `json:"data"`
}

type CountData struct {
    Count int64 `gorm:"column:count_data"`
}


type IdToDevice = sync.Map

