package rest

import (
	"encoding/json"
	"iaas/model"
	"iaas/pkgs/config"
	"iaas/pkgs/database"
)

var (
	listUrl   = config.Conf.ListUrl
	detailUrl = config.Conf.DetailUrl
	log       = config.Log
)

const (
	CondicationCiSearch       string = "htyw_ci_search"
	CondicationIdcSearch      string = "htyw_idc_search"
	CondicationTenantSearch   string = "htyw_org_search"
	CondicationBizSearch      string = "htyw_business_search"
	CondicationBizQuotaSearch string = "htyw_business_quota_search"
)

func GetAllCmdbRecode() {
	var (
		ch = make(chan *model.Resource)
	)

	for devType, _ := range model.DevTypeMap {
		getCmdb(ch, devType)
		getCmdb(ch, devType)
	}
	close(ch)
}

func getCmdb(ch chan *model.Resource, devType string) {
	var (
		err     error
		reqData []byte
		fr      = &model.FullCmdbResp{}
		r       = NewReqData(&ReqData{PageSize: 100, DevType: devType})
		//ch      = make(chan *model.Resource)
	)

	reqData, err = json.Marshal(r)
	if err != nil {
		log.Errorln("err:", err)
	}

	fr = &model.FullCmdbResp{}
	if err = json.Unmarshal(Post(listUrl, string(reqData)), fr); err != nil {
		log.Errorln(err)
	}

	go func() {
		for m := range ch {
			database.DBConn.CreateOrUpdateResource(m)
		}
		log.Info("get all cmdb resource done.")
	}()

	totalPage := fr.Count/r.PageSize + 1

	for ; r.CurPage <= totalPage; r.CurPage++ {
		reqData, err := json.Marshal(r)
		if err != nil {
			log.Errorln("err:", err)
		}

		if err = json.Unmarshal(Post(listUrl, string(reqData)), fr); err != nil {
			log.Errorln(err)
		}

		for _, d := range fr.Data {
			m := model.Resource{
				DeviceId:     d.DeviceId,
				DeviceName:   d.DeviceName,
				DeviceIP:     d.Ip,
				DeviceType:   d.DeviceType,
				BizSys:       d.BizSys,
				Dept1:        d.Dept1,
				Dept2:        d.Dept2,
				Dept1Name:    d.Dept1Name,
				Dept2Name:    d.Dept2Name,
				IdcType:      d.IdcType,
				IdcTypeName:  d.IdcTypeName,
				DevTypeName:  d.DevTypeName,
				NodeTypeName: d.NodeTypeName,
				CpuCoreNum:   d.CpuCoreNum,
				CpuNum:       d.CpuNum,
				MemSize:      d.MemSize,
			}
			ch <- &m
		}
		log.Infof("page %d of total page %d", r.CurPage, totalPage)
	}
}

func GetAllBizSystem() {
	var (
		reqByte []byte
		err     error
		fb      = &model.FullBizResp{}
		ch      = make(chan *model.BizSys)
	)
	r := ReqData{CondCode: CondicationBizSearch}
	req := NewReqData(&r)

	if reqByte, err = json.Marshal(req); err != nil {
		log.Errorln(err)
	}

	if err = json.Unmarshal(Post(listUrl, string(reqByte)), fb); err != nil {
		log.Errorln(err)
	}

	go func() {
		for m := range ch {
			database.DBConn.CreateOrUpdateBiz(m)
		}
		log.Info("get all business done.")
	}()

	totalPage := fb.Count/r.PageSize + 1
	for ; r.CurPage <= totalPage; r.CurPage++ {
		log.Infof("page %d of total page %d", r.CurPage, totalPage)
		reqByte, err = json.Marshal(r)
		if err != nil {
			log.Errorln("err:", err)
		}
		if err = json.Unmarshal(Post(listUrl, string(reqByte)), fb); err != nil {
			log.Errorln(err)
		}
		for _, d := range fb.Data {
			m := model.BizSys{
				BizSysId:   d.BizSysId,
				BizSysName: d.BizSysName,
			}
			ch <- &m
		}
	}
	close(ch)
}

func GetAllIdcType() {
	var (
		reqByte []byte
		err     error
		fb      = &model.FullIdc{}
		ch      = make(chan *model.IdcType)
	)
	r := ReqData{CondCode: CondicationIdcSearch}
	req := NewReqData(&r)

	if reqByte, err = json.Marshal(req); err != nil {
		log.Errorln(err)
	}

	if err = json.Unmarshal(Post(listUrl, string(reqByte)), fb); err != nil {
		log.Errorln(err)
	}

	go func() {
		for m := range ch {
			database.DBConn.CreateOrUpdateIdc(m)
		}
		log.Info("get all idc done.")
	}()

	totalPage := fb.Count/r.PageSize + 1
	for ; r.CurPage <= totalPage; r.CurPage++ {
		//log.Infof("page %d of total page %d", r.CurPage, totalPage)
		reqByte, err = json.Marshal(r)
		if err != nil {
			log.Errorln("err:", err)
		}
		if err = json.Unmarshal(Post(listUrl, string(reqByte)), fb); err != nil {
			log.Errorln(err)
		}
		for _, d := range fb.Data {
			ch <- &d
		}
	}
	close(ch)
}

//func GetAllTenant() {
//	var (
//		reqByte []byte
//		err     error
//		fb      = &model.FullTenant{}
//		ch      = make(chan *model.Tenant)
//	)
//	r := ReqData{CondCode: CondicationTenantSearch}
//	req := NewReqData(&r)
//
//	if reqByte, err = json.Marshal(req); err != nil {
//		log.Errorln(err)
//	}
//
//	if err = json.Unmarshal(Post(listUrl, string(reqByte)), fb); err != nil {
//		log.Errorln(err)
//	}
//
//	go func() {
//		for m := range ch {
//			database.DBConn.CreateOrUpdateTenant(m)
//		}
//		log.Info("get all tenant done.")
//	}()
//	totalPage := fb.Count/r.PageSize + 1
//	for ; r.CurPage <= totalPage; r.CurPage++ {
//		//log.Infof("page %d of total page %d", r.CurPage, totalPage)
//		reqByte, err = json.Marshal(r)
//		if err != nil {
//			log.Errorln("err:", err)
//		}
//		if err = json.Unmarshal(Post(listUrl, string(reqByte)), fb); err != nil {
//			log.Errorln(err)
//		}
//		for _, d := range fb.Data {
//			ch <- &d
//		}
//	}
//	close(ch)
//}

func GetBizQuota() {
	var (
		reqByte []byte
		err     error
		fb      = &model.FullBizQuotaResp{}
		ch      = make(chan *model.BizSysQuota)
	)
	r := ReqData{CondCode: CondicationBizQuotaSearch}
	req := NewReqData(&r)

	if reqByte, err = json.Marshal(req); err != nil {
		log.Errorln(err)
	}

	if err = json.Unmarshal(Post(listUrl, string(reqByte)), fb); err != nil {
		log.Errorln(err)
	}

	totalPage := fb.Count/r.PageSize + 1
	log.Info("total page ", totalPage)
	go func() {
		for m := range ch {
			database.DBConn.CreateOrUpdateBizSysQuota(m)
		}
		log.Info("get all business quota done.")
	}()

	for ; r.CurPage <= totalPage; r.CurPage++ {
		//log.Infof("page %d of total page %d", r.CurPage, totalPage)
		reqByte, err = json.Marshal(r)
		if err != nil {
			log.Errorln("err:", err)
		}
		if err = json.Unmarshal(Post(listUrl, string(reqByte)), fb); err != nil {
			log.Errorln(err)
		}
		for _, d := range fb.Data {
			ch <- &d
		}
	}
	close(ch)
}
