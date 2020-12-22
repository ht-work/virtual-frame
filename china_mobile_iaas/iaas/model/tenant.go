package model

//type FullTenant struct {
//	Count int      `json:"totalSize"`
//	Data  []Tenant `json:"data"`
//}

//type Tenant struct {
//	TenantId   string `gorm:"column:tenant_id" json:"id"`
//	TenantName string `gorm:"column:tenant_name" json:"orgName"`
//	ParentId   string `gorm:"column:parent_id" json:"parent_id"`
//	ParentName string `gorm:"column:parent_name" json:"parent_id_orgName_name"`
//}
//
//func (*Tenant) TableName() string {
//	return `tb_tenant`
//}




// type TenantQuotaDetail struct {
// 	TenantId    string `json:"id"`
// 	AppCount     int64 `json:"app_count"`
// 	Dept1           string `json:"department1"`
// 	Dept1Name       string `json:"department1_orgName_name"`
// 	Dept2           string `json:"department2"`
// 	Dept2Name       string `json:"department2_orgName_name"`
// 	IdcType         string `json:"idcType"`
// 	IdcTypeName     string `json:"idcType_idc_name_name"`
// 	YzjAllocate     int64 `json:"yzj_allocation_amount"`           //云主机已分配设备总台数
// 	YzjVcpuAllocate int64 `json:"yzj_vcpu_allocation_amount"` //云主机已分配核数VCPU总量（个）
// 	YzjMemAllocate  int64 `json:"yzj_mem_allocation_amount"`   //云主机已分配内存总额
// 	LjsAllocate int64 `json:"ljs_allocation_amount"` //裸金属已分配量
// }

type TenantDetail struct {
	TenantId    string `json:"id"`
	AppCount     int64 `json:"app_count"`
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
