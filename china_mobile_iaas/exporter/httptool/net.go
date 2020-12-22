package httptool

import (
	"exporter/config"
	"gopkg.in/resty.v1"
)

var localConf *config.Conf

func InitConf(conf *config.Conf){
	if conf == nil ||
		(conf != nil && conf.Asset == nil){
		panic("error in getting config from configuration file")
	}
	localConf = conf
}

// this method is for UT only
func SetConfAssetPropertyForUT(key string, v string) {
	if key == config.GetDeviceDetailUrl(){
		localConf.Asset.Host = v
		localConf.Asset.DeviceDetail = ""
	} else if key == config.GetAlertStatUrl(){
		localConf.Asset.Host = v
		localConf.Asset.AlertStat = ""
	} else if key == config.GetAppsUrl(){
		localConf.Asset.Host = v
		localConf.Asset.Apps = ""
	}
}

const inner_token = "chinamobileiaaschinamobileiaas"

func get(url string, params map[string]string)([]byte,error){
	resp, err := resty.R().SetHeader("token", inner_token).SetQueryParams(params).Get(url)
	if err != nil{
		return nil,err
	}
	return resp.Body(),nil
}


