package app

import (
	"exporter/httptool"
	. "exporter/models"
	"fmt"
	"strconv"
)

var appQuotaMap AppQuotaMap
var appQuotaMap_initialized bool = false

func strToFloat(str string)float64{
	var v float64 = 0
	if len(str) > 0{
		f, err := strconv.ParseFloat(str, 64)
		if err != nil{
			fmt.Printf("convert the str:%s to float failed\n", str)
			f = 0
		}
		v = f
	}
	return v
}

func respToQuota(resp *AppResp)*AppQuota{
	return &AppQuota{
		AppInfo: resp.AppInfo,
		BM:      strToFloat(resp.BM),
		VM:      strToFloat(resp.VM),
		VMVcpu:      strToFloat(resp.VMVcpu),
		VMMem:      strToFloat(resp.VMMem),
	}
}

func loadAppQuota()error{
	list, err := httptool.QueryAppQuotaList()
	if err != nil{
		fmt.Printf("something wrong in getting app quota list: %+v\n", err)
		return err
	}
	//if config.IsDebug(){
	//	for i:=0;i<len(list);i++{
	//		fmt.Printf("get app Quota:%+v\n", *list[i])
	//	}
	//}
	for i:=0; i<len(list); i++{
		item := list[i]
		//一份配额数据的key为 appId+tenantId+RPId
		appQuotaMap[item.ID + item.Tenant + item.RP] = respToQuota(item)
	}
	//if config.IsDebug(){
	//	for k,v := range appQuotaMap{
	//		fmt.Printf("k:%s, v:%+v\n", k, *v)
	//	}
	//}
	appQuotaMap_initialized = true
	return nil
}

func init(){
	appQuotaMap = make(AppQuotaMap)
	go func() {
		_ = loadAppQuota()
	}()
}

func GetAppQuotaMap()(AppQuotaMap,error){
	if !appQuotaMap_initialized{
		err := loadAppQuota()
		if err != nil{
			return nil,err
		}
	}
	return appQuotaMap,nil
}
