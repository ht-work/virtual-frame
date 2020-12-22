package rest

import (
	"errors"
	"iaas/pkgs/config"
	"io/ioutil"
	"net/http"
	"strings"
)

type ReqData struct {
	Token      string `json:"token"`                  //认证token
	CondCode   string `json:"condicationCode"`        //查询配置编码
	PageSize   int    `json:"pageSize,omitempty"`     //每页记录数, 默认100
	CurPage    int    `json:"currentPage,omitempty"`  //当前页数, 默认1
	DevType    string `json:"device_type,omitempty"`  //设备类型
	IdcType    string `json:"idcType,omitempty"`      //资源池
	PodName    string `json:"pod_name,omitempty"`     //POD池名称
	Ip         string `json:"ip,omitempty"`           //管理IP地址
	Dept1      string `json:"department1,omitempty"`  //一级部门
	Dept2      string `json:"department2,omitempty"`  //二级部门
	BizSystem  string `json:"bizSystem,omitempty"`    //业务系统
	IdcCabinet string `json:"idc_cabinet,omitempty"`  //所属机柜
	UNum       string `json:"u_num,omitempty"`        //U位
	RoomId     string `json:"roomId,omitempty"`       //所属机房
	DevMfrs    string `json:"device_mfrs,omitempty"`  //设备品牌
	DevModel   string `json:"device_model,omitempty"` //设备型号
}

func NewReqData(r *ReqData) *ReqData {
	if r.CondCode == "" {
		r.CondCode = CondicationCiSearch
	}
	if r.PageSize == 0 {
		r.PageSize = 100
	}
	if r.CurPage == 0 {
		r.CurPage = 1
	}
	if r.Token == "" {
		r.Token = GetToken()
	}
	return r
}

func GetToken() string {
	return config.Conf.Token
}

func Post(url string, data string) []byte {
	log.Debug("post data:", data)
	body, err := httpDo("POST", url, data)
	if err != nil {
		log.Errorln(err)
	}
	//log.Println(string(body))
	return body
}

func Get(url string, param string) {
	body, err := httpDo("GET", url, param)
	log.Println(body, err)
}

func httpDo(method string, url string, data string) ([]byte, error) {
	client := &http.Client{}

	req, err := http.NewRequest(method, url, strings.NewReader(data))
	if err != nil {
		log.Errorln("http request make err:", err)
		return nil, err
	}

	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Connection", "keep-alive")
	req.Header.Set("Accept", "application/json")
	req.Header.Set("head_orgAccount", "alauda")
	req.Header.Set("head_userName", "alauda")
	req.Header.Set("head_isAdmin", "true")
	req.Header.Set("head_isSuperUser", "true")

	log.Debugln("post url:", url, "post header:", req.Header)
	resp, err := client.Do(req)
	if err != nil {
		log.Errorln(err)
		log.Panic(err)
	}

	defer resp.Body.Close()

	var body []byte
	if resp.StatusCode != 200 {
		log.Errorf("http request got err code: %d, msg: %s\n", resp.StatusCode,resp.Status)
		body = []byte{}
		return body, errors.New("http request err")
	}

	body, err = ioutil.ReadAll(resp.Body)
	if err != nil {
		log.Errorln("http request get err:", err)
		return nil, err
	}

	return body, nil
	//fmt.Println(string(body))
}
