/*
各种指标计算的算法实现
 */

package algo

import (
	"exporter/config"
	. "exporter/models"
	"math"
	//"fmt"
)

const FLOAT_ZERO_VALUE float64 = 0.00001

const MAX_ALERT_SCORE int64 = 100
func CalculateDeviceHealth(alertStat *StatAlert)int64{
	weight := config.GetAlertWeight()
	var alertScore int64 = 0
	alertScore += alertStat.Urgent * weight.Urgent
	alertScore += alertStat.Important * weight.Important
	alertScore += alertStat.Secondary * weight.Secondary
	alertScore += alertStat.Normal * weight.Normal
	if alertScore >= MAX_ALERT_SCORE {
		alertScore = MAX_ALERT_SCORE
	}
	return MAX_ALERT_SCORE - alertScore
}

func GetBusy(cpuUsage float64, memUsage float64)float64{
	return (cpuUsage + memUsage) / 2
}

func GetUnbalance(cpuUsage float64, memUsage float64)float64{
	return math.Abs(cpuUsage - memUsage)
}

//计算不可用，如果健康度分值为0，则不可用，该值为true；否则为false
func GetUnavailable(healthScore float64)float64{
	var res float64
	res = 0
	if healthScore <= FLOAT_ZERO_VALUE {
		res = 1
	}
	return res
}

func GetAssignRatio(assigned float64, quota float64)float64{
	if quota <= FLOAT_ZERO_VALUE {
		//in this case, quota metric is NOT collected
		return 0
	}else{
		//fmt.Printf("assign: %f, quota: %f, assign_ratio: %f \n", assigned, quota, math.Min(100, 100 * assigned / quota));
		return math.Min(100, 100 * assigned / quota )
	}
}

func GetAppAssignRatio(am *AppMetric)float64{
	used := am.Used
	quota := am.Quota
	return GetAssignRatio(used.VM + used.BM, quota.VM + quota.BM)
}
