//  Copyright 2020 The HTZG. All rights reserved.
//

package web

import (
	"encoding/json"
	"fmt"
	"github.com/gin-gonic/gin"
	"iaas/model"
	"iaas/pkgs/config"
	"iaas/pkgs/database"
	"net/http"
	"net/http/httputil"
	_ "os"
	_ "path/filepath"
	"strconv"
	"strings"
)

var log = config.Conf.GetLogger()

type App struct {
	*gin.Engine
	*database.DbService
	*config.Config
}

func (p *App) Start() {
	p.Engine = gin.Default()
	p.Engine.Use(gin.Logger())
	p.Engine.Use(gin.Recovery())

	p.setupRoute()
	p.Run(p.Config.ListenAddr)
}

func (p *App) setupRoute() {
	//http.Handle("/", http.FileServer(http.Dir("E:\\iaas\\dist")))
	//p.Engine.Static("/dist", http.Dir("E:\\iaas\\dist"))

	//p.Engine.StaticFile("/index.html", ".E:\\iaas\\dist\\index.html")
	// pwd, _ := os.Getwd()

	// p.Engine.StaticFS("/s", http.Dir(filepath.Join(pwd, "dist")))
	p.Engine.StaticFS("/s", http.Dir("/etc/iaas/dist"))
	p.Engine.POST("/login", p.Login)

	apiV1 := p.Engine.Group("/api/v1/")
	if config.TestMode == config.PRODUCT {
		apiV1.Use(MiddleWareAuth())
	}
	{
		apiV1.POST("/changePassword", p.ChangePasswd)
		apiV1.GET("/device/:id", p.GetTargetCMDB) //根据resourceID查询配置信息
		apiV1.GET("/devices", p.ListCMDB)         //根据ids列表查询配置信息
		apiV1.GET("/apps", p.ListQuotaByBizSys)   //查询所有业务系统
		apiV1.GET("/app/:id", p.GetAppDetailById)
		apiV1.GET("/stat/app", p.GetTotalResourceByBizSys)

		apiV1.GET("/tenant/:id", p.GetTenantDetailById) //根据ID查租户详情
		apiV1.GET("/tenants", p.ListQuotaByTenant)      //查询所有租户
		apiV1.GET("/rps", p.ListQuotaByIdc)             //查询所有资源池及配额信息
		apiV1.GET("/stat/rps", p.ListTotalResourceByIdc)
		apiV1.GET("/stat/rp", p.GetTotalResource)         //查询资源总量
		apiV1.GET("/rp/:id", p.GetResourcePoolDetailById) //根据ID查资源池
		//apiV1.GET("/Alert/:dev_id", p.ListAlertByDevId)         //根据device id查询告警信息
		apiV1.GET("/stat/alert", p.ListAlertByLevel) //统计不同告警级别条目(全部告警)
		apiV1.GET("/alerts", p.ListTopAlert)         //获取最近N条告警记录

		apiV1.GET("/query", p.Forward)
		apiV1.GET("/query_range", p.ForwardRange)

		//apiV1.GET("/bizSys/:id", p.GetTargetBizSys)        //根据ID查询业务系统
		//apiV1.GET("/tenant/:id", p.GetTargetTenant)        //根据ID查询租户
		//apiV1.GET("/resourcePool/:id", p.GetTargetResPool) //根据ID查询资源池
	}
}

var devicesMap model.IdToDevice

//后续可以做缓存，以快速返回需要读取的数据，暂时还没用上
func init() {
	fmt.Printf("start to init all devices...\n")
	list := database.DBConn.GetAllResources()
	for i := 0; i < len(list); i++ {
		currentData := list[i]
		devicesMap.LoadOrStore(currentData.Id, currentData)
		if i%1000 == 0 {
			fmt.Printf("load device data :%d\n", i)
		}
	}
	fmt.Printf("init all devices done.\n")
}

func (p *App) GetTargetCMDB(c *gin.Context) {
	deviceId := c.Param("id")

	if deviceId == "" {
		c.JSON(http.StatusBadRequest, ParameterError("source id must not null"))
		c.Abort()
		return
	}

	newEntry := database.DBConn.GetResourceById(deviceId)
	c.JSON(http.StatusOK, newEntry)

	//后续可以做缓存
	// v,ok := devicesMap.LoadOrStore(deviceId, &model.Resource{})
	// if !ok{
	//     //新记录，进行数据库查询
	//     fmt.Printf("returned 1 v: %+v\n", v)
	//     newEntry := database.DBConn.GetResourceById(deviceId)
	//     devicesMap.LoadOrStore(deviceId, newEntry)
	//     fmt.Printf("returned 1: %+v\n", newEntry)
	//     c.JSON(http.StatusOK, newEntry)
	// }else{
	//     result := v.(*model.Resource)
	//     fmt.Printf("returned 2: %+v\n", result)
	//     c.JSON(http.StatusOK, result)
	// }
}

func (p *App) ListCMDB(c *gin.Context) {
	//idArr := c.QueryArray("ids")
	var (
		e      error
		idArry []string
	)

	idstr := c.DefaultQuery("ids", "[]")
	e = json.Unmarshal([]byte(idstr), &idArry)
	if e != nil {
		c.JSON(http.StatusBadRequest, ParameterError("param err"))
		c.Abort()
		return
	}

	c.JSON(http.StatusOK, database.DBConn.GetResourceByIds(idArry))
}

func (p *App) ListQuotaByBizSys(c *gin.Context) {
	//param := make(map[string]int)
	//data, _ := ioutil.ReadAll(c.Request.Body)
	//_ = json.Unmarshal(data, &param)

	var (
		pageNo   int
		total    int64
		pageSize = 10
		e        error
		idArry   []string
		list     []model.BizSysQuota
	)
	sqlAll := `select owner_biz_sys biz_sys_id, idc_type, dept2, owner_biz_sys, owner_biz_sys_name,dept2_name, sum(allocate_ljs) as allocate_ljs,
sum(allocate_yyfwq) as allocate_yyfwq, sum(allocate_fxxfwq) as allocate_fxxfwq,
sum(allocate_fbsfwq) as allocate_fbsfwq, sum(allocate_hcxfwq) as allocate_hcxfwq,
sum(allocate_gdyyfwq) as allocate_gdyyfwq, sum(allocate_djdfwq) as allocate_djdfwq,
sum(allocate_yzj) as allocate_yzj, sum(allocate_yzj_vcpu) as allocate_yzj_vcpu,
sum(allocate_yzj_mem) as allocate_yzj_mem
from tb_biz_sys_quota group by idc_type, dept2, owner_biz_sys, owner_biz_sys_name, dept2_name;`

	sqlstr := `select owner_biz_sys biz_sys_id, idc_type, owner_biz_sys, owner_biz_sys_name,dept2_name, sum(allocate_ljs) as allocate_ljs,
sum(allocate_yyfwq) as allocate_yyfwq, sum(allocate_fxxfwq) as allocate_fxxfwq,
sum(allocate_fbsfwq) as allocate_fbsfwq, sum(allocate_hcxfwq) as allocate_hcxfwq,
sum(allocate_gdyyfwq) as allocate_gdyyfwq, sum(allocate_djdfwq) as allocate_djdfwq,
sum(allocate_yzj) as allocate_yzj, sum(allocate_yzj_vcpu) as allocate_yzj_vcpu,
sum(allocate_yzj_mem) as allocate_yzj_mem
from tb_biz_sys_quota where owner_biz_sys_name like ? group by idc_type, dept2, owner_biz_sys, owner_biz_sys_name, dept2_name limit ?, ?;`

	countstr := `select count(owner_biz_sys) count_data from
    (select owner_biz_sys
        from tb_biz_sys_quota
        where owner_biz_sys_name like ?
        group by idc_type, dept2, owner_biz_sys, owner_biz_sys_name, dept2_name) subquery;`

	sqlstrByids := `select owner_biz_sys biz_sys_id, idc_type, owner_biz_sys, owner_biz_sys_name, dept2_name, sum(allocate_ljs) as allocate_ljs,
sum(allocate_yyfwq) as allocate_yyfwq, sum(allocate_fxxfwq) as allocate_fxxfwq,
sum(allocate_fbsfwq) as allocate_fbsfwq, sum(allocate_hcxfwq) as allocate_hcxfwq,
sum(allocate_gdyyfwq) as allocate_gdyyfwq, sum(allocate_djdfwq) as allocate_djdfwq,
sum(allocate_yzj) as allocate_yzj, sum(allocate_yzj_vcpu) as allocate_yzj_vcpu,
sum(allocate_yzj_mem) as allocate_yzj_mem
from tb_biz_sys_quota where owner_biz_sys in (?) group by idc_type, dept2,owner_biz_sys, owner_biz_sys_name, dept2_name;`

	_, hasPage := c.GetQuery("pageNo")
	_, hasName := c.GetQuery("name")
	_, hasIds := c.GetQuery("ids")

	if !hasPage && !hasName && !hasIds {
		e = database.DBConn.Conn.Debug().Raw(sqlAll).Scan(&list).Error
		if e != nil {
			log.Errorln(e)
			c.JSON(http.StatusNotAcceptable, UnknownError("db err"))
			c.Abort()
			return
		}
		c.JSON(http.StatusOK, list)
		c.Abort()
		return
	}

	pageNostr := c.DefaultQuery("pageNo", "1")
	namestr := c.DefaultQuery("name", "")
	idstr := c.DefaultQuery("ids", "")
	e = json.Unmarshal([]byte(idstr), &idArry)

	nameCondi := "%"
	if namestr != "" {
		nameCondi = fmt.Sprintf("%%%s%%", namestr)
	}

	pageNo, _ = strconv.Atoi(pageNostr)

	//start := int((pageNo - 1) * pageSize)
	//var raw *gorm.DB
	db := database.DBConn.Conn.Model(&model.BizSysQuota{}).Debug()
	if idArry == nil || len(idArry) == 0 {
		//db.Where("owner_biz_sys like ?", nameCondi).Count(&total)
		var count model.CountData
		db.Raw(countstr, nameCondi).Scan(&count)
		total = count.Count
		e = db.Raw(sqlstr, nameCondi, (pageNo-1)*pageSize, pageSize).Scan(&list).Error
	} else {
		e = db.Raw(sqlstrByids, idArry).Scan(&list).Error
	}

	if e != nil {
		log.Infoln(e)
	}

	//if e != nil {
	//	log.Errorln(e)
	//	c.JSON(http.StatusNotAcceptable, UnknownError("db err"))
	//	c.Abort()
	//	return
	//}

	c.JSON(http.StatusOK, gin.H{
		"data":     list,
		"total":    total,
		"pageNo":   pageNo,
		"pageSize": pageSize,
	})
}

func (p *App) ListQuotaByTenant(c *gin.Context) {
	//param := make(map[string]int)
	//data, _ := ioutil.ReadAll(c.Request.Body)
	//_ = json.Unmarshal(data, &param)
	var (
		pageNo   int
		total    int64
		pageSize = 10
		e        error
		idArry   []string
		list     []model.BizSysQuota
	)

	sqlAll := `select dept2 biz_sys_id, dept1_name, dept2, dept2_name, sum(allocate_ljs) as allocate_ljs,
            sum(allocate_yyfwq) as allocate_yyfwq, sum(allocate_fxxfwq) as allocate_fxxfwq,
            sum(allocate_fbsfwq) as allocate_fbsfwq, sum(allocate_hcxfwq) as allocate_hcxfwq,
            sum(allocate_gdyyfwq) as allocate_gdyyfwq, sum(allocate_djdfwq) as allocate_djdfwq,
            sum(allocate_yzj) as allocate_yzj, sum(allocate_yzj_vcpu) as allocate_yzj_vcpu,
            sum(allocate_yzj_mem) as allocate_yzj_mem
        from tb_biz_sys_quota group by dept1_name, dept2, dept2_name;`

	sqlstr := `select dept2 biz_sys_id, dept1_name, dept2, dept2_name, sum(allocate_ljs) as allocate_ljs,
            sum(allocate_yyfwq) as allocate_yyfwq, sum(allocate_fxxfwq) as allocate_fxxfwq,
            sum(allocate_fbsfwq) as allocate_fbsfwq, sum(allocate_hcxfwq) as allocate_hcxfwq,
            sum(allocate_gdyyfwq) as allocate_gdyyfwq, sum(allocate_djdfwq) as allocate_djdfwq,
            sum(allocate_yzj) as allocate_yzj, sum(allocate_yzj_vcpu) as allocate_yzj_vcpu,
            sum(allocate_yzj_mem) as allocate_yzj_mem
        from tb_biz_sys_quota
        where dept2_name like ?
        group by dept1_name,dept2,dept2_name limit ?, ?;`

	countstr := `select count(dept2) count_data from
                (select dept2
                    from tb_biz_sys_quota
                    where dept2_name like ?
                    group by dept1_name, dept2, dept2_name) subquery;`

	sqlstrByids := `select dept2 biz_sys_id, dept1_name, dept2, dept2_name, sum(allocate_ljs) as allocate_ljs,
            sum(allocate_yyfwq) as allocate_yyfwq, sum(allocate_fxxfwq) as allocate_fxxfwq,
            sum(allocate_fbsfwq) as allocate_fbsfwq, sum(allocate_hcxfwq) as allocate_hcxfwq,
            sum(allocate_gdyyfwq) as allocate_gdyyfwq, sum(allocate_djdfwq) as allocate_djdfwq,
            sum(allocate_yzj) as allocate_yzj, sum(allocate_yzj_vcpu) as allocate_yzj_vcpu,
            sum(allocate_yzj_mem) as allocate_yzj_mem
        from tb_biz_sys_quota where dept2 in (?) group by dept1_name, dept2,dept2_name;`

	_, hasPage := c.GetQuery("pageNo")
	_, hasName := c.GetQuery("name")
	idstr, hasIds := c.GetQuery("ids")
	if !hasPage && !hasName && !hasIds {
		e = database.DBConn.Conn.Debug().Raw(sqlAll).Scan(&list).Error
		if e != nil {
			log.Errorln(e)
			c.JSON(http.StatusNotAcceptable, UnknownError("db err"))
			c.Abort()
			return
		}
		c.JSON(http.StatusOK, list)
		c.Abort()
		return
	} else {
		pageNostr := c.DefaultQuery("pageNo", "1")
		pageNo, _ = strconv.Atoi(pageNostr)
		namestr := c.DefaultQuery("name", "")

		nameCondi := "%"
		if namestr != "" {
			nameCondi = fmt.Sprintf("%%%s%%", namestr)
		}

		var counts []model.CountData

		db := database.DBConn.Conn.Model(&model.BizSysQuota{}).Debug()
		start := int((pageNo - 1) * pageSize)
		if !hasIds {
			db.Raw(countstr, nameCondi).Scan(&counts)
			total = counts[0].Count
			e = db.Raw(sqlstr, nameCondi, start, int(pageSize)).Scan(&list).Error
		} else {
			e = json.Unmarshal([]byte(idstr), &idArry)
			e = db.Raw(sqlstrByids, idArry).Scan(&list).Error
			//既然指定了id，数量就是id的数量
			total = int64(len(list))
		}
		if e != nil {
			log.Errorln(e)
			c.JSON(http.StatusNotAcceptable, UnknownError("db err"))
			c.Abort()
			return
		}
		c.JSON(http.StatusOK, gin.H{
			"data":     list,
			"total":    total,
			"pageNo":   pageNo,
			"pageSize": pageSize,
		})
	}
}

func (p *App) ListQuotaByIdc(c *gin.Context) {
	var list []model.BizSysQuota

	sqlstr := `select idc_type, idc_type_name, sum(allocate_ljs) as allocate_ljs,
            sum(allocate_yyfwq) as allocate_yyfwq, sum(allocate_fxxfwq) as allocate_fxxfwq,
            sum(allocate_fbsfwq) as allocate_fbsfwq, sum(allocate_hcxfwq) as allocate_hcxfwq,
            sum(allocate_gdyyfwq) as allocate_gdyyfwq, sum(allocate_djdfwq) as allocate_djdfwq,
            sum(allocate_yzj) as allocate_yzj, sum(allocate_yzj_vcpu) as allocate_yzj_vcpu,
            sum(allocate_yzj_mem)
        from tb_biz_sys_quota group by idc_type,idc_type_name;`
	result := database.DBConn.Conn.Debug().Raw(sqlstr).Scan(&list)
	if result.Error != nil {
		log.Fatalln(result.Error)
	}

	c.JSON(http.StatusOK, list)
}

type ListTotalResByIdcResp struct {
	Id          string  `gorm:"column:idc_type" json:"id"`
	Name        string  `gorm:"column:idc_type_name" json:"name"`
	TenantCount int64   `gorm:"column:tenantCount" json:"tenantCount"` //租户数量
	AppCount    int64   `gorm:"column:appCount" json:"appCount"`       //业务系统数量
	BM          int64   `gorm:"column:BM" json:"BM"`                   //裸金属总数
	VM          int64   `gorm:"column:VM" json:"VM"`                   //云主机总数
	PM          int64   `gorm:"column:PM" json:"PM"`                   //物理服务器
	VCpu        float64 `gorm:"column:VCPU" json:"VCpu"`               //
	MEM         float64 `gorm:"column:MEM" json:"MEM"`
}

func (p *App) ListTotalResourceByIdc(c *gin.Context) {
	var (
		res []ListTotalResByIdcResp
		e   error
	)

	db := database.DBConn.Conn.Model(&model.Resource{}).Debug()

	//db.Where(&model.Resource{DeviceType: DevTypeVser, BizSys: id}).Count(&res.VM)
	//db.Where(&model.Resource{BizSys: id, DeviceType: DevTypeX86ser, NodeTypeName: NodeTypeBm}).Count(&res.BM)
	//db.Where(&model.Resource{BizSys: id, DeviceType: DevTypeX86ser, NodeTypeName: NodeTypeKVM}).Count(&res.PM)

	//resource := model.Resource{}

	sqlstr := `select idc_type, idc_type_name, count(distinct dept2) as tenantCount, count(distinct biz_sys) as appCount, sum(if(device_type!='f5f6b15cc48a43a1b02467f0bfcfbeae', cpu_core_num * cpu_num, 0)) as VCPU,
     sum(mem_size)/1024/1024 as MEM, count(device_type=? OR NULL) as VM,
count(device_type=? AND node_type_name=? OR NULL) as BM, count(device_type=? AND node_type_name=? OR NULL) as PM
from tb_resource group by idc_type, idc_type_name;`
	//`select distinct(idc_type), idc_type_name from tb_resource where `
	e = db.Raw(sqlstr, DevTypeVser, DevTypeX86ser, NodeTypeBm, DevTypeX86ser, NodeTypeKVM).Scan(&res).Error

	if e != nil {
		log.Errorln(e)
		c.JSON(http.StatusBadRequest, ParameterError("param err"))
		c.Abort()
		return
	}
	//res.VCpu, _ = strconv.ParseFloat(resource.CpuCoreNum, 64)
	//res.MEM, _ = strconv.ParseFloat(resource.MemSize, 64)

	c.JSON(http.StatusOK, res)
}

func (p *App) ListAlertByLevel(c *gin.Context) {
	type Resp struct {
		Level string `gorm:"level"`
		Count string `gorm:"count"`
	}
	id, hasId := c.GetQuery("id")

	resp := make([]Resp, 0)
	if hasId {
		_ = database.DBConn.Conn.Debug().Model(&model.Alert{}).Select("dev_id,alert_level as level, count(*) as count").Where("dev_id=?", id).Group("alert_level,dev_id").Scan(&resp)
	} else {
		_ = database.DBConn.Conn.Debug().Model(&model.Alert{}).Select("alert_level as level, count(*) as count").Group("alert_level").Scan(&resp)
	}

	r := make(map[string]int)
	for _, v := range resp {
		count, _ := strconv.Atoi(v.Count)
		r[v.Level] = count
	}

	c.JSON(http.StatusOK, r)
}

func (p *App) ListTopAlert(c *gin.Context) {
	var (
		e   error
		num int
	)

	numStr, hasNum := c.GetQuery("limit")
	if !hasNum {
		c.JSON(http.StatusBadRequest, ParameterError("param err"))
		c.Abort()
		return
	}

	num, e = strconv.Atoi(numStr)
	if e != nil {
		log.Errorln(e)
		c.JSON(http.StatusBadRequest, ParameterError("param must be int type"))
		c.Abort()
		return
	}

	c.JSON(http.StatusOK, database.DBConn.GetLatestAlert(num))
}

func (p *App) CreateOrUpdateResource(c *gin.Context) {
	p.DbService = database.DBConn
	resource := &model.Resource{}
	if err := c.ShouldBindJSON(resource); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	r := p.Conn.First(&model.Resource{}, resource.DeviceId)
	fmt.Println(r.RowsAffected)
	fmt.Println(resource)
	switch r.RowsAffected {
	case 0:
		p.Conn.Model(&model.Resource{}).Create(resource)
	case 1:
		p.Conn.Model(&model.Resource{}).Updates(resource)
	}

	c.JSON(http.StatusOK, gin.H{"msg": "ok"})
}

// func (p *App) GetQuotaByBizSys(c *gin.Context) {
//     bizSysId := c.Param("id")

//     if bizSysId == "" {
//         c.JSON(http.StatusBadRequest, ParameterError("biz sys id must not null"))
//         c.Abort()
//         return
//     }
//     resource := model.BizSysQuota{}
//     sqlstr := `select biz_sys_id, owner_biz_sys, sum(allocate_ljs) as allocate_ljs,
//         sum(allocate_yyfwq) as allocate_yyfwq,
//          sum(allocate_fxxfwq) as allocate_fxxfwq, sum(allocate_fbsfwq) as allocate_fbsfwq,
//         sum(allocate_hcxfwq) as allocate_hcxfwq, sum(allocate_gdyyfwq) as allocate_gdyyfwq,
//         sum(allocate_djdfwq) as allocate_djdfwq, sum(allocate_yzj) as allocate_yzj,
//         sum(allocate_yzj_vcpu) as allocate_yzj_vcpu, sum(allocate_yzj_mem) as allocate_yzj_mem
//         from tb_biz_sys_quota where biz_sys_id=? group by biz_sys_id, owner_biz_sys;`
//     e := database.DBConn.Conn.Raw(sqlstr, bizSysId).Scan(&resource).Error
//     if e != nil {
//         log.Errorln(e)
//         c.JSON(http.StatusNotAcceptable, UnknownError("db err"))
//         c.Abort()
//         return
//     }

//     c.JSON(http.StatusOK, resource)
// }

func (p *App) GetAppDetailById(c *gin.Context) {
	bizSysId := c.Param("id")

	if bizSysId == "" {
		c.JSON(http.StatusBadRequest, ParameterError("biz sys id must not null"))
		c.Abort()
		return
	}
	//第一步：在配额表里查出应用系统的基本信息
	baseInfoSqlStr := `select owner_biz_sys, owner_biz_sys_name, dept1, dept1_name, dept2, dept2_name, idc_type, idc_type_name
    from tb_biz_sys_quota where owner_biz_sys=? group by dept1, dept1_name, dept2, dept2_name, idc_type, idc_type_name, owner_biz_sys, owner_biz_sys_name;`
	baseInfos := []model.BizBaseInfo{}
	e := database.DBConn.Conn.Raw(baseInfoSqlStr, bizSysId).Scan(&baseInfos).Error
	if e != nil {
		log.Errorln(e)
		c.JSON(http.StatusBadRequest, ParameterError("param err or id not found[base info]"))
		c.Abort()
		return
	}
	if len(baseInfos) == 0 {
		c.JSON(http.StatusBadRequest, ParameterError("param err or id not found. baseInfos is empty"))
		c.Abort()
		return
	}

	var bizSysDetail = model.BizSysDetail{}
	bizSysDetail.BizSysId = baseInfos[0].BizSys
	bizSysDetail.BizSysName = baseInfos[0].BizSysName
	bizSysDetail.Dept1 = ""
	bizSysDetail.Dept1Name = ""
	bizSysDetail.Dept2 = ""
	bizSysDetail.Dept2Name = ""
	bizSysDetail.IdcType = ""
	bizSysDetail.IdcTypeName = ""
	//对于一个业务系统，可能对应多个二级部门、一级部门以及多个资源池，拼接起来
	for i := 0; i < len(baseInfos); i++ {
		bizBaseInfo := baseInfos[i]
		if !containsKey(&bizSysDetail.Dept1, &bizBaseInfo.Dept1) {
			bizSysDetail.Dept1 = bizSysDetail.Dept1 + bizBaseInfo.Dept1 + ","
		}
		if !containsKey(&bizSysDetail.Dept1Name, &bizBaseInfo.Dept1Name) {
			bizSysDetail.Dept1Name = bizSysDetail.Dept1Name + bizBaseInfo.Dept1Name + ","
		}
		if !containsKey(&bizSysDetail.Dept2, &bizBaseInfo.Dept2) {
			bizSysDetail.Dept2 = bizSysDetail.Dept2 + bizBaseInfo.Dept2 + ","
		}
		if !containsKey(&bizSysDetail.Dept2Name, &bizBaseInfo.Dept2Name) {
			bizSysDetail.Dept2Name = bizSysDetail.Dept2Name + bizBaseInfo.Dept2Name + ","
		}
		if !containsKey(&bizSysDetail.IdcType, &bizBaseInfo.IdcType) {
			bizSysDetail.IdcType = bizSysDetail.IdcType + bizBaseInfo.IdcType + ","
		}
		if !containsKey(&bizSysDetail.IdcTypeName, &bizBaseInfo.IdcTypeName) {
			bizSysDetail.IdcTypeName = bizSysDetail.IdcTypeName + bizBaseInfo.IdcTypeName + ","
		}
	}

	bizSysDetail.Dept1 = strings.Trim(bizSysDetail.Dept1, ",")
	bizSysDetail.Dept1Name = strings.Trim(bizSysDetail.Dept1Name, ",")
	bizSysDetail.Dept2 = strings.Trim(bizSysDetail.Dept2, ",")
	bizSysDetail.Dept2Name = strings.Trim(bizSysDetail.Dept2Name, ",")
	bizSysDetail.IdcType = strings.Trim(bizSysDetail.IdcType, ",")
	bizSysDetail.IdcTypeName = strings.Trim(bizSysDetail.IdcTypeName, ",")

	fmt.Printf("bizsys detail 1: %+v \n", bizSysDetail)

	//第二步：在资源表中查询出资源使用情况（云主机、裸金属、CPU、内存）
	var resourceBizSysBaseInfo = model.ResourceBizSysBaseInfo{}
	usedDataSqlStr := `select biz_sys, sum(if(device_type!='f5f6b15cc48a43a1b02467f0bfcfbeae', cpu_core_num * cpu_num, 0)) as VCPU,
    sum(mem_size)/1024/1024 as MEM, count(device_type='f5f6b15cc48a43a1b02467f0bfcfbeae' OR NULL) as VM,
count(device_type='85a802f297a24b2e9c9ec58dd15846b7' AND node_type_name='计算节点' OR NULL) as BM, count(device_type='85a802f297a24b2e9c9ec58dd15846b7' AND node_type_name='宿主机' OR NULL) as PM
from tb_resource where biz_sys=? group by biz_sys;`
	e = database.DBConn.Conn.Raw(usedDataSqlStr, bizSysDetail.BizSysId).Scan(&resourceBizSysBaseInfo).Error
	bizSysDetail.VmCount = resourceBizSysBaseInfo.VM
	bizSysDetail.VcpuCount = resourceBizSysBaseInfo.VCPU
	bizSysDetail.MemCount = resourceBizSysBaseInfo.MEM
	bizSysDetail.BmCount = resourceBizSysBaseInfo.BM

	fmt.Printf("bizsys detail 2: %+v \n", bizSysDetail)

	c.JSON(http.StatusOK, bizSysDetail)
}

// func (p *App) GetQuotaByTenant(c *gin.Context) {
//     tenantId := c.Param("id")

//     if tenantId == "" {
//         c.JSON(http.StatusBadRequest, ParameterError("tenant id must not null"))
//         c.Abort()
//         return
//     }
//     resource := model.BizSysQuota{}
//     sqlstr := `select dept2, dept2_name, sum(allocate_ljs) as allocate_ljs,
//         sum(allocate_yyfwq) as allocate_yyfwq,
//          sum(allocate_fxxfwq) as allocate_fxxfwq, sum(allocate_fbsfwq) as allocate_fbsfwq,
//         sum(allocate_hcxfwq) as allocate_hcxfwq, sum(allocate_gdyyfwq) as allocate_gdyyfwq,
//         sum(allocate_djdfwq) as allocate_djdfwq, sum(allocate_yzj) as allocate_yzj,
//         sum(allocate_yzj_vcpu) as allocate_yzj_vcpu, sum(allocate_yzj_mem) as allocate_yzj_mem
//         from tb_biz_sys_quota where dept2=? group by dept2, dept2_name;`

//     e := database.DBConn.Conn.Raw(sqlstr, tenantId).Scan(&resource).Error
//     if e != nil {
//         log.Errorln(e)
//         c.JSON(http.StatusBadRequest, ParameterError("param err or id not found[quota info]"))
//         c.Abort()
//         return
//     }
//     baseInfoSqlStr := `select dept1, dept1_name, dept2, dept2_name, idc_type, idc_type_name, count(distinct owner_biz_sys) app_count
//     from tb_biz_sys_quota where dept2=? group by dept1, dept1_name, dept2, dept2_name, idc_type, idc_type_name;`
//     baseInfos := []model.BizBaseInfo{};
//     e = database.DBConn.Conn.Raw(baseInfoSqlStr, tenantId).Scan(&baseInfos).Error
//     if e != nil {
//         log.Errorln(e)
//         c.JSON(http.StatusBadRequest, ParameterError("param err or id not found[base info]"))
//         c.Abort()
//         return
//     }
//     if(len(baseInfos) == 0){
//         c.JSON(http.StatusBadRequest, ParameterError("param err or id not found. baseInfos is empty"))
//         c.Abort()
//         return
//     }

//     var tenantDetail = model.TenantQuotaDetail{}

//     tenantDetail.TenantId = resource.Dept2
//     tenantDetail.AppCount = 0
//     tenantDetail.Dept1 = ""
//     tenantDetail.Dept1Name = ""
//     tenantDetail.Dept2 = resource.Dept2
//     tenantDetail.Dept2Name = resource.Dept2Name
//     tenantDetail.IdcType = ""
//     tenantDetail.IdcTypeName = ""
//     tenantDetail.YzjAllocate, e = strconv.ParseInt(resource.YzjAllocate, 10, 64)
//     tenantDetail.YzjVcpuAllocate, e = strconv.ParseInt(resource.YzjVcpuAllocate, 10, 64)
//     tenantDetail.YzjMemAllocate, e = strconv.ParseInt(resource.YzjMemAllocate, 10, 64)
//     tenantDetail.LjsAllocate, e = strconv.ParseInt(resource.LjsAllocate, 10, 64)

//     fmt.Printf("tenant detail 1: %+v \n", tenantDetail)
//     fmt.Printf("base infos: %+v \n", baseInfos)

//     for i:=0; i<len(baseInfos); i++{
//         bizBaseInfo := baseInfos[i]
// 		if(!containsKey(&tenantDetail.Dept1, &bizBaseInfo.Dept1)){
//             tenantDetail.Dept1 = tenantDetail.Dept1 + bizBaseInfo.Dept1 + ","
//         }
//         if(!containsKey(&tenantDetail.Dept1Name, &bizBaseInfo.Dept1Name)){
//             tenantDetail.Dept1Name = tenantDetail.Dept1Name + bizBaseInfo.Dept1Name + ","
//         }
//         if(!containsKey(&tenantDetail.IdcType, &bizBaseInfo.IdcType)){
//             tenantDetail.IdcType = tenantDetail.IdcType + bizBaseInfo.IdcType + ","
//         }
//         if(!containsKey(&tenantDetail.IdcTypeName, &bizBaseInfo.IdcTypeName)){
//             tenantDetail.IdcTypeName = tenantDetail.IdcTypeName + bizBaseInfo.IdcTypeName + ","
//         }
//         tenantDetail.AppCount = tenantDetail.AppCount + bizBaseInfo.AppCount
//     }

//     fmt.Printf("tenant detail 2: %+v \n", tenantDetail)

//     tenantDetail.Dept1 = strings.Trim(tenantDetail.Dept1, ",");
//     tenantDetail.Dept1Name = strings.Trim(tenantDetail.Dept1Name, ",");
//     tenantDetail.IdcType = strings.Trim(tenantDetail.IdcType, ",");
//     tenantDetail.IdcTypeName = strings.Trim(tenantDetail.IdcTypeName, ",");

//     fmt.Printf("tenant detail 3: %+v \n", tenantDetail)

//     c.JSON(http.StatusOK, tenantDetail)
// }

func containsKey(wholeStr, needAddStr *string) bool {
	fmt.Printf("judge wholeStr: %s \n", *wholeStr)
	fmt.Printf("judge needAddStr: %s \n", *needAddStr)
	fmt.Printf("judge result1: %t \n", strings.Index(*wholeStr, ","+*needAddStr+",") >= 0)
	fmt.Printf("judge result2: %t \n", strings.Index(*wholeStr, *needAddStr+",") == 0)
	return strings.Index(*wholeStr, ","+*needAddStr+",") >= 0 || strings.Index(*wholeStr, *needAddStr+",") == 0
}

func (p *App) GetTenantDetailById(c *gin.Context) {
	tenantId := c.Param("id")

	if tenantId == "" {
		c.JSON(http.StatusBadRequest, ParameterError("tenant id must not null"))
		c.Abort()
		return
	}

	//第一步：在配额表里查出租户的基本信息
	baseInfoSqlStr := `select dept1, dept1_name, dept2, dept2_name, idc_type, idc_type_name, count(distinct owner_biz_sys) app_count
    from tb_biz_sys_quota where dept2=? group by dept1, dept1_name, dept2, dept2_name, idc_type, idc_type_name;`
	baseInfos := []model.BizBaseInfo{}
	e := database.DBConn.Conn.Raw(baseInfoSqlStr, tenantId).Scan(&baseInfos).Error
	if e != nil {
		log.Errorln(e)
		c.JSON(http.StatusBadRequest, ParameterError("param err or id not found[base info]"))
		c.Abort()
		return
	}
	if len(baseInfos) == 0 {
		c.JSON(http.StatusBadRequest, ParameterError("param err or id not found. baseInfos is empty"))
		c.Abort()
		return
	}

	var tenantDetail = model.TenantDetail{}
	tenantDetail.TenantId = baseInfos[0].Dept2
	tenantDetail.Dept1 = ""
	tenantDetail.Dept1Name = ""
	tenantDetail.Dept2 = baseInfos[0].Dept2
	tenantDetail.Dept2Name = baseInfos[0].Dept2Name
	tenantDetail.IdcType = ""
	tenantDetail.IdcTypeName = ""
	//对于一个租户（二级部门id），可能对应多个一级部门以及多个资源池，拼接起来
	for i := 0; i < len(baseInfos); i++ {
		bizBaseInfo := baseInfos[i]
		if !containsKey(&tenantDetail.Dept1, &bizBaseInfo.Dept1) {
			tenantDetail.Dept1 = tenantDetail.Dept1 + bizBaseInfo.Dept1 + ","
		}
		if !containsKey(&tenantDetail.Dept1Name, &bizBaseInfo.Dept1Name) {
			tenantDetail.Dept1Name = tenantDetail.Dept1Name + bizBaseInfo.Dept1Name + ","
		}
		if !containsKey(&tenantDetail.IdcType, &bizBaseInfo.IdcType) {
			tenantDetail.IdcType = tenantDetail.IdcType + bizBaseInfo.IdcType + ","
		}
		if !containsKey(&tenantDetail.IdcTypeName, &bizBaseInfo.IdcTypeName) {
			tenantDetail.IdcTypeName = tenantDetail.IdcTypeName + bizBaseInfo.IdcTypeName + ","
		}
	}

	tenantDetail.Dept1 = strings.Trim(tenantDetail.Dept1, ",")
	tenantDetail.Dept1Name = strings.Trim(tenantDetail.Dept1Name, ",")
	tenantDetail.IdcType = strings.Trim(tenantDetail.IdcType, ",")
	tenantDetail.IdcTypeName = strings.Trim(tenantDetail.IdcTypeName, ",")

	fmt.Printf("tenant detail 1: %+v \n", tenantDetail)

	//第二步：在资源表里查询出该租户的云主机、CPU、内存、裸金属的使用情况
	var resourceTenantBaseInfo = model.ResourceTenantBaseInfo{}
	usedDataSqlStr := `select dept2, dept2_name, count(distinct biz_sys) as app_count, sum(if(device_type!='f5f6b15cc48a43a1b02467f0bfcfbeae', cpu_core_num * cpu_num, 0)) as VCPU,
    sum(mem_size)/1024/1024 as MEM, count(device_type='f5f6b15cc48a43a1b02467f0bfcfbeae' OR NULL) as VM,
count(device_type='85a802f297a24b2e9c9ec58dd15846b7' AND node_type_name='计算节点' OR NULL) as BM, count(device_type='85a802f297a24b2e9c9ec58dd15846b7' AND node_type_name='宿主机' OR NULL) as PM
from tb_resource where dept2=? and dept2_name=? group by dept2, dept2_name;`
	e = database.DBConn.Conn.Raw(usedDataSqlStr, tenantDetail.Dept2, tenantDetail.Dept2Name).Scan(&resourceTenantBaseInfo).Error
	tenantDetail.VmCount = resourceTenantBaseInfo.VM
	tenantDetail.VcpuCount = resourceTenantBaseInfo.VCPU
	tenantDetail.MemCount = resourceTenantBaseInfo.MEM
	tenantDetail.BmCount = resourceTenantBaseInfo.BM
	tenantDetail.AppCount = resourceTenantBaseInfo.AppCount

	fmt.Printf("tenant detail 2: %+v \n", tenantDetail)

	c.JSON(http.StatusOK, tenantDetail)
}

// func (p *App) GetQuotaByIdc(c *gin.Context) {
//     var e error
//     idcId := c.Param("id")

//     if idcId == "" {
//         c.JSON(http.StatusBadRequest, ParameterError("resource pool id must not null"))
//         c.Abort()
//         return
//     }
//     //resource := model.Resource{IdcType: idcId}
//     //resource := model.BizSysQuota{IdcType: idcId}
//     res := model.BizSysQuota{}
//     sqlstr := `select idc_type, idc_type_name, sum(allocate_ljs) as allocate_ljs,
//         sum(allocate_yyfwq) as allocate_yyfwq,
//          sum(allocate_fxxfwq) as allocate_fxxfwq, sum(allocate_fbsfwq) as allocate_fbsfwq,
//         sum(allocate_hcxfwq) as allocate_hcxfwq, sum(allocate_gdyyfwq) as allocate_gdyyfwq,
//         sum(allocate_djdfwq) as allocate_djdfwq, sum(allocate_yzj) as allocate_yzj,
//         sum(allocate_yzj_vcpu) as allocate_yzj_vcpu, sum(allocate_yzj_mem) as allocate_yzj_mem
//         from tb_biz_sys_quota where idc_type=? group by idc_type,idc_type_name;`
//     e = database.DBConn.Conn.Raw(sqlstr, idcId).Scan(&res).Error
//     if e != nil {
//         log.Errorln(e)
//         c.JSON(http.StatusBadRequest, ParameterError("param err"))
//         c.Abort()
//         return
//     }

//     c.JSON(http.StatusOK, res)
// }

func (p *App) GetResourcePoolDetailById(c *gin.Context) {
	var e error
	idcId := c.Param("id")

	if idcId == "" {
		c.JSON(http.StatusBadRequest, ParameterError("resource pool id must not null"))
		c.Abort()
		return
	}

	//第一步：在配额表里查出资源池的基本信息
	baseInfoSqlStr := `select idc_type, idc_type_name, count(distinct owner_biz_sys) app_count, count(distinct dept2) tenant_count
    from tb_biz_sys_quota where idc_type=? group by idc_type, idc_type_name;`
	baseInfo := model.BizBaseInfo{}
	e = database.DBConn.Conn.Raw(baseInfoSqlStr, idcId).Scan(&baseInfo).Error
	if e != nil {
		log.Errorln(e)
		c.JSON(http.StatusBadRequest, ParameterError("param err or id not found[base info]"))
		c.Abort()
		return
	}

	var resourcePoolDetail = model.ResourcePoolDetail{}
	resourcePoolDetail.IdcType = baseInfo.IdcType
	resourcePoolDetail.IdcTypeName = baseInfo.IdcTypeName
	resourcePoolDetail.AppCount = baseInfo.AppCount
	resourcePoolDetail.TenantCount = baseInfo.TenantCount
	fmt.Printf("resource pool detail 1: %+v \n", resourcePoolDetail)

	//第二步：在资源表里查询出该租户的云主机、CPU、内存、裸金属的使用情况
	var resourcePoolBaseInfo = model.ResourcePoolBaseInfo{}
	usedDataSqlStr := `select idc_type, sum(if(device_type!='f5f6b15cc48a43a1b02467f0bfcfbeae', cpu_core_num * cpu_num, 0)) as VCPU,
    sum(mem_size)/1024/1024 as MEM, count(device_type='f5f6b15cc48a43a1b02467f0bfcfbeae' OR NULL) as VM,
count(device_type='85a802f297a24b2e9c9ec58dd15846b7' AND node_type_name='计算节点' OR NULL) as BM, count(device_type='85a802f297a24b2e9c9ec58dd15846b7' AND node_type_name='宿主机' OR NULL) as PM
from tb_resource where idc_type=? group by idc_type;`
	e = database.DBConn.Conn.Raw(usedDataSqlStr, resourcePoolDetail.IdcType).Scan(&resourcePoolBaseInfo).Error
	resourcePoolDetail.VmCount = resourcePoolBaseInfo.VM
	resourcePoolDetail.VcpuCount = resourcePoolBaseInfo.VCPU
	resourcePoolDetail.MemCount = resourcePoolBaseInfo.MEM
	resourcePoolDetail.BmCount = resourcePoolBaseInfo.BM
	resourcePoolDetail.PmCount = resourcePoolBaseInfo.PM

	fmt.Printf("tenant detail 2: %+v \n", resourcePoolDetail)

	c.JSON(http.StatusOK, resourcePoolDetail)
}

func (p *App) Forward(c *gin.Context) {
	promhost := fmt.Sprintf("%s%s%s", config.Conf.PromServer, ":", config.Conf.PromPort)
	targetHost := &httputil.ReverseProxy{
		Director: func(req *http.Request) {
			req.URL.Scheme = "http"
			req.URL.Host = promhost
			req.URL.Path = config.Conf.PromUri
		},
	}
	targetHost.ServeHTTP(c.Writer, c.Request)
}

func (p *App) ForwardRange(c *gin.Context) {
	promhost := fmt.Sprintf("%s%s%s", config.Conf.PromServer, ":", config.Conf.PromPort)
	targetHost := &httputil.ReverseProxy{
		Director: func(req *http.Request) {
			req.URL.Scheme = "http"
			req.URL.Host = promhost
			req.URL.Path = config.Conf.PromUriRange
		},
	}
	targetHost.ServeHTTP(c.Writer, c.Request)
}

type GetTotalResourceResp struct {
	Id      string  `json:"id"`          //数据id（业务系统id）
	Tenant  string  `json:"department2"` // 租户id
	IdcType string  `json:"idcType"`     //资源池id
	BM      int64   //裸金属总数
	VM      int64   //云主机总数
	PM      int64   //物理服务器
	VCpu    float64 //
	MEM     float64
}

/**
统计资源池总量
param:
  id
return:
  GetTotalResourceResp{}
*/
func (p *App) GetTotalResource(c *gin.Context) {
	var (
		res GetTotalResourceResp
		e   error
	)

	id := c.Query("id")
	if id == "" {
		c.JSON(http.StatusBadRequest, ParameterError("resource pool id must not null"))
		c.Abort()
		return
	}

	db := database.DBConn.Conn.Model(&model.Resource{}).Debug()
	db.Where(&model.Resource{DeviceType: DevTypeVser, IdcType: id}).Count(&res.VM)
	db.Where(&model.Resource{IdcType: id, DeviceType: DevTypeX86ser, NodeTypeName: NodeTypeBm}).Count(&res.BM)
	db.Where(&model.Resource{IdcType: id, DeviceType: DevTypeX86ser, NodeTypeName: NodeTypeKVM}).Count(&res.PM)

	resource := model.Resource{}
	sqlstr := `select idc_type, sum(cpu_core_num * cpu_num) as cpu_core_num, sum(mem_size) as mem_size
 from tb_resource where idc_type=? group by idc_type;`
	e = db.Raw(sqlstr, id).Scan(&resource).Error

	if e != nil {
		log.Errorln(e)
		c.JSON(http.StatusBadRequest, ParameterError("param err"))
		c.Abort()
		return
	}
	res.Id = resource.IdcType
	res.IdcType = resource.IdcType
	res.VCpu, _ = strconv.ParseFloat(resource.CpuCoreNum, 64)
	res.MEM, _ = strconv.ParseFloat(resource.MemSize, 64)

	c.JSON(http.StatusOK, res)
}


type GetAppResourceResp struct {
    Id   string `json:"id"` //数据id（业务系统id）
    Tenant string `json:"department2"` // 租户id
    IdcType string `json:"idcType"` //资源池id
    BM   int64   //裸金属总数
    VM   int64   //云主机总数
    PM   int64   //物理服务器
    VMVCpu float64 //
    VMMEM  float64
}

func (p *App) GetTotalResourceByBizSys(c *gin.Context) {
    var (
        res GetAppResourceResp
        e   error
    )

    appId := c.Query("id")
    if appId == "" {
        c.JSON(http.StatusBadRequest, ParameterError("biz sys id must not null"))
        c.Abort()
        return
    }

    tenantId := c.Query("tenantId")
    if tenantId == "" {
        c.JSON(http.StatusBadRequest, ParameterError("tenant id must not null"))
        c.Abort()
        return
    }

    rpId := c.Query("rpId")
    if rpId == "" {
        c.JSON(http.StatusBadRequest, ParameterError("resource pool id must not null"))
        c.Abort()
        return
    }

    sqlResult := model.ResourceBizSysBaseInfo{}

    //只有云主机才计算cpu和内存、内存除以1024是因为resource很多都是按M算的，quota都是按G算的
    sqlstr := `select a.biz_sys, VM, BM, PM, VCPU, MEM from
    (
    select biz_sys, dept2, idc_type, count(device_type='f5f6b15cc48a43a1b02467f0bfcfbeae' OR NULL) as VM, 
        count(device_type='85a802f297a24b2e9c9ec58dd15846b7' AND node_type_name='计算节点' OR NULL) as BM, 
        count(device_type='85a802f297a24b2e9c9ec58dd15846b7' AND node_type_name='宿主机' OR NULL) as PM
        from tb_resource where biz_sys=? and dept2=? and idc_type=?
        group by biz_sys, dept2, idc_type) a
    left join 
    (		
    select biz_sys, dept2, idc_type, sum(cpu_core_num * cpu_num) as VCPU, sum(mem_size)/1024 as MEM
    from tb_resource where biz_sys=? and dept2=? and idc_type=? and device_type='f5f6b15cc48a43a1b02467f0bfcfbeae' GROUP BY  biz_sys, dept2, idc_type) b
    on a.biz_sys = b.biz_sys and a.dept2 = b.dept2 and a.idc_type = b.idc_type;`

    e = database.DBConn.Conn.Raw(sqlstr, appId, tenantId, rpId, appId, tenantId, rpId).Scan(&sqlResult).Error
    if e != nil {
        log.Errorln(e)
        c.JSON(http.StatusBadRequest, ParameterError("param err"))
        c.Abort()
        return
    }
//     db := database.DBConn.Conn.Model(&model.Resource{}).Debug()
//     db.Where(&model.Resource{DeviceType: DevTypeVser, BizSys: id}).Count(&res.VM)
//     db.Where(&model.Resource{BizSys: id, DeviceType: DevTypeX86ser, NodeTypeName: NodeTypeBm}).Count(&res.BM)
//     db.Where(&model.Resource{BizSys: id, DeviceType: DevTypeX86ser, NodeTypeName: NodeTypeKVM}).Count(&res.PM)

//     resource := model.Resource{}
//     sqlstr := `select biz_sys data_id, dept2, idc_type, biz_sys, sum(cpu_core_num * cpu_num) as cpu_core_num, sum(mem_size) as mem_size 
// from tb_resource where biz_sys=? group by biz_sys, dept2, idc_type;`
//     e = db.Raw(sqlstr, id).Scan(&resource).Error

//     if e != nil {
//         log.Errorln(e)
//         c.JSON(http.StatusBadRequest, ParameterError("param err"))
//         c.Abort()
//         return
//     }
    res.Id = appId
    res.IdcType = rpId
    res.Tenant = tenantId
    res.VM = sqlResult.VM
    res.BM = sqlResult.BM
    res.PM = sqlResult.PM
    res.VMVCpu = sqlResult.VCPU
    res.VMMEM = sqlResult.MEM

    c.JSON(http.StatusOK, res)
}
