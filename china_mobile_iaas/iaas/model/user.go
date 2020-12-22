package model

type User struct {
	ID     int `gorm:"column:id;not null;primary_key"`
	Name   string `gorm:"column:name;not null" json:"username"`
	Passwd string `gorm:"column:password;not null" json:"password"`
}

func (*User) TableName() string {
	return `tb_user`
}