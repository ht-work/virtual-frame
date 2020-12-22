package httptool

import (
	"testing"
)

const AppList string = "appList"

func TestQueryAppList(t *testing.T) {
	//resourceList := ResourceQuotaList{
	//	&ResourceQuota{
	//		ID:     "app1",
	//		Name:   "业务系统1",
	//		BM:     "12",
	//		Yy:     "4",
	//		Fxx:    "4",
	//		Fbs:    "4",
	//		Hcx:    "0",
	//		Gdyy:   "0",
	//		Djd:    "0",
	//		VM:     "0",
	//		VMVcpu: "0",
	//		VMMem:  "0",
	//	},
	//	&ResourceQuota{
	//		ID:     "app2",
	//		Name:   "业务系统2",
	//		BM:     "0",
	//		Yy:     "0",
	//		Fxx:    "0",
	//		Fbs:    "0",
	//		Hcx:    "0",
	//		Gdyy:   "0",
	//		Djd:    "0",
	//		VM:     "845",
	//		VMVcpu: "10724",
	//		VMMem:  "48256",
	//	},
	//}
	//ts := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
	//	w.WriteHeader(http.StatusOK)
	//	w.Header().Set("Content-Type", "application/json")
	//	infoInBytes,_ := json.Marshal(resourceList)
	//	w.Write(infoInBytes)
	//}))
	//defer ts.Close()
	//
	//mock_url(AppList, ts.URL)
	//
	//resList,_ := QueryAppList()
	//res := (resList != nil && len(resList) == 2 && resList[0].ID == resourceList[0].ID &&
	//	resList[1].VM == resourceList[1].VM)
	//if !res{
	//	t.Errorf("error in QueryAppList\n")
	//}
}
