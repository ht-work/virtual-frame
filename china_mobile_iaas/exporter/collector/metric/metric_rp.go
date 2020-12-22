package metric

import (
	"exporter/collector/rp"
	. "exporter/models"
	"fmt"
	"sync"
)

//type RPMetrics []*RPMetric
func GetResourcePoolMetrics()(RpMetrics,error){
	//get list
	//query item one by one
	var resList RpMetrics
	list,err := rp.GetRpList()
	if err != nil{
		fmt.Printf("error in QueryRPList: %+v\n", err)
		return nil,err
	}else{
		if list != nil && len(list) > 0{
			length := len(list)
			resList = make(RpMetrics, length)

			const metricRpChanLength int = 2
			metricRpChan := make(chan int, metricRpChanLength)

			var mu sync.Mutex
			wg := new(sync.WaitGroup)

			for i:=0;i<length;i++{
				//增加WG的数量
				wg.Add(1)
				// 使用chan限制go-routine数量，如果在通道允许范围内，可以执行go-routine，否则则阻塞
				// 直到chan有空余空间（某个go-routine执行完毕，释放空间），则允许继续执行
				metricRpChan <- 1
				go func(id string) {
					defer wg.Done()
					rpQuota,err := rp.GetRpQuota(id)
					if err != nil{
						fmt.Printf("error in QueryRpById(%s) : %+v\n", id, err)
						<- metricRpChan
						return
					}
					//fmt.Printf("RPQuota: %+v \n", rpQuota)
					metric := &RpMetric{
						Quota: rpQuota,
					}
					//fmt.Printf("metric:\n %+v \n", metric)
					//fmt.Printf("Quota: %+v \n", metric.Quota)
					mu.Lock()
					resList = append(resList, metric)
					mu.Unlock()
					<- metricRpChan
				}(list[i].ID)
			}
			wg.Wait()
		}
		return resList,nil
	}
}
