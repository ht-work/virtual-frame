package httptool

import (
	"encoding/json"
	"errors"
	"exporter/config"
	. "exporter/models"
	"fmt"
	"strconv"
)

var log = config.GetLogger()

//type RpInfo struct{
//	ID string			`json:"id"`
//	Name string			`json:"name"`
//	BMTotal	float64		`json:"bmCount"`	//裸金属总数
//	VCPUTotal	float64	`json:"vcpuTotal"`	//vCPU总数，此处应该是指物理CPU核数，用于计算分配率：vCPU/CPU，可能会超配
//	MemTotal	float64	`json:"memTotal"`	//内存总数
//	AppCount	float64	`json:"appCount"`		//应用系统数量
//}
////****************************资源池****************************
////根据id，获取资源池信息：设备总数、应用系统数量
///// TODO
//func QueryRpById(id string)(*RpInfo,error){
//	objBytes,err := getItemById(id, "rp")
//	if err != nil {
//		return nil, err
//	}
//	var obj RpInfo
//	err = json.Unmarshal(objBytes, &obj)
//	if err == nil{
//		return &obj,nil
//	}else{
//		return nil,errors.New("convert to RpInfo failed")
//	}
//}
////****************************资源池****************************
//
//
//type TenantInfo struct{
//	ID string			`json:"id"`
//	Name string			`json:"name"`
//	//AppCount	int64	`json:"appCount"`
//	RP	string 			`json:"rp"`		//所属资源池
//}
////****************************租户****************************
////根据id，获取租户信息：业务系统数量
///// TODO
//func QueryTenantById(id string)(*TenantInfo, error){
//	objBytes,err := getItemById(id, "tenant")
//	if err != nil {
//		return nil, err
//	}
//	var obj TenantInfo
//	err = json.Unmarshal(objBytes, &obj)
//	if err == nil{
//		return &obj,nil
//	}else{
//		return nil,errors.New("convert to TenantInfo failed")
//	}
//}
////****************************租户****************************
//
//
//type AppInfo struct{
//	BMAssigned float64	`json:"bmassign"`	//裸金属已分配数
//	BMQuota	float64	`json:"bmquota"`//裸金属配额
//	VMAssigned float64	`json:"vmassign"`	//虚拟机已分配数
//	VMQuota	float64	`json:"vmquota"`//虚拟机配额
//	VCPUAssigned float64	`json:"vcpuassign"`	//vCPU已分配数
//	VCPUQuota	float64	`json:"vcpuquota"`//vCPU配额
//	MemAssigned float64	`json:"memassign"`	//内存已分配数
//	MemQuota	float64	`json:"memquota"`//内存配额
//	ID string			`json:"id"`
//	Name string			`json:"name"`
//	Tenant	string 			`json:"tenant"`		//所属租户
//	RP	string 			`json:"rp"`		//所属资源池
//}
////****************************业务/应用系统****************************
////根据id，获取业务系统信息：已分配资源、资源配额，进而计算分配率
///// TODO
//func QueryAppById(id string)(*AppInfo,error){
//	objBytes,err := getItemById(id, "app")
//	if err != nil {
//		return nil, err
//	}
//	var obj AppInfo
//	err = json.Unmarshal(objBytes, &obj)
//	if err == nil{
//		return &obj,nil
//	}else{
//		return nil,errors.New("convert to AppInfo failed")
//	}
//}
////****************************业务/应用系统****************************

//****************************告警统计****************************
/*
查询设备的告警统计
 */
func QueryAlertStat(id string)(*StatAlert, error){
	params := map[string]string{
		"id": id,
	}
	url := config.GetAlertStatUrl()
	objBytes,err := sendGetRequest(url, params)
	if err != nil {
		return nil, err
	}
	var alertStat StatAlert
	alertStat.ID = id
	if config.IsDebug(){
		log.Debugf("alert result: %s\n", string(objBytes))
	}
	err = json.Unmarshal(objBytes, &alertStat)
	if err == nil{
		return &alertStat,nil
	}else{
		return nil,errors.New("convert to Alerts failed")
	}
}
//****************************告警统计****************************


//****************************设备配置信息查询****************************
////根据resourceid 查询配置信息
func QueryDeviceCMDB(id string)(*ResourceInfo, error){
	url := config.GetDeviceDetailUrl()
	url = fmt.Sprintf("%s/%s", url, id)
	objBytes,err := sendGetRequest(url, nil)
	if err != nil {
		return nil, err
	}
	var obj ResourceInfo
	err = json.Unmarshal(objBytes, &obj)
	if err == nil{
		return &obj,nil
	}else{
		return nil,errors.New("convert to ResourceInfo failed")
	}
}
//****************************设备配置信息查询****************************

//****************************业务系统统计信息查询****************************
////根据appid查询已使用/已分配信息
func QueryAppUsed(appId, tenantId, rpId string)(*AppResp, error){
	url := config.GetAppUsedUrl()
	url = fmt.Sprintf("%s?id=%s&tenantId=%s&rpId=%s", url, appId, tenantId, rpId)
	objBytes,err := sendGetRequest(url, nil)
	//fmt.Printf("Url: %s \n Get app used response: %s \n", url, objBytes)
	if err != nil {
		return nil, err
	}
	//这里因为不知道之前的开发者的想法，但是字段有没有对上，所以使用一个中间字段过度一下，保证返回值不变
	var obj AppUsed
	var result AppResp
	err = json.Unmarshal(objBytes, &obj)
	if err == nil{
		result.AppInfo = obj.AppInfo
		result.BM = strconv.FormatFloat(obj.BM, 'E', -1, 64)
		result.VM = strconv.FormatFloat(obj.VM, 'E', -1, 64)
		result.VMVcpu = strconv.FormatFloat(obj.VMVcpu, 'E', -1, 64)
		result.VMMem = strconv.FormatFloat(obj.VMMem, 'E', -1, 64)
		return &result,nil
	}else{
		return nil,errors.New("convert to AppUsed failed")
	}
}
//****************************业务系统统计信息查询****************************

//****************************资源池统计信息查询****************************
////根据appid查询已使用/已分配信息
func QueryRpQuota(id string)(*RpQuota, error){
	url := config.GetRpQuotaUrl()
	url = fmt.Sprintf("%s?id=%s", url, id)
	objBytes,err := sendGetRequest(url, nil)
	//fmt.Printf("Url: %s \n Get app used response: %s \n", url, objBytes)
	if err != nil {
		return nil, err
	}

	//这里因为不知道之前的开发者的想法，但是字段有没有对上，所以使用一个中间字段过度一下，保证返回值不变
	var obj RpQuotaInner
	var result RpQuota
	err = json.Unmarshal(objBytes, &obj)
	if err == nil{
		result.ID = obj.Id
		result.BM = obj.BM
		result.VM = obj.VM
		result.VMVcpu = obj.Vcpu
		result.VMMem = obj.MEM
		return &result,nil
	}else{
		result = RpQuota{}
		result.ID = id
		//return nil,errors.New("convert to RpQuota failed")
		return &result, nil
	}
}
//****************************资源池统计信息查询****************************
