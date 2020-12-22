package web

import (
	"encoding/json"
	"exporter/collector/device"
	. "exporter/models"
	"fmt"
	"io/ioutil"
	"net/http"
	"strings"
)

//handle the performance data from kafka
type PerfHandler struct{}

func (h *PerfHandler) ServeHTTP(w http.ResponseWriter, req *http.Request) {
	//build up the data with post body
	if strings.ToLower(req.Method)  == "post"{
		b,err := ioutil.ReadAll(req.Body)
		if err != nil{
			//invalid bytes from request body
			fmt.Printf("invalid bytes from request body %+v\n", err)
			return
		}
		var m PermMetric
		err = json.Unmarshal(b, &m)
		if err != nil{
			//invalid data format
			fmt.Printf("invalid data format %+v\n", err)
			return
		}
		device.HandleMetricFromKafka(&m)
		w.Header().Set("Content-type", "application/json; charset=utf-8")
		w.WriteHeader(http.StatusOK)
	}else{
		//do nothing
		str := "unsupported method(only post is allowed for this URI)"
		//w.Header().Set("Content-type", "application/json; charset=utf-8")
		w.WriteHeader(http.StatusBadRequest)
		_, _ = w.Write([]byte(str))
	}
}
