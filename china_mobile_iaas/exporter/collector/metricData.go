package collector

import (
	"exporter/collector/metric"
	"exporter/config"
	"fmt"
	"sync"
	"time"
)

var metricDataForPrometheus *MetricsForCollector
var metricDataInitialized bool

func getMetricData()*MetricsForCollector {
	if !metricDataInitialized{
		fmt.Printf("NOT initialized and try to fetch first\n")
		fetchAndUpdate()
		metricDataInitialized = true
		fmt.Printf("start timer to do metric data update\n")
		startTimer()
	}
	//如果定时器时间没有到达，始终返回相同的数据
	//该数据除了第一次初始化之外，仅会被定时器所更新
	return metricDataForPrometheus
}

func startTimer(){
	conf,_ := config.GetConf()
	sec := conf.Other.Refresh
	d := time.Duration(sec) * time.Second
	t := time.NewTimer(d)
	fmt.Printf("start timer with %+vs\n", sec)
	//as this method is NOT in the main, so Stop() should not be called
	//defer t.Stop()
	go func(t *time.Timer) {
		for {
			<- t.C
			fetchAndUpdate()
			t.Reset(d)
		}
	}(t)
}

func fetchAndUpdate(){
	metricDataForPrometheus = fetchData()
}

//获取数据/数据更新
func fetchData()*MetricsForCollector{
	method := "getMetricData"
	c := new(MetricsForCollector)
	var wg sync.WaitGroup
	func1 := func() {
		list := metric.GetDeviceMetrics()
		if list != nil{
			c.Devices = list
		}else{
			fmt.Printf("in (%s), GetDeviceMetrics() return nil\n", method)
		}
		wg.Done()
	}
	func2 := func() {
		list,err := metric.GetAppMetrics()
		if err == nil && list != nil{
			c.Apps = list
		}else{
			fmt.Printf("in (%s), GetAppMetrics() return error: %+v\n", method, err)
		}
		wg.Done()
	}
	func3 := func() {
		list,err := metric.GetResourcePoolMetrics()
		if err == nil && list != nil{
			c.Rps = list
		}else{
			fmt.Printf("in (%s), GetResourcePoolMetrics() return error: %+v\n", method, err)
		}
		wg.Done()
	}
	list := []func(){
		func1,
		func2,
		func3,
	}
	length := len(list)
	wg.Add(length)
	for i:=0; i<length; i++{
		list[i]()
	}
	wg.Wait()
	return c
}
