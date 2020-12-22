package collector
//
//import (
//	"exporter/collector/device"
//	"exporter/config"
//	. "exporter/httptool"
//	"fmt"
//	"math"
//	"math/rand"
//	"sync"
//	"time"
//)
//
///*
//TODO: ///这个文件用来进行数据mock，项目交付时考虑删除！！！
//*/
//
//func getMetricData_mock()*MetricsForCollector {
//	if !metricDataInitialized{
//		fmt.Printf("NOT initialized and try to fetch first\n")
//		fetchAndUpdate_mock()
//		metricDataInitialized = true
//		fmt.Printf("start timer to do metric data update\n")
//		startTimer_mock()
//	}
//	//如果定时器时间没有到达，始终返回相同的数据
//	//该数据除了第一次初始化之外，仅会被定时器所更新
//	return metricDataForPrometheus
//}
//
//func startTimer_mock(){
//	conf,_ := config.GetConf()
//	sec := conf.Other.Refresh
//	d := time.Duration(sec) * time.Second
//	t := time.NewTimer(d)
//	fmt.Printf("start timer with %+vs\n", sec)
//	//defer t.Stop()
//	go func(t *time.Timer) {
//		for {
//			<- t.C
//			fetchAndUpdate_mock()
//			t.Reset(d)
//		}
//	}(t)
//}
//
//func fetchAndUpdate_mock(){
//	fmt.Printf("update metric data at %+v\n", time.Now())
//	metricDataForPrometheus = fetchData_mock()
//}
//
//var randCount int64 = 0
//
//func getRandInt1(max int)float64{
//	randCount++
//	rand.Seed(time.Now().UnixNano() + randCount)
//	return float64(rand.Intn(max))
//}
//
//func getDeviceData_mock()*device.DeviceMetric {
//	memUsed := getRandInt1(4*1024)
//	memTotal := math.Max(memUsed + 2*1024, 1024*getRandInt1(20))
//	d1 := &device.DeviceMetric{
//		ResourceInfo:ResourceInfo{
//			ID:     "123",
//			IP:     "172.23.0.1",
//			Name:   "vm1",
//			Type:   "VM",
//			App:    "app1",
//			Tenant: "IT",
//			RP:     "Huchi",
//		},
//		ResourceMetric:ResourceMetric{
//			CPUUsage:    getRandInt1(100),
//			MemUsed:     memUsed,
//			MemTotal:    memTotal,
//			MemUsage:    0,
//			Busy:        0,
//			Unbalance:   0,
//			Health:      getRandInt1(100),
//			Unavailable: 0,
//		},
//	}
//	calResourceMetric(d1)
//	return d1
//}
//
//func getDeviceDataList_mock() device.DeviceMetrics {
//	//vm type: vm1、vm2
//	d1 := getDeviceData_mock()
//	d2 := getDeviceData_mock()
//	d2.IP = "172.23.0.2"
//	d2.Name = "vm2"
//	//bm type：bm1
//	d3 := getDeviceData_mock()
//	d3.IP = "172.2.0.1"
//	d3.Type = "BM"
//	d3.Name = "bm1"
//	//pm type: pm1
//	d4 := getDeviceData_mock()
//	d4.App = ""
//	d4.Tenant = ""
//	d4.IP = "172.3.0.1"
//	d4.Type = "PM"
//	d4.Name = "pm1"
//	dm := device.DeviceMetrics{
//		d1,
//		d2,
//		d3,
//		d4,
//	}
//	return dm
//}
//
//func getAppData_mock(quota float64)*AppMetric{
//	base := getRandInt1(int(quota))
//	info := AppInfo{
//		ID:       "12",
//		BMAssigned: base,
//		BMQuota:    quota,
//		VCPUAssigned: base * 16,
//		VCPUQuota:    quota * 32,
//		MemAssigned: base * 64,
//		MemQuota:    quota * 128,
//		VMAssigned: (base+10) * 2,
//		VMQuota:    (quota+10) * 2,
//		Name:     "App1",
//		Tenant:   "IT",
//		RP:       "huchi1",
//	}
//	app := &AppMetric{
//		AppInfo: info,
//	}
//	fillAppMetric(app)
//	return app
//}
//
//func getAppDataList_mock()AppMetrics{
//	app1 := getAppData_mock(60)
//	app2 := getAppData_mock(80)
//	app2.ID = "13"
//	app2.Name = "App2"
//	app3 := getAppData_mock(80)
//	app3.ID = "14"
//	app3.Name = "App3"
//	app3.Tenant = "HR"
//	list := AppMetrics{
//		app1,
//		app2,
//		app3,
//	}
//	return list
//}
//
//func getRpData_mock(quota float64)*RPMetric{
//	base := getRandInt1(int(quota))
//	info := RpInfo{
//		ID:        "rp1",
//		Name:      "huchi1",
//		BMTotal:   quota,
//		VCPUTotal: base * 16,
//		MemTotal:  base * 64,
//		AppCount: quota / 10,
//	}
//	item := &RPMetric{
//		RpInfo: info,
//	}
//	fillRPMetric(item)
//	return item
//}
//
//func getRpDataList_mock()RPMetrics{
//	item1 := getRpData_mock(800)
//	item2 := getRpData_mock(1000)
//	item2.ID = "rp2"
//	item2.Name = "哈尔滨"
//	item3 := getRpData_mock(2000)
//	item3.ID = "rp3"
//	item3.Name = "信息港"
//	list := RPMetrics{
//		item1,
//		item2,
//		item3,
//	}
//	return list
//}
//
//func fetchData_mock()*MetricsForCollector{
//	c := new(MetricsForCollector)
//	var wg sync.WaitGroup
//	//func1 := func() {
//	//	list := getDeviceDataList_mock()
//	//	if list != nil{
//	//		c.Devices = list
//	//	}
//	//	wg.Done()
//	//}
//	func2 := func() {
//		list := getAppDataList_mock()
//		if list != nil{
//			c.Apps = list
//		}
//		wg.Done()
//	}
//	func4 := func() {
//		list := getRpDataList_mock()
//		if list != nil{
//			c.Rps = list
//		}
//		wg.Done()
//	}
//	list := []func(){
//		//func1,
//		func2,
//		func4,
//	}
//	length := len(list)
//	wg.Add(length)
//	for i:=0; i<length; i++{
//		list[i]()
//	}
//	wg.Wait()
//	return c
//}
