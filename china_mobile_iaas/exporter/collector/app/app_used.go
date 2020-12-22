package app

import (
	"exporter/httptool"
	. "exporter/models"
)

func respToUsed(resp *AppResp)*AppUsed{
	return &AppUsed{
		AppInfo: resp.AppInfo,
		BM:      strToFloat(resp.BM),
		VM:      strToFloat(resp.VM),
		VMVcpu:      strToFloat(resp.VMVcpu),
		VMMem:      strToFloat(resp.VMMem),
	}
}

func GetAppUsed(appId, tenantId, rpId string)(*AppUsed,error){
	resp, err := httptool.QueryAppUsed(appId, tenantId, rpId)
	if err == nil{
		used := respToUsed(resp)
		return used,nil
	}else{
		// 如果出错，就返回默认对象
		entry := &AppUsed{}
		entry.ID = appId
		return entry,nil
	}
}
