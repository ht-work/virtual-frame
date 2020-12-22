package metric

//func load_conf(){
//	conf,_ := config.GetConf()
//	fmt.Printf("get conf:%+v", conf)
//	InitConf(conf)
//}
//
//func mock_url(key string, url string){
//	SetConfAssetProperty(key, url)
//}
//
//func prepareTestData()(*PermMetric, *PermMetric, *PermMetric, *device.DeviceMetric){
//	resourceId := "123"
//	pCPU := &PermMetric{
//		ID:    resourceId,
//		Name:  "vm_realtime_cpu_avg_util_percent",
//		Type:  "",
//		Time:  time.Now().Unix(),
//		Value: 23,
//	}
//	pMemUsed := &PermMetric{
//		ID:    resourceId,
//		Name:  "vm_realtime_mem_used_size",	//单位：MB
//		Type:  "",
//		Time:  time.Now().Unix(),
//		Value: 2200,
//	}
//	pMemTotal := &PermMetric{
//		ID:    resourceId,
//		Name:  "vm_realtime_mem_total_size",	//单位：MB
//		Type:  "",
//		Time:  time.Now().Unix(),
//		Value: 8 * 1024,
//	}
//	conf1 := kafkaMetricMap[pCPU.Name]
//	metric := &device.DeviceMetric{}
//	device.updateDeviceMetric(pCPU, conf1, metric)
//	conf2 := kafkaMetricMap[pMemUsed.Name]
//	device.updateDeviceMetric(pMemUsed, conf2, metric)
//	conf3 := kafkaMetricMap[pMemTotal.Name]
//	device.updateDeviceMetric(pMemTotal, conf3, metric)
//	return pCPU, pMemUsed, pMemTotal, metric
//}
//
//func TestUpdateDeviceMetric(t *testing.T){
//	pCPU,pMemUsed,pMemTotal,metric := prepareTestData()
//
//	res := metric.ID == pCPU.ID && metric.Type == "VM" &&
//		metric.CPUUsage == pCPU.Value && metric.MemUsed == pMemUsed.Value &&
//		metric.MemTotal == pMemTotal.Value
//	if !res{
//		t.Errorf("error in updateDeviceMetric\n")
//	}
//}
//
//func TestFillDeviceMetric(t *testing.T) {
//	pCPU,pMemUsed,pMemTotal,metric := prepareTestData()
//	resourceId := pCPU.ID
//	info := ResourceInfo{
//		ID:     "123",
//		IP:     "172.23.0.1",
//		Name:   "vm1",
//		Type:   "VM",
//		App:    "app1",
//		Tenant: "IT",
//		RP:     "Huchi",
//	}
//	//mock http server
//	ts := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
//		_ = r.ParseForm()
//		itemType := r.Form.Get("type")
//		w.WriteHeader(http.StatusOK)
//		w.Header().Set("Content-Type", "application/json")
//		var infoInBytes []byte
//		if itemType == "alert"{
//			list := []*AlertItem{
//				&AlertItem{
//					AlertId:    "1",
//					DeviceId:   resourceId,
//					Level:      "2",
//					ItemId:     "",
//					EndTime:    fmt.Sprintf("%d",time.Now().UnixNano()),
//					ObjectType: "",
//				},
//				&AlertItem{
//					AlertId:    "2",
//					DeviceId:   resourceId,
//					Level:      "3",
//					ItemId:     "",
//					EndTime:    fmt.Sprintf("%d",time.Now().UnixNano()),
//					ObjectType: "",
//				},
//				&AlertItem{
//					AlertId:    "3",
//					DeviceId:   resourceId,
//					Level:      "4",
//					ItemId:     "",
//					EndTime:    fmt.Sprintf("%d",time.Now().UnixNano()),
//					ObjectType: "",
//				},
//			}
//			infoInBytes,_ = json.Marshal(list)
//		}else if itemType == "device"{
//			infoInBytes,_ = json.Marshal(info)
//		}else{
//			fmt.Printf("unsupported item type: %+v\n", itemType)
//		}
//		w.Write(infoInBytes)
//	}))
//	defer ts.Close()
//
//	load_conf()
//	mock_url(config.GetItemQueryKey(), ts.URL)
//
//	fillDeviceMetric(metric)
//
//	var expectedScore float64
//	expectedScore = 100 - 1*1 - 5*1 - 10*1
//	res := metric.ID == pCPU.ID && metric.Name == info.Name && metric.App == info.App
//	res = res && metric.Tenant == info.Tenant && metric.RP == info.RP && metric.CPUUsage == pCPU.Value
//	res = res && metric.MemUsage == pMemUsed.Value/pMemTotal.Value * 100 && metric.Health == expectedScore
//	res = res && metric.Busy == (metric.MemUsage + metric.CPUUsage)/2
//	res = res && metric.Unbalance == math.Abs(metric.CPUUsage - metric.MemUsage)
//	res = res && metric.Unavailable == 0
//	if !res{
//		t.Errorf("error in fillDeviceMetric\n")
//	}
//}
