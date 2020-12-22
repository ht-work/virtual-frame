package rp

import (
	"exporter/httptool"
	. "exporter/models"
)

func GetRpQuota(id string)(*RpQuota,error){
	return httptool.QueryRpQuota(id)
}
