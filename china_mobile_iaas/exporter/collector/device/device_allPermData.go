package device

import (
	"exporter/config"
	. "exporter/models"
	"fmt"
	"time"
)

/*
该全局变量，需要通过方法进行访问，不允许直接访问！

id -> metric
{
	id1: { metric1:xx, metric2:xx },
	id2: { metric1:xx, metric2:xx },
	id3: { metric1:xx, metric2:xx },
}
*/
var allMetrics IdToMetric
//var permDataMutex sync.Mutex
// 实际处理性能数据的通道
var newDeviceChan chan *PermMetric
// 通道的缓冲区长度
const newDeviceChanLength int = 5
// go协程数量，可以并发读取通道
const gRoutineCountForDeviceMetricHandle = 5

const gRoutineCountForDevicePermWrite = 1
// 通知通道，用于性能数据队列的写入/读取协程进行通知
//const queueNotifyChanLength int = 10
//var queueNotifyChan chan bool

// 性能数据队列，简单写入和读取
const PermDataQueueSize int = 100001
var permQueue *MyQueue

func init(){
	newDeviceChan = make(chan *PermMetric, newDeviceChanLength)
	//queueNotifyChan = make(chan bool, queueNotifyChanLength)
	permQueue = new(MyQueue)
	permQueue.InitQueue(PermDataQueueSize)
	// 1个往队列写入，多个读取（等待队列写入）
	for i:=0; i<gRoutineCountForDevicePermWrite; i++{
		go writePermToChan()
	}
	// 初始化多个go协程来处理设备性能数据（即更新配置数据以及告警数据）
	for i:=0; i<gRoutineCountForDeviceMetricHandle; i++{
		go handleDevicePermDataFromChan()
	}
}

//type DeviceMetrics []*DeviceMetric
//type DeviceMetric collector.ResourceMetric
//resourceid到指标的字典
//type IdToMetric map[string]*ResourceMetric //id -> metric

func updateDeviceMetric(m *PermMetric, metric *ResourceMetric){
	if m == nil{
		return
	}
	conf := kafkaMetricMap[m.Name]
	metric.ID = m.ID
	switch conf.FieldName {
	case GetCPUUsage():
		metric.CPUUsage = m.Value
	case GetMemUsage():
		metric.MemUsage = m.Value
	}
}

func debugText(msg string){
	log.Debugf("%s\n", msg)
}

// below are defined for debug only
var deQueueCount int = 0
var sendToChanCount int = 0
var recvChanCount int = 0
var doneHandleCount int = 0

func writePermToChan(){
	if config.IsDebug(){
		log.Debugf("lanuch writePermToChan to dequeue\n")
	}
	for{
		err,permEntry := permQueue.DeQueue()
		if err == nil && permEntry != nil{
			if config.IsDebug(){
				deQueueCount++
				log.Debugf("dequeue: %+v\n", *permEntry)
				debugText(fmt.Sprintf("deQueueCount:%d", deQueueCount))
			}
			// 拷贝
			newEntry := *permEntry
			newDeviceChan <- &newEntry
			if config.IsDebug(){
				sendToChanCount++
				debugText(fmt.Sprintf("sendToChanCount:%d", sendToChanCount))
				log.Debugf("done to write into newDeviceChan: %+v\n", newEntry)
			}
			// sendToChanCount++
			// if (sendToChanCount % 1000 == 0){
			// 	fmt.Printf("sendToChanCount:%d\n", sendToChanCount)
			// }
		}else{
			if config.IsDebug(){
				log.Debugf("dequeue error: %+v\n", err)
			}
			//如果没有数据，则睡眠2ms
			time.Sleep(100 * time.Millisecond)
		}
	}
}

func UpdateDevicePermData(m *PermMetric){
	if config.IsDebug(){
		log.Debugf("enqueue: %+v\n", *m)
	}
	//将性能数据加入队列，通知消费队列取数据
	err := permQueue.EnQueue(m)
	if err != nil{
		log.Debugf("get err: %+v\n", err)
	}
}

//用从kafka中获取的性能数据更新到最终的数据结构中
func handleDevicePermDataFromChan(){
	for m:=range newDeviceChan{
		if config.IsDebug(){
			log.Debugf("get data from chan: %+v\n", *m)
			recvChanCount++
			debugText(fmt.Sprintf("recvChanCount:%d", recvChanCount))
		}
		id := m.ID
		//log.Infof("get data from kafka 1: %+v\n", m)
		v,ok := allMetrics.LoadOrStore(id, &ResourceMetric{})
		if !ok{
			//新记录，进行处理
			notifyNewEntry(id)
		}
		metric := v.(*ResourceMetric)
		updateDeviceMetric(m, metric)
		//log.Infof("get data from kafka 2: %+v\n", metric)

		v,ok = allMetrics.LoadOrStore(id, &ResourceMetric{})
		// cmdb1 := GetDeviceCMDBById(id);
        // log.Infof("Get perm data. cmdb: %+v\n", cmdb1)

		// if(cmdb1 == nil){
		// 	log.Errorf("get cmdb for id %s error. cmdb is nil.\n", id)
		// }else{
		// 	if(cmdb1.RPId != "6d40d847-90a7-11e9-bb30-0242ac110002"){
		// 		log.Infof("OHHHHHHHHH.Device metric received.Get rp id from cmdb: %s\n", cmdb1.RPId)
		// 	}else{
		// 		log.Infof("Device metric received.Get rp id from cmdb: %s\n", cmdb1.RPId)
		// 	}
		// }
		if config.IsDebug(){
			log.Debugf("done with device data: %+v\n", *metric)
			doneHandleCount++
			debugText(fmt.Sprintf("doneHandleCount:%d", doneHandleCount))
		}
		// doneHandleCount++
		// if (doneHandleCount % 1000 == 0){
		// 	fmt.Printf("doneHandleCount:%d\n", doneHandleCount)
		// }
	}
}

func notifyNewEntry(devId string){
	UpdateDeviceCMDB(devId)
	UpdateAlertScore(devId)
}

////返回所有指标数据（引用地址，不会进行数据拷贝）
//func GetAllDeviceMetricsMap() IdToMetric {
//	return allMetrics
//}
/////每次Prometheus请求所有指标数据时，先复制全局设备指标，再清空该指标
////every time Prometheus calls me to do collector, reset this map and make a clean start
//func ResetAllMetrics(){
//	allMetrics = make(IdToMetric)
//}

func clearOldPerms(keys []string){
	for i:=0; i<len(keys); i++{
		allMetrics.Delete(keys[i])
	}
}

func RestoreAllPermData()IdToMetricMap{
	newMap := make(IdToMetricMap)
	idsToDelete := make([]string, 0)
	allMetrics.Range(func(key, value interface{}) bool {
		// cast value to correct format
		val, ok := value.(*ResourceMetric)
		if !ok {
			// skip the entry
			return true
		}
		k := key.(string)
		newMap[k] = val
		idsToDelete = append(idsToDelete, k)
		return true
	})
	go func() {
		log.Debugln("launch a new go-routine to clean old perm data")
		clearOldPerms(idsToDelete)
	}()
	return newMap
}
