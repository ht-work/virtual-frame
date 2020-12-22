package service

import (
	"github.com/jinzhu/gorm"
	"iaas/model"
	"iaas/pkgs/database"
)

type ResourceService struct {
	*database.DbService
	Device database.DbService
}

func (d *ResourceService) FindAll() *gorm.DB {
	res := d.DB.Find(&model.Resource{})
	return res
}

func (d *ResourceService) FindOne() {

}

func (d *ResourceService) Update() {

}

func (d *ResourceService) Delete() {

}

func (d *ResourceService) Add() {

}
