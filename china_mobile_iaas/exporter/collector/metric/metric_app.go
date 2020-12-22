package metric

import (
	"exporter/collector/algo"
	"exporter/collector/app"
	. "exporter/models"
	"fmt"
	"sync"
)

func fillAppMetric(am *AppMetric){
	used := am.Used
	if used == nil{
		used = &AppUsed{}
		am.Used = used
	}
	quota := am.Quota
	if quota == nil{
		quota = &AppQuota{}
		am.Quota = quota
	}
	p := am.Usage
	if p == nil{
		p = &AppUsage{}
		am.Usage = p
	}
	p.BM = algo.GetAssignRatio(used.BM, quota.BM)
	p.VM = algo.GetAssignRatio(used.VM, quota.VM)
	p.VMVcpu = algo.GetAssignRatio(used.VMVcpu, quota.VMVcpu)
	p.VMMem = algo.GetAssignRatio(used.VMMem, quota.VMMem)
	p.APPUsage = algo.GetAppAssignRatio(am)
}

func GetAppMetrics()(AppMetrics,error){
	//get list
	//query item one by one
	appQuotaObj,err := app.GetAppQuotaMap()
	if err != nil {
		fmt.Printf("get error in GetAppQuotaMap: %+v\n", err)
		return nil,err
	}
	length := len(appQuotaObj)
	appMetricsList := make(AppMetrics, length)

	const metricAppChanLength int = 10
	metricAppChan := make(chan int, metricAppChanLength)

	var mu sync.Mutex
	var wg sync.WaitGroup
	for k,v := range appQuotaObj{
		//增加WG的数量
		wg.Add(1)
		// 使用chan限制go-routine数量，如果在通道允许范围内，可以执行go-routine，否则则阻塞
		// 直到chan有空余空间（某个go-routine执行完毕，释放空间），则允许继续执行
		metricAppChan <- 1

		go func(key string, quotaInfo *AppQuota) {
			//一份配额数据的key为 appId+tenantId+RPId
			//所以这里传入的key为 appId+tenantId+RPId
			defer wg.Done()
			appId := quotaInfo.AppInfo.ID
			tenantId := quotaInfo.AppInfo.Tenant
			rpId := quotaInfo.AppInfo.RP

			// fmt.Printf("Ready to get app used. Key: %s, AppId: %s, tenantId: %s, rpId: %s\n", key, 
		    //     appId, tenantId, rpId)
			usedInfo,err := app.GetAppUsed(appId, tenantId, rpId)
			if err != nil{
				fmt.Printf("error in GetAppUsed(%s) : %+v\n", appId, err)
				<- metricAppChan
				return
			}
			metric := &AppMetric{
				Quota: quotaInfo,
				Used: usedInfo,
			}
			// fmt.Printf("metric:\n %+v \n", metric)
			// fmt.Printf("Quota: %+v \n", metric.Quota)
			// fmt.Printf("Used: %+v \n", metric.Used)
			
			fillAppMetric(metric)
			// fmt.Printf("Quota: %+v \n", metric.Quota)
			// fmt.Printf("Used: %+v \n", metric.Used)
			// fmt.Printf("Usage: %+v \n", metric.Usage)
			mu.Lock()
			appMetricsList = append(appMetricsList, metric)
			mu.Unlock()
			<- metricAppChan
		}(k, v)
	}

	wg.Wait()
	// for i:=0; i<len(appMetricsList); i++{
	// 	item := appMetricsList[i]
	// 	if item != nil{
	// 		fmt.Printf("appMetricsList %d:\n", i)
	// 		fmt.Printf("quota: %+v:\n", item.Quota)
	// 		fmt.Printf("used: %+v:\n", item.Used)
	// 		fmt.Printf("usage: %+v:\n", item.Usage)
	// 	}
		
	// }
	
	return appMetricsList,nil
}
