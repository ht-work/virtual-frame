package device

import (
	"exporter/config"
	. "exporter/models"
)

//存储卓望指标名称到资源配置（本系统指标名称、资源类型）的映射，指标名称统一
var kafkaMetricMap map[string]*ResourceConf

func getResourceConf(fieldName string)*ResourceConf{
	return &ResourceConf{
		FieldName:    fieldName,
	}
}

var log = config.GetLogger()

func init(){
	kafkaMetricMap = map[string]*ResourceConf{
		///KVM云主机监控指标
		//单位：%
		"vm_realtime_cpu_avg_util_percent": getResourceConf(GetCPUUsage()),
		"vm_realtime_mem_avg_util_percent": getResourceConf(GetMemUsage()),

		///裸金属监控指标
		//单位：%
		"bm_realtime_agg_cpu_percent_percent_avg":     getResourceConf(GetCPUUsage()),
		"bm_realtime_mem_percent_usedWOBuffersCaches": getResourceConf(GetMemUsage()),

		///裸金属监控指标
		//单位：%
		"pm_realtime_cpu_avg_util_percent_percent_avg": getResourceConf(GetCPUUsage()),
		"pm_realtime_mem_percent_usedWOBuffersCaches":  getResourceConf(GetMemUsage()),
	}
}

func HandleMetricFromKafka(m *PermMetric){
	if len(m.ID) > 0 {
	}else{
		if config.IsDebug(){
			log.Debugf("invalid metric and try to ignore: %v\n", m)
		}
		return
	}
	_,ok := kafkaMetricMap[m.Name]
	if !ok{
		//not valid metric we care
		if config.IsDebug(){
			log.Debugf("invalid metric and try to ignore: %s\n", m.Name)
		}
		return
	}
	UpdateDevicePermData(m)
}
