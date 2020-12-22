package database

import (
	"fmt"
	"github.com/jinzhu/gorm"
	_ "github.com/jinzhu/gorm/dialects/mysql"
	"iaas/model"
	"iaas/pkgs/config"
)

var DelTable = false

type DbService struct {
	Conn   *gorm.DB
	Config *config.Config
}

var (
	DBConn *DbService = &DbService{}
	log               = config.Log
)

func init() {
	DBConn.Config = config.Conf
	if err := DBConn.Init(); err != nil {
		log.Info("open database failed", err)
		log.Panic(err)
	}
	DBConn.Conn.AutoMigrate(&model.Resource{})
	//DBConn.Conn.AutoMigrate(&model.IdcType{})
	DBConn.Conn.AutoMigrate(&model.BizSysQuota{})
	//DBConn.Conn.AutoMigrate(&model.BizSys{})
	//DBConn.Conn.AutoMigrate(&model.Tenant{})
	DBConn.Conn.AutoMigrate(&model.User{})
	DBConn.Conn.AutoMigrate(&model.Alert{})

	if DelTable {
		DBConn.Conn.DropTable(&model.Resource{})
		//DBConn.Conn.DropTable(&model.IdcType{})
		//DBConn.Conn.DropTable(&model.BizSys{})
		DBConn.Conn.DropTable(&model.BizSysQuota{})
		//DBConn.Conn.DropTable(&model.Tenant{})
		DBConn.Conn.DropTable(&model.User{})
	}

	if !DBConn.Conn.HasTable(&model.Resource{}) {
		DBConn.Conn.CreateTable(&model.Resource{})
	}

	if !DBConn.Conn.HasTable(&model.Alert{}) {
		DBConn.Conn.CreateTable(&model.Alert{})
	}

	if !DBConn.Conn.HasTable(&model.User{}) {
		DBConn.Conn.CreateTable(&model.User{})
	}

	//if !DBConn.Conn.HasTable(&model.IdcType{}) {
	//	DBConn.Conn.CreateTable(&model.IdcType{})
	//}
	//
	//if !DBConn.Conn.HasTable(&model.Tenant{}) {
	//	DBConn.Conn.CreateTable(&model.Tenant{})
	//}
	//
	//if !DBConn.Conn.HasTable(&model.BizSys{}) {
	//	DBConn.Conn.CreateTable(&model.BizSys{})
	//}

	if !DBConn.Conn.HasTable(&model.BizSysQuota{}) {
		DBConn.Conn.CreateTable(&model.BizSysQuota{})
	}
	defaultUser()
	log.Infoln("init db ok")
}

func (d *DbService) Init() error {
	dbConf := d.Config.Database
	var err error

	dsn := dsn(&dbConf)
	d.Conn, err = gorm.Open(dbConf.Driver, dsn)

	if err != nil {
		return err
	}

	d.Conn.DB().SetMaxIdleConns(dbConf.MaxIdleConnCount)
	d.Conn.DB().SetMaxOpenConns(100)
	d.Conn.DB().SetConnMaxIdleTime(50)
	//if dbConf.MaxConnLifeTime != 0 {
	//	d.Conn.DB().SetConnMaxLifetime(time.Duration(dbConf.MaxConnLifeTime))
	//}

	return nil
}

func dsn(dbConf *config.DatabaseConfig) string {
	return fmt.Sprintf("%s:%s@%s(%s:%s)/%s?charset=utf8mb4&parseTime=True&loc=Local", dbConf.User, dbConf.Passwd, dbConf.Network, dbConf.Host, dbConf.Port, dbConf.Db)
}

func defaultUser() {
	var user model.User
	var e error
	user.Name = "admin"
	user.Passwd = "WVdSdGFXND0="
	user.ID = 1

	count := 0
	e = DBConn.Conn.Model(&model.User{}).Where(&model.User{Name: user.Name}).Count(&count).Error

	if count > 0 {
		e = DBConn.Conn.Model(&model.User{}).Delete(&user).Error
	}

	e = DBConn.Conn.Model(&model.User{}).Create(&user).Error

	if e != nil {
		log.Error("init user failed")
		log.Fatal(e)
	}
}
