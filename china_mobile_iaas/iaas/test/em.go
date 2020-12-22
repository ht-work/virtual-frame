package test

import (
	"fmt"
	"github.com/gin-gonic/gin"
	"github.com/jinzhu/gorm"
	_ "github.com/jinzhu/gorm/dialects/mysql"
)

type Product struct {
	Id int
	Code string
}

func main() {
	dsn := fmt.Sprintf("%s:%s@%s(%s:%s)/%s", "root", "root", "tcp", "172.23.5.87", "3306", "iaas")
	db, err := gorm.Open("mysql", dsn)
	if err != nil {
		panic(err)
	}
	defer db.Close()

	if ! db.HasTable(&Product{}) {
		db.CreateTable(&Product{})
	}

	db.Create(&Product{Code: "L11001",Id: 1})

	p := db.First(&Product{})
	fmt.Println(*p)

	gin.New()
	gin.Default()
}
