package model

type FullIdc struct {
	Count int       `json:"totalSize"`
	Data  []IdcType `json:"data"`
}

type IdcType struct {
	IdcId   string `gorm:"column:idc_id;not null;primary_key" json:"id"`
	IdcName string `gorm:"column:idc_name" json:"idc_name"`
}

type ResourcePoolDetail struct {
	AppCount     int64 `json:"app_count"`
	TenantCount  int64 `json:"tenant_count"`
	IdcType         string `json:"idcType"`
	IdcTypeName     string `json:"idcType_idc_name_name"`
	VmCount     int64 `json:"vm_amount"`           //云主机设备总台数
	VcpuCount float64 `json:"vcpu_amount"` //云主机核数VCPU总量（个）
	MemCount  float64 `json:"mem_amount"`   //云主机内存总额
	BmCount int64 `json:"bm_amount"` //裸金属总量
	PmCount int64 `json:"pm_amount"` //物理服务器数量
}

func (*IdcType) TableName() string {
	return `tb_idc`
}
