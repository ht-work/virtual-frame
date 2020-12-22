package rp

import (
	"exporter/httptool"
	. "exporter/models"
	"fmt"
)

var rpInfoList RpInfoList
var rpInfoList_initialized bool = false

func loadAllRps()error{
	list, err := httptool.QueryAllRpList()
	if err != nil{
		fmt.Printf("something wrong in getting rp info list: %+v\n", err)
		return err
	}
	//if config.IsDebug(){
	//	for i:=0;i<len(list);i++{
	//		fmt.Printf("get rp Quota:%+v\n", *list[i])
	//	}
	//}
	rpInfoList_initialized = true
	rpInfoList = list
	return nil
}

func init(){
	go func() {
		_ = loadAllRps()
	}()
}

func GetRpList()(RpInfoList,error){
	if !rpInfoList_initialized{
		err := loadAllRps()
		if err != nil{
			return nil,err
		}
	}
	return rpInfoList,nil
}
