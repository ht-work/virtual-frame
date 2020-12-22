package database

import (
	"iaas/model"
)

func (d *DbService) CreateOrUpdateResource(m *model.Resource) {
	//d.Conn.Model(m).Where(model.Resource{DeviceId: m.DeviceId}).FirstOrCreate(&m)
	var e error

	if d.IsExistResource(m) {
		e = d.Conn.Model(m).Updates(m).Error
	} else {
		e = d.Conn.Model(m).Create(m).Error
	}

	if e != nil {
		log.Warnln(e)
	}
}

func (d *DbService) CreateOrUpdateBiz(m *model.BizSys) {
	count := 0
	e := d.Conn.Model(&model.BizSys{}).Where(&model.BizSys{BizSysId: m.BizSysId}).Count(&count).Error
	if e != nil {
		log.Warnln("db error")
	}
	if count == 0 {
		d.Conn.Model(&model.BizSys{}).Create(&m)
	} else {
		d.Conn.Model(m).Updates(&m)
	}
}

func (d *DbService) DelResource(m *model.Resource) {
	if d.IsExistResource(m) {
		d.Conn.Model(m).Delete(m)
	}
}

func (d *DbService) AddResource(m *model.Resource) {
	if d.IsExistResource(m) {
		return
	}
	if err := d.Conn.Model(m).Create(m); err != nil {
		log.Errorln("create recode err:", err)
	}
}

func (d *DbService) CreateOrUpdateIdc(m *model.IdcType) {
	count := 0
	e := d.Conn.Model(model.IdcType{}).Where(&model.IdcType{IdcId: m.IdcId}).Count(&count).Error
	if e != nil {
		log.Warnln("db err:", e)
		return
	}

	if count > 0 {
		d.Conn.Model(model.IdcType{}).Delete(&model.IdcType{IdcId: m.IdcId})
	}

	if e := d.Conn.Model(model.IdcType{}).Create(&m).Error; e != nil {
		log.Warnln("create resource pool fail", e)
	}
}

func (d *DbService) DelIdc(m *model.IdcType) {
	count := 0
	e := d.Conn.Model(model.IdcType{}).Where(&model.IdcType{IdcId: m.IdcId}).Count(&count).Error
	if e != nil {
		log.Warnln("db err:", e)
		return
	}

	if count > 0 {
		d.Conn.Model(model.IdcType{}).Delete(&model.IdcType{IdcId: m.IdcId})
	}
}

func (d *DbService) UpdateBizSys(m *model.BizSys) {
	if d.IsExistResource(m) {
		d.Conn.Model(m).Update(m)
		return
	} else {
		result := d.Conn.Model(m).Create(m)
		if result.Error != nil {
			log.Errorln("insert db err:", result.Error)
			return
		}
	}
}

func (d *DbService) DelBizSys(m *model.BizSys) {
	if d.IsExistResource(m) {
		d.Conn.Model(m).Delete(m)
	}
}

//func (d *DbService) CreateOrUpdateTenant(m *model.Tenant) {
//	count := 0
//	e := d.Conn.Model(model.Tenant{}).Where(&model.Tenant{TenantId: m.TenantId}).Count(&count).Error
//	if e != nil {
//		log.Warnln("db err:", e)
//		return
//	}
//
//	if count > 0 {
//		d.Conn.Model(model.Tenant{}).Delete(&model.Tenant{TenantId: m.TenantId})
//	}
//
//	if e := d.Conn.Model(model.Tenant{}).Create(&m).Error; e != nil {
//		log.Warnln("create tenant fail", e)
//	}
//}

//func (d *DbService) DelTenant(m *model.Tenant) {
//	if d.IsExistResource(m) {
//		d.Conn.Model(m).Delete(m)
//	}
//}

func (d *DbService) CreateOrUpdateBizSysQuota(m *model.BizSysQuota) {
	count := 0
	e := d.Conn.Model(model.BizSysQuota{}).Where(&model.BizSysQuota{BizSysId: m.BizSysId}).Count(&count).Error
	if e != nil {
		log.Warnln("db err:", e)
		return
	}

	if count > 0 {
		d.Conn.Model(model.BizSysQuota{}).Delete(&model.BizSysQuota{BizSysId: m.BizSysId})
	}

	if e := d.Conn.Model(model.BizSysQuota{}).Create(&m).Error; e != nil {
		log.Warnln("create business quota fail", e)
	}
}

func (d *DbService) AddAlert(m *model.Alert) {
	d.Conn.Model(model.Alert{}).Create(&m)
	//if !d.AlertExist(m) {
	//	if result := d.Conn.Model(m).Create(&m); result.Error != nil {
	//		log.Warnln("create alert recode [%s] err [%s]", m.AlertId, result.Error)
	//	}
	//}
}

func (d *DbService) UpdateAlert(m *model.Alert) {
	d.Conn.Model(model.Alert{}).Delete(model.Alert{DevId: m.DevId})
	d.Conn.Model(model.Alert{}).Create(&m)
	//if d.AlertExist(m) {
	//	if err := d.Conn.Model(m).Where(model.Alert{AlertId: m.AlertId}).Updates(&m).Error; err != nil {
	//		log.Errorf("update alert recode [%s] err [%s]", m.AlertId, err)
	//		log.Errorf("alert value:", *m)
	//	}
	//}
}

func (d *DbService) AlertExist(m *model.Alert) bool {
	count := 0
	if err := d.Conn.Model(m).Where(&model.Alert{AlertId: m.AlertId}).Count(&count).Error; err != nil {
		log.Errorf("count alert recode [%s] err [%s]", m.AlertId, err)
	}

	return count > 0
}

func (d *DbService) DelAlert(m *model.Alert) {
	if !d.AlertExist(m) {
		return
	}

	if e := d.Conn.Model(m).Delete(&model.Alert{}, m.AlertId).Error; e != nil {
		log.Warnln("del alert recode [%s] err [%s]", m.AlertId, e)
	}
}

func (d *DbService) IsExistResource(m interface{}) bool {
	count := 0

	if v, ok := m.(*model.Resource); ok {
		result := d.Conn.Model(&model.Resource{}).Where(&model.Resource{DeviceId: v.DeviceId}).Count(&count)

		if result.Error != nil {
			log.Errorln("connect db err:", result.Error)
		}

		return count > 0
	}

	if v, ok := m.(*model.IdcType); ok {
		return d.Conn.Model(m).Where(v.IdcId).RowsAffected > 0
	}
	if v, ok := m.(*model.BizSys); ok {
		return d.Conn.Model(m).Where(v.BizSysId).RowsAffected > 0
	}
	//if v, ok := m.(*model.Tenant); ok {
	//	return d.Conn.Model(m).Where(v.TenantId).RowsAffected > 0
	//}

	return false
}

func (d *DbService) IsValidUser(m *model.User) bool {
	count := 0
	result := d.Conn.Model(&model.User{}).Where(&m).Count(&count)

	if result.Error != nil {
		log.Warnln("query user in db failed.", result.Error)
		return false
	}
	return count == 1
}

func (d *DbService) GetAllList(m *model.Resource) (list []model.Resource) {
	result := d.Conn.Where(&m).Find(&list)

	if result.Error != nil {
		log.Errorln("retrieve all list failed:", result.Error)
	}

	return list
}

func (d *DbService) GetBizSysList(m *model.Resource) (list []model.Resource) {
	result := d.Conn.Raw("select distinct biz_sys, biz_sys_name from tb_resource").Scan(&list)

	if result.Error != nil {
		log.Errorln(result.Error)
	}

	return list
}

func (d *DbService) GetResourceById(id string) (res model.Resource) {
	result := d.Conn.Model(&model.Resource{}).Debug().Where(&model.Resource{DeviceId: id}).Scan(&res)

	if result.Error != nil {
		log.Errorln("retrieve resource failed:", result.Error)
	}

	return res
}
func (d *DbService) GetResourceByIds(m []string) (list []model.Resource) {
	result := d.Conn.Model(&model.Resource{}).Debug().Where("device_id in (?)", m).Scan(&list)

	if result.Error != nil {
		log.Errorln("retrieve resource failed:", result.Error)
	}

	return list
}

func (d *DbService) GetAllResources() (list []model.Resource) {
	result := d.Conn.Model(&model.Resource{}).Debug().Scan(&list)
	if result.Error != nil {
		log.Errorln("retrieve resource failed:", result.Error)
	}
	return list
}

func (d *DbService) GetTenantList(m *model.Resource) (list []model.Resource) {
	result := d.Conn.Raw("select distinct dept2, dept2_name from tb_resource").Scan(&list)

	if result.Error != nil {
		log.Errorln(result.Error)
	}

	return list
}

func (d *DbService) GetIdcList(m *model.Resource) (list []model.Resource) {
	result := d.Conn.Raw("select distinct idc_type, idc_type_name from tb_resource").Scan(&list)

	if result.Error != nil {
		log.Errorln(result.Error)
	}

	return list
}

func (d *DbService) CountAlert(m *model.Resource) int {
	count := 0
	if result := d.Conn.Where(&m).Count(&count); result.Error != nil {
		log.Errorln("count alert err:", result.Error)
	}

	return count
}

func (d *DbService) GetLatestAlert(n int) (list []model.Alert) {
    sqlstr := `SELECT alert_id, source, a.dev_id, dev_type, a.idc_type_name idc_type_name, a.biz_sys biz_sys, moni_object, moni_index, cur_moni_time, cur_mon_value,
	item_id, start_time, end_time, alert_level, r.device_ip dev_ip ,r.device_name dev_name
	FROM tb_alert a left join tb_resource r on a.dev_id=r.device_id ORDER BY cur_moni_time desc LIMIT ?;`;
	result := d.Conn.Raw(sqlstr, n).Scan(&list);
	if result.Error != nil {
		log.Errorln(result.Error)
	}
	return list
}
