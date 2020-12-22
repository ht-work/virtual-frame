package kafka

import (
	"encoding/json"
	"iaas/model"
	"iaas/pkgs/config"
	"iaas/pkgs/database"
	"net/http"
	"strings"
	"time"
)

const (
	ChangeTypeAdd    = 1
	ChangeTypeModify = 2
	ChangeTypeDel    = 3
	AlertAdd         = 1
	AlertModify      = 2
	AlertDel         = 3
)

func UpgradeCMDB() {
	message := <-chCmdb

	d := &model.Response{}

	if err := json.Unmarshal(message.Value, d); err != nil {
		log.Errorf("msg from topic %s encode to json failed.\n", message.Topic)
	}

	if len(d.Data.PhyServer) > 0 {
		//log.Info("update physerver total", len(d.Data.PhyServer))
		for _, ph := range d.Data.PhyServer {
			if ph.ServerId == "" {
				log.Warnf("ignore msg for id is null %+v", ph)
				continue
			}
			m := model.Resource{
				DeviceId:   ph.ServerId,
				DeviceName: ph.DevName,
				DeviceIP:   ph.Ip,
				//DeviceType: model.DeviceType["PhyServer"],
				DeviceType:  ph.DevType,
				Dept1:       ph.Dept1Id,
				Dept2:       ph.Dept2Id,
				Dept1Name:   ph.Dept1Name,
				Dept2Name:   ph.Dept2Name,
				BizSys:      ph.BizSys,
				IdcType:     ph.IdcType,
				IdcTypeName: ph.IdcTypeName,
			}
			updateResource(&m, ph.ChangeType)
		}
	}

	if len(d.Data.BizSys) > 0 {
		//log.Infof("update biz sys: %+v\n", d.Data.BizSys)
		for _, d := range d.Data.BizSys {
			m := model.BizSys{
				BizSysId:   d.ResourceId,
				BizSysName: d.ResourceName,
			}
			updateBizSys(&m, d.ChangeType)
		}
	}

	if len(d.Data.VirServer) > 0 {
		//log.Infof("update virtual server: %+v\n", d.Data.VirServer)
		for _, d := range d.Data.VirServer {
			if d.Id == "" {
				continue
			}
			m := model.Resource{
				DeviceId:    d.Id,
				DeviceName:  d.DevName,
				DeviceIP:    d.Ip,
				DeviceType:  d.DevTypeId,
				BizSys:      d.BizSysId,
				IdcType:     d.IdcType,
				IdcTypeName: d.IdcName,
				Dept1:       d.Dept1Id,
				Dept2:       d.Dept2Id,
			}
			updateResource(&m, d.ChangeType)
		}
	}
}

func UpgradeAlert() {
	message := <-chAlert

	d := &model.Alert{}

	if err := json.Unmarshal(message.Value, d); err != nil {
		log.Errorf("msg from topic %s encode to json failed.\n", message.Topic)
	}

	switch d.AlertType {
	case AlertAdd:
		time.Sleep(100 * time.Millisecond)
		database.DBConn.AddAlert(d)
	case AlertModify:
		time.Sleep(100 * time.Millisecond)
		database.DBConn.UpdateAlert(d)
	case AlertDel:
		database.DBConn.DelAlert(d)
	}
}

func UpgradeMonitor() {
	message := <-chMoni

	msg := string(message.Value)
	url := config.Conf.MonitorUrl

	//log.Info(msg, url)

	postMon(msg, url)
	time.Sleep(100 * time.Millisecond)
}

func postMon(value, url string) {
	var err error

	client := &http.Client{}

	req, err := http.NewRequest("POST", url, strings.NewReader(value))
	if err != nil {
		log.Warnln("make http client err: ", err)
		return
	}

	resp, err := client.Do(req)
	if err != nil {
		log.Warnln("post to prometheus err: ", err)
		return
	}

	defer resp.Body.Close()

	if resp.StatusCode != 200 {
		log.Error("post to prometheus got failed: ", resp.Status)
	}
}

func updateResource(r *model.Resource, t int) {
	switch t {
	case ChangeTypeDel:
		database.DBConn.DelResource(r)
	default:
		database.DBConn.CreateOrUpdateResource(r)
	}
}

func updateIdc(r *model.IdcType, t int) {
	switch t {
	case ChangeTypeDel:
		database.DBConn.DelIdc(r)
	default:
		database.DBConn.CreateOrUpdateIdc(r)
	}
}

func updateBizSys(b *model.BizSys, t int) {
	switch t {
	case ChangeTypeModify:
		database.DBConn.UpdateBizSys(b)
	case ChangeTypeDel:
		database.DBConn.DelBizSys(b)
	default:
		database.DBConn.UpdateBizSys(b)
	}
}
