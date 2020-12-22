package config

import (
	"fmt"
	"gopkg.in/yaml.v2"
	"io/ioutil"
	"os"
	"path/filepath"
)

type AssetConf struct{						//资产/CMDB相关的配置
	Host	string 	`yaml:"host"`
	ItemQuery	string 	`yaml:"itemQuery"`
	ListQuery	string 	`yaml:"listQuery"`
	DeviceDetail	string 	`yaml:"deviceDetail"`
	AlertStat	string 	`yaml:"alertStat"`
	AppStat	string 	`yaml:"appStat"`
	RpStat	string 	`yaml:"rpStat"`
	Apps	string 	`yaml:"apps"`
	//Tenants	string 	`yaml:"tenants"`
	ResourcePools	string 	`yaml:"rps"`
	AlertWeight	*AlertWeight 	`yaml:"alertWeight"`
}

type OtherConf struct{
	Refresh	int64 	`yaml:"refresh"`			//数据刷新间隔，用于刷新提供给Prometheus的指标数据
	Port int64 	`yaml:"port"`			//监听端口
}

type AlertWeight struct{
	Urgent int64 	`yaml:"urgent"`
	Important int64 	`yaml:"important"`
	Secondary int64 	`yaml:"secondary"`
	Normal int64 	`yaml:"normal"`
}

type Conf struct{
	Asset	*AssetConf `yaml:"asset"`
	Other	*OtherConf `yaml:"other"`
}

func GetEnv()string{
	return os.Getenv("env")
}

func IsDebug()bool{
	//env := GetEnv()
	//return env != "product"
	return false
}

func getConfigFilePath()string{
	fileName := "config_debug.yaml"
	env := GetEnv()
	if env == "product" {
		//try to load the production config
		fileName = "/etc/exporter/config.yaml"
	}
	fmt.Printf("use config file: %s\n", fileName)
	str, _ := os.Getwd()
	fileName = filepath.Join(str, fileName)
	fmt.Printf("use config file: %s\n", fileName)
	return fileName
}

func loadConf()(*Conf,error){
	fileName := getConfigFilePath()
	yamlFile,err := ioutil.ReadFile(fileName)
	if err != nil{
		fmt.Printf("read file failed: %+v", err)
		return nil,err
	}
	c := new(Conf)
	err = yaml.Unmarshal(yamlFile, c)
	if err != nil{
		fmt.Printf("Unmarshal failed: %+v", err)
		return nil,err
	}
	return c,nil
}

//func debug(s string){
//	fmt.Println(s)
//}
//func GetItemQueryKey()string{
//	return "itemQuery"
//}
//
//func GetListQueryKey()string{
//	return "listQuery"
//}

func GetPort()int64{
	if configureObj != nil{
		return configureObj.Other.Port
	} else {
		panic("config is NOT initialized")
		return -1
	}
}

func _getUrl(uri string)string{
	return fmt.Sprintf("%s%s", configureObj.Asset.Host, uri)
}

func GetAlertStatUrl()string{
	return _getUrl(configureObj.Asset.AlertStat)
}

func GetDeviceDetailUrl()string{
	return _getUrl(configureObj.Asset.DeviceDetail)
}

func GetAlertWeight()*AlertWeight{
	return configureObj.Asset.AlertWeight
}

func GetAppsUrl()string{
	return _getUrl(configureObj.Asset.Apps)
}

func GetAppUsedUrl()string{
	return _getUrl(configureObj.Asset.AppStat)
}

func GetRpQuotaUrl()string{
	return _getUrl(configureObj.Asset.RpStat)
}

func GetRpsUrl()string{
	return _getUrl(configureObj.Asset.ResourcePools)
}

var configureObj *Conf

func GetConf()(*Conf, error){
	//fast path
	if configureObj != nil{
		return configureObj,nil
	}else{
		confObj,err := loadConf()
		if err != nil{
			return nil,err
		}
		configureObj = confObj
		return configureObj,nil
	}
}

func init(){
	_,_ = GetConf()
	Log = GetLogger()
}
