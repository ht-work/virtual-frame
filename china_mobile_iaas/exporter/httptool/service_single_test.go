package httptool

import (
	"encoding/json"
	"exporter/config"
	. "exporter/models"
	"fmt"
	"net/http"
	"net/http/httptest"
	"testing"
)

const DeviceDetail string = "deviceDetail"
const AlertStat string = "alertStat"

func mock_url(key string, url string){
	conf,_ := config.GetConf()
	fmt.Printf("get conf:%+v", conf)
	InitConf(conf)
	if key == DeviceDetail{
		key = config.GetDeviceDetailUrl()
	} else if key == AlertStat{
		key = config.GetAlertStatUrl()
	} else if key == AppList{
		key = config.GetAppsUrl()
	}
	SetConfAssetPropertyForUT(key, url)
}

func TestQueryDeviceCMDB(t *testing.T) {
	info := ResourceInfo{
		ID:         "1",
		DeviceType: "",
		NodeTypeName:   "计算节点",
		Type:       "",
		AppId:      "app1",
		TenantId:   "tenant1",
		RPId:       "rp1",
	}
	ts := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		w.Header().Set("Content-Type", "application/json")
		infoInBytes,_ := json.Marshal(info)
		w.Write(infoInBytes)
	}))
	defer ts.Close()

	mock_url(DeviceDetail, ts.URL)

	resInfo,_ := QueryDeviceCMDB(info.ID)
	res := (resInfo != nil && resInfo.ID == info.ID && resInfo.RPId == info.RPId)
	if !res{
		t.Errorf("error in QueryDeviceCMDB\n")
	}
}

func TestQueryAlertStat(t *testing.T) {
	info := StatAlert{
		ID:        "1",
		Urgent:    2,
		Important: 3,
		Secondary: 4,
		Normal:    5,
	}
	ts := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		w.Header().Set("Content-Type", "application/json")
		infoInBytes,_ := json.Marshal(info)
		w.Write(infoInBytes)
	}))
	defer ts.Close()

	mock_url(AlertStat, ts.URL)

	resInfo,_ := QueryAlertStat(info.ID)
	res := (resInfo != nil && resInfo.ID == info.ID && resInfo.Urgent == info.Urgent)
	if !res{
		t.Errorf("error in QueryAlertStat\n")
	}
}
