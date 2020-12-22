package collector

import (
	"exporter/config"
	. "exporter/models"
	"github.com/prometheus/client_golang/prometheus"
)

type NodeCollector struct {
	//云资源/设备相关
	//以下指标来自性能数据
	cpuUsage			*deviceStatsMetrics
	memUsage			*deviceStatsMetrics
	//以下指标基于以上指标计算而来
	busy			*deviceStatsMetrics			//繁忙度
	unbalance			*deviceStatsMetrics		//不平衡度
	health			*deviceStatsMetrics		//健康度
	unavailable			*deviceStatsMetrics		//不可用，可用度 = 100 - 不可用累加/总次数*100

	///业务/应用系统相关
	//以下指标来自配置数据查询
	app_resource_assign			*deviceStatsMetrics		//资源已分配
	app_resource_quota			*deviceStatsMetrics		//资源配额
	//以下指标基于前面指标计算而来
	app_resource_assign_ratio			*deviceStatsMetrics		//资源分配率
	app_assign_ratio			*deviceStatsMetrics		//业务系统分配率

	///资源池相关
	rp_resource_quota			*deviceStatsMetrics		//资源总数
}

type deviceStatsMetrics struct {
	desc    *prometheus.Desc
	valType prometheus.ValueType
}

var log = config.GetLogger()

func getDeviceMetricDefine()*NodeCollector{
	deviceLabels := getDeviceLabelNames()
	metricDefine := &NodeCollector{
		////从性能数据中直接获取
		cpuUsage: &deviceStatsMetrics{
			desc: prometheus.NewDesc(
				"device_cpu_usage",
				"CPU利用率",
				deviceLabels, nil),
			valType: prometheus.GaugeValue,
		},
		////从性能数据中直接获取
		memUsage: &deviceStatsMetrics{
			desc: prometheus.NewDesc(
				"device_mem_usage",
				"内存利用率",
				deviceLabels, nil),
			valType: prometheus.GaugeValue,
		},
		///根据当前数据计算
		busy: &deviceStatsMetrics{
			desc: prometheus.NewDesc(
				"device_busy",
				"繁忙度",
				deviceLabels, nil),
			valType: prometheus.GaugeValue,
		},
		///根据当前数据计算
		unbalance: &deviceStatsMetrics{
			desc: prometheus.NewDesc(
				"device_unbalance",
				"不平衡度",
				deviceLabels, nil),
			valType: prometheus.GaugeValue,
		},
		//（配置查询）传入resourceId，结合告警查询结果进行内存计算
		health: &deviceStatsMetrics{
			desc: prometheus.NewDesc(
				"device_health",
				"健康度",
				deviceLabels, nil),
			valType: prometheus.GaugeValue,
		},
		//传根据健康度进行内存计算
		unavailable: &deviceStatsMetrics{
			desc: prometheus.NewDesc(
				"device_un_available",
				"不可用",
				deviceLabels, nil),
			valType: prometheus.GaugeValue,
		},
	}
	return metricDefine
}

func defineAppMetric(n *NodeCollector){
	labels := getAppLabelNames()
	appAssignRatioLabels := getAppLabelNamesForAppAssignRatio()
	d := &NodeCollector{
		///（配置查询）查询配置数据得到
		app_resource_assign: &deviceStatsMetrics{
			desc: prometheus.NewDesc(
				"app_resource_assign",
				"业务系统资源实际使用数/已分配",
				labels, nil),
			valType: prometheus.GaugeValue,
		},
		///（配置查询）查询配置数据得到
		app_resource_quota: &deviceStatsMetrics{
			desc: prometheus.NewDesc(
				"app_resource_quota",
				"业务系统资源配额",
				labels, nil),
			valType: prometheus.GaugeValue,
		},
		////根据当前数据计算
		app_resource_assign_ratio: &deviceStatsMetrics{
			desc: prometheus.NewDesc(
				"app_resource_assign_ratio",
				"业务系统资源分配率",
				labels, nil),
			valType: prometheus.GaugeValue,
		},
		////根据当前数据计算
		app_assign_ratio: &deviceStatsMetrics{
			desc: prometheus.NewDesc(
				"app_assign_ratio",
				"业务系统分配率",
				appAssignRatioLabels, nil),
			valType: prometheus.GaugeValue,
		},
	}
	//配置数据查询指标
	n.app_resource_assign = d.app_resource_assign
	n.app_resource_quota = d.app_resource_quota
	//计算得出的指标
	n.app_resource_assign_ratio = d.app_resource_assign_ratio
	n.app_assign_ratio = d.app_assign_ratio
}

func defineRPMetric(n *NodeCollector){
	labels := getRPLabelNames()
	d := &NodeCollector{
		////（配置查询）从配置数据中查询
		rp_resource_quota: &deviceStatsMetrics{
			desc: prometheus.NewDesc(
				"rp_resource_quota",
				"资源池资源总数",
				labels, nil),
			valType: prometheus.GaugeValue,
		},
	}
	n.rp_resource_quota = d.rp_resource_quota
}

//初始化采集器
func NewNodeCollector() prometheus.Collector {
	n := getDeviceMetricDefine()
	defineAppMetric(n)
	defineRPMetric(n)
	return n
}

// Describe returns all descriptions of the collector.
//实现采集器Describe接口
func (n *NodeCollector) Describe(ch chan<- *prometheus.Desc) {
	//device metric
	ch <- n.cpuUsage.desc
	ch <- n.memUsage.desc
	ch <- n.busy.desc
	ch <- n.unbalance.desc
	ch <- n.health.desc
	ch <- n.unavailable.desc
	//app metric
	ch <- n.app_resource_assign.desc
	ch <- n.app_resource_quota.desc
	ch <- n.app_resource_assign_ratio.desc
	ch <- n.app_assign_ratio.desc
	//rp metric
	ch <- n.rp_resource_quota.desc
}

type MetricsForCollector struct{
	Devices DeviceMetrics
	Apps    AppMetrics
	//Tenants TenantMetrics
	Rps     RpMetrics
}

// Collect returns the current state of all metrics of the collector.
//实现采集器Collect接口,真正采集动作
func (n *NodeCollector) Collect(ch chan<- prometheus.Metric) {
	var c *MetricsForCollector
	c = getMetricData()
	writeMetric(n, ch, c)
}

func writeMetric(n *NodeCollector, ch chan<- prometheus.Metric, c *MetricsForCollector){
	method := "writeMetric"
	if c != nil{
		if c.Devices != nil{
			writeDeviceMetric(n, c.Devices, ch)
		}
		if c.Apps != nil{
			writeAppMetric(n, c.Apps, ch)
		}
		if c.Rps != nil{
			writeResourcePoolMetric(n, c.Rps, ch)
		}
	}else{
		log.Printf("in (%s), the metric data is empty\n", method)
	}
}

func writeDeviceMetric(n *NodeCollector, list DeviceMetrics, ch chan<- prometheus.Metric){
	length := len(list)
	for i:=0; i<length; i++{
		item := list[i]
		if item == nil{
			continue
		}
		values := getDeviceLabelValues(item)
		//log.Infof("Write device metric. item: %+v\n", item)
		//log.Infof("Labels: %+v\n", values)

		if(values == nil){
			log.Infof("Get device metric nil. Ignore");
			continue
		}
		v := item.Metric
		if v == nil{
			v = &ResourceMetric{}
			v.Unavailable = 0
			v.Health = 100
			item.Metric = v
		}
		ch <- prometheus.MustNewConstMetric(n.cpuUsage.desc, n.cpuUsage.valType, v.CPUUsage, values...)
		ch <- prometheus.MustNewConstMetric(n.memUsage.desc, n.memUsage.valType, v.MemUsage, values...)
		ch <- prometheus.MustNewConstMetric(n.busy.desc, n.busy.valType, v.Busy, values...)
		ch <- prometheus.MustNewConstMetric(n.unbalance.desc, n.unbalance.valType, v.Unbalance, values...)
		ch <- prometheus.MustNewConstMetric(n.health.desc, n.health.valType, v.Health, values...)
		ch <- prometheus.MustNewConstMetric(n.unavailable.desc, n.unavailable.valType, v.Unavailable, values...)
	}
}

func writeAppMetric(n *NodeCollector, list AppMetrics, ch chan<- prometheus.Metric){
	length := len(list)
	for i:=0; i<length; i++{
		v := list[i]
		if v == nil{
			continue
		}
		quota := v.Quota
		if quota == nil{
			quota = &AppQuota{}
			v.Quota = quota
		}
		used := v.Used
		if used == nil{
			used = &AppUsed{}
			v.Used = used
		}
		usage := v.Usage
		if usage == nil{
			usage = &AppUsage{}
			v.Usage = usage
		}
		//裸金属
		values_bm := getAppLabelValues(v, GetBareMetalType())
		ch <- prometheus.MustNewConstMetric(n.app_resource_assign.desc, n.app_resource_assign.valType, used.BM, values_bm...)
		ch <- prometheus.MustNewConstMetric(n.app_resource_quota.desc, n.app_resource_quota.valType, quota.BM, values_bm...)
		ch <- prometheus.MustNewConstMetric(n.app_resource_assign_ratio.desc, n.app_resource_assign_ratio.valType, usage.BM, values_bm...)
		//虚拟机
		values_vm := getAppLabelValues(v, GetVMType())
		ch <- prometheus.MustNewConstMetric(n.app_resource_assign.desc, n.app_resource_assign.valType, used.VM, values_vm...)
		ch <- prometheus.MustNewConstMetric(n.app_resource_quota.desc, n.app_resource_quota.valType, quota.VM, values_vm...)
		ch <- prometheus.MustNewConstMetric(n.app_resource_assign_ratio.desc, n.app_resource_assign_ratio.valType, usage.VM, values_vm...)
		//vCPU
		values_vcpu := getAppLabelValues(v, getVCPUType())
		ch <- prometheus.MustNewConstMetric(n.app_resource_assign.desc, n.app_resource_assign.valType, used.VMVcpu, values_vcpu...)
		ch <- prometheus.MustNewConstMetric(n.app_resource_quota.desc, n.app_resource_quota.valType, quota.VMVcpu, values_vcpu...)
		ch <- prometheus.MustNewConstMetric(n.app_resource_assign_ratio.desc, n.app_resource_assign_ratio.valType, usage.VMVcpu, values_vcpu...)
		//内存
		values_mem := getAppLabelValues(v, getMemType())
		ch <- prometheus.MustNewConstMetric(n.app_resource_assign.desc, n.app_resource_assign.valType, used.VMMem, values_mem...)
		ch <- prometheus.MustNewConstMetric(n.app_resource_quota.desc, n.app_resource_quota.valType, quota.VMMem, values_mem...)
		ch <- prometheus.MustNewConstMetric(n.app_resource_assign_ratio.desc, n.app_resource_assign_ratio.valType, usage.VMMem, values_mem...)
		//app分配率
		values_app := getAppLabelValues(v, "")
		ch <- prometheus.MustNewConstMetric(n.app_assign_ratio.desc, n.app_assign_ratio.valType, usage.APPUsage, values_app...)
	}
}

func writeResourcePoolMetric(n *NodeCollector, list RpMetrics, ch chan<- prometheus.Metric){
	length := len(list)
	for i:=0; i<length; i++{
		item := list[i]
		if item == nil{
			continue
		}
		v := item.Quota
		if v == nil{
			v = &RpQuota{}
			item.Quota = v
		}
		//裸金属
		values_BM := getRPLabelValues(item, GetBareMetalType())
		ch <- prometheus.MustNewConstMetric(n.rp_resource_quota.desc, n.rp_resource_quota.valType, v.BM, values_BM...)
		//虚拟机
		values_vm := getRPLabelValues(item, GetVMType())
		ch <- prometheus.MustNewConstMetric(n.rp_resource_quota.desc, n.rp_resource_quota.valType, v.VM, values_vm...)
		//vCPU
		values_vcpu := getRPLabelValues(item, getVCPUType())
		ch <- prometheus.MustNewConstMetric(n.rp_resource_quota.desc, n.rp_resource_quota.valType, v.VMVcpu, values_vcpu...)
		//内存
		values_mem := getRPLabelValues(item, getMemType())
		ch <- prometheus.MustNewConstMetric(n.rp_resource_quota.desc, n.rp_resource_quota.valType, v.VMMem, values_mem...)
	}
}


