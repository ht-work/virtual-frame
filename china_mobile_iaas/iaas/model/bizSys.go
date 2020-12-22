package model

type FullBizResp struct {
	Count int      `json:"totalSize"`
	Data  []BizSys `json:"data"`
}

//type FullBizContext struct {
//	BizSysName string `json:"bizSystem"`
//	Id         string `json:"id"`
//}

type BizSys struct {
	BizSysId   string `gorm:"column:biz_sys_id;primary_key" json:"id"`
	BizSysName string `gorm:"column:biz_sys_name" json:"bizSystem"`
}

func (*BizSys) TableName() string {
	return `tb_biz_sys`
}

type FullBizQuotaResp struct {
	Count int           `json:"totalSize"`
	Data  []BizSysQuota `json:"data"`
}

type BizSysQuota struct {
	BizSysId    string `gorm:"column:biz_sys_id;primary_key" json:"id"`
	LjsAllocate string `gorm:"column:allocate_ljs" json:"ljs_allocation_amount"` //裸金属已分配量
	YyfwqAllocate   string `gorm:"column:allocate_yyfwq" json:"yyfwq_allocation_amount"`       //引用服务器已分配量
	FxxfwqAllocate  string `gorm:"column:allocate_fxxfwq" json:"fxxfwq_allocation_amount"`     //分析型服务器已分配量
	FbsfwqAllocate  string `gorm:"column:allocate_fbsfwq" json:"fbsfwq_allocation_amount"`     //分布式服务器已分配量
	HcxfwqAllocate  string `gorm:"column:allocate_hcxfwq" json:"hcxfwq_allocation_amount"`     //缓存型服务器已分配量
	GdyyfwqAllocate string `gorm:"column:allocate_gdyyfwq" json:"gdyyfwq_allocation_amount"`   //高端应用服务器已分配量
	DjdfwqAllocate  string `gorm:"column:allocate_djdfwq" json:"djdfwq_allocation_amount"`     //多节点服务器已分配量
	YzjAllocate     string `gorm:"column:allocate_yzj" json:"yzj_allocation_amount"`           //云主机已分配设备总台数
	YzjVcpuAllocate string `gorm:"column:allocate_yzj_vcpu" json:"yzj_vcpu_allocation_amount"` //云主机已分配核数VCPU总量（个）
	YzjMemAllocate  string `gorm:"column:allocate_yzj_mem" json:"yzj_memory_allocation_amount"`   //云主机已分配内存总额
	OwnerBizSys     string `gorm:"column:owner_biz_sys" json:"owner_biz_system"`
	OwnerBizSysName string `gorm:"column:owner_biz_sys_name" json:"owner_biz_system_bizSystem_name"`
	Dept1           string `gorm:"column:dept1" json:"department1"`
	Dept1Name       string `gorm:"column:dept1_name" json:"department1_orgName_name"`
	Dept2           string `gorm:"column:dept2" json:"department2"`
	Dept2Name       string `gorm:"column:dept2_name" json:"department2_orgName_name"`
	IdcType         string `gorm:"column:idc_type" json:"idcType"`
	IdcTypeName     string `gorm:"column:idc_type_name" json:"idcType_idc_name_name"`
	BizLevel        string `gorm:"column:buz_level" json:"business_level"` //业务系统级别
}

type BizBaseInfo struct {
	Dept1           string `gorm:"column:dept1" json:"department1"`
	Dept1Name       string `gorm:"column:dept1_name" json:"department1_orgName_name"`
	Dept2           string `gorm:"column:dept2" json:"department2"`
	Dept2Name       string `gorm:"column:dept2_name" json:"department2_orgName_name"`
	IdcType         string `gorm:"column:idc_type" json:"idcType"`
	IdcTypeName     string `gorm:"column:idc_type_name" json:"idcType_idc_name_name"`
	BizSys          string `gorm:"column:owner_biz_sys" json:"bizSys"`
	BizSysName      string `gorm:"column:owner_biz_sys_name" json:"bizSysName"`
	AppCount        int64  `gorm:"column:app_count" json:"app_count"`
	TenantCount     int64  `gorm:"column:tenant_count" json:"tenant_count"`
}

type BizSysDetail struct {
	BizSysId    string `json:"id"`
	BizSysName  string `json:"biz_sys_name"`
	Dept1           string `json:"department1"`
	Dept1Name       string `json:"department1_orgName_name"`
	Dept2           string `json:"department2"`
	Dept2Name       string `json:"department2_orgName_name"`
	IdcType         string `json:"idcType"`
	IdcTypeName     string `json:"idcType_idc_name_name"`
	VmCount     int64 `json:"vm_amount"`           //云主机设备总台数
	VcpuCount float64 `json:"vcpu_amount"` //云主机核数VCPU总量（个）
	MemCount  float64 `json:"mem_amount"`   //云主机内存总额
	BmCount int64 `json:"bm_amount"` //裸金属总量
}


func (*BizSysQuota) TableName() string {
	return "tb_biz_sys_quota"
}
