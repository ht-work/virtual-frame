package rest

import (
	"iaas/pkgs/config"
	"fmt"
)

var (
	initWholeData = config.Conf.InitWholeData
)


func Run() {
	if(initWholeData){
		fmt.Printf("init whole data is true.\n")
		GetAllCmdbRecode()
		GetAllIdcType()
		GetAllBizSystem()
		//GetAllTenant()
		GetBizQuota()
	}else{
		fmt.Printf("init whole data is false.\n")
	}
}
