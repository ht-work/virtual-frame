package model

const (
	AlertLow      = 2
	AlertMid      = 3
	AlertHi       = 4
	AlertCritical = 5
)

type Alert struct {
	AlertType    int    `json:"alert_type" sql:"-"` //require 1 新增，2 解除，3 修改（主要用于持续上报时更新时间）
	AlertId      string `gorm:"column:alert_id;primary_key" json:"alert_id"`
	Source       string `gorm:"column:source;type:varchar(255)" json:"source"` //require `ZABBIX`
	DevId        string `gorm:"column:dev_id;type:varchar(255)" json:"device_id"`
	DevType      string `gorm:"column:dev_type;type:varchar(255)" json:"device_type"`
	IdcTypeName  string `gorm:"column:idc_type_name;type:varchar(255)" json:"idc_type"`      //資源池
	BizSys       string `gorm:"column:biz_sys;type:varchar(255)" json:"biz_sys"`             //所属业务系统
	MoniObject   string `gorm:"column:moni_object" json:"moni_object,omitempty"`             //require 监控对象，用以区分不同类型告警 e.g. “CPU”
	MoniIndex    string `gorm:"column:moni_index;type:longtext" json:"moni_index,omitempty"` //require 告警内容
	CurMoniTime  string `gorm:"column:cur_moni_time" json:"cur_moni_time,omitempty"`         //require 当前检测时间 yyyy-MM-dd HH:mm:ss
	CurMoniValue string `gorm:"column:cur_mon_value;type:longtext" json:"cur_moni_value,omitempty"`
	ItemId       string `gorm:"column:item_id" json:"item_id,omitempty"`                               //require 监控项ID，用于区分不同类型告警
	StartTime    string `gorm:"column:start_time;type:varchar(255)" json:"alert_start_time,omitempty"` //告警开始时间
	EndTime      string `gorm:"column:end_time;type:varchar(255)" json:"alert_end_time,omitempty"`     //告警结束时间
	AlertLevel   string `gorm:"column:alert_level" json:"alert_level"`                                 //告警级别 2 低，3 中，4 高，5 重大
	DevIp        string `gorm:"column:dev_ip;type:varchar(255)" json:"device_ip"`    //告警设备的ip地址
	DevName      string `gorm:"column:dev_name;type:varchar(255)" json:"device_name"`        //告警设备名称       
	AlertCount   string `gorm:"-" json:"count,omitempty"`
}

func (*Alert) TableName() string {
	return `tb_alert`
}
