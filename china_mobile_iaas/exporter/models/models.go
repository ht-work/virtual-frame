package models

import "sync"

type PermMetric struct{
	ID	string `json:"resourceId"`	//':"5f8c5a9f92e243bea11215f0631639d4"
	Name string `json:"metricName"`	//:"vm_realtime_disk_percent",
	Type string `json:"_"`			//this field is not in the data from performance metric
	Time	int64	`json:"time"`	//':1588986300,
	Value	float64	`json:"value"`	//:3.1415926
}

type ResourceConf struct {
	FieldName		string		//字段名称
	//ResourceType	string		//资源类型
}

//****************************资源池****************************
type RpMetric struct{
	Quota *RpQuota
}
type RpMetrics []*RpMetric
//资源池CMDB信息
type RpInfo struct{
	ID string			`json:"idcType"`
}
type RpInfoList []*RpInfo
//资源池配额/总量信息
type RpQuota struct{
	RpInfo
	BM float64 `json:"ljs_allocation_amount"`			//裸金属总量
	VM float64 `json:"yzj_allocation_amount"`			//云主机总量
	VMVcpu float64 `json:"yzj_vcpu_allocation_amount"`		//云主机VCPU总量
	VMMem float64 `json:"yzj_memory_allocation_amount"`	//云主机内存总量
}

type RpQuotaInner struct{
	Id string `json:"idcType"`
	BM float64 `json:"BM"`
	VM float64 `json:"VM"`
	Vcpu float64 `json:"VCpu"`
	MEM float64 `json:"MEM"`
}
//****************************资源池****************************

//****************************业务系统****************************
type AppMetric struct{
	Quota *AppQuota
	Used *AppUsed
	Usage *AppUsage
}
type AppMetrics []*AppMetric
//业务系统CMDB信息
type AppInfo struct{
	ID string			`json:"id"`
	Tenant	string 			`json:"department2"`		//所属租户
	RP	string 			`json:"idcType"`		//所属资源池
}
//业务系统使用率/分配率
type AppUsage struct{
	ID string
	BM float64			//资源使用率，对应app_resource_assign_ratio
	VM float64			//资源使用率，对应app_resource_assign_ratio
	VMVcpu float64		//资源使用率，对应app_resource_assign_ratio
	VMMem float64		//资源使用率，对应app_resource_assign_ratio
	APPUsage float64	//业务系统使用率，对应app_assign_ratio
}
//业务系统已使用/已分配
//type AppUsed struct{
//	ID   string `json:"id"`
//	BM float64 			//裸金属已使用数
//	VM float64		//云主机已使用数
//	VMVcpu float64 		//云主机VCPU已使用数
//	VMMem float64 	//云主机内存已使用数
//}

//业务系统配额
type AppQuota struct{
	AppInfo
	BM float64 			//裸金属已分配总量(台)
	VM float64 			//云主机已分配设备总量(台)
	VMVcpu float64 		//云主机已分配核数VCPU总量(个)
	VMMem float64 	//云主机已分配内存总量(G)
}
type AppResp struct{
	AppInfo
	BM string `json:"ljs_allocation_amount"`			//裸金属已分配总量(台)
	VM string `json:"yzj_allocation_amount"`			//云主机已分配设备总量(台)
	VMVcpu string `json:"yzj_vcpu_allocation_amount"`		//云主机已分配核数VCPU总量(个)
	VMMem string `json:"yzj_memory_allocation_amount"`	//云主机已分配内存总量(G)
}
// 已使用跟配额的结构体以及字段都一样
type AppUsed AppQuota
// 这个数据结构用于进行过渡，因为服务器返回的字段为字符串类型，需要进行转换！
type AppRespList []*AppResp

//type AppQuotaList []*AppQuota
// id -> appQuota
type AppQuotaMap map[string]*AppQuota
//****************************业务系统****************************


//****************************设备配置信息查询****************************
type ResourceInfo struct{
	ID string	`json:"device_id"`		//资源ID
	DeviceType string	 `json:"device_type"`	//类型
	//DeviceTypeName string	 `json:"device_type_dict_note_name"`	//类型
	NodeTypeName string	 `json:"node_type_dict_note_name"`	//节点类型：node_type_dict_note_name
	Type string	 `json:"-"`	//类型
	AppId string	`json:"bizSystem"`	//应用系统
	TenantId string `json:"department2"`	//租户
	RPId	string	`json:"idcType"`	//所属资源池
}
type ResourceMetric struct{
	ID	string
	CPUUsage	float64		//CPU利用率
	MemUsage	float64		//内存利用率
	Busy		float64		//繁忙度，(cpuusage+memusage)/2
	Unbalance	float64		//不平衡度，abs(cpuusage - memusage)
	Health		float64		//健康度，100-累加(未恢复告警级别*未恢复告警级别数量)
	Unavailable	float64		//不可用，如果health为0，则该值为1，否则为0，表示可用
}
//type IdToMetric map[string]*ResourceMetric //id -> metric
type IdToMetric = sync.Map //id -> metric
type IdToMetricMap map[string]*ResourceMetric //id -> metric
type DeviceMetric struct {
	CMDB *ResourceInfo
	Metric *ResourceMetric
}
type DeviceMetrics []*DeviceMetric
//****************************设备配置信息查询****************************


//****************************告警统计****************************
type StatAlert struct{
	ID string 	`json:"device_id"`	//设备id，如果为空，则表明是所有的统计
	Urgent	int64  	`json:"2"`	//告警数量：紧急
	Important	int64  	`json:"3"`	//告警数量：重要
	Secondary	int64  	`json:"4"`	//告警数量：次要
	Normal	int64  	`json:"5"`	//告警数量：一般
}
//****************************告警统计****************************
