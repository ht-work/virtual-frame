package metric

import (
	"exporter/collector/algo"
	"exporter/collector/device"
	. "exporter/models"
	"fmt"
)

//基于已有的指标数据，丰富设备指标信息，包括计算繁忙度、标签相关的数据（配置关联数据）等
func fillDeviceMetric(p *DeviceMetric, alertScore int64){
	m := p.Metric
	m.Health = float64(alertScore)
	m.Busy = algo.GetBusy(m.CPUUsage, m.MemUsage)
	m.Unbalance = algo.GetUnbalance(m.CPUUsage, m.MemUsage)
	m.Unavailable = algo.GetUnavailable(m.Health)
}

/*
获取所有设备指标数据：
	1、获取所有设备数据（从kafka中接收的增量数据，包含部分性能数据，如CPU、内存等）
	2、计算相关的指标，如繁忙度
	3、同时查询相关的配置数据，构建标签，如所属应用系统、租户、资源池等，构造Prometheus所需要的指标格式
	4、返回结果列表，用于Collect()函数进行指标查询返回
 */
func GetDeviceMetrics()DeviceMetrics {
	////获取截止到当前函数调用时的全部性能指标数据，构建新的指标数据
	// 重置指标数据、告警分值/健康度数据
	deviceMetrics := device.RestoreAllPermData()
	deviceAlerts := device.RestoreAllAlertScore()

	length := len(deviceMetrics)
	var count int32 = 0
	resultList := make(DeviceMetrics, length)
	fmt.Printf("get device cmdb info for ids. count: %d", len(deviceMetrics))
	for id,v := range deviceMetrics{
		//fmt.Printf("%s\n", id)
		item := &DeviceMetric{
			CMDB: device.GetDeviceCMDBById(id),
			Metric: v,
		}
		fillDeviceMetric(item, deviceAlerts[id])
		resultList[count] = item
		count++
	}
	fmt.Printf("get device cmdb info for ids done.")
	return resultList
}


