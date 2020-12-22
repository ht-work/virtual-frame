package device

//import (
//	. "exporter/models"
//	"testing"
//)
//
//func TestHandleMetricFromKafka(t *testing.T) {
//	perm := PermMetric{
//		ID:    "5f8c5a9f92e243bea11215f0631639d4",
//		Name:  "pm_realtime_cpu_avg_util_percent_percent_avg",
//		Type:  "",
//		Time:  1588986300,
//		Value: 3.1415926,
//	}
//	HandleMetricFromKafka(&perm)
//
//	permMap := RestoreAllPermData()
//	metric,_ := permMap[perm.ID]
//	res := metric.ID == perm.ID && metric.CPUUsage == perm.Value
//	if !res{
//		t.Errorf("error in HandleMetricFromKafka\n")
//	}
//}
