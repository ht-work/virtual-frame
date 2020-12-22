package metric

//
//import (
//	"encoding/json"
//	"exporter/config"
//	. "exporter/httptool"
//	"fmt"
//	"net/http"
//	"net/http/httptest"
//	"testing"
//)
//
//var appList ResourceList
//var appMap map[string]*AppInfo
//
//func prepareHttpServer()*httptest.Server{
//	appList = ResourceList{
//		&Resource{
//			ID:   "12",
//			Name: "国际业务支撑系统一期",
//		},
//		&Resource{
//			ID:   "13",
//			Name: "物联网CMIOT系统",
//		},
//	}
//	tenant := "te2"
//	rp := "rp1"
//	appMap = map[string]*AppInfo{
//		"12": &AppInfo{
//			BMAssigned: 40,
//			BMQuota:    60,
//			ID:       appList[0].ID,
//			Name:     appList[0].Name,
//			Tenant:   tenant,
//			RP:       rp,
//		},
//		"13": &AppInfo{
//			BMAssigned: 15,
//			BMQuota: 20,
//			VMAssigned: 30,
//			VMQuota:    40,
//			ID:       appList[1].ID,
//			Name:     appList[1].Name,
//			Tenant:   tenant,
//			RP:       rp,
//		},
//	}
//	ts := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
//		_ = r.ParseForm()
//		itemType := r.Form.Get("type")
//		itemId := r.Form.Get("id")
//		w.WriteHeader(http.StatusOK)
//		w.Header().Set("Content-Type", "application/json")
//		var infoInBytes []byte
//		if itemId != ""{
//			//query app by id
//			app,_ := appMap[itemId]
//			infoInBytes,_ = json.Marshal(*app)
//		}else if itemType == "App"{
//			//query app list
//			infoInBytes,_ = json.Marshal(appList)
//		}else{
//			fmt.Printf("unsupported item type: %+v\n", itemType)
//		}
//		w.Write(infoInBytes)
//	}))
//	return ts
//}
//
//
//func TestGetAppMetrics(t *testing.T) {
//	//mock http server
//	ts := prepareHttpServer()
//	defer ts.Close()
//
//	load_conf()
//	mock_url(config.GetListQueryKey(), ts.URL)
//	mock_url(config.GetItemQueryKey(), ts.URL)
//
//	list,err := GetAppMetrics()
//
//	res := len(list) == len(appList)
//	res = res && (list[0].AssignRatio == (list[0].BMAssigned/list[0].BMQuota *100) )
//	res = res && (list[1].AssignRatio == ( (list[1].BMAssigned+list[1].VMAssigned)/(list[1].BMQuota+list[1].VMQuota) *100) )
//	if !res || err != nil{
//		t.Errorf("error in GetAppMetrics: %+v\n", err)
//	}
//}
