package main

import (
	"exporter/collector"
	"exporter/config"
	"exporter/httptool"
	"exporter/web"
	"fmt"
	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promhttp"
	"net/http"
)


func init()  {
	InitConfFile()
	///try to unregister the default collector first
	prometheus.Unregister(prometheus.NewGoCollector())
	prometheus.Unregister(prometheus.NewProcessCollector(prometheus.ProcessCollectorOpts{}))
	//注册自身采集器
	prometheus.MustRegister(collector.NewNodeCollector())
}

func InitConfFile(){
	conf,_ := config.GetConf()
	//fmt.Printf("get conf:%+v", conf)
	fmt.Printf("get Asset:%+v", conf.Asset)
	fmt.Printf("get Other:%+v", conf.Other)
	httptool.InitConf(conf)
}

func main() {
	fmt.Printf("Env: %+v and IsDebug:%+v\n", config.GetEnv(), config.IsDebug())
	http.Handle("/perf", new(web.PerfHandler))
	http.Handle("/metrics", promhttp.Handler())
	addr := fmt.Sprintf(":%d", config.GetPort())
	if err := http.ListenAndServe(addr, nil); err != nil {
		fmt.Printf("Error occur when start server %v", err)
	}
}
