package httptool

import (
	"encoding/json"
	"errors"
	"exporter/config"
	. "exporter/models"
)

func QueryAppQuotaList()(AppRespList,error){
	objBytes,err := sendGetRequest(config.GetAppsUrl(), nil)
	if err != nil {
		return nil, err
	}
	list := make(AppRespList,0)
	err = json.Unmarshal(objBytes, &list)
	if err == nil{
		return list,nil
	}else{
		return nil,errors.New("convert to ResourceQuotaList failed")
	}
}

func QueryAllRpList()(RpInfoList,error){
	objBytes,err := sendGetRequest(config.GetRpsUrl(), nil)
	if err != nil {
		return nil, err
	}
	list := make(RpInfoList,0)
	err = json.Unmarshal(objBytes, &list)
	if err == nil{
		return list,nil
	}else{
		return nil,errors.New("convert to RpInfoList failed")
	}
}
