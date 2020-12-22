package device

import (
	// "exporter/collector/algo"
	// "exporter/config"
	// . "exporter/httptool"
	// "fmt"
	"sync"
)

// deviceId -> alertScore
var allAlertScore sync.Map//map[string]int64
var deviceAlertScoreMu sync.Mutex

func init(){
	//allAlertScore = make(map[string]int64)
}

const ALERT_SCORE_NOT_EXIST int64 = -1

func UpdateAlertScore(devId string){
	score := _getDeviceScoreById(devId)
	if score == ALERT_SCORE_NOT_EXIST {
		//fetch the CMDB data from net
		// stat,err := QueryAlertStat(devId)
		// if err == nil {
		// 	score := algo.CalculateDeviceHealth(stat)
			// if config.IsDebug(){
			// 	debugText(fmt.Sprintf("device alert info: %+v and score: %d\n", *stat, score))
			// }
		// 	_updateAlertScore(devId, score)
		// }
		var score int64 = 0
		score = 100
		_updateAlertScore(devId, score)
	}
}

func _updateAlertScore(devId string, score int64){
	//deviceAlertScoreMu.Lock()
	//allAlertScore[devId] = score
	//deviceAlertScoreMu.Unlock()
	allAlertScore.Store(devId, score)
}

func _getDeviceScoreById(devId string)int64{
	score,ok := allAlertScore.Load(devId)
	if ok {
		return score.(int64)
	} else {
		return ALERT_SCORE_NOT_EXIST
	}
}

func clearOldAlerts(keys []string){
	for i:=0; i<len(keys); i++{
		allAlertScore.Delete(keys[i])
	}
}

func RestoreAllAlertScore()map[string]int64{
	//deviceAlertScoreMu.Lock()
	//newMap := allAlertScore
	//allAlertScore = make(map[string]int64)
	//deviceAlertScoreMu.Unlock()
	//return newMap
	newMap := make(map[string]int64)
	idsToDelete := make([]string, 0)
	allAlertScore.Range(func(key, value interface{}) bool {
		// cast value to correct format
		val, ok := value.(int64)
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
		log.Debugln("launch a new go-routine to clean old alerts")
		clearOldAlerts(idsToDelete)
	}()
	return newMap
}
